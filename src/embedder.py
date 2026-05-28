"""
Embedder Module
Creates embeddings and answers using Gemini or Perplexity APIs.
"""
import base64
import hashlib
import json
import logging
import math
import re
import time
from typing import List, Dict, Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from google import genai
from google.genai import types
import google.generativeai as legacy_genai
from openai import OpenAI

logger = logging.getLogger(__name__)


class GeminiEmbedder:
    """Create embeddings using Google's Generative AI API"""
    
    def __init__(
        self,
        api_key: str,
        model: str = "gemini-embedding-001",
        generation_model: str = "gemini-2.5-flash",
        embedding_dimension: int = 768
    ):
        """
        Initialize the embedder
        
        Args:
            api_key: Google Generative AI API key
            model: Model name for embeddings
        """
        self.api_key = api_key
        self.model = model
        self.embedding_dimension = embedding_dimension
        self.logger = logging.getLogger(__name__)
        
        # Configure Generative AI
        self.embedding_client = genai.Client(api_key=api_key)
        legacy_genai.configure(api_key=api_key)
        self.generative_model = legacy_genai.GenerativeModel(generation_model)

    def _embedding_config(self, task_type: str) -> types.EmbedContentConfig:
        kwargs = {
            "task_type": task_type,
            "output_dimensionality": self.embedding_dimension,
        }
        if task_type == "RETRIEVAL_DOCUMENT":
            kwargs["title"] = "RAG Document"
        return types.EmbedContentConfig(**kwargs)
    
    def create_embedding(self, text: str, task_type: str = "RETRIEVAL_DOCUMENT") -> List[float]:
        """
        Create embedding for a single text
        
        Args:
            text: Text to embed
            task_type: Type of task (RETRIEVAL_DOCUMENT, RETRIEVAL_QUERY, etc.)
            
        Returns:
            Embedding vector as list of floats
        """
        try:
            if not text or not isinstance(text, str):
                raise ValueError("Invalid text provided for embedding")
            
            # Truncate text if too long (Gemini has limits)
            if len(text) > 10000:
                text = text[:10000]
                self.logger.warning("Text truncated to 10000 characters")
            
            response = self.embedding_client.models.embed_content(
                model=self.model,
                contents=text,
                config=self._embedding_config(task_type),
            )

            return list(response.embeddings[0].values)
            
        except Exception as e:
            self.logger.error(f"Error creating embedding: {str(e)}")
            raise
    
    def create_embeddings_batch(self, texts: List[str], 
                                task_type: str = "RETRIEVAL_DOCUMENT",
                                batch_size: int = 10) -> List[Dict[str, Any]]:
        """
        Create embeddings for multiple texts with rate limiting
        
        Args:
            texts: List of texts to embed
            task_type: Type of task for embeddings
            batch_size: Number of requests before adding delay
            
        Returns:
            List of dictionaries with text and embedding
        """
        embeddings = []
        failed_texts = []
        
        self.logger.info(f"Creating embeddings for {len(texts)} texts")
        
        for idx, text in enumerate(texts):
            try:
                embedding = self.create_embedding(text, task_type)
                embeddings.append({
                    "text": text[:100] + "..." if len(text) > 100 else text,
                    "embedding": embedding,
                    "original_text": text
                })
                
                # Add delay to respect rate limits
                if (idx + 1) % batch_size == 0:
                    self.logger.info(f"Processed {idx + 1}/{len(texts)} embeddings, waiting...")
                    time.sleep(2)  # 2 second delay between batches
                    
            except Exception as e:
                self.logger.error(f"Failed to embed text {idx}: {str(e)}")
                failed_texts.append((idx, text[:50]))
                continue
        
        if failed_texts:
            self.logger.warning(f"Failed to embed {len(failed_texts)} texts")
        
        self.logger.info(f"Successfully created {len(embeddings)} embeddings")
        return embeddings
    
    def embed_chunks(self, chunks: List[dict]) -> List[dict]:
        """
        Create embeddings for document chunks
        
        Args:
            chunks: List of chunk dictionaries with 'content' key
            
        Returns:
            List of chunks with added 'embedding' key
        """
        texts = [chunk['content'] for chunk in chunks]
        embeddings = self.create_embeddings_batch(texts, task_type="RETRIEVAL_DOCUMENT")
        
        # Combine chunks with embeddings
        for i, chunk in enumerate(chunks):
            if i < len(embeddings):
                chunk['embedding'] = embeddings[i]['embedding']
        
        self.logger.info(f"Added embeddings to {len(chunks)} chunks")
        return chunks

    def create_embeddings(self, texts: List[str], task_type: str = "RETRIEVAL_DOCUMENT") -> List[List[float]]:
        """
        Create embeddings for a batch of texts.
        """
        self.logger.info(f"Starting embeddings creation for {len(texts)} texts")
        prepared_texts = []
        invalid_indexes = set()

        for i, text in enumerate(texts):
            if not text or not isinstance(text, str):
                self.logger.warning(f"Invalid text at index {i}; using zero embedding")
                prepared_texts.append("")
                invalid_indexes.add(i)
                continue

            if len(text) > 10000:
                text = text[:10000]
                self.logger.warning(f"Text {i} truncated to 10000 characters")

            prepared_texts.append(text)

        zero_embedding = [0] * self.embedding_dimension
        embeddings = [zero_embedding.copy() for _ in prepared_texts]
        valid_pairs = [
            (i, text)
            for i, text in enumerate(prepared_texts)
            if i not in invalid_indexes
        ]

        if not valid_pairs:
            return embeddings

        valid_indexes = [i for i, _ in valid_pairs]
        valid_texts = [text for _, text in valid_pairs]

        try:
            kwargs = {
                "model": self.model,
                "contents": valid_texts,
                "config": self._embedding_config(task_type),
            }

            response = self.embedding_client.models.embed_content(**kwargs)
            batch_embeddings = [list(embedding.values) for embedding in response.embeddings]

            for original_index, embedding in zip(valid_indexes, batch_embeddings):
                embeddings[original_index] = embedding or zero_embedding.copy()
        except Exception as e:
            self.logger.error(f"Batch embedding failed; falling back to one-by-one embeddings: {str(e)}")
            for original_index, text in valid_pairs:
                try:
                    embeddings[original_index] = self.create_embedding(text, task_type=task_type)
                    time.sleep(0.2)
                except Exception as single_error:
                    self.logger.error(f"Error creating embedding {original_index}: {str(single_error)}")
        
        self.logger.info(f"Embeddings creation complete. Successfully created: {len([e for e in embeddings if e != zero_embedding])}/{len(embeddings)}")
        return embeddings

    def generate_answer(self, question: str, context_chunks: List[str]) -> str:
        """Generate an answer based on question and context using Gemini"""
        try:
            context = "\n\n".join(context_chunks)
            prompt = f"""Based on the following context, answer the question concisely.

CONTEXT:
{context}

QUESTION: {question}

ANSWER:"""
            
            self.logger.info(f"Generating answer for: {question[:50]}...")
            response = self.generative_model.generate_content(prompt)
            return response.text
            
        except Exception as e:
            self.logger.error(f"Error generating answer: {str(e)}")
            return f"Error: {str(e)}"


