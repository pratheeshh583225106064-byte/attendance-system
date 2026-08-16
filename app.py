@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        
        # பயனர் ஏற்கனவே உள்ளாரா எனச் சரிபார்த்தல்
        cursor.execute("SELECT email FROM members WHERE email=?", (email,))
        user = cursor.fetchone()
        
        # பயனர் இல்லையென்றால் புதிய பெயருடன் தானாகப் பதிவு செய்தல்
        if not user:
            cursor.execute("INSERT INTO members (name, email, role) VALUES (?, ?, ?)", 
                           (name, email, 'Student'))
            conn.commit()
        else:
            # பெயர் மாறியிருந்தால் அப்டேட் செய்தல்
            cursor.execute("UPDATE members SET name=? WHERE email=?", (name, email))
            conn.commit()
            
        conn.close()
        
        return redirect(url_for('dashboard', email=email))
        
    return render_template('login.html')
