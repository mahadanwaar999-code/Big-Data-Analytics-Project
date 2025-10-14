# app.py
from flask import Flask, render_template, request, redirect, url_for, session, flash
import sqlite3
from sqlite3 import Error
import os

app = Flask(__name__)
app.secret_key = 'super_secret_key'  # Change this in production

DATABASE = 'inventory.db'

def create_connection():
    conn = None
    try:
        conn = sqlite3.connect(DATABASE)
    except Error as e:
        print(e)
    return conn

def create_tables():
    conn = create_connection()
    if conn:
        cursor = conn.cursor()
        # Admins table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS admins (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL UNIQUE,
                password TEXT NOT NULL
            )
        ''')
        # Customers table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS customers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                email TEXT NOT NULL UNIQUE,
                password TEXT NOT NULL
            )
        ''')
        # Stocks table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS stocks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                brand TEXT NOT NULL,
                condition TEXT NOT NULL,
                quality TEXT NOT NULL,
                quantity INTEGER NOT NULL,
                original_price REAL NOT NULL,
                sale_price REAL NOT NULL
            )
        ''')
        conn.commit()
        # Insert default admins if not exist
        cursor.execute("SELECT COUNT(*) FROM admins")
        if cursor.fetchone()[0] == 0:
            cursor.execute("INSERT INTO admins (username, password) VALUES (?, ?)", ('mahad', 'mahad1122@'))
            cursor.execute("INSERT INTO admins (username, password) VALUES (?, ?)", ('aqeel', 'aqeel1122@'))
            conn.commit()
        # Insert example stocks if not exist
        cursor.execute("SELECT COUNT(*) FROM stocks")
        if cursor.fetchone()[0] == 0:
            stocks_data = [
                ('Plugs', 'BYD', 'New', 'A1', 0, 22000, 25000),
                ('Steering', 'KIA', 'New', 'Genuine', 96, 3500, 4200),
                ('Air Suspension', 'Toyota', 'New', 'Genuine', 0, 45000, 53500),
                ('Speaker', 'Audionic', 'New', '8D', 60, 15500, 21500)
            ]
            cursor.executemany("INSERT INTO stocks (name, brand, condition, quality, quantity, original_price, sale_price) VALUES (?, ?, ?, ?, ?, ?, ?)", stocks_data)
            conn.commit()
        conn.close()

create_tables()

# Index
@app.route('/')
def index():
    return render_template('index.html')

# Admin Login
@app.route('/admin_login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        conn = create_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM admins WHERE username = ? AND password = ?", (username, password))
        admin = cursor.fetchone()
        conn.close()
        if admin:
            session['admin_id'] = admin[0]
            return redirect(url_for('admin_panel'))
        else:
            flash('Invalid credentials')
    return render_template('admin_login.html')

# Admin Change Password
@app.route('/admin_change_password', methods=['GET', 'POST'])
def admin_change_password():
    if 'admin_id' not in session:
        return redirect(url_for('admin_login'))
    if request.method == 'POST':
        old_password = request.form['old_password']
        new_password = request.form['new_password']
        confirm_password = request.form['confirm_password']
        if new_password != confirm_password:
            flash('Passwords do not match')
        else:
            conn = create_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT password FROM admins WHERE id = ?", (session['admin_id'],))
            if cursor.fetchone()[0] == old_password:
                cursor.execute("UPDATE admins SET password = ? WHERE id = ?", (new_password, session['admin_id']))
                conn.commit()
                flash('Password changed successfully')
            else:
                flash('Incorrect old password')
            conn.close()
    return render_template('admin_change_password.html')

# Customer Login
@app.route('/customer_login', methods=['GET', 'POST'])
def customer_login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        conn = create_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM customers WHERE email = ? AND password = ?", (email, password))
        customer = cursor.fetchone()
        conn.close()
        if customer:
            session['customer_id'] = customer[0]
            return redirect(url_for('customer_panel'))
        else:
            flash('Invalid credentials')
    return render_template('customer_login.html')

# Customer Signup
@app.route('/customer_signup', methods=['GET', 'POST'])
def customer_signup():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        password = request.form['password']
        confirm_password = request.form['confirm_password']
        if password != confirm_password:
            flash('Passwords do not match')
        else:
            conn = create_connection()
            cursor = conn.cursor()
            try:
                cursor.execute("INSERT INTO customers (name, email, password) VALUES (?, ?, ?)", (name, email, password))
                conn.commit()
                flash('Account created successfully. Please login.')
                return redirect(url_for('customer_login'))
            except sqlite3.IntegrityError:
                flash('Email already exists')
            conn.close()
    return render_template('customer_signup.html')

# Customer Panel
@app.route('/customer_panel')
def customer_panel():
    if 'customer_id' not in session:
        return redirect(url_for('customer_login'))
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM stocks")
    stocks = cursor.fetchall()
    conn.close()
    return render_template('customer_panel.html', stocks=stocks)

# Add to Cart
@app.route('/add_to_cart/<int:item_id>')
def add_to_cart(item_id):
    if 'customer_id' not in session:
        return redirect(url_for('customer_login'))
    if 'cart' not in session:
        session['cart'] = []
    session['cart'].append(item_id)
    session.modified = True
    flash('Item added to cart')
    return redirect(url_for('customer_panel'))

# Cart
@app.route('/cart')
def cart():
    if 'customer_id' not in session:
        return redirect(url_for('customer_login'))
    cart_items = []
    total = 0
    if 'cart' in session and session['cart']:
        conn = create_connection()
        cursor = conn.cursor()
        for item_id in session['cart']:
            cursor.execute("SELECT * FROM stocks WHERE id = ?", (item_id,))
            item = cursor.fetchone()
            if item and item[5] > 0:  # quantity > 0
                cart_items.append(item)
                total += item[7]  # sale_price
        conn.close()
    return render_template('cart.html', cart_items=cart_items, total=total)

# Pay
@app.route('/pay')
def pay():
    if 'customer_id' not in session or 'cart' not in session or not session['cart']:
        return redirect(url_for('customer_panel'))
    conn = create_connection()
    cursor = conn.cursor()
    for item_id in session['cart']:
        cursor.execute("SELECT quantity FROM stocks WHERE id = ?", (item_id,))
        qty = cursor.fetchone()[0]
        if qty > 0:
            cursor.execute("UPDATE stocks SET quantity = quantity - 1 WHERE id = ?", (item_id,))
    conn.commit()
    conn.close()
    session.pop('cart')
    flash('Payment successful. Items deducted from stock.')
    return redirect(url_for('customer_panel'))

# Admin Panel
@app.route('/admin_panel')
def admin_panel():
    if 'admin_id' not in session:
        return redirect(url_for('admin_login'))
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM stocks")
    stocks = cursor.fetchall()
    # Calculate stats
    cursor.execute("SELECT SUM(quantity) FROM stocks")
    current_units = cursor.fetchone()[0] or 0
    cursor.execute("SELECT SUM(quantity * sale_price) FROM stocks")
    stock_values = cursor.fetchone()[0] or 0
    cursor.execute("SELECT SUM(quantity * original_price) FROM stocks")
    stock_costs = cursor.fetchone()[0] or 0
    cursor.execute("SELECT COUNT(*) FROM stocks WHERE quantity = 0")
    out_of_stock = cursor.fetchone()[0] or 0
    conn.close()
    return render_template('admin_panel.html', stocks=stocks, current_units=current_units, stock_values=stock_values, stock_costs=stock_costs, out_of_stock=out_of_stock)

# Add Item
@app.route('/add_item', methods=['POST'])
def add_item():
    if 'admin_id' not in session:
        return redirect(url_for('admin_login'))
    name = request.form['name']
    brand = request.form['brand']
    condition = request.form['condition']
    quality = request.form['quality']
    quantity = int(request.form['quantity'])
    original_price = float(request.form['original_price'])
    sale_price = float(request.form['sale_price'])
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO stocks (name, brand, condition, quality, quantity, original_price, sale_price) VALUES (?, ?, ?, ?, ?, ?, ?)", (name, brand, condition, quality, quantity, original_price, sale_price))
    conn.commit()
    conn.close()
    flash('Item added')
    return redirect(url_for('admin_panel'))

# Delete Item
@app.route('/delete_item/<int:item_id>')
def delete_item(item_id):
    if 'admin_id' not in session:
        return redirect(url_for('admin_login'))
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM stocks WHERE id = ?", (item_id,))
    conn.commit()
    conn.close()
    flash('Item deleted')
    return redirect(url_for('admin_panel'))

# Update Item
@app.route('/update_item/<int:item_id>', methods=['POST'])
def update_item(item_id):
    if 'admin_id' not in session:
        return redirect(url_for('admin_login'))
    name = request.form['name']
    brand = request.form['brand']
    condition = request.form['condition']
    quality = request.form['quality']
    quantity = int(request.form['quantity'])
    original_price = float(request.form['original_price'])
    sale_price = float(request.form['sale_price'])
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE stocks SET name=?, brand=?, condition=?, quality=?, quantity=?, original_price=?, sale_price=? WHERE id=?", (name, brand, condition, quality, quantity, original_price, sale_price, item_id))
    conn.commit()
    conn.close()
    flash('Item updated')
    return redirect(url_for('admin_panel'))

# Logout
@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)