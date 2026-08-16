import re  # 1. கோப்பின் தொடக்கத்தில் re module சேர்க்கவும்

@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        
        if not name or not email:
            flash("Please enter both Name and Email!")
            return redirect(url_for('login'))

        # 2. மின்னஞ்சல் வடிவத்தை சரிபார்க்கும் Regex pattern (e.g., name1234@gmail.com)
        # இதில் எழுத்துக்கள், அதைத் தொடர்ந்து எண்கள், பிறகு @gmail.com இருக்க வேண்டும்
        email_pattern = r'^[a-zA-C-a-z]+[0-9]+@gmail\.com$'
        
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
