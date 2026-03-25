import sqlite3
import datetime
import logging
from config import Config

logger = logging.getLogger(__name__)

def get_connection():
    return sqlite3.connect(Config.DATABASE_PATH)

def init_db():
    conn = get_connection()
    cursor = conn.cursor()
    
    # Bankroll table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS bankroll (
            id INTEGER PRIMARY KEY CHECK (id = 1),
            amount REAL,
            updated_at TIMESTAMP
        )
    ''')
    
    # Bets table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS bets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sport TEXT,
            game_id TEXT,
            home_team TEXT,
            away_team TEXT,
            market_type TEXT,
            
            book_a TEXT,
            outcome_a TEXT,
            odds_a INTEGER,
            stake_a REAL,
            
            book_b TEXT,
            outcome_b TEXT,
            odds_b INTEGER,
            stake_b REAL,
            
            guaranteed_profit REAL,
            guaranteed_profit_pct REAL,
            
            placed_at TIMESTAMP,
            status TEXT, -- 'OPEN', 'SETTLED'
            settled_at TIMESTAMP,
            result_profit REAL
        )
    ''')
    
    # Initialize bankroll if empty
    cursor.execute('SELECT amount FROM bankroll WHERE id = 1')
    if not cursor.fetchone():
        cursor.execute(
            'INSERT INTO bankroll (id, amount, updated_at) VALUES (1, ?, ?)',
            (Config.STARTING_BANKROLL, datetime.datetime.now())
        )
        
    # Config table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS config (
            key TEXT PRIMARY KEY,
            value TEXT
        )
    ''')
    
    defaults = {
        'arb_threshold': str(Config.MIN_PROFIT_MARGIN),
        'max_stake_pct': str(Config.MAX_STAKE_PCT),
        'max_open_bets': str(Config.MAX_OPEN_BETS),
        'polling_paused': 'false'
    }
    for k, v in defaults.items():
        cursor.execute('INSERT OR IGNORE INTO config (key, value) VALUES (?, ?)', (k, v))
        
    conn.commit()
    conn.close()

def get_bankroll() -> float:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT amount FROM bankroll WHERE id = 1')
    row = cursor.fetchone()
    conn.close()
    return row[0] if row else 0.0

def update_bankroll(new_amount: float):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        'UPDATE bankroll SET amount = ?, updated_at = ? WHERE id = 1',
        (new_amount, datetime.datetime.now())
    )
    conn.commit()
    conn.close()

def get_config(key: str, default: str = None) -> str:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT value FROM config WHERE key = ?', (key,))
    row = cursor.fetchone()
    conn.close()
    return row[0] if row else default

def set_config(key: str, value: str):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        'INSERT INTO config (key, value) VALUES (?, ?) ON CONFLICT(key) DO UPDATE SET value=excluded.value',
        (key, str(value))
    )
    conn.commit()
    conn.close()

def save_bet(bet_data: dict) -> int:
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        INSERT INTO bets (
            sport, game_id, home_team, away_team, market_type,
            book_a, outcome_a, odds_a, stake_a,
            book_b, outcome_b, odds_b, stake_b,
            guaranteed_profit, guaranteed_profit_pct,
            placed_at, status
        ) VALUES (
            :sport, :game_id, :home_team, :away_team, :market_type,
            :book_a, :outcome_a, :odds_a, :stake_a,
            :book_b, :outcome_b, :odds_b, :stake_b,
            :guaranteed_profit, :guaranteed_profit_pct,
            :placed_at, 'OPEN'
        )
    ''', {
        **bet_data,
        'placed_at': datetime.datetime.now()
    })
    
    bet_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return bet_id

def get_open_bets() -> list:
    conn = get_connection()
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM bets WHERE status = 'OPEN'")
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]

def get_open_bet_count() -> int:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM bets WHERE status = 'OPEN'")
    count = cursor.fetchone()[0]
    conn.close()
    return count

def get_recent_bets(limit=5) -> list:
    conn = get_connection()
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM bets ORDER BY placed_at DESC LIMIT ?", (limit,))
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]

def settle_bet(bet_id: int, result_profit: float):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        UPDATE bets 
        SET status = 'SETTLED', settled_at = ?, result_profit = ?
        WHERE id = ?
    ''', (datetime.datetime.now(), result_profit, bet_id))
    conn.commit()
    conn.close()
    
def get_daily_pnl() -> dict:
    conn = get_connection()
    cursor = conn.cursor()
    
    today_start = datetime.datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    
    cursor.execute('''
        SELECT COUNT(*), SUM(result_profit) 
        FROM bets 
        WHERE status = 'SETTLED' AND settled_at >= ?
    ''', (today_start,))
    
    row = cursor.fetchone()
    conn.close()
    
    return {
        'settled_today': row[0] or 0,
        'profit_today': row[1] or 0.0
    }
