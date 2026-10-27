import sqlite3, random, os
from pathlib import Path
from datetime import date, timedelta

admin_password = os.environ.get('CAMPUSCART_ADMIN_PASSWORD')
analyst_password = os.environ.get('CAMPUSCART_ANALYST_PASSWORD')
if not admin_password or not analyst_password:
    raise RuntimeError(
        'Set CAMPUSCART_ADMIN_PASSWORD and CAMPUSCART_ANALYST_PASSWORD before creating the database.'
    )

db_path = Path(__file__).resolve().parent / 'campuscart.db'
if db_path.exists():
    db_path.unlink()

conn = sqlite3.connect(db_path)
cur = conn.cursor()

# ---------- DDL: tables ----------
cur.executescript("""
CREATE TABLE Students (
  student_id INTEGER PRIMARY KEY,
  name TEXT NOT NULL,
  course TEXT,
  year INTEGER,
  phone TEXT
);

CREATE TABLE Products (
  product_id INTEGER PRIMARY KEY,
  name TEXT NOT NULL,
  category TEXT,
  price REAL CHECK (price > 0),
  stock INTEGER DEFAULT 0
);

CREATE TABLE Orders (
  order_id INTEGER PRIMARY KEY,
  student_id INTEGER,
  order_date TEXT,
  status TEXT,
  FOREIGN KEY (student_id) REFERENCES Students(student_id)
);

CREATE TABLE Order_Items (
  item_id INTEGER PRIMARY KEY,
  order_id INTEGER,
  product_id INTEGER,
  quantity INTEGER,
  FOREIGN KEY (order_id) REFERENCES Orders(order_id),
  FOREIGN KEY (product_id) REFERENCES Products(product_id)
);

CREATE TABLE Users (
  user_id INTEGER PRIMARY KEY AUTOINCREMENT,
  username TEXT UNIQUE,
  password TEXT,
  role TEXT
);

-- DDL ALTER example
ALTER TABLE Students ADD COLUMN email TEXT;
""")
cur.executemany(
    "INSERT INTO Users (username, password, role) VALUES (?,?,?)",
    [('admin', admin_password, 'admin'), ('analyst', analyst_password, 'analyst')]
)

# ---------- Dummy data ----------
first = ['Aarav','Riya','Vivaan','Ananya','Aditya','Diya','Rohan','Sneha','Karan','Priya',
         'Arjun','Neha','Rahul','Pooja','Amit','Kavya','Manav','Isha','Yash','Simran']
last = ['Sharma','Verma','Gupta','Singh','Khan','Mehta','Jain','Yadav','Kumar','Chopra']

students = []
for i in range(1, 41):
    students.append((i, random.choice(first) + ' ' + random.choice(last),
                     random.choice(['BCA', 'BBA', 'B.Com', 'BSc']),
                     random.randint(1, 3),
                     '9' + ''.join(str(random.randint(0, 9)) for _ in range(9))))
cur.executemany("INSERT INTO Students (student_id,name,course,year,phone) VALUES (?,?,?,?,?)", students)

prods = [('Samosa','Snacks',15), ('Sandwich','Snacks',40), ('Chai','Beverages',10),
         ('Cold Coffee','Beverages',50), ('Maggi','Meals',35), ('Thali','Meals',80),
         ('Notebook','Stationery',60), ('Pen','Stationery',10), ('Highlighter','Stationery',30),
         ('Juice','Beverages',30), ('Burger','Snacks',45), ('Fried Rice','Meals',70)]
products = [(i + 1, n, c, p, random.randint(20, 100)) for i, (n, c, p) in enumerate(prods)]
cur.executemany("INSERT INTO Products (product_id,name,category,price,stock) VALUES (?,?,?,?,?)", products)

orders, items = [], []
item_id = 1
for oid in range(1, 181):
    sid = random.randint(1, 35)          # students 36-40 kabhi order nahi karte
    d = date(2025, 1, 1) + timedelta(days=random.randint(0, 300))
    status = random.choice(['Delivered', 'Delivered', 'Delivered', 'Pending', 'Cancelled'])
    orders.append((oid, sid, d.isoformat(), status))
    for _ in range(random.randint(1, 4)):
        items.append((item_id, oid, random.randint(1, 12), random.randint(1, 5)))
        item_id += 1

# 2 bulk orders (outlier analysis ke liye)
orders.append((181, 5, '2025-03-15', 'Delivered'))
items.append((item_id, 181, 1, 80)); item_id += 1
orders.append((182, 12, '2025-08-20', 'Delivered'))
items.append((item_id, 182, 6, 60))

cur.executemany("INSERT INTO Orders (order_id,student_id,order_date,status) VALUES (?,?,?,?)", orders)
cur.executemany("INSERT INTO Order_Items (item_id,order_id,product_id,quantity) VALUES (?,?,?,?)", items)

conn.commit()
conn.close()
print("Database ban gaya: campuscart.db")
print("Students:", len(students), "| Orders:", len(orders), "| Items:", len(items))