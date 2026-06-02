import sqlite3
from shared import db_path

DB_PATH = db_path("tabs", "budget", "budget.db")


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db():
    conn = get_db()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS monthly_budgets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            month TEXT NOT NULL UNIQUE,
            total_budget REAL NOT NULL DEFAULT 0,
            created_at TEXT DEFAULT (datetime('now'))
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS budget_categories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            budget_id INTEGER NOT NULL,
            name TEXT NOT NULL,
            budget_amount REAL NOT NULL,
            budget_impact TEXT NOT NULL DEFAULT 'stagnant'
                CHECK(budget_impact IN ('increase', 'decrease', 'stagnant')),
            created_at TEXT DEFAULT (datetime('now')),
            FOREIGN KEY (budget_id) REFERENCES monthly_budgets(id) ON DELETE CASCADE,
            UNIQUE(budget_id, name)
        )
    """)
    # Migration: add budget_impact column if upgrading from older schema
    try:
        conn.execute("ALTER TABLE budget_categories ADD COLUMN budget_impact TEXT NOT NULL DEFAULT 'stagnant'")
    except sqlite3.OperationalError:
        pass  # column already exists
    conn.execute("""
        CREATE TABLE IF NOT EXISTS budget_transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            budget_id INTEGER NOT NULL,
            category_id INTEGER NOT NULL,
            date TEXT NOT NULL,
            amount REAL NOT NULL,
            note TEXT DEFAULT '',
            created_at TEXT DEFAULT (datetime('now')),
            FOREIGN KEY (budget_id) REFERENCES monthly_budgets(id) ON DELETE CASCADE,
            FOREIGN KEY (category_id) REFERENCES budget_categories(id) ON DELETE RESTRICT
        )
    """)
    conn.commit()
    conn.close()


# ── Budgets ──

def get_or_create_budget(month):
    """Get the budget_id for a month, creating it with total=0 if it doesn't exist."""
    conn = get_db()
    row = conn.execute(
        "SELECT id, total_budget FROM monthly_budgets WHERE month = ?", (month,)
    ).fetchone()
    if row:
        conn.close()
        return row["id"], row["total_budget"]
    cur = conn.execute(
        "INSERT INTO monthly_budgets (month, total_budget) VALUES (?, 0)", (month,)
    )
    conn.commit()
    bid = cur.lastrowid
    conn.close()
    return bid, 0.0


def update_total_budget(budget_id, amount):
    conn = get_db()
    conn.execute(
        "UPDATE monthly_budgets SET total_budget = ? WHERE id = ?",
        (amount, budget_id)
    )
    conn.commit()
    conn.close()


def get_total_budget(budget_id):
    conn = get_db()
    row = conn.execute(
        "SELECT total_budget FROM monthly_budgets WHERE id = ?", (budget_id,)
    ).fetchone()
    conn.close()
    return row["total_budget"] if row else 0.0


# ── Budget Categories ──

def add_budget_category(budget_id, name, amount, impact="stagnant"):
    conn = get_db()
    try:
        cur = conn.execute(
            "INSERT INTO budget_categories (budget_id, name, budget_amount, budget_impact) "
            "VALUES (?, ?, ?, ?)",
            (budget_id, name, amount, impact)
        )
        conn.commit()
        return cur.lastrowid
    except sqlite3.IntegrityError:
        return None
    finally:
        conn.close()


def get_budget_categories(budget_id):
    conn = get_db()
    rows = conn.execute(
        "SELECT * FROM budget_categories WHERE budget_id = ? ORDER BY budget_impact, name",
        (budget_id,)
    ).fetchall()
    conn.close()
    return rows


def get_category_sum(budget_id, exclude_id=None):
    """Sum of all category budgets for a budget, optionally excluding one."""
    conn = get_db()
    if exclude_id:
        row = conn.execute(
            "SELECT COALESCE(SUM(budget_amount), 0) as total FROM budget_categories "
            "WHERE budget_id = ? AND id != ?",
            (budget_id, exclude_id)
        ).fetchone()
    else:
        row = conn.execute(
            "SELECT COALESCE(SUM(budget_amount), 0) as total FROM budget_categories "
            "WHERE budget_id = ?",
            (budget_id,)
        ).fetchone()
    conn.close()
    return row["total"]


