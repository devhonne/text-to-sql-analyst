"""
Step 1: create the sample business database.

Run:
    python setup_db.py

Creates business.db with 4 tables (customers, products, orders, order_items)
and realistic sample data with intentional patterns (repeat customers,
seasonal orders, a mix of statuses) so query results are meaningful.
"""
import sqlite3
import random
from datetime import date, timedelta

random.seed(42)

conn = sqlite3.connect("business.db")
cur = conn.cursor()

cur.executescript("""
DROP TABLE IF EXISTS order_items;
DROP TABLE IF EXISTS orders;
DROP TABLE IF EXISTS products;
DROP TABLE IF EXISTS customers;

CREATE TABLE customers (
    customer_id   INTEGER PRIMARY KEY,
    name          TEXT NOT NULL,
    email         TEXT,
    city          TEXT,
    signup_date   DATE
);

CREATE TABLE products (
    product_id    INTEGER PRIMARY KEY,
    name          TEXT NOT NULL,
    category      TEXT,
    price         DECIMAL(10,2) NOT NULL,
    stock_qty     INTEGER NOT NULL
);

CREATE TABLE orders (
    order_id      INTEGER PRIMARY KEY,
    customer_id   INTEGER REFERENCES customers(customer_id),
    order_date    DATE NOT NULL,
    status        TEXT CHECK (status IN ('pending','shipped','delivered','cancelled'))
);

CREATE TABLE order_items (
    order_item_id INTEGER PRIMARY KEY,
    order_id      INTEGER REFERENCES orders(order_id),
    product_id    INTEGER REFERENCES products(product_id),
    quantity      INTEGER NOT NULL,
    unit_price    DECIMAL(10,2) NOT NULL
);
""")

# --- Customers ---
cities = ["Hyderabad", "Bengaluru", "Chennai", "Mumbai", "Pune", "Delhi", "Kolkata"]
first_names = ["Aarav", "Vivaan", "Ananya", "Diya", "Ishaan", "Kavya", "Rohan",
              "Priya", "Arjun", "Sneha", "Karan", "Meera", "Aditya", "Neha",
              "Rahul", "Pooja", "Vikram", "Anjali", "Sanjay", "Divya"]
last_names = ["Sharma", "Verma", "Reddy", "Gupta", "Nair", "Iyer", "Rao",
             "Patel", "Singh", "Menon"]

customers = []
for i in range(1, 41):
    name = f"{random.choice(first_names)} {random.choice(last_names)}"
    email = name.lower().replace(" ", ".") + f"{i}@example.com"
    city = random.choice(cities)
    signup = date(2024, 1, 1) + timedelta(days=random.randint(0, 600))
    customers.append((i, name, email, city, signup.isoformat()))

cur.executemany(
    "INSERT INTO customers VALUES (?,?,?,?,?)", customers
)

# --- Products ---
products_data = [
    ("Wireless Mouse", "Electronics", 499.00, 150),
    ("Mechanical Keyboard", "Electronics", 2499.00, 80),
    ("USB-C Hub", "Electronics", 1299.00, 100),
    ("Laptop Stand", "Accessories", 899.00, 60),
    ("Webcam HD", "Electronics", 1899.00, 45),
    ("Desk Lamp", "Home Office", 749.00, 90),
    ("Notebook Set", "Stationery", 199.00, 300),
    ("Ballpoint Pens (Pack of 10)", "Stationery", 99.00, 500),
    ("Office Chair", "Furniture", 5999.00, 25),
    ("Standing Desk", "Furniture", 8999.00, 15),
    ("Bluetooth Speaker", "Electronics", 1599.00, 70),
    ("Monitor 24-inch", "Electronics", 8499.00, 35),
    ("Cable Organizer", "Accessories", 249.00, 200),
    ("Desk Mat", "Accessories", 599.00, 120),
    ("Wireless Charger", "Electronics", 999.00, 85),
    ("Coffee Mug", "Home Office", 299.00, 250),
    ("Planner Diary 2026", "Stationery", 349.00, 180),
    ("External SSD 1TB", "Electronics", 6999.00, 40),
    ("Ergonomic Footrest", "Furniture", 1199.00, 55),
    ("LED Desk Light", "Home Office", 649.00, 95),
]
products = [(i + 1, *p) for i, p in enumerate(products_data)]
cur.executemany("INSERT INTO products VALUES (?,?,?,?,?)", products)

# --- Orders + Order Items ---
statuses = ["delivered", "delivered", "delivered", "shipped", "pending", "cancelled"]
orders = []
order_items = []
order_id = 1
item_id = 1

start_date = date(2025, 1, 1)
end_date = date(2026, 9, 1)
days_range = (end_date - start_date).days

# give some customers more orders than others (repeat-customer pattern)
weighted_customers = list(range(1, 41)) + random.sample(range(1, 41), 15)

for _ in range(220):
    cust_id = random.choice(weighted_customers)
    order_date = start_date + timedelta(days=random.randint(0, days_range))
    status = random.choice(statuses)
    orders.append((order_id, cust_id, order_date.isoformat(), status))

    # 1-4 line items per order
    for _ in range(random.randint(1, 4)):
        prod_id = random.randint(1, len(products_data))
        price = products_data[prod_id - 1][2]
        qty = random.randint(1, 3)
        order_items.append((item_id, order_id, prod_id, qty, price))
        item_id += 1

    order_id += 1

cur.executemany("INSERT INTO orders VALUES (?,?,?,?)", orders)
cur.executemany("INSERT INTO order_items VALUES (?,?,?,?,?)", order_items)

conn.commit()

# Quick sanity check
for table in ["customers", "products", "orders", "order_items"]:
    count = cur.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
    print(f"{table}: {count} rows")

conn.close()
print("\nDone. Created business.db")
