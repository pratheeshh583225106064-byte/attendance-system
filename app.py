import sqlite3
from flask import Flask, render_template, request, redirect, url_for, flash, send_file
import openpyxl
from openpyxl.styles import Font, Alignment, PatternFill, Border, Side
from openpyxl.utils import get_column_letter
import os
from datetime import datetime

app = Flask(__name__)
app.secret_key = "attendance_secret_key_2026"

DB_NAME = "attendance.db"
EXCEL_NAME = "attendance.xlsx"

# 1. Database & Custom 6 Members Initialization
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
            name TEXT NOT NULL,
            email TEXT NOT NULL,
            date TEXT NOT NULL,
            time TEXT NOT NULL,
            status TEXT NOT NULL
        )
    ''')
    
    cursor.execute("SELECT COUNT(*) FROM members")
    if cursor.fetchone()[0] == 0:
        # REPLACE YOUR 6 MEMBERS DATA HERE IF NEEDED
        default_members = [
            ("SIVAMANI V", "sivamani1234@gmail.com", "Founder & CEO"),
            ("PRATHEESH H", "pratheesh1234@gmail.com", "Web Developer"),
            ("SHYAM KUMAR M", "shyamkumar1234@gmail.com", "PCB Designer"),
            ("MEENAKSHI PRIYADHARSHINI", "meenakshipriyadhashini1234@gmail.com", "Embedded Engineer"),
            ("ANUSHA", "anusha1234@gmail.com", "Data Analyst"),
            ("DHARSHANA", "dharshana1234@gmail.com", "DevOps Engineer"),
            ("AISHA", "aisha@gmail.com", "Software Engineer")
        ]
        cursor.executemany("INSERT INTO members (name, email, role) VALUES (?, ?, ?)", default_members)
    
    conn.commit()
    conn.close()

# 2. Excel Initialization
def init_excel():
    if not os.path.exists(EXCEL_NAME):
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "Attendance Records"
        ws.views.sheetView[0].showGridLines = True
        
        headers = ["Log ID", "Name", "Email", "Date", "Time", "Status"]
        ws.append(headers)
        
        header_fill = PatternFill(start_color="1F4E79", end_color="1F4E79", fill_type="solid")
        header_font = Font(name="Segoe UI", size=11, bold=True, color="FFFFFF")
        
        for col_num, h in enumerate(headers, 1):
            cell = ws.cell(row=1, column=col_num)
            cell.fill = header_fill
            cell.font = header_font
            cell.alignment = Alignment(horizontal="center", vertical="center")
            
        ws.row_dimensions[1].height = 25
        wb.save(EXCEL_NAME)

init_db()
init_excel()

# ----------------- ROUTES -----------------

@app.route('/')
def home():
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        name = request.form['name'].strip()
        email = request.form['email'].strip().lower()
        
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        cursor.execute("SELECT name, email, role FROM members WHERE LOWER(name)=LOWER(?) AND LOWER(email)=?", (name, email))
        user = cursor.fetchone()
        conn.close()
        
        if user:
            return redirect(url_for('dashboard', email=user[1]))
        else:
            flash("Access Denied! Only authorized registered members can log in.")
            
    return render_template('login.html')

@app.route('/dashboard')
def dashboard():
    email = request.args.get('email')
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
    
    today_date = datetime.now().strftime("%Y-%m-%d")
    cursor.execute("SELECT status, time FROM attendance WHERE email=? AND date=?", (email, today_date))
    today_record = cursor.fetchone()
    
    # Calculate Quick Analytics
    total_present = sum(1 for row in history if row[2] == 'Present')
    total_absent = sum(1 for row in history if row[2] == 'Absent')
    
    conn.close()
    
    return render_template('dashboard.html', user=user, history=history, 
                           today_record=today_record, today_date=today_date,
                           total_present=total_present, total_absent=total_absent)

@app.route('/mark_attendance', methods=['POST'])
def mark_attendance():
    email = request.form['email']
    status = request.form['status']
    
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM members WHERE email=?", (email,))
    user = cursor.fetchone()
    
    if not user:
        conn.close()
        return redirect(url_for('login'))
        
    name = user[0]
    now = datetime.now()
    c_date = now.strftime("%Y-%m-%d")
    c_time = now.strftime("%H:%M:%S")
    
    cursor.execute("SELECT id FROM attendance WHERE email=? AND date=?", (email, c_date))
    existing = cursor.fetchone()
    
    if existing:
        flash("Attendance already submitted for today!")
    else:
        cursor.execute("INSERT INTO attendance (name, email, date, time, status) VALUES (?, ?, ?, ?, ?)",
                       (name, email, c_date, c_time, status))
        conn.commit()
        log_id = cursor.lastrowid
        
        # Save to Excel Sheet
        wb = openpyxl.load_workbook(EXCEL_NAME)
        ws = wb.active
        ws.append([f"LOG{log_id:04d}", name, email, c_date, c_time, status])
        
        last_row = ws.max_row
        thin_border = Border(left=Side(style='thin', color='D9D9D9'), right=Side(style='thin', color='D9D9D9'),
                             top=Side(style='thin', color='D9D9D9'), bottom=Side(style='thin', color='D9D9D9'))
        
        for col_idx in range(1, 7):
            cell = ws.cell(row=last_row, column=col_idx)
            cell.border = thin_border
            cell.alignment = Alignment(horizontal="center" if col_idx in [1, 4, 5, 6] else "left", vertical="center")
            if col_idx == 6:
                if status == "Present":
                    cell.fill = PatternFill(start_color="E2EFDA", end_color="E2EFDA", fill_type="solid")
                    cell.font = Font(name="Segoe UI", size=10, color="375623", bold=True)
                else:
                    cell.fill = PatternFill(start_color="FCE4D6", end_color="FCE4D6", fill_type="solid")
                    cell.font = Font(name="Segoe UI", size=10, color="C65911", bold=True)
                    
        for col in ws.columns:
            max_len = max(len(str(cell.value or '')) for cell in col)
            col_letter = get_column_letter(col[0].column)
            ws.column_dimensions[col_letter].width = max(max_len + 4, 14)
            
        wb.save(EXCEL_NAME)
        flash(f"Attendance marked successfully as {status}!")
        
    conn.close()
    return redirect(url_for('dashboard', email=email))

@app.route('/report')
def report():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT name, email, date, time, status FROM attendance ORDER BY id DESC")
    records = cursor.fetchall()
    conn.close()
    return render_template('report.html', records=records)

@app.route('/download_excel')
def download_excel():
    if os.path.exists(EXCEL_NAME):
        return send_file(EXCEL_NAME, as_attachment=True)
    flash("Excel report file not found!")
    return redirect(url_for('report'))

if __name__ == '__main__':
    app.run(debug=True)