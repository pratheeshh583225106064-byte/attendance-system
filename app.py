from flask import Flask, render_template, request, redirect, url_for, flash
import sqlite3
from datetime import datetime
import pytz

app = Flask(__name__)
app.secret_key = "secret_key_123"
DB_NAME = "attendance.db"

# இந்திய நேர மண்டலம் (IST)
IST = pytz.timezone('Asia/Kolkata')

@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
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
    
    # இந்திய நேரப்படி இன்றைய தேதி
    now = datetime.now(IST)
    today_date = now.strftime("%Y-%m-%d")
    
    # கேலண்டர் மூலம் தேதியைத் தேர்ந்தெடுத்தால் அந்த தேதி
    selected_date = request.form.get('selected_date', today_date)
    
    # தேர்ந்தெடுத்த தேதிக்கான வருகைப் பதிவு
    cursor.execute("SELECT status, time FROM attendance WHERE email=? AND date=?", (email, selected_date))
    date_record = cursor.fetchone()
    
    # கணக்கீடு (Analytics)
    total_present = sum(1 for row in history if row[2] == 'Present')
    total_absent = sum(1 for row in history if row[2] == 'Absent')
    
    conn.close()
    
    return render_template('dashboard.html', user=user, history=history, 
                           today_date=today_date, selected_date=selected_date,
                           date_record=date_record,
                           total_present=total_present, total_absent=total_absent)

@app.route('/mark_attendance', methods=['POST'])
def mark_attendance():
    email = request.form['email']
    status = request.form['status']
    
    # இந்திய நேரத்தைச் சேமித்தல்
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
