from flask import Flask, render_template, request, redirect, url_for, flash
import sqlite3
from datetime import datetime
import pytz

app = Flask(__name__)
app.secret_key = "secret_key_123"
DB_NAME = "attendance.db"

# இந்திய நேர மண்டலம் (IST)
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
    
    conn.commit()
    conn.close()

# ஆப் தொடங்கும் போது டேட்டாபேஸை தயார் செய்ய
init_db()

@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        
        if not name or not email:
            flash("Please fill in both Name and Email!")
            return redirect(url_for('login'))

        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        
        cursor.execute("SELECT email FROM members WHERE email=?", (email,))
        user = cursor.fetchone()
        
        if not user:
            cursor.execute("INSERT INTO members (name, email, role) VALUES (?, ?, ?)", 
                           (name, email, 'Student'))
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
    
    selected_date = request.form.get('selected_date', today_date)
    
    cursor.execute("SELECT status, time FROM attendance WHERE email=? AND date=?", (email, selected_date))
    date_record = cursor.fetchone()
    
    total_present = sum(1 for row in history if row[2] == 'Present')
    total_absent = sum(1 for row in history if row[2] == 'Absent')
    
    conn.close()
    
    return render_template('dashboard.html', user=user, history=history, 
                           today_date=today_date, selected_date=selected_date,
                           date_record=date_record,
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
    cursor.execute("INSERT INTO attendance (email, date, time, status) VALUES (?, ?, ?, ?)", 
                   (email, date, time, status))
    conn.commit()
    conn.close()
    
    flash("Attendance Marked Successfully!")
    return redirect(url_for('dashboard', email=email))

@app.route('/report')
def report():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT m.name, a.email, a.date, a.time, a.status FROM attendance a JOIN members m ON a.email = m.email ORDER BY a.id DESC")
    all_records = cursor.fetchall()
    conn.close()
    return render_template('report.html', all_records=all_records)

if __name__ == '__main__':
    app.run(debug=True)
