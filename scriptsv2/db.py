import sqlite3

DB_NAME = 'trades.db'

def create_connection():
    conn = sqlite3.connect(DB_NAME)
    return conn

def create_table():
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS trades (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        ticker TEXT NOT NULL,
        strategy_name TEXT NOT NULL,
        current_price REAL NOT NULL,
        date_alerted DATE NOT NULL,
        expiration_date DATE NOT NULL,
        option_type TEXT NOT NULL,
        strike_price REAL NOT NULL,
        status TEXT
    )
    ''')
    cursor.execute('DELETE FROM trades')

    conn.commit()
    conn.close()

def get_all_trades(ticker_list):
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM trades WHERE ticker IN ({})'.format(','.join('?' * len(ticker_list))), ticker_list)
    trades = cursor.fetchall()
    conn.close()
    return trades

def save_trade_to_db(trade, status):
    conn = create_connection()
    cursor = conn.cursor()
    
    # First check if trade already exists
    cursor.execute('''
    SELECT id FROM trades 
    WHERE ticker = ? 
    AND strategy_name = ? 
    AND expiration_date = ? 
    AND option_type = ? 
    AND strike_price = ?
    ''', (trade.ticker, trade.strategy_name, 
          trade.expiration_date.strftime('%Y-%m-%d'),
          trade.option_type, trade.strike_price))
    
    existing_trade = cursor.fetchone()
    
    if existing_trade:
        # Trade already exists, don't insert
        conn.close()
        return False
        
    # Trade doesn't exist, proceed with insert
    cursor.execute('''
    INSERT INTO trades (ticker, strategy_name, current_price, date_alerted, 
                       expiration_date, option_type, strike_price, status)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    ''', (trade.ticker, trade.strategy_name, trade.current_price,
          trade.date_alerted.strftime('%Y-%m-%d'), 
          trade.expiration_date.strftime('%Y-%m-%d'),
          trade.option_type, trade.strike_price, status))
    
    conn.commit()
    conn.close()
    return True

def get_trades_for_streak(ticker, check_date_str):
    conn = create_connection()
    cursor = conn.cursor()
    
    # Get trades up to check_date ordered by date descending
    cursor.execute("""
        SELECT date_alerted, status
        FROM trades 
        WHERE date_alerted <= ?
        AND status IS NOT NULL 
        AND ticker = ?
        ORDER BY date_alerted DESC
    """, (check_date_str, ticker))
    
    trades = cursor.fetchall()
    conn.close()
    return trades

def get_expired_trades(check_date_str):
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id, ticker, strategy_name, current_price, date_alerted, 
               expiration_date, option_type, strike_price 
        FROM trades 
        WHERE status IS NULL 
        AND expiration_date <= ?
        AND date_alerted <= ?
    """, (check_date_str, check_date_str))
    trades = cursor.fetchall()
    conn.close()
    return trades

def update_trade_status(trade_id, status):
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE trades 
        SET status = ? 
        WHERE id = ?
    """, (status, trade_id))
    conn.commit()
    conn.close()

def check_duplicate_trades(trade, date_limit_str, check_date_str):
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT COUNT(*) 
        FROM trades 
        WHERE ticker = ? 
        AND strategy_name = ? 
        AND expiration_date = ? 
        AND date_alerted BETWEEN ? AND ?
    """, (
        trade.ticker,
        trade.strategy_name,
        trade.expiration_date.strftime('%Y-%m-%d'),
        date_limit_str,
        check_date_str
    ))
    count = cursor.fetchone()[0]
    conn.close()
    return count
