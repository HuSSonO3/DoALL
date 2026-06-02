import sqlite3
from shared import db_path

DB_PATH = db_path("tabs", "money", "money.db")


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db():
    conn = get_db()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS accounts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,
            type TEXT NOT NULL DEFAULT 'general',
            balance REAL NOT NULL DEFAULT 0,
            created_at TEXT DEFAULT (datetime('now'))
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS categories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,
            type TEXT NOT NULL CHECK(type IN ('income', 'expense')),
            created_at TEXT DEFAULT (datetime('now'))
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT NOT NULL,
            amount REAL NOT NULL,
            type TEXT NOT NULL CHECK(type IN ('income', 'expense')),
            account_id INTEGER NOT NULL,
            category_id INTEGER NOT NULL,
            note TEXT DEFAULT '',
            created_at TEXT DEFAULT (datetime('now')),
            FOREIGN KEY (account_id) REFERENCES accounts(id) ON DELETE RESTRICT,
            FOREIGN KEY (category_id) REFERENCES categories(id) ON DELETE RESTRICT
        )
    """)
    conn.commit()
    conn.close()


# ── Accounts ──

def add_account(name, acct_type="general"):
    conn = get_db()
    try:
        cur = conn.execute(
            "INSERT INTO accounts (name, type) VALUES (?, ?)",
            (name, acct_type)
        )
        conn.commit()
        return cur.lastrowid
    except sqlite3.IntegrityError:
        return None
    finally:
        conn.close()


def get_accounts():
    conn = get_db()
    rows = conn.execute(
        "SELECT * FROM accounts ORDER BY name"
    ).fetchall()
    conn.close()
    return rows


def get_account_txn_count(account_id):
    conn = get_db()
    row = conn.execute(
        "SELECT COUNT(*) as c FROM transactions WHERE account_id = ?",
        (account_id,)
    ).fetchone()
    conn.close()
    return row["c"]


def delete_account(account_id, force=False):
    conn = get_db()
    try:
        if force:
            conn.execute("DELETE FROM transactions WHERE account_id = ?", (account_id,))
        conn.execute("DELETE FROM accounts WHERE id = ?", (account_id,))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False
    finally:
        conn.close()


def recalc_account_balances():
    """Recalculate cached balance for every account from transactions."""
    conn = get_db()
    conn.execute("UPDATE accounts SET balance = 0")
    rows = conn.execute("""
        SELECT account_id, type, SUM(amount) as total
        FROM transactions
        GROUP BY account_id, type
    """).fetchall()
    for row in rows:
        delta = row["total"] if row["type"] == "income" else -row["total"]
        conn.execute(
            "UPDATE accounts SET balance = balance + ? WHERE id = ?",
            (delta, row["account_id"])
        )
    conn.commit()
    conn.close()


# ── Categories ──

def add_category(name, cat_type):
    conn = get_db()
    try:
        cur = conn.execute(
            "INSERT INTO categories (name, type) VALUES (?, ?)",
            (name, cat_type)
        )
        conn.commit()
        return cur.lastrowid
    except sqlite3.IntegrityError:
        return None
    finally:
        conn.close()


def get_categories(cat_type=None):
    conn = get_db()
    if cat_type:
        rows = conn.execute(
            "SELECT * FROM categories WHERE type = ? ORDER BY name",
            (cat_type,)
        ).fetchall()
    else:
        rows = conn.execute(
            "SELECT * FROM categories ORDER BY type, name"
        ).fetchall()
    conn.close()
    return rows


def get_category_txn_count(category_id):
    conn = get_db()
    row = conn.execute(
        "SELECT COUNT(*) as c FROM transactions WHERE category_id = ?",
        (category_id,)
    ).fetchone()
    conn.close()
    return row["c"]


def delete_category(category_id, force=False):
    conn = get_db()
    try:
        if force:
            conn.execute("DELETE FROM transactions WHERE category_id = ?", (category_id,))
        conn.execute("DELETE FROM categories WHERE id = ?", (category_id,))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False
    finally:
        conn.close()


# ── Transactions ──

def add_transaction(date, amount, txn_type, account_id, category_id, note=""):
    conn = get_db()
    cur = conn.execute(
        """INSERT INTO transactions (date, amount, type, account_id, category_id, note)
           VALUES (?, ?, ?, ?, ?, ?)""",
        (date, amount, txn_type, account_id, category_id, note)
    )
    conn.commit()
    txn_id = cur.lastrowid
    # Update account balance
    delta = amount if txn_type == "income" else -amount
    conn.execute(
        "UPDATE accounts SET balance = balance + ? WHERE id = ?",
        (delta, account_id)
    )
    conn.commit()
    conn.close()
    return txn_id


def get_transactions(month=None, account_id=None, category_id=None, txn_type=None):
    conn = get_db()
    query = """
        SELECT t.*, a.name as account_name, c.name as category_name
        FROM transactions t
        JOIN accounts a ON t.account_id = a.id
        JOIN categories c ON t.category_id = c.id
        WHERE 1=1
    """
    params = []
    if month:
        query += " AND strftime('%Y-%m', t.date) = ?"
        params.append(month)
    if account_id:
        query += " AND t.account_id = ?"
        params.append(account_id)
    if category_id:
        query += " AND t.category_id = ?"
        params.append(category_id)
    if txn_type:
        query += " AND t.type = ?"
        params.append(txn_type)
    query += " ORDER BY t.date DESC, t.id DESC"
    rows = conn.execute(query, params).fetchall()
    conn.close()
    return rows


def delete_transaction(txn_id):
    conn = get_db()
    txn = conn.execute("SELECT * FROM transactions WHERE id = ?", (txn_id,)).fetchone()
    if txn:
        delta = txn["amount"] if txn["type"] == "income" else -txn["amount"]
        conn.execute(
            "UPDATE accounts SET balance = balance - ? WHERE id = ?",
            (delta, txn["account_id"])
        )
        conn.execute("DELETE FROM transactions WHERE id = ?", (txn_id,))
        conn.commit()
        conn.close()
        return True
    conn.close()
    return False


def get_distinct_months():
    conn = get_db()
    rows = conn.execute(
        """SELECT DISTINCT strftime('%Y-%m', date) as month
           FROM transactions
           WHERE date IS NOT NULL AND date GLOB '[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9]'
           ORDER BY month DESC"""
    ).fetchall()
    conn.close()
    return [r["month"] for r in rows if r["month"] is not None]


# ── Summary ──

def get_summary(month=None, account_id=None):
    conn = get_db()
    params_inc = []
    params_exp = []
    month_clause = ""
    acct_clause = ""
    if month:
        month_clause = " AND strftime('%Y-%m', t.date) = ?"
        params_inc.append(month)
        params_exp.append(month)
    if account_id:
        acct_clause = " AND t.account_id = ?"
        params_inc.append(account_id)
        params_exp.append(account_id)

    # Totals
    income_row = conn.execute(
        f"""SELECT COALESCE(SUM(amount), 0) as total FROM transactions t
            WHERE type = 'income'{month_clause}{acct_clause}""",
        params_inc
    ).fetchone()
    expense_row = conn.execute(
        f"""SELECT COALESCE(SUM(amount), 0) as total FROM transactions t
            WHERE type = 'expense'{month_clause}{acct_clause}""",
        params_exp
    ).fetchone()

    total_income = income_row["total"]
    total_expenses = expense_row["total"]

    # By category — use a correlated approach: join on category, filter in ON clause
    cat_params = []
    cat_conditions = ""
    if month:
        cat_conditions += " AND strftime('%Y-%m', t.date) = ?"
        cat_params.append(month)
    if account_id:
        cat_conditions += " AND t.account_id = ?"
        cat_params.append(account_id)

    cat_rows = conn.execute(
        f"""SELECT c.name, c.type, COALESCE(SUM(t.amount), 0) as total
            FROM categories c
            LEFT JOIN transactions t ON c.id = t.category_id{cat_conditions}
            GROUP BY c.id
            ORDER BY total DESC""",
        cat_params
    ).fetchall()

    conn.close()
    return {
        "total_income": total_income,
        "total_expenses": total_expenses,
        "net_balance": total_income - total_expenses,
        "category_breakdown": [dict(r) for r in cat_rows],
    }


def seed_defaults():
    """Seed default accounts and categories if tables are empty."""
    conn = get_db()
    acct_count = conn.execute("SELECT COUNT(*) as c FROM accounts").fetchone()["c"]
    if acct_count == 0:
        conn.execute("INSERT INTO accounts (name, type) VALUES ('Cash', 'cash')")
        conn.execute("INSERT INTO accounts (name, type) VALUES ('Bank', 'bank')")
    cat_count = conn.execute("SELECT COUNT(*) as c FROM categories").fetchone()["c"]
    if cat_count == 0:
        for name in ["Salary", "Freelance", "Investments", "Gifts"]:
            conn.execute("INSERT INTO categories (name, type) VALUES (?, 'income')", (name,))
        for name in ["Food", "Rent", "Transport", "Utilities", "Entertainment", "Shopping", "Health", "Education"]:
            conn.execute("INSERT INTO categories (name, type) VALUES (?, 'expense')", (name,))
    conn.commit()
    conn.close()