def delete_budget_category(category_id, budget_id):
    conn = get_db()
    # Look up category details before deleting
    cat = conn.execute(
        "SELECT budget_amount, budget_impact FROM budget_categories WHERE id = ?",
        (category_id,)
    ).fetchone()
    if not cat:
        conn.close()
        return False

    # Sum transaction amounts for reversing their effects
    txn_sum = conn.execute(
        "SELECT COALESCE(SUM(amount), 0) as total FROM budget_transactions "
        "WHERE category_id = ? AND budget_id = ?",
        (category_id, budget_id)
    ).fetchone()["total"]

    if cat["budget_impact"] == "increase":
        # Reverse all increase-transaction bumps
        if txn_sum > 0:
            conn.execute(
                "UPDATE monthly_budgets SET total_budget = total_budget - ? WHERE id = ?",
                (txn_sum, budget_id)
            )

    # Delete transactions and category
    conn.execute(
        "DELETE FROM budget_transactions WHERE category_id = ? AND budget_id = ?",
        (category_id, budget_id)
    )
    conn.execute(
        "DELETE FROM budget_categories WHERE id = ? AND budget_id = ?",
        (category_id, budget_id)
    )
    conn.commit()
    conn.close()
    return True


# ── Budget Transactions ──

def add_budget_transaction(budget_id, category_id, date, amount, note=""):
    conn = get_db()
    conn.execute(
        """INSERT INTO budget_transactions (budget_id, category_id, date, amount, note)
           VALUES (?, ?, ?, ?, ?)""",
        (budget_id, category_id, date, amount, note)
    )
    # Increase category: transaction amount increases total budget
    impact = conn.execute(
        "SELECT budget_impact FROM budget_categories WHERE id = ?", (category_id,)
    ).fetchone()
    if impact and impact["budget_impact"] == "increase":
        conn.execute(
            "UPDATE monthly_budgets SET total_budget = total_budget + ? WHERE id = ?",
            (amount, budget_id)
        )
    conn.commit()
    conn.close()


def get_budget_transactions(budget_id, category_id=None):
    conn = get_db()
    if category_id:
        rows = conn.execute(
            """SELECT t.*, c.name as category_name
               FROM budget_transactions t
               JOIN budget_categories c ON t.category_id = c.id
               WHERE t.budget_id = ? AND t.category_id = ?
               ORDER BY t.date DESC, t.id DESC""",
            (budget_id, category_id)
        ).fetchall()
    else:
        rows = conn.execute(
            """SELECT t.*, c.name as category_name
               FROM budget_transactions t
               JOIN budget_categories c ON t.category_id = c.id
               WHERE t.budget_id = ?
               ORDER BY t.date DESC, t.id DESC""",
            (budget_id,)
        ).fetchall()
    conn.close()
    return rows


def delete_budget_transaction(txn_id):
    conn = get_db()
    # If this was an increase-category transaction, reverse the total budget bump
    row = conn.execute(
        """SELECT t.amount, t.budget_id, c.budget_impact
           FROM budget_transactions t
           JOIN budget_categories c ON t.category_id = c.id
           WHERE t.id = ?""", (txn_id,)
    ).fetchone()
    if row and row["budget_impact"] == "increase":
        conn.execute(
            "UPDATE monthly_budgets SET total_budget = total_budget - ? WHERE id = ?",
            (row["amount"], row["budget_id"])
        )
    conn.execute("DELETE FROM budget_transactions WHERE id = ?", (txn_id,))
    conn.commit()
    conn.close()


# ── Summary ──

def get_category_summary(budget_id):
    """Return per-category: name, budget_amount, spent, remaining."""
    conn = get_db()
    rows = conn.execute("""
        SELECT
            c.id,
            c.name,
            c.budget_amount,
            c.budget_impact,
            COALESCE(SUM(t.amount), 0) as spent
        FROM budget_categories c
        LEFT JOIN budget_transactions t ON c.id = t.category_id AND t.budget_id = ?
        WHERE c.budget_id = ?
        GROUP BY c.id
        ORDER BY c.budget_impact, c.name
    """, (budget_id, budget_id)).fetchall()
    conn.close()
    result = []
    for r in rows:
        remaining = r["budget_amount"] - r["spent"]
        result.append({
            "id": r["id"],
            "name": r["name"],
            "budget_amount": r["budget_amount"],
            "budget_impact": r["budget_impact"],
            "spent": r["spent"],
            "remaining": remaining,
        })
    return result


def get_total_summary(budget_id):
    """Return total budget, total spent, total remaining.

    Only decrease-category transactions count as spending.
    Increase-category transactions add to the total budget (handled at insert).
    Stagnant-category transactions are neutral (reimbursable tracking).
    """
    conn = get_db()
    budget_row = conn.execute(
        "SELECT total_budget FROM monthly_budgets WHERE id = ?", (budget_id,)
    ).fetchone()
    total_budget = budget_row["total_budget"] if budget_row else 0

    spent_row = conn.execute(
        """SELECT COALESCE(SUM(t.amount), 0) as total
           FROM budget_transactions t
           JOIN budget_categories c ON t.category_id = c.id
           WHERE t.budget_id = ? AND c.budget_impact = 'decrease'""",
        (budget_id,)
    ).fetchone()
    total_spent = spent_row["total"]

    conn.close()
    return {
        "total_budget": total_budget,
        "total_spent": total_spent,
        "total_remaining": total_budget - total_spent,
    }
