"""
Step 2: ask questions in English, get SQL + results.

Setup:
    pip install groq python-dotenv

Add to .env (same folder as this script):
    GROQ_API_KEY=gsk_...

Run:
    python ask.py "What are the top 5 products by revenue?"
    python ask.py "Which customers signed up in 2025?"
    python ask.py "Delete all orders"   <- should be BLOCKED, not executed
"""
import argparse
import os
import re
import sqlite3
import sys
from pathlib import Path

from dotenv import load_dotenv
from groq import Groq

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

DB_PATH = "business.db"
GROQ_MODEL = "openai/gpt-oss-20b"

SCHEMA = """
customers(customer_id, name, email, city, signup_date)
products(product_id, name, category, price, stock_qty)
orders(order_id, customer_id, order_date, status)   -- status: pending/shipped/delivered/cancelled
order_items(order_item_id, order_id, product_id, quantity, unit_price)

Relationships:
  orders.customer_id -> customers.customer_id
  order_items.order_id -> orders.order_id
  order_items.product_id -> products.product_id
"""

# Only these statement types are ever allowed to run
ALLOWED_START = ("select", "with")
# Extra defense: block dangerous keywords even inside an allowed statement
BLOCKED_KEYWORDS = (
    "insert", "update", "delete", "drop", "alter", "create",
    "truncate", "attach", "pragma", "replace", "grant", "vacuum",
)


def generate_sql(client, question):
    system = (
        "You are a SQLite expert. Given the schema below, write ONE read-only "
        "SQL query that answers the question. Output ONLY the SQL query, no "
        "explanation, no markdown fences, no semicolon at the end.\n\n"
        f"Schema:\n{SCHEMA}"
    )
    resp = client.chat.completions.create(
        model=GROQ_MODEL,
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": question},
        ],
        temperature=0,
        max_tokens=300,
        reasoning_effort="low",
    )
    sql = resp.choices[0].message.content.strip()
    # strip accidental markdown fences if the model adds them anyway
    sql = re.sub(r"^```sql|^```|```$", "", sql, flags=re.MULTILINE).strip()
    return sql


def is_safe(sql):
    """Only allow a single read-only SELECT/WITH statement."""
    normalized = sql.strip().lower()

    if ";" in normalized.rstrip(";"):
        return False, "Multiple statements are not allowed."

    if not normalized.startswith(ALLOWED_START):
        return False, "Only SELECT/WITH queries are allowed."

    for word in BLOCKED_KEYWORDS:
        if re.search(rf"\b{word}\b", normalized):
            return False, f"Blocked keyword detected: {word}"

    return True, None


def run_query(sql):
    conn = sqlite3.connect(f"file:{DB_PATH}?mode=ro", uri=True)  # read-only connection
    cur = conn.cursor()
    cur.execute(sql)
    cols = [d[0] for d in cur.description] if cur.description else []
    rows = cur.fetchall()
    conn.close()
    return cols, rows


def print_table(cols, rows, limit=20):
    if not rows:
        print("(no rows returned)")
        return
    widths = [max(len(str(c)), max((len(str(r[i])) for r in rows), default=0))
             for i, c in enumerate(cols)]
    header = " | ".join(c.ljust(widths[i]) for i, c in enumerate(cols))
    print(header)
    print("-" * len(header))
    for row in rows[:limit]:
        print(" | ".join(str(v).ljust(widths[i]) for i, v in enumerate(row)))
    if len(rows) > limit:
        print(f"... ({len(rows) - limit} more rows not shown)")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("question")
    args = ap.parse_args()

    load_dotenv()
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise SystemExit("GROQ_API_KEY not found in .env")
    client = Groq(api_key=api_key)

    print(f"\nQuestion: {args.question}")

    sql = generate_sql(client, args.question)
    print(f"\nGenerated SQL:\n  {sql}")

    safe, reason = is_safe(sql)
    if not safe:
        print(f"\nBLOCKED: {reason}")
        print("This query was not executed.")
        return

    try:
        cols, rows = run_query(sql)
    except Exception as e:
        print(f"\nQuery failed to run: {e}")
        return

    print(f"\nResults ({len(rows)} rows):")
    print_table(cols, rows)


if __name__ == "__main__":
    main()
