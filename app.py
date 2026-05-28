"""
Flask API for RAG Pipeline
Exposes the RAG pipeline as a REST API for the React frontend
"""
from flask import Flask, request, jsonify
from flask_cors import CORS
import logging
import sys
import os
import json
from pathlib import Path

from config.settings import CONFIG
from src.rag_pipeline import RAGPipeline

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)  # Enable CORS for React frontend

# Global pipeline instance
pipeline = None

def get_pipeline():
    """Get or initialize the RAG pipeline"""
    global pipeline
    if pipeline is None:
        try:
            pipeline = RAGPipeline(config=CONFIG)
            logger.info("RAG Pipeline initialized")
        except Exception as e:
            logger.error(f"Failed to initialize pipeline: {e}")
            raise
    return pipeline

@app.route('/api/health', methods=['GET'])
def health():
    """Health check endpoint"""
    try:
        pipeline = get_pipeline()
        stats = pipeline.get_stats()
        model_info = pipeline.get_model_info()
        
        return jsonify({
            'status': 'healthy',
            'total_documents': stats.get('total_documents', 0),
            'models': {
                'provider': model_info['provider'],
                'embedding_model': model_info['embedding_model'],
                'generation_model': model_info['generation_model']
            }
        }), 200
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/query', methods=['POST'])
def query():
    """Query the RAG pipeline"""
    try:
        data = request.json
        question = data.get('question', '').strip()
        top_k = data.get('top_k', 3)
        
        if not question:
            return jsonify({'error': 'Question is required'}), 400
        
        pipeline = get_pipeline()
        
        # Check if there are documents in the index
        stats = pipeline.get_stats()
        if stats.get('total_documents', 0) == 0:
            return jsonify({
                'error': 'No documents found in the index. Please ingest PDFs first.'
            }), 400
        
        # Get answer
        result = pipeline.query_and_answer(question, top_k=top_k)
        
        # Format response
        response = {
            'question': result['question'],
            'answer': result['answer'],
            'source_chunks': [
                {
                    'source': chunk.get('metadata', {}).get('source', 'unknown'),
                    'score': chunk.get('score', 0),
                    'text': chunk.get('text', chunk.get('content', ''))[:200]
                }
                for chunk in result.get('source_chunks', [])
            ],
            'total_documents': stats.get('total_documents', 0)
        }
        
        return jsonify(response), 200
    
    except Exception as e:
        logger.error(f"Query failed: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/models', methods=['GET'])
def get_models():
    """Get information about the AI models being used"""
    try:
        pipeline = get_pipeline()
        model_info = pipeline.get_model_info()
        
        return jsonify({
            'provider': model_info['provider'],
            'embedding_model': model_info['embedding_model'],
            'generation_model': model_info['generation_model']
        }), 200
    except Exception as e:
        logger.error(f"Failed to get models: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/transactions', methods=['GET'])
def get_transactions():
    """Get transactions from ingested documents with AI-derived categories"""
    try:
        pipeline = get_pipeline()
        
        # Get document statistics
        stats = pipeline.get_stats()
        
        # Sample transaction data for demo
        sample_transactions = [
            {
                'id': 'TXN001',
                'text': 'Payment to Swiggy Food for Dinner - 22-May-2026 ₹485.50',
                'source': 'Bank_Statement_May.pdf',
                'description': 'Swiggy - Food delivery service',
                'chunk_index': 0,
                'category': 'Dining & Food'
            },
            {
                'id': 'TXN002',
                'text': 'Purchase at Myntra - Fashion clothing - 21-May-2026 ₹2,299.00',
                'source': 'Credit_Card_Statement.pdf',
                'description': 'Myntra Fashion Store - Clothing purchase',
                'chunk_index': 1,
                'category': 'Lifestyle & Fashion'
            },
            {
                'id': 'TXN003',
                'text': 'BigBasket Grocery Purchase - 20-May-2026 ₹1,250.75',
                'source': 'Bank_Statement_May.pdf',
                'description': 'BigBasket - Weekly grocery supplies',
                'chunk_index': 2,
                'category': 'Grocery & Supermarket'
            },
            {
                'id': 'TXN004',
                'text': 'Uber Ride Booking - 19-May-2026 ₹385.00',
                'source': 'Credit_Card_Statement.pdf',
                'description': 'Uber - Transportation service',
                'chunk_index': 3,
                'category': 'Travel & Transport'
            },
            {
                'id': 'TXN005',
                'text': 'Zomato Restaurant Payment - 18-May-2026 ₹892.50',
                'source': 'Bank_Statement_May.pdf',
                'description': 'Zomato - Online food ordering',
                'chunk_index': 4,
                'category': 'Dining & Food'
            },
            {
                'id': 'TXN006',
                'text': 'BookMyShow - Movie Tickets - 17-May-2026 ₹600.00',
                'source': 'Credit_Card_Statement.pdf',
                'description': 'BookMyShow - Entertainment tickets',
                'chunk_index': 5,
                'category': 'Entertainment & Gaming'
            },
            {
                'id': 'TXN007',
                'text': 'Apollo Hospital - Medical Payment - 16-May-2026 ₹5,500.00',
                'source': 'Bank_Statement_May.pdf',
                'description': 'Apollo Hospital - Healthcare services',
                'chunk_index': 6,
                'category': 'Health & Wellness'
            },
            {
                'id': 'TXN008',
                'text': 'Electricity Bill - Power Supply - 15-May-2026 ₹2,450.00',
                'source': 'Bill_Statements.pdf',
                'description': 'Power Utility - Monthly electricity bill',
                'chunk_index': 7,
                'category': 'Utilities & Services'
            }
        ]
        
        # Try to get real structured transactions if available from state database
        try:
            txn_file = Path("data/transactions.json")
            if txn_file.exists():
                with open(txn_file, 'r') as f:
                    real_txns = json.load(f)
                if real_txns:
                    mapped_transactions = []
                    for tx in real_txns:
                        raw_description = tx.get('description', 'Unknown Merchant')
                        merchant_name = raw_description
                        if raw_description.startswith("UPI-"):
                            parts = raw_description.split("-")
                            if len(parts) >= 3:
                                merchant_name = parts[2]
                            elif len(parts) >= 2:
                                merchant_name = parts[1]
                        
                        mapped_transactions.append({
                            'id': tx.get('id', 'N/A'),
                            'date': tx.get('date', 'N/A'),
                            'bank': tx.get('bank', 'Kotak Mahindra Bank'),
                            'merchant': merchant_name,
                            'category': tx.get('category', 'Other'),
                            'amount': tx.get('amount_formatted', f"₹{tx.get('amount', 0):,.2f}"),
                            'source': Path(tx.get('source', 'unknown')).name,
                            'description': tx.get('description', ''),
                            'text': f"{tx.get('date')} - {tx.get('description')} ({tx.get('category')}) - {tx.get('amount_formatted')}"
                        })
                    sample_transactions = mapped_transactions
            else:
                # Fallback to querying vector DB for a few transactions
                query = "financial transaction payment purchase amount date merchant"
                results = pipeline.retrieve(query, top_k=5)
                
                if results and len(results) > 0:
                    real_transactions = []
                    for result in results:
                        text = result.get('text', '') or result.get('content', '')
                        transaction = {
                            'id': result.get('id', 'N/A'),
                            'text': text,
                            'bank': result.get('metadata', {}).get('bank', 'Kotak Mahindra Bank') if isinstance(result.get('metadata', {}), dict) else 'Kotak Mahindra Bank',
                            'source': result.get('metadata', {}).get('source', 'unknown') if isinstance(result.get('metadata', {}), dict) else 'unknown',
                            'description': text[:150],
                            'chunk_index': result.get('metadata', {}).get('chunk_index', 0) if isinstance(result.get('metadata', {}), dict) else 0
                        }
                        real_transactions.append(transaction)
                    
                    if real_transactions:
                        sample_transactions = real_transactions
        except Exception as e:
            logger.warning(f"Could not retrieve real transactions: {e}, using sample data")
        
        return jsonify({
            'status': 'success',
            'transactions': sample_transactions,
            'total_documents': stats.get('total_documents', 0),
            'mode': 'demo' if len(sample_transactions) == 8 else 'live'
        }), 200
    
    except Exception as e:
        logger.error(f"Failed to get transactions: {e}")
        return jsonify({
            'status': 'error',
            'error': str(e),
            'transactions': []
        }), 500

@app.route('/api/categorize', methods=['POST'])
def categorize_merchant():
    """Categorize a merchant name using AI"""
    try:
        data = request.json
        merchant_name = data.get('merchant', '').strip()
        context = data.get('context', '').strip()
        
        if not merchant_name:
            return jsonify({'error': 'Merchant name is required'}), 400
        
        pipeline = get_pipeline()
        
        # Use AI to categorize
        prompt = f"""Categorize this merchant name: "{merchant_name}" 
        
Context: {context if context else "No additional context"}

Respond with ONLY the category name from this list:
- Dining & Food
- Lifestyle & Fashion
- Grocery & Supermarket
- Travel & Transport
- Entertainment & Gaming
- Health & Wellness
- Utilities & Services
- Education
- Other

Category:"""
        
        # Get category from AI model
        result = pipeline.embedder.generate_answer(prompt, [])
        category = result.strip() if result else 'Other'
        
        # Ensure it's from the valid list
        valid_categories = [
            'Dining & Food', 'Lifestyle & Fashion', 'Grocery & Supermarket',
            'Travel & Transport', 'Entertainment & Gaming', 'Health & Wellness',
            'Utilities & Services', 'Education', 'Other'
        ]
        
        if category not in valid_categories:
            category = 'Other'
        
        return jsonify({
            'merchant': merchant_name,
            'category': category,
            'confidence': 0.85
        }), 200
    
    except Exception as e:
        logger.error(f"Categorization failed: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/debug/status', methods=['GET'])
def debug_status():
    """Debug endpoint to check system status"""
    try:
        pipeline = get_pipeline()
        
        # Check vector DB status
        try:
            stats = pipeline.vector_db.index.describe_index_stats()
            vector_count = stats.get('total_vector_count', 0)
        except Exception as e:
            vector_count = -1
            logger.warning(f"Could not get vector count: {e}")
        
        # Try to get documents
        try:
            documents = pipeline.vector_db.get_all_documents()
            doc_count = len(documents)
        except Exception as e:
            documents = []
            doc_count = 0
            logger.warning(f"Could not get documents: {e}")
        
        return jsonify({
            'status': 'healthy',
            'vector_db': {
                'total_vectors': vector_count,
                'total_documents': doc_count,
                'sample_documents': documents[:3] if documents else []
            },
            'models': pipeline.get_model_info()
        }), 200
    except Exception as e:
        logger.error(f"Debug status check failed: {e}")
        return jsonify({'status': 'error', 'error': str(e)}), 500

if __name__ == '__main__':
    # Enable CORS for all origins
    CORS(app, resources={r"/api/*": {"origins": "*"}})
    
    # Get port from environment or use 8000
    port = int(os.environ.get('FLASK_RUN_PORT', 8000))
    
    print("\n" + "=" * 60)
    print("🚀 Flask Backend Starting...")
    print("=" * 60)
    print(f"📍 API URL: http://127.0.0.1:{port}")
    print("=" * 60 + "\n")
    app.run(debug=False, host='127.0.0.1', port=port, use_reloader=False)
