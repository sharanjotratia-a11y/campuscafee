import csv, sqlite3

conn = sqlite3.connect('campuscart.db')
cur = conn.cursor()
cur.execute("""
    SELECT o.order_id, o.order_date, s.name AS student, s.course,
           p.name AS product, p.category, oi.quantity, p.price,
           oi.quantity * p.price AS amount, o.status
    FROM Orders o
    JOIN Students s ON o.student_id = s.student_id
    JOIN Order_Items oi ON o.order_id = oi.order_id
    JOIN Products p ON oi.product_id = p.product_id
""")
rows = cur.fetchall()
headers = [d[0] for d in cur.description]

with open('campuscart_data.csv', 'w', newline='', encoding='utf-8') as f:
    w = csv.writer(f)
    w.writerow(headers)
    w.writerows(rows)

print("campuscart_data.csv ban gayi:", len(rows), "rows")
conn.close()