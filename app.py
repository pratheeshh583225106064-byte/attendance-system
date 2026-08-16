from flask import Flask, render_template, request, redirect, url_for, flash, send_file
import sqlite3
from datetime import datetime
import pytz
import pandas as pd
import io
import re

app = Flask(__name__)
app.secret_key = "secret_key_123"
DB_NAME = "attendance.db"

IST = pytz.timezone('Asia/Kolkata')

def init_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS members (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            role TEXT NOT NULL
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS attendance (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT NOT NULL,
            date TEXT NOT NULL,
            time TEXT NOT NULL,
            status TEXT NOT NULL
        )
    ''')
    
    default_members = [
        ('Sivamani V', 'sivamani1234@gmail.com', 'CEO & Founder'),
        ('Anusha', 'anusha1234@gmail.com', 'Technical coordinator'),
        ('Dharshan G', 'dharshan1234@gmail.com', 'IoT Engineer'),
        ('Aisha mariyam', 'aisha1234@gmail.com', 'IoT Engineer'),
        ('Meenakshi Priyadarshini', 'meenakshi1234@gmail.com', 'PCB Designer'),
        ('Shyam kumar M', 'shyam1234@gmail.com', 'PCB designer')
    ]
    
    for name, email, role in default_members:
        cursor.execute("INSERT OR IGNORE INTO members (name, email, role) VALUES (?, ?, ?)", (name, email, role))
        
    conn.commit()
    conn.close()

init_db()

@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        
        if not name or not email:
            flash("Please enter both Name and Email!")
            return redirect(url_for('login'))

        email_pattern = r'^[a-zA-Z]+[0-9]+@gmail\.com$'
        if not re.match(email_pattern, email):
            flash("❌ Invalid Email Format! Email must be like: name1234@gmail.com")
            return redirect(url_for('login'))

        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        
        cursor.execute("SELECT email FROM members WHERE email=?", (email,))
        user = cursor.fetchone()
        
        if not user:
            cursor.execute("INSERT INTO members (name, email, role) VALUES (?, ?, ?)", 
                           (name, email, 'Team Member'))
            conn.commit()
        else:
            cursor.execute("UPDATE members SET name=? WHERE email=?", (name, email))
            conn.commit()
            
        conn.close()
        return redirect(url_for('dashboard', email=email))
        
    return render_template('login.html')

@app.route('/dashboard', methods=['GET', 'POST'])
def dashboard():
    email = request.args.get('email') or request.form.get('email')
    if not email:
        return redirect(url_for('login'))
        
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    cursor.execute("SELECT name, email, role FROM members WHERE email=?", (email,))
    user = cursor.fetchone()
    
    if not user:
        conn.close()
        return redirect(url_for('login'))
        
    cursor.execute("SELECT date, time, status FROM attendance WHERE email=? ORDER BY id DESC", (email,))
    history = cursor.fetchall()
    
    now = datetime.now(IST)
    today_date = now.strftime("%Y-%m-%d")
    
    cursor.execute("SELECT status, time FROM attendance WHERE email=? AND date=?", (email, today_date))
    today_attendance = cursor.fetchone()
    
    selected_date = request.form.get('selected_date', today_date)
    
    cursor.execute("SELECT status, time FROM attendance WHERE email=? AND date=?", (email, selected_date))
    date_record = cursor.fetchone()
    
    total_present = sum(1 for row in history if row[2] == 'Present')
    total_absent = sum(1 for row in history if row[2] == 'Absent')
    
    conn.close()
    
    return render_template('dashboard.html', user=user, history=history, 
                           today_date=today_date, selected_date=selected_date,
                           date_record=date_record, today_attendance=today_attendance,
                           total_present=total_present, total_absent=total_absent)

@app.route('/mark_attendance', methods=['POST'])
def mark_attendance():
    email = request.form.get('email')
    status = request.form.get('status')
    
    now = datetime.now(IST)
    date = now.strftime("%Y-%m-%d")
    time = now.strftime("%I:%M:%S %p")
    
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    cursor.execute("SELECT id FROM attendance WHERE email=? AND date=?", (email, date))
    existing_record = cursor.fetchone()
    
    if existing_record:
        flash("❌ Attendance already marked for today!")
    else:
        cursor.execute("INSERT INTO attendance (email, date, time, status) VALUES (?, ?, ?, ?)", 
                       (email, date, time, status))
        conn.commit()
        flash("✅ Attendance Marked Successfully!")
        
    conn.close()
    return redirect(url_for('dashboard', email=email))

@app.route('/download_excel')
def download_excel():
    conn = sqlite3.connect(DB_NAME)
    query = """
        SELECT m.name AS 'Name', m.role AS 'Role', a.email AS 'Email', 
               a.date AS 'Date', a.time AS 'Time (IST)', a.status AS 'Status'
        FROM attendance a 
        JOIN members m ON a.email = m.email 
        ORDER BY a.id DESC
    """
    df = pd.read_sql_query(query, conn)
    conn.close()
    
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Attendance_Report')
    
    output.seek(0)
    return send_file(output, 
                     download_name=f"Attendance_Report_{datetime.now(IST).strftime('%Y-%m-%d')}.xlsx", 
                     as_attachment=True)

if __name__ == '__main__':
    app.run(debug=True)