class PerplexityEmbedder:
    """Create embeddings and answers using Perplexity APIs"""

    def __init__(
        self,
        api_key: str,
        model: str = "pplx-embed-v1-4b",
        generation_model: str = "sonar-reasoning-pro",
        embedding_dimension: int = 768,
        base_url: str = "https://api.perplexity.ai",
    ):
        if not api_key:
            raise ValueError("Perplexity API key not provided. Set PERPLEXITY_API_KEY.")

        self.api_key = api_key
        self.model = model
        self.generation_model = generation_model
        self.embedding_dimension = embedding_dimension
        self.base_url = base_url.rstrip("/")
        self.logger = logging.getLogger(__name__)

    def _post(self, path: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        request = Request(
            f"{self.base_url}{path}",
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
            method="POST",
        )

        try:
            with urlopen(request, timeout=120) as response:
                return json.loads(response.read().decode("utf-8"))
        except HTTPError as exc:
            body = exc.read().decode("utf-8", errors="replace")
            try:
                error_payload = json.loads(body)
                error = error_payload.get("error", {})
                if error.get("type") == "insufficient_quota":
                    raise RuntimeError(
                        "Perplexity API quota exhausted. Add credits/billing at "
                        "https://www.perplexity.ai/settings/api or switch LLM_PROVIDER."
                    ) from exc
            except json.JSONDecodeError:
                pass

            raise RuntimeError(f"Perplexity API error {exc.code}: {body}") from exc
        except URLError as exc:
            raise RuntimeError(f"Perplexity API connection error: {exc.reason}") from exc

    def _decode_embedding(self, encoded_embedding: str) -> List[float]:
        raw = base64.b64decode(encoded_embedding)
        return [float(value - 256 if value > 127 else value) for value in raw]

    def create_embedding(self, text: str, task_type: str = "RETRIEVAL_DOCUMENT") -> List[float]:
        embeddings = self.create_embeddings([text], task_type=task_type)
        if not embeddings:
            return [0] * self.embedding_dimension
        return embeddings[0]

    def create_embeddings(self, texts: List[str], task_type: str = "RETRIEVAL_DOCUMENT") -> List[List[float]]:
        self.logger.info(f"Starting Perplexity embeddings creation for {len(texts)} texts")

        prepared_texts = []
        invalid_indexes = set()
        for index, text in enumerate(texts):
            if not text or not isinstance(text, str):
                self.logger.warning(f"Invalid text at index {index}; using zero embedding")
                prepared_texts.append("")
                invalid_indexes.add(index)
                continue
            prepared_texts.append(text)

        zero_embedding = [0] * self.embedding_dimension
        embeddings = [zero_embedding.copy() for _ in prepared_texts]
        valid_pairs = [
            (index, text)
            for index, text in enumerate(prepared_texts)
            if index not in invalid_indexes
        ]

        if not valid_pairs:
            return embeddings

        valid_indexes = [index for index, _ in valid_pairs]
        valid_texts = [text for _, text in valid_pairs]

        try:
            response = self._post(
                "/v1/embeddings",
                {
                    "input": valid_texts,
                    "model": self.model,
                    "dimensions": self.embedding_dimension,
                    "encoding_format": "base64_int8",
                },
            )

            for item in response.get("data", []):
                item_index = item.get("index", 0)
                original_index = valid_indexes[item_index]
                embeddings[original_index] = self._decode_embedding(item["embedding"])
        except Exception as exc:
            self.logger.error(f"Perplexity embedding failed: {str(exc)}")
            raise

        self.logger.info(
            f"Perplexity embeddings complete. Successfully created: "
            f"{len([e for e in embeddings if e != zero_embedding])}/{len(embeddings)}"
        )
        return embeddings

    def create_embeddings_batch(
        self,
        texts: List[str],
        task_type: str = "RETRIEVAL_DOCUMENT",
        batch_size: int = 10,
    ) -> List[Dict[str, Any]]:
        embeddings = self.create_embeddings(texts, task_type=task_type)
        return [
            {
                "text": text[:100] + "..." if len(text) > 100 else text,
                "embedding": embedding,
                "original_text": text,
            }
            for text, embedding in zip(texts, embeddings)
        ]

    def embed_chunks(self, chunks: List[dict]) -> List[dict]:
        texts = [chunk["content"] for chunk in chunks]
        embeddings = self.create_embeddings(texts, task_type="RETRIEVAL_DOCUMENT")

        for chunk, embedding in zip(chunks, embeddings):
            chunk["embedding"] = embedding

        self.logger.info(f"Added Perplexity embeddings to {len(chunks)} chunks")
        return chunks

    def generate_answer(self, question: str, context_chunks: List[str]) -> str:
        """Generate an answer based on retrieved context using Perplexity Sonar."""
        try:
            context = "\n\n".join(context_chunks)
            prompt = f"""Answer the question using only the context below. If the context does not contain enough information, say so.

CONTEXT:
{context}

QUESTION: {question}

ANSWER:"""

            response = self._post(
                "/v1/sonar",
                {
                    "model": self.generation_model,
                    "messages": [{"role": "user", "content": prompt}],
                    "web_search_options": {"disable_search": True},
                },
            )
            return response["choices"][0]["message"]["content"]
        except Exception as exc:
            self.logger.error(f"Error generating Perplexity answer: {str(exc)}")
            return f"Error: {str(exc)}"


class GroqEmbedder:
    """
    Use local deterministic embeddings and Groq for answer generation.

    Groq does not currently expose a text embeddings API, so this class avoids
    Gemini entirely by using a local hash-based embedding for retrieval.
    """

    def __init__(
        self,
        api_key: str,
        generation_model: str = "llama-3.3-70b-versatile",
        embedding_dimension: int = 768,
        base_url: str = "https://api.groq.com/openai/v1",
    ):
        if not api_key:
            raise ValueError("Groq API key not provided. Set GROQ_API_KEY.")

        self.api_key = api_key
        self.generation_model = generation_model
        self.embedding_dimension = embedding_dimension
        self.logger = logging.getLogger(__name__)
        
        # Initialize OpenAI client for Groq
        self.client = OpenAI(api_key=api_key, base_url=base_url)

    def _token_features(self, text: str) -> List[str]:
        tokens = re.findall(r"[a-z0-9]+", text.lower())
        bigrams = [f"{left}_{right}" for left, right in zip(tokens, tokens[1:])]
        return tokens + bigrams

    def _hash_feature(self, feature: str) -> tuple[int, float]:
        digest = hashlib.blake2b(feature.encode("utf-8"), digest_size=8).digest()
        value = int.from_bytes(digest, byteorder="big", signed=False)
        index = value % self.embedding_dimension
        sign = 1.0 if value & 1 else -1.0
        return index, sign

    def create_embedding(self, text: str, task_type: str = "RETRIEVAL_DOCUMENT") -> List[float]:
        if not text or not isinstance(text, str):
            return [0] * self.embedding_dimension

        vector = [0.0] * self.embedding_dimension
        for feature in self._token_features(text):
            index, sign = self._hash_feature(feature)
            vector[index] += sign

        magnitude = math.sqrt(sum(value * value for value in vector))
        if magnitude == 0:
            return [0] * self.embedding_dimension

        return [value / magnitude for value in vector]

    def create_embeddings(self, texts: List[str], task_type: str = "RETRIEVAL_DOCUMENT") -> List[List[float]]:
        self.logger.info(f"Creating local hash embeddings for {len(texts)} texts")
        return [self.create_embedding(text, task_type=task_type) for text in texts]

    def create_embeddings_batch(
        self,
        texts: List[str],
        task_type: str = "RETRIEVAL_DOCUMENT",
        batch_size: int = 10,
    ) -> List[Dict[str, Any]]:
        embeddings = self.create_embeddings(texts, task_type=task_type)
        return [
            {
                "text": text[:100] + "..." if len(text) > 100 else text,
                "embedding": embedding,
                "original_text": text,
            }
            for text, embedding in zip(texts, embeddings)
        ]

    def embed_chunks(self, chunks: List[dict]) -> List[dict]:
        texts = [chunk["content"] for chunk in chunks]
        embeddings = self.create_embeddings(texts, task_type="RETRIEVAL_DOCUMENT")

        for chunk, embedding in zip(chunks, embeddings):
            chunk["embedding"] = embedding

        self.logger.info(f"Added local hash embeddings to {len(chunks)} chunks")
        return chunks

    def generate_answer(self, question: str, context_chunks: List[str]) -> str:
        """Generate an answer based on retrieved context using Groq Llama."""
        try:
            context = "\n\n".join(context_chunks)
            prompt = f"""Answer the question using only the context below. If the context does not contain enough information, say so.

CONTEXT:
{context}

QUESTION: {question}

ANSWER:"""

            response = self.client.chat.completions.create(
                model=self.generation_model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.2,
            )
            return response.choices[0].message.content
        except Exception as exc:
            self.logger.error(f"Error generating Groq answer: {str(exc)}")
            return f"Error: {str(exc)}"
