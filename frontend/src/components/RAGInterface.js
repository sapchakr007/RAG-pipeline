import React, { useState, useEffect } from 'react';
import axios from 'axios';
import './RAGInterface.css';
import TransactionTable from './TransactionTable';

const RAGInterface = () => {
  const [question, setQuestion] = useState('');
  const [answer, setAnswer] = useState('');
  const [sources, setSources] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [modelInfo, setModelInfo] = useState(null);
  const [totalDocs, setTotalDocs] = useState(0);
  const [history, setHistory] = useState([]);
  const [darkMode, setDarkMode] = useState(true);

  const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:5001/api';

  // Fetch health status and model info on component mount
  useEffect(() => {
    let retries = 0;
    const maxRetries = 10;
    
    const attemptConnection = async () => {
      try {
        await fetchHealth();
      } catch (err) {
        if (retries < maxRetries) {
          retries++;
          console.log(`Connection attempt ${retries}/${maxRetries}...`);
          setTimeout(attemptConnection, 1000); // Retry every 1 second
        }
      }
    };
    
    attemptConnection();
  }, []);

  const fetchHealth = async () => {
    try {
      const response = await axios.get(`${API_URL}/health`);
      setModelInfo(response.data.models);
      setTotalDocs(response.data.total_documents);
      setError('');
    } catch (err) {
      setError('Failed to connect to backend. Make sure Flask server is running on http://localhost:5001');
      console.error(err);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();

    if (!question.trim()) {
      setError('Please enter a question');
      return;
    }

    setLoading(true);
    setError('');
    setAnswer('');
    setSources([]);

    try {
      const response = await axios.post(`${API_URL}/query`, {
        question: question.trim(),
        top_k: 3
      });

      setAnswer(response.data.answer);
      setSources(response.data.source_chunks);
      setTotalDocs(response.data.total_documents);

      // Add to history
      setHistory([
        {
          question: question.trim(),
          answer: response.data.answer,
          timestamp: new Date().toLocaleTimeString()
        },
        ...history
      ].slice(0, 5)); // Keep last 5

      setQuestion('');
    } catch (err) {
      setError(err.response?.data?.error || 'Failed to get answer. Please try again.');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className={`rag-container ${darkMode ? 'dark-theme' : ''}`}>
      {/* Header */}
      <div className="header">
        <div className="header-content">
          <h1>📚 RAG Pipeline</h1>
          <p>Ask questions about your documents</p>
        </div>
        <div className="header-stats">
          <button 
            className="theme-toggle-btn"
            onClick={() => setDarkMode(!darkMode)}
            title={darkMode ? "Switch to Light Mode" : "Switch to Dark Mode"}
          >
            {darkMode ? '☀️' : '🌙'}
          </button>
          <div className="stat">
            <span className="stat-label">Documents</span>
            <span className="stat-value">{totalDocs}</span>
          </div>
        </div>
      </div>

      {/* Model Info */}
      {modelInfo && (
        <div className="model-info">
          <div className="info-item">
            <span className="info-label">Provider:</span>
            <span className="info-value">{modelInfo.provider}</span>
          </div>
          <div className="info-item">
            <span className="info-label">Embedding:</span>
            <span className="info-value">{modelInfo.embedding_model}</span>
          </div>
          <div className="info-item">
            <span className="info-label">Generation:</span>
            <span className="info-value">{modelInfo.generation_model}</span>
          </div>
        </div>
      )}

      {/* Main Content */}
      <div className="main-content">
        {/* Query Section */}
        <div className="query-section">
          <form onSubmit={handleSubmit} className="query-form">
            <div className="input-group">
              <input
                type="text"
                value={question}
                onChange={(e) => setQuestion(e.target.value)}
                placeholder="Ask a question about your documents..."
                disabled={loading}
                className="query-input"
              />
              <button
                type="submit"
                disabled={loading}
                className="query-button"
              >
                {loading ? (
                  <>
                    <span className="spinner"></span>
                    Searching...
                  </>
                ) : (
                  <>
                    <span className="send-icon">→</span>
                    Ask
                  </>
                )}
              </button>
            </div>
          </form>

          {/* Error Message */}
          {error && (
            <div className="error-message">
              <span className="error-icon">⚠️</span>
              {error}
            </div>
          )}
        </div>

        {/* Results Section */}
        <div className="results-section">
          {/* Answer */}
          {answer && (
            <div className="answer-card">
              <h2 className="answer-title">💡 Answer</h2>
              <p className="answer-text">{answer}</p>
            </div>
          )}

          {/* Sources */}
          {sources.length > 0 && (
            <div className="sources-card">
              <h3 className="sources-title">📖 Sources</h3>
              <div className="sources-list">
                {sources.map((source, index) => (
                  <div key={index} className="source-item">
                    <div className="source-header">
                      <span className="source-number">{index + 1}</span>
                      <span className="source-confidence">
                        Relevance: {(source.score * 100).toFixed(1)}%
                      </span>
                    </div>
                    <p className="source-text">{source.text}</p>
                    <span className="source-file">
                      📄 {source.source.split('/').pop()}
                    </span>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* History */}
          {history.length > 0 && !answer && (
            <div className="history-card">
              <h3 className="history-title">⏱️ Recent Queries</h3>
              <div className="history-list">
                {history.map((item, index) => (
                  <div
                    key={index}
                    className="history-item"
                    onClick={() => setQuestion(item.question)}
                  >
                    <p className="history-question">{item.question}</p>
                    <span className="history-time">{item.timestamp}</span>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Transactions Table */}
          <TransactionTable />
        </div>
      </div>

      {/* Footer */}
      <div className="footer">
        <p>RAG Pipeline powered by Groq LLaMA 3.3 70B</p>
      </div>
    </div>
  );
};

export default RAGInterface;
