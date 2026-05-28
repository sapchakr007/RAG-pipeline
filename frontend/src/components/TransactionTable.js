import React, { useState, useEffect } from 'react';
import './TransactionTable.css';

const getCategoryIcon = (category) => {
  switch (category) {
    case 'Dining & Food': return '🍔';
    case 'Lifestyle & Fashion': return '🛍️';
    case 'Grocery & Supermarket': return '🛒';
    case 'Travel & Transport': return '✈️';
    case 'Entertainment & Gaming': return '🎮';
    case 'Health & Wellness': return '🏥';
    case 'Utilities & Services': return '⚡';
    case 'Education': return '🎓';
    case 'IMPS': return '💸';
    case 'Other': return '🏷️';
    default: return '💰';
  }
};

const TransactionTable = () => {
  const [transactions, setTransactions] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [sortConfig, setSortConfig] = useState({ key: 'date', direction: 'desc' });
  const [filterText, setFilterText] = useState('');
  const [selectedTransaction, setSelectedTransaction] = useState(null);
  
  // Column-specific filters
  const [filters, setFilters] = useState({
    date: '',
    merchant: '',
    amount: '',
    source: ''
  });
  
  // Category selection
  const [selectedCategory, setSelectedCategory] = useState('all');

  const API_URL = 'http://localhost:5001/api';

  // Fetch transactions on component mount
  useEffect(() => {
    fetchTransactions();
  }, []);

  const fetchTransactions = async () => {
    setLoading(true);
    setError('');
    try {
      console.log('Fetching transactions from:', `${API_URL}/transactions`);
      const response = await fetch(`${API_URL}/transactions`);
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      
      const data = await response.json();
      console.log('Raw data from API:', data);
      
      if (!data.transactions || !Array.isArray(data.transactions)) {
        console.warn('No transactions in response or invalid format:', data);
        setTransactions([]);
        setError('📝 Transaction data not available. The system is ready for querying documents.');
        setLoading(false);
        return;
      }
      
      // Parse and enrich transaction data
      const enrichedTransactions = data.transactions.map((tx, index) => {
        try {
          return parseTransactionData(tx);
        } catch (parseErr) {
          console.warn(`Error parsing transaction ${index}:`, parseErr, tx);
          return null;
        }
      }).filter(tx => tx !== null);
      
      console.log('Enriched transactions:', enrichedTransactions);
      setTransactions(enrichedTransactions);
      if (enrichedTransactions.length === 0) {
        setError('No valid transactions could be parsed.');
      }
    } catch (err) {
      const errorMsg = `Failed to load transactions: ${err.message}`;
      console.error(errorMsg, err);
      setError(errorMsg);
      setTransactions([]);
    } finally {
      setLoading(false);
    }
  };

  const extractMerchantName = (text) => {
    // Strategy 1: Look for patterns like "PYUSwiggy Food Bangalore IN" or "Swiggy"
    // Common merchant pattern: [PREFIX][MERCHANT_NAME][LOCATION][COUNTRY_CODE]
    
    // Extract merchant from transaction keywords (common patterns)
    const patterns = [
      // Pattern: "at [Merchant] [Location]"
      /(?:at|from|to)\s+([A-Z][A-Za-z\d\s&.'-]+?)(?:\s+(?:IN|US|UK|AU|CA|DE|FR)(?:\s|$|₹|Rupees|Amount))/i,
      // Pattern: Just capitalized merchant name
      /^([A-Z][A-Za-z\d\s&.'-]+?)(?:\s+(?:Food|Bangalore|Delhi|Mumbai|IN|₹))/i,
      // Pattern: Payment/Transaction to merchant
      /(?:payment|transaction|charge|debit|purchase)\s+to\s+([A-Za-z\d\s&.'-]+?)(?:\s{2,}|₹|Amount)/i,
      // Pattern: Generic transaction line
      /^([A-Z][A-Za-z\d\s&.'-]+?)(?:\s+\d+\.?\d*|\s+₹|\s+Amount)/
    ];

    for (let pattern of patterns) {
      const match = text.match(pattern);
      if (match && match[1]) {
        let merchantName = match[1].trim();
        // Clean up the merchant name
        merchantName = merchantName.replace(/\s{2,}/g, ' ').trim();
        // If it's too long (probably includes location), try to extract just the brand
        if (merchantName.length > 50) {
          const words = merchantName.split(/\s+/);
          merchantName = words.slice(0, Math.ceil(words.length / 2)).join(' ');
        }
        if (merchantName.length > 3) {
          return merchantName;
        }
      }
    }

    // Fallback: Get first meaningful words
    const firstLine = text.split('\n')[0];
    const words = firstLine.split(/\s+/).filter(w => w.length > 2 && /^[A-Z]/.test(w));
    if (words.length > 0) {
      return words.slice(0, 3).join(' ');
    }

    return 'Unknown Merchant';
  };

  const parseTransactionData = (transaction) => {
    // Parse transaction text to extract date, merchant, amount
    const text = transaction.text || '';
    
    // Try to extract date (various formats: DD-MMM-YYYY, DD/MM/YYYY, etc.)
    const dateRegex = /(\d{1,2}[-\/]\w{3}[-\/]\d{4}|\d{1,2}[-\/]\d{1,2}[-\/]\d{4}|\d{4}[-\/]\d{1,2}[-\/]\d{1,2})/;
    const dateMatch = text.match(dateRegex);
    
    // Try to extract amount (numbers with currency symbols or decimals)
    const amountRegex = /[₹$€£]\s*[\d,]+\.?\d*|[\d,]+\.?\d*\s*(?:INR|USD|EUR|GBP)/i;
    const amountMatch = text.match(amountRegex);
    
    // Extract merchant name using improved logic
    const merchantName = extractMerchantName(text);
    
    // Get source file name as additional context
    const source = transaction.source || 'Unknown';
    const fileName = source.split('/').pop() || 'Unknown';
    
    // Determine merchant category based on merchant name and full text
    const category = categorizeMerchant(merchantName, text.toLowerCase());
    
    return {
      id: transaction.id || 'N/A',
      date: transaction.date || (dateMatch ? dateMatch[0] : 'N/A'),
      bank: transaction.bank || 'Kotak Mahindra Bank',
      merchant: transaction.merchant || merchantName,
      amount: transaction.amount || (amountMatch ? amountMatch[0] : 'N/A'),
      source: fileName,
      description: transaction.description || text.substring(0, 100),
      fullText: text,
      chunkIndex: transaction.chunk_index || 0,
      category: transaction.category || category
    };
  };

  const categorizeMerchant = (merchantText, fullText) => {
    // Enhanced merchant categories with specific brand/merchant names
    const categories = {
      'Dining & Food': {
        keywords: ['swiggy', 'zomato', 'uber eats', 'doordash', 'restaurant', 'cafe', 'coffee', 'pizza', 'burger', 'food', 'hotel', 'bar', 'pub', 'dining', 'diner', 'bistro', 'kitchen', 'bakery', 'sweets', 'icecream', 'biryani', 'curry', 'noodles', 'pizza hut', 'kfc', 'mcdonalds', 'dominos', 'subway', 'starbucks', 'dunkin'],
        brands: ['Swiggy', 'Zomato', 'Uber Eats', 'DoorDash', 'GrubHub']
      },
      'Lifestyle & Fashion': {
        keywords: ['fashion', 'clothing', 'apparel', 'boutique', 'mall', 'retail', 'designer', 'brand', 'dress', 'shoes', 'accessories', 'lifestyle', 'zara', 'h&m', 'forever 21', 'uniqlo', 'myntra', 'flipkart fashion'],
        brands: ['Zara', 'H&M', 'Forever 21', 'Uniqlo', 'Myntra', 'Amazon Fashion']
      },
      'Grocery & Supermarket': {
        keywords: ['grocery', 'supermarket', 'market', 'vegetables', 'fruits', 'daily needs', 'supplies', 'big basket', 'amazon fresh', 'blink', 'mother dairy', 'milkbasket'],
        brands: ['BigBasket', 'Amazon Fresh', 'Blink', 'Grofers', 'Mother Dairy']
      },
      'Travel & Transport': {
        keywords: ['travel', 'hotel', 'airline', 'flight', 'taxi', 'uber', 'ola', 'transport', 'booking', 'transit', 'ride', 'car', 'train', 'railway', 'bus', 'airbnb', 'booking.com'],
        brands: ['Uber', 'Ola', 'Airbnb', 'Booking.com', 'MakeMyTrip', 'GoIbibo']
      },
      'Entertainment & Gaming': {
        keywords: ['entertainment', 'cinema', 'movie', 'gaming', 'game', 'play', 'show', 'ticket', 'concert', 'event', 'bookmyshow', 'netflix', 'prime video'],
        brands: ['BookMyShow', 'Netflix', 'Prime Video', 'Disney+']
      },
      'Health & Wellness': {
        keywords: ['hospital', 'clinic', 'doctor', 'pharmacy', 'medical', 'health', 'wellness', 'gym', 'fitness', 'healthcare', 'ayurveda', 'apollo', 'fortis', 'max healthcare'],
        brands: ['Apollo', 'Fortis', 'Max Healthcare', 'Practo']
      },
      'Utilities & Services': {
        keywords: ['utility', 'electricity', 'water', 'gas', 'phone', 'internet', 'service', 'bill', 'payment', 'subscription'],
        brands: ['BSNL', 'Airtel', 'Jio', 'Vodafone']
      },
      'Education': {
        keywords: ['school', 'college', 'university', 'education', 'course', 'training', 'institute', 'academy', 'coaching', 'udemy', 'coursera'],
        brands: ['Udemy', 'Coursera', 'BYJU\'s']
      }
    };

    const searchText = merchantText.toLowerCase() + ' ' + fullText;
    
    // Check for exact brand matches first (higher priority)
    for (const [category, config] of Object.entries(categories)) {
      if (config.brands) {
        for (const brand of config.brands) {
          if (searchText.includes(brand.toLowerCase())) {
            return category;
          }
        }
      }
    }
    
    // Then check for keyword matches
    for (const [category, config] of Object.entries(categories)) {
      for (const keyword of config.keywords) {
        if (searchText.includes(keyword)) {
          return category;
        }
      }
    }
    
    return 'Other';
  };

  const handleSort = (key) => {
    setSortConfig(prev => ({
      key,
      direction: prev.key === key && prev.direction === 'asc' ? 'desc' : 'asc'
    }));
  };

  // Get unique categories
  const categories = ['all', ...new Set(transactions.map(t => t.category))];

  // Filter transactions by search and category
  const filteredTransactions = transactions.filter(tx => {
    const matchesCategory = selectedCategory === 'all' || tx.category === selectedCategory;
    const searchLower = filterText.toLowerCase();
    const matchesSearch = (
      tx.merchant.toLowerCase().includes(searchLower) ||
      tx.date.toLowerCase().includes(searchLower) ||
      (tx.bank && tx.bank.toLowerCase().includes(searchLower)) ||
      tx.amount.toLowerCase().includes(searchLower) ||
      tx.source.toLowerCase().includes(searchLower) ||
      tx.description.toLowerCase().includes(searchLower) ||
      tx.category.toLowerCase().includes(searchLower)
    );
    return matchesCategory && matchesSearch;
  });

  const sortedTransactions = [...filteredTransactions].sort((a, b) => {
    const aValue = a[sortConfig.key];
    const bValue = b[sortConfig.key];
    
    // Handle numeric comparison for amounts
    if (sortConfig.key === 'amount') {
      const aNum = parseFloat(aValue.replace(/[^\d.-]/g, '')) || 0;
      const bNum = parseFloat(bValue.replace(/[^\d.-]/g, '')) || 0;
      return sortConfig.direction === 'asc' ? aNum - bNum : bNum - aNum;
    }
    
    // String comparison for dates and merchant names
    if (aValue < bValue) return sortConfig.direction === 'asc' ? -1 : 1;
    if (aValue > bValue) return sortConfig.direction === 'asc' ? 1 : -1;
    return 0;
  });

  // Calculate KPIs
  const calculateKPIs = () => {
    const categoryData = {};
    let totalAmount = 0;
    
    filteredTransactions.forEach(tx => {
      const amount = parseFloat(tx.amount.replace(/[^\d.-]/g, '')) || 0;
      totalAmount += amount;
      
      if (!categoryData[tx.category]) {
        categoryData[tx.category] = {
          count: 0,
          total: 0,
          items: []
        };
      }
      categoryData[tx.category].count += 1;
      categoryData[tx.category].total += amount;
      categoryData[tx.category].items.push(tx);
    });
    
    return { categoryData, totalAmount };
  };

  const { categoryData, totalAmount } = calculateKPIs();

  const SortIcon = ({ active, direction }) => {
    if (!active) return <span className="sort-icon">⇅</span>;
    return direction === 'asc' ? <span className="sort-icon active">↑</span> : <span className="sort-icon active">↓</span>;
  };

  if (loading) {
    return (
      <div className="transaction-container">
        <div className="loading">
          <span className="spinner"></span>
          Loading transactions...
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="transaction-container">
        <div className="error-message">
          <span className="error-icon">⚠️</span>
          {error}
        </div>
      </div>
    );
  }

  const uniqueMerchants = new Set(filteredTransactions.map(tx => tx.merchant.toLowerCase())).size;
  const uniqueBanks = Array.from(new Set(filteredTransactions.map(tx => tx.bank || 'Kotak Mahindra Bank').filter(Boolean)));
  const bankNamesDisplay = uniqueBanks.length > 0 ? uniqueBanks.join(', ') : 'Kotak Mahindra Bank';

  return (
    <div className="transaction-container">
      {/* KPI Dashboard */}
      <div className="kpi-dashboard">
        <div className="kpi-card total">
          <div className="kpi-label">Total Transactions</div>
          <div className="kpi-value">{filteredTransactions.length}</div>
        </div>
        <div className="kpi-card amount">
          <div className="kpi-label">Total Spend</div>
          <div className="kpi-value">₹{totalAmount.toFixed(2)}</div>
        </div>
        <div className="kpi-card categories">
          <div className="kpi-label">Unique Merchants</div>
          <div className="kpi-value">{uniqueMerchants}</div>
        </div>
        <div className="kpi-card average">
          <div className="kpi-label">Bank Name(s)</div>
          <div className="kpi-value" style={{ fontSize: bankNamesDisplay.length > 20 ? '0.9rem' : '1.3rem', wordBreak: 'break-word' }} title={bankNamesDisplay}>
            {bankNamesDisplay}
          </div>
        </div>
      </div>

      {/* Category KPI Breakdown */}
      <div className="category-breakdown">
        <h3 className="breakdown-title">📊 Spending by Category</h3>
        {Object.entries(categoryData).length > 0 ? (
          <div className="category-grid">
            {Object.entries(categoryData).map(([category, data]) => (
              <div 
                key={category} 
                className={`category-card ${selectedCategory === category ? 'active' : ''}`}
                onClick={() => setSelectedCategory(category)}
              >
                <div className="category-name">{getCategoryIcon(category)} {category}</div>
                <div className="category-count">{data.count} items</div>
                <div className="category-amount">₹{data.total.toFixed(2)}</div>
              </div>
            ))}
          </div>
        ) : (
          <div className="no-category-data">
            <p>📭 No transactions loaded yet. Please ensure PDFs are ingested and the backend is running.</p>
            <button className="refresh-button" onClick={fetchTransactions}>
              🔄 Reload Transactions
            </button>
          </div>
        )}
      </div>

      {/* Category Summary Table */}
      <div className="category-summary-section">
        <h3 className="summary-title">📊 Category Summary - Consolidated View</h3>
        {Object.entries(categoryData).length > 0 ? (
          <div className="summary-table-wrapper">
            <table className="summary-table">
              <thead>
                <tr>
                  <th>🏷️ Category</th>
                  <th>📝 Line Items</th>
                  <th>💰 Total Amount</th>
                  <th>📈 Avg per Item</th>
                  <th>% of Total</th>
                </tr>
              </thead>
              <tbody>
                {Object.entries(categoryData).map(([category, data]) => {
                  const percentage = totalAmount > 0 ? ((data.total / totalAmount) * 100).toFixed(1) : '0.0';
                  const avgAmount = data.count > 0 ? (data.total / data.count).toFixed(2) : '0.00';
                  return (
                    <tr key={category}>
                      <td className="summary-category">
                        <span className="summary-category-icon">{getCategoryIcon(category)}</span> {category}
                      </td>
                      <td className="summary-count">{data.count}</td>
                      <td className="summary-amount">₹{data.total.toFixed(2)}</td>
                      <td className="summary-avg">₹{avgAmount}</td>
                      <td className="summary-percentage">
                        <div className="progress-bar">
                          <div 
                            className="progress-fill"
                            style={{width: `${percentage}%`}}
                          ></div>
                        </div>
                        <span>{percentage}%</span>
                      </td>
                    </tr>
                  );
                })}
                <tr className="summary-total">
                  <td className="summary-category"><strong>TOTAL</strong></td>
                  <td className="summary-count"><strong>{filteredTransactions.length}</strong></td>
                  <td className="summary-amount"><strong>₹{totalAmount.toFixed(2)}</strong></td>
                  <td className="summary-avg"><strong>₹{filteredTransactions.length > 0 ? (totalAmount / filteredTransactions.length).toFixed(2) : '0.00'}</strong></td>
                  <td className="summary-percentage"><strong>100%</strong></td>
                </tr>
              </tbody>
            </table>
          </div>
        ) : (
          <div className="empty-table-state">
            <p>📭 No transactions available</p>
            <p style={{fontSize: '12px', color: '#999'}}>Transactions will appear here once PDFs are ingested</p>
          </div>
        )}
      </div>

      {/* Table Header */}
      <div className="table-header">
        <h2 className="table-title">💳 Detailed Transactions</h2>
        <div className="table-stats">
          <span className="stat-item">
            Showing: <strong>{sortedTransactions.length}</strong>
          </span>
          {selectedCategory !== 'all' && (
            <button 
              className="clear-category-btn"
              onClick={() => setSelectedCategory('all')}
            >
              ✕ Show All
            </button>
          )}
        </div>
      </div>

      {/* Search and Filter */}
      <div className="filter-section">
        <input
          type="text"
          placeholder="Search by merchant, date, amount, or source..."
          value={filterText}
          onChange={(e) => setFilterText(e.target.value)}
          className="filter-input"
        />
        {filterText && (
          <button
            className="filter-clear"
            onClick={() => setFilterText('')}
          >
            ✕ Clear
          </button>
        )}
      </div>

      {/* Transactions Table */}
      <div className="table-wrapper">
        <table className="transactions-table">
          <thead>
            <tr>
              <th onClick={() => handleSort('date')} className="sortable">
                📅 Date
                <span className="sort-icon">{sortConfig.key === 'date' ? (sortConfig.direction === 'asc' ? '↑' : '↓') : '⇅'}</span>
              </th>
              <th onClick={() => handleSort('bank')} className="sortable">
                🏦 Bank
                <span className="sort-icon">{sortConfig.key === 'bank' ? (sortConfig.direction === 'asc' ? '↑' : '↓') : '⇅'}</span>
              </th>
              <th onClick={() => handleSort('merchant')} className="sortable">
                🏪 Merchant
                <span className="sort-icon">{sortConfig.key === 'merchant' ? (sortConfig.direction === 'asc' ? '↑' : '↓') : '⇅'}</span>
              </th>
              <th onClick={() => handleSort('category')} className="sortable">
                🏷️ Category
                <span className="sort-icon">{sortConfig.key === 'category' ? (sortConfig.direction === 'asc' ? '↑' : '↓') : '⇅'}</span>
              </th>
              <th onClick={() => handleSort('amount')} className="sortable">
                💰 Amount
                <span className="sort-icon">{sortConfig.key === 'amount' ? (sortConfig.direction === 'asc' ? '↑' : '↓') : '⇅'}</span>
              </th>
              <th onClick={() => handleSort('source')} className="sortable">
                📄 Source
                <span className="sort-icon">{sortConfig.key === 'source' ? (sortConfig.direction === 'asc' ? '↑' : '↓') : '⇅'}</span>
              </th>
              <th>📝 Description</th>
              <th>🔍 Details</th>
            </tr>
          </thead>
          <tbody>
            {sortedTransactions.length > 0 ? (
              sortedTransactions.map((transaction, index) => (
                <tr key={transaction.id || index} className="transaction-row">
                  <td className="date-cell">{transaction.date}</td>
                  <td className="bank-cell">
                    <span className={`bank-badge ${(transaction.bank || 'Kotak Mahindra Bank').toLowerCase().replace(/[^a-z0-9]/g, '-')}`}>
                      {transaction.bank === 'ICICI Bank' ? '🦁 ICICI Bank' : '🛡️ Kotak Bank'}
                    </span>
                  </td>
                  <td className="merchant-cell">{transaction.merchant}</td>
                  <td className="category-cell">
                    <span className={`category-badge ${(transaction.category || 'other').toLowerCase().replace(/[^a-z0-9]/g, '-')}`}>
                      {getCategoryIcon(transaction.category)} {transaction.category}
                    </span>
                  </td>
                  <td className="amount-cell">
                    <span className="amount-badge">{transaction.amount}</span>
                  </td>
                  <td className="source-cell">{transaction.source}</td>
                  <td className="description-cell">
                    <span className="description-text">{transaction.description}</span>
                  </td>
                  <td className="details-cell">
                    <button
                      className="details-button"
                      title="View full transaction details"
                      onClick={() => setSelectedTransaction(transaction)}
                    >
                      View
                    </button>
                  </td>
                </tr>
              ))
            ) : (
              <tr>
                <td colSpan="8" className="no-data">
                  📭 No transactions found{filterText && ' matching your search'}{selectedCategory !== 'all' && ' in this category'}
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>

      {/* Footer */}
      <div className="table-footer">
        <span className="footer-text">
          Showing <strong>{sortedTransactions.length}</strong> of <strong>{transactions.length}</strong> transactions
        </span>
        <button className="refresh-button" onClick={fetchTransactions}>
          🔄 Refresh
        </button>
      </div>

      {/* Transaction Details Modal */}
      {selectedTransaction && (
        <div className="modal-overlay" onClick={() => setSelectedTransaction(null)}>
          <div className="modal-content animate-slide-in" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h3>🔍 Transaction Insight</h3>
              <button className="modal-close" onClick={() => setSelectedTransaction(null)}>✕</button>
            </div>
            <div className="modal-body">
              <div className="modal-hero">
                <div className="modal-amount-container">
                  <span className="modal-amount-label">Amount</span>
                  <div className="modal-amount-value">{selectedTransaction.amount}</div>
                </div>
                <div className="modal-merchant-title">{selectedTransaction.merchant}</div>
              </div>
              <div className="modal-info-grid">
                <div className="modal-info-card">
                  <span className="modal-info-label">📅 Date</span>
                  <span className="modal-info-value">{selectedTransaction.date}</span>
                </div>
                <div className="modal-info-card">
                  <span className="modal-info-label">🏦 Bank</span>
                  <span className="modal-info-value">{selectedTransaction.bank || 'Kotak Mahindra Bank'}</span>
                </div>
                <div className="modal-info-card">
                  <span className="modal-info-label">🏷️ Category</span>
                  <span className="modal-info-value">
                    {getCategoryIcon(selectedTransaction.category)} {selectedTransaction.category}
                  </span>
                </div>
                <div className="modal-info-card">
                  <span className="modal-info-label">📄 Source File</span>
                  <span className="modal-info-value">{selectedTransaction.source}</span>
                </div>
              </div>
              <div className="modal-description-section">
                <h4>📝 Statement Description</h4>
                <p className="modal-description-text">{selectedTransaction.description}</p>
              </div>
              <div className="modal-raw-section">
                <h4>📜 Extracted Text Context (Vector Raw)</h4>
                <div className="modal-raw-wrapper">
                  <pre className="modal-raw-text">{selectedTransaction.fullText}</pre>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default TransactionTable;
