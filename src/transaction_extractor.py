"""
Transaction Extractor Module
Extracts and structures transaction details from bank statements
Focuses on spending patterns: merchant, amount, category, date
"""
import logging
import re
from typing import List, Dict, Any
from datetime import datetime

logger = logging.getLogger(__name__)


class TransactionExtractor:
    """Extract and structure transaction details from bank statements"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        # Patterns to identify transaction rows
        self.transaction_pattern = re.compile(
            r'(\d{1,2}-\w{3}-\d{4})\s+(.+?)\s{2,}(\w+(?:\s+&\s+\w+)?)\s+([\d,]+\.?\d*)',
            re.MULTILINE
        )
    
    def _parse_icici_amount(self, val_str: str) -> float:
        """Parse squashed credit card transaction amounts cleanly using heuristics"""
        if "," in val_str:
            parts = val_str.split(",")
            first_part = parts[0]
            thousands_digit = first_part[-1]
            amount_str = thousands_digit + "," + ",".join(parts[1:])
            return float(amount_str.replace(",", ""))
        
        parts = val_str.split(".")
        integer_part = parts[0]
        decimal_part = parts[1]
        
        if len(integer_part) >= 4:
            last_4 = int(integer_part[-4:])
            if last_4 < 2000:
                return float(f"{last_4}.{decimal_part}")
            else:
                return float(f"{integer_part[-3:]}.{decimal_part}")
        elif len(integer_part) == 3:
            return float(val_str)
        elif len(integer_part) <= 2:
            if integer_part.startswith("0") and len(integer_part) > 1:
                return float(f"{integer_part[1:]}.{decimal_part}")
            return float(val_str)
            
        return float(val_str)

    def _guess_category(self, merchant: str) -> str:
        """Categorize merchant using common brand mapping keyword matches"""
        merchant_lower = merchant.lower()
        if any(w in merchant_lower for w in ['coffee', 'tokai', 'zomato', 'food', 'restaurant', 'cafe', 'sweets', 'kanti', 'bhukkad', 'dining', 'starbucks', 'pizza', 'mcdonalds', 'kfc', 'dominos', 'burger', 'burrito', 'california']):
            return 'Dining & Food'
        elif any(w in merchant_lower for w in ['myntra', 'fashion', 'clothing', 'apparel', 'shoes', 'adidas', 'nike', 'zara', 'h&m', 'lifestyle', 'fashnear', 'meesho']):
            return 'Lifestyle & Fashion'
        elif any(w in merchant_lower for w in ['bigbasket', 'grocery', 'supermarket', 'mart', 'groceries', 'basket', 'spencer', 'reliance fresh', 'blinkit', 'zepto', 'gramiq', 'hypermart', 'fruits', 'anusuya', 'ibrahim', 'radhakrishnam', 'manjunatha']):
            return 'Grocery & Supermarket'
        elif any(w in merchant_lower for w in ['uber', 'olacabs', 'ola', 'transport', 'taxi', 'cab', 'travel', 'flight', 'irctc', 'rail', 'metro', 'kanchan kumar']):
            return 'Travel & Transport'
        elif any(w in merchant_lower for w in ['bookmyshow', 'show', 'movie', 'cinema', 'netflix', 'prime', 'spotify', 'gaming', 'steam', 'playstation', 'xbox', 'entertainment']):
            return 'Entertainment & Gaming'
        elif any(w in merchant_lower for w in ['hospital', 'apollo', 'medical', 'medicine', 'pharmacy', 'health', 'wellness', 'clinic', 'doctor', 'dentist']):
            return 'Health & Wellness'
        elif any(w in merchant_lower for w in ['electricity', 'power', 'water', 'gas', 'bill', 'utilities', 'recharge', 'myjio', 'jio', 'airtel', 'idea', 'vodafone', 'bsnl', 'broadband', 'act', 'tata sky', 'dth']):
            return 'Utilities & Services'
        elif any(w in merchant_lower for w in ['surcharge', 'fuel', 'petrol', 'diesel', 'shell', 'hpcl', 'bpcl', 'iocl', 'cng']):
            return 'Automotive'
        elif any(w in merchant_lower for w in ['school', 'college', 'university', 'education', 'fees', 'tuition', 'udemy', 'coursera', 'edx', 'learning']):
            return 'Education'
        return 'Other'

    def extract_transactions(self, text: str, source: str = "statement") -> List[Dict[str, Any]]:
        """
        Extract transaction details from bank statement text
        
        Args:
            text: Text from bank statement PDF
            source: Source identifier (e.g., "kotak.pdf")
            
        Returns:
            List of transaction dictionaries
        """
        # 1. First check if this is an ICICI Bank statement style or a squashed single-line statement
        text_lower = text.lower()
        if "dateserno.transaction details" in text_lower or ("icici" in text_lower and len(re.findall(r'\d{2}/\d{2}/\d{4}', text)) > 5):
            self.logger.info(f"Using relaxed ICICI/single-line split parsing for {source}")
            transactions = []
            
            # Find all dates in text
            dates = re.findall(r'(\d{2}/\d{2}/\d{4})', text)
            parts = re.split(r'(\d{2}/\d{2}/\d{4})', text)
            
            i = 1
            while i < len(parts) - 1:
                date_str = parts[i]
                content = parts[i+1].strip()
                
                # Check if this segment contains an amount (e.g. 10515.00)
                amount_match = re.search(r'([\d,]+\.\d{2})\s*(CR)?', content)
                if amount_match:
                    raw_amt_str = amount_match.group(1)
                    is_credit = bool(amount_match.group(2))
                    
                    # Parse amount using our advanced heuristic
                    amount = self._parse_icici_amount(raw_amt_str)
                    
                    # Extract merchant / description
                    middle = content[:amount_match.start()].strip()
                    middle_clean = re.sub(r'^\d+', '', middle).strip()
                    middle_clean = re.sub(r'\s*\d+$', '', middle_clean).strip()
                    
                    merchant = middle_clean
                    if merchant.endswith(" IN"):
                        merchant = merchant[:-3].strip()
                    words = merchant.split()
                    if len(words) > 2 and words[-1].isupper() and len(words[-1]) > 3:
                        merchant = " ".join(words[:-1])
                    
                    # Categorize merchant
                    category = self._guess_category(merchant)
                    
                    # Convert Date format from DD/MM/YYYY to DD-MMM-YYYY
                    try:
                        dt = datetime.strptime(date_str, "%d/%m/%Y")
                        formatted_date = dt.strftime("%d-%b-%Y")
                    except Exception:
                        formatted_date = date_str
                    
                    transaction = {
                        'date': formatted_date,
                        'description': merchant,
                        'category': category,
                        'amount': amount,
                        'amount_formatted': f"₹{amount:,.2f}" if not is_credit else f"₹{amount:,.2f} (Cr)",
                        'is_credit': is_credit,
                        'source': source,
                        'section': 'Purchases made in this cycle - Primary Card'
                    }
                    transactions.append(transaction)
                i += 2
                
            self.logger.info(f"Extracted {len(transactions)} transactions via ICICI splitter")
            return transactions

        # 2. Standard row-by-row parsing (Kotak, etc.)
        transactions = []
        lines = text.split('\n')
        
        # Skip to transactions section
        transaction_start = -1
        for i, line in enumerate(lines):
            if 'Transactions Details' in line or 'Purchases made' in line:
                transaction_start = i
                break
        
        if transaction_start == -1:
            self.logger.warning(f"No transactions section found in {source}")
            return []
        
        current_section = None
        
        # Parse transactions line by line
        for i in range(transaction_start + 1, len(lines)):
            line = lines[i].strip()
            
            # Skip empty lines
            if not line:
                continue
            
            # Detect section headers or end markers
            if any(marker in line for marker in ['Payments', 'Purchases', 'Credits', 'GST applicable', 'Total Purchases']):
                if 'Payments' in line or 'Purchases' in line or 'Credits' in line:
                    current_section = line
                continue
            
            # Skip header row
            if any(header in line for header in ['Date', 'Description', 'Spends', 'Amount', 'Category']):
                continue
            
            # Try to parse transaction line
            # Format: Date Description Category Amount
            
            # Match date pattern at start (DD-MMM-YYYY)
            date_match = re.match(r'^(\d{1,2}-\w{3}-\d{4})\s+(.+)', line)
            
            if date_match:
                try:
                    date_str = date_match.group(1)
                    rest = date_match.group(2)
                    
                    # Extract amount (ends with number, possibly with Cr)
                    amount_match = re.search(r'\s([\d,]+\.?\d*)\s*(Cr)?$', rest)
                    
                    if amount_match:
                        amount_str = amount_match.group(1).replace(',', '')
                        try:
                            amount = float(amount_str)
                        except ValueError:
                            continue
                        
                        is_credit = bool(amount_match.group(2))
                        
                        # Extract description and category from the middle part
                        description_part = rest[:amount_match.start()].strip()
                        
                        # Try to separate description and category
                        # Usually the last word or two words are the category
                        parts = description_part.split()
                        
                        if len(parts) >= 2:
                            # Category is often the last token(s) before amount
                            # For UPI transactions: UPI-XXXXX-NAME Category
                            if 'UPI' in description_part:
                                # Find category - it comes after the name
                                words = description_part.split()
                                # Usually category is 1-2 words at the end
                                if len(words) >= 2:
                                    category = ' '.join(words[-2:]) if '&' in description_part else words[-1]
                                    description = ' '.join(words[:-2] if '&' in description_part else words[:-1])
                                else:
                                    category = words[-1] if words else "Other"
                                    description = ' '.join(words[:-1]) if len(words) > 1 else description_part
                            else:
                                # Non-UPI transaction
                                words = description_part.split()
                                category = words[-1] if words else "Other"
                                description = ' '.join(words[:-1]) if len(words) > 1 else description_part
                        else:
                            description = description_part
                            category = "Other"
                        
                        # Skip if this looks like a header or total line
                        if any(skip in description for skip in ['Total', 'GST', 'Due', 'Previous']):
                            continue
                        if description.isupper() and len(description) < 10:
                            continue
                        
                        # Skip if description is too short
                        if len(description.strip()) < 3:
                            continue
                        
                        transaction = {
                            'date': date_str,
                            'description': description.strip(),
                            'category': category.strip(),
                            'amount': amount,
                            'amount_formatted': f"₹{amount:,.2f}" if not is_credit else f"₹{amount:,.2f} (Cr)",
                            'is_credit': is_credit,
                            'source': source,
                            'section': current_section or 'Purchases'
                        }
                        transactions.append(transaction)
                
                except (ValueError, IndexError) as e:
                    self.logger.debug(f"Could not parse transaction line: {line}")
                    continue
        
        self.logger.info(f"Extracted {len(transactions)} transactions from {source}")
        return transactions
    
    def create_transaction_chunks(self, transactions: List[Dict[str, Any]], 
                                 chunk_size: int = 5) -> List[Dict[str, Any]]:
        """
        Create chunks grouping multiple transactions together
        
        Args:
            transactions: List of transaction dictionaries
            chunk_size: Number of transactions per chunk
            
        Returns:
            List of chunk dictionaries
        """
        chunks = []
        
        for i in range(0, len(transactions), chunk_size):
            transaction_group = transactions[i:i + chunk_size]
            
            # Create chunk content
            chunk_content = self._format_transaction_chunk(transaction_group)
            
            chunk = {
                'id': f"transaction_chunk_{i // chunk_size}",
                'content': chunk_content,
                'transactions': transaction_group,
                'transaction_count': len(transaction_group),
                'total_amount': sum(t['amount'] for t in transaction_group),
                'categories': list(set(t['category'] for t in transaction_group)),
                'source': transaction_group[0]['source'] if transaction_group else 'unknown',
                'date_range': f"{transaction_group[0]['date']} to {transaction_group[-1]['date']}" if transaction_group else '',
                'type': 'transaction_group'
            }
            chunks.append(chunk)
        
        self.logger.info(f"Created {len(chunks)} transaction chunks from {len(transactions)} transactions")
        return chunks
    
    def _format_transaction_chunk(self, transactions: List[Dict[str, Any]]) -> str:
        """Format transactions into readable chunk content"""
        lines = []
        
        for i, txn in enumerate(transactions, 1):
            line = (f"{i}. {txn['date']} - {txn['description']} "
                   f"({txn['category']}) - {txn['amount_formatted']}")
            lines.append(line)
        
        return '\n'.join(lines)
    
    def create_spending_summary_chunks(self, transactions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Create summary chunks grouped by category
        
        Args:
            transactions: List of transaction dictionaries
            
        Returns:
            List of spending summary chunks
        """
        chunks = []
        
        # Group by category
        category_spending = {}
        for txn in transactions:
            category = txn['category']
            if category not in category_spending:
                category_spending[category] = {
                    'total': 0,
                    'count': 0,
                    'transactions': []
                }
            category_spending[category]['total'] += txn['amount']
            category_spending[category]['count'] += 1
            category_spending[category]['transactions'].append(txn)
        
        # Create chunks for each category
        for category, data in sorted(category_spending.items(), 
                                     key=lambda x: x[1]['total'], 
                                     reverse=True):
            
            # Format transactions in this category
            txn_list = '\n'.join([
                f"  • {t['date']} - {t['description']} - {t['amount_formatted']}"
                for t in data['transactions']
            ])
            
            content = (f"Category: {category}\n"
                      f"Total Spent: ₹{data['total']:,.2f}\n"
                      f"Transactions: {data['count']}\n\n"
                      f"Details:\n{txn_list}")
            
            chunk = {
                'id': f"spending_summary_{category.lower().replace(' ', '_')}",
                'content': content,
                'category': category,
                'total_amount': data['total'],
                'transaction_count': data['count'],
                'source': transactions[0]['source'] if transactions else 'unknown',
                'type': 'spending_summary'
            }
            chunks.append(chunk)
        
        self.logger.info(f"Created {len(chunks)} spending summary chunks for {len(category_spending)} categories")
        return chunks
