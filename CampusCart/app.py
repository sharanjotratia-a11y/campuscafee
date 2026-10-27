from functools import wraps
import os
from pathlib import Path
import secrets
import sqlite3
from flask import Flask, render_template, request, redirect, session, flash

app = Flask(__name__, template_folder='../templates', static_folder='../static')
app.secret_key = os.environ.get('FLASK_SECRET_KEY') or secrets.token_hex(32)
DB = Path(__file__).resolve().parent / 'campuscart.db'


def query(sql, params=(), one=False, commit=False):
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    cur = conn.cursor()
    try:
        cur.execute(sql, params)
        if commit:
            conn.commit()
            return None
        return cur.fetchone() if one else cur.fetchall()
    finally:
        conn.close()


def login_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if 'role' not in session:
            return redirect('/')
        return f(*args, **kwargs)
    return wrapper


def admin_only(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if session.get('role') != 'admin':
            flash('Ye kaam sirf admin kar sakta hai.', 'error')
            return redirect(request.referrer or '/dashboard')
        return f(*args, **kwargs)
    return wrapper


# ---------- LOGIN / LOGOUT ----------
@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        user = query("SELECT * FROM Users WHERE username=? AND password=?",
                     (request.form['username'], request.form['password']), one=True)
        if user:
            session['role'] = user['role']
            session['username'] = user['username']
            return redirect('/dashboard')
        flash('Galat username ya password', 'error')
    return render_template('login.html')


@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')


# ---------- DASHBOARD ----------
@app.route('/dashboard')
@login_required
def dashboard():
    kpi = query("""
        SELECT COALESCE(SUM(oi.quantity*p.price),0) AS revenue,
               COUNT(DISTINCT o.order_id) AS orders
        FROM Orders o
        JOIN Order_Items oi ON o.order_id=oi.order_id
        JOIN Products p ON oi.product_id=p.product_id
        WHERE o.status='Delivered'""", one=True)
    students = query("SELECT COUNT(*) AS c FROM Students", one=True)['c']
    top = query("""
        SELECT p.name, SUM(oi.quantity) AS sold, SUM(oi.quantity*p.price) AS revenue
        FROM Order_Items oi JOIN Products p ON oi.product_id=p.product_id
        JOIN Orders o ON o.order_id=oi.order_id
        WHERE o.status='Delivered'
        GROUP BY p.name ORDER BY revenue DESC LIMIT 5""")
    cats = query("""
        SELECT p.category, SUM(oi.quantity*p.price) AS revenue
        FROM Order_Items oi JOIN Products p ON oi.product_id=p.product_id
        JOIN Orders o ON o.order_id=oi.order_id
        WHERE o.status='Delivered'
        GROUP BY p.category ORDER BY revenue DESC""")
    return render_template('dashboard.html', kpi=kpi, students=students, top=top, cats=cats)


# ---------- STUDENTS (INSERT / UPDATE / DELETE) ----------
@app.route('/students', methods=['GET', 'POST'])
@login_required
def students():
    if request.method == 'POST':
        if session['role'] != 'admin':
            flash('Sirf admin student add kar sakta hai.', 'error')
        else:
            new_id = query("SELECT COALESCE(MAX(student_id),0)+1 AS n FROM Students", one=True)['n']
            query("INSERT INTO Students (student_id,name,course,year,phone) VALUES (?,?,?,?,?)",
                  (new_id, request.form['name'], request.form['course'],
                   request.form['year'], request.form['phone']), commit=True)
            flash('Student add ho gaya.', 'success')
        return redirect('/students')
    rows = query("SELECT * FROM Students ORDER BY student_id")
    return render_template('students.html', rows=rows)


@app.route('/students/edit/<int:sid>', methods=['GET', 'POST'])
@login_required
@admin_only
def edit_student(sid):
    if request.method == 'POST':
        query("UPDATE Students SET name=?, course=?, year=?, phone=? WHERE student_id=?",
              (request.form['name'], request.form['course'],
               request.form['year'], request.form['phone'], sid), commit=True)
        flash('Student update ho gaya.', 'success')
        return redirect('/students')
    s = query("SELECT * FROM Students WHERE student_id=?", (sid,), one=True)
    return render_template('edit_student.html', s=s)


@app.route('/students/delete/<int:sid>')
@login_required
@admin_only
def delete_student(sid):
    try:
        query("DELETE FROM Students WHERE student_id=?", (sid,), commit=True)
        flash('Student delete ho gaya.', 'success')
    except sqlite3.IntegrityError:
        flash('Is student ke orders hain, isliye delete nahi ho sakta.', 'error')
    return redirect('/students')


# ---------- ORDERS ----------
@app.route('/orders', methods=['GET', 'POST'])
@login_required
def orders():
    if request.method == 'POST':
        if session['role'] != 'admin':
            flash('Sirf admin order add kar sakta hai.', 'error')
        else:
            oid = query("SELECT COALESCE(MAX(order_id),0)+1 AS n FROM Orders", one=True)['n']
            iid = query("SELECT COALESCE(MAX(item_id),0)+1 AS n FROM Order_Items", one=True)['n']
            query("INSERT INTO Orders (order_id,student_id,order_date,status) VALUES (?,?,date('now'),?)",
                  (oid, request.form['student_id'], request.form['status']), commit=True)
            query("INSERT INTO Order_Items (item_id,order_id,product_id,quantity) VALUES (?,?,?,?)",
                  (iid, oid, request.form['product_id'], request.form['quantity']), commit=True)
            flash('Order add ho gaya.', 'success')
        return redirect('/orders')
    rows = query("""
        SELECT o.order_id, s.name AS student, o.order_date, o.status,
               SUM(oi.quantity*p.price) AS total
        FROM Orders o
        JOIN Students s ON o.student_id=s.student_id
        JOIN Order_Items oi ON o.order_id=oi.order_id
        JOIN Products p ON oi.product_id=p.product_id
        GROUP BY o.order_id, s.name, o.order_date, o.status
        ORDER BY o.order_id DESC LIMIT 50""")
    stu = query("SELECT student_id, name FROM Students ORDER BY name")
    prod = query("SELECT product_id, name FROM Products ORDER BY name")
    return render_template('orders.html', rows=rows, stu=stu, prod=prod)


@app.route('/orders/delete/<int:oid>')
@login_required
@admin_only
def delete_order(oid):
    query("DELETE FROM Order_Items WHERE order_id=?", (oid,), commit=True)
    query("DELETE FROM Orders WHERE order_id=?", (oid,), commit=True)
    flash('Order delete ho gaya.', 'success')
    return redirect('/orders')


# ---------- REPORTS ----------
@app.route('/reports')
@login_required
def reports():
    spending = query("""
        SELECT s.name, s.course, COALESCE(SUM(oi.quantity*p.price),0) AS total
        FROM Students s
        LEFT JOIN Orders o ON s.student_id=o.student_id
        LEFT JOIN Order_Items oi ON o.order_id=oi.order_id
        LEFT JOIN Products p ON oi.product_id=p.product_id
        GROUP BY s.student_id, s.name, s.course
        ORDER BY total DESC""")
    inactive = [r for r in spending if r['total'] == 0]
    return render_template('reports.html', spending=spending, inactive=inactive)


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001, debug=False)