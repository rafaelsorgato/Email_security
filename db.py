import sqlite3,hashlib,os
from flask import redirect


password_hash = hashlib.sha256("123456".encode()).hexdigest()

conn = sqlite3.connect('db.sqlite', check_same_thread=False)

cursor = conn.cursor()

cursor.execute('''CREATE TABLE IF NOT EXISTS users
             (id INTEGER PRIMARY KEY AUTOINCREMENT,
             username TEXT NOT NULL UNIQUE,
             fullname TEXT NOT NULL,
             password TEXT NOT NULL,
             permission TEXT NOT NULL,
             picture TEXT NOT NULL
             )''')

conn.commit()

cursor.execute('''CREATE TABLE IF NOT EXISTS action
             (id INTEGER PRIMARY KEY AUTOINCREMENT,
             action TEXT NOT NULL UNIQUE,
             score NUMBER NOT NULL
             )''')

conn.commit()

cursor.execute('''CREATE TABLE IF NOT EXISTS emails
             (id INTEGER PRIMARY KEY UNIQUE,
             subject TEXT NOT NULL,
             body TEXT,
             subject_score INT,
             body_score INT,
             url_score INT,
             status TEXT,
             hash TEXT UNIQUE,
             timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
             sender TEXT
             )''')

conn.commit()

cursor.execute('''CREATE TABLE IF NOT EXISTS urls
             (id INTEGER PRIMARY KEY AUTOINCREMENT,
             url NOT NULL,
             email_id INT NOT NULL,
             score INT,
             FOREIGN KEY (email_id) REFERENCES emails(id)
             )''')

conn.commit()

cursor.execute('''CREATE TABLE IF NOT EXISTS score
             (id INTEGER PRIMARY KEY,
             text TEXT NOT NULL,
             type TEXT NOT NULL,
             score INT NOT NULL,
             timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
             )''')
conn.commit()


cursor.execute('''
    INSERT INTO users (username, fullname, password, permission, picture)
    SELECT ?, ?, ?, ?, ?
    WHERE NOT EXISTS (SELECT 1 FROM users)
''', ("root", "root user", password_hash, "admin", "static/images/default.png"))

conn.commit()  

cursor.execute('''
    INSERT INTO action (action, score)
    SELECT ?, ?
    WHERE NOT EXISTS (SELECT action FROM action where action = ?)
''', ("delete", 1000, "delete"))
cursor.execute('''
    INSERT INTO action (action, score)
    SELECT ?, ?
    WHERE NOT EXISTS (SELECT action FROM action where action = ?)
''', ("quarantine", 1000, "quarantine"))
conn.commit()  

def update_profile(session,username,fullname,password,newpassword,picture):
        from main import app
        conn = sqlite3.connect('db.sqlite', check_same_thread=False)
        cursor = conn.cursor()
        if newpassword:
            #HASH THE PASSWORD
            password_hash = hashlib.sha256(password.encode()).hexdigest()
            newpassword_hash = hashlib.sha256(newpassword.encode()).hexdigest()
            cursor.execute("UPDATE users SET password=? WHERE username=? AND password=?", (newpassword_hash, username,password_hash))
            conn.commit()
            if conn.total_changes > 0:
                result = "Update Sucessfull&url=/profile"
            else:
                result = "Wrong Password&url=/profile"

                 
        #IF A PICTURE WAS SENT IN THE UPDATE FORM
        if picture:
                picture_name = username + ".png"
                file_path = os.path.join(app.config['IMAGES_FOLDER'], picture_name)
                picture.save(file_path)
                cursor.execute("UPDATE users SET picture=? WHERE username=?", (str(file_path) , username))
        #IF A USERNAME WAS SENT IN THE UPDATE FORM
        if fullname:
            cursor.execute("UPDATE users SET fullname=? WHERE username=?", (fullname, username,))
        conn.commit()
        if conn.total_changes == 0:
            result = "Update Error&url=/profile"
        else:
            cursor.execute("SELECT * FROM users WHERE username=?", (session['username'],))
            user = cursor.fetchone()
            conn.close()
            if user:
                session['username'] = user[1]
                session['fullname'] = user[2]
                session['permission'] = user[4]
                session['picture'] = user[5]
                session.permanent = True
            result = "Update Sucessfull&url=/profile"
            conn.close()

            return redirect("/result?result={}&url=/profile".format(result))
        conn.close()
        return redirect("/result?result={}&url=/profile".format(result))


def update_users(session,username,fullname,password,permission,picture):
        from main import app
        conn = sqlite3.connect('db.sqlite', check_same_thread=False)
        cursor = conn.cursor()
            
        if password:
            #HASH THE PASSWORD
            password_hash = hashlib.sha256(password.encode()).hexdigest()
            cursor.execute("UPDATE users SET fullname=?, password=?, permission=? WHERE username=?", (fullname, password_hash, permission, username))
        #IF A PICTURE WAS SENT IN THE UPDATE FORM
        if picture:
                picture_name = username + ".png"
                file_path = os.path.join(app.config['IMAGES_FOLDER'], picture_name)
                picture.save(file_path)
                cursor.execute("UPDATE users SET picture=? WHERE username=?", (str(file_path) , username))
        #IF A USERNAME WAS SENT IN THE UPDATE FORM
        cursor.execute("UPDATE users SET fullname=? WHERE username=?", (fullname, username,))
        if permission:
            cursor.execute("UPDATE users SET permission=? WHERE username=?", (permission, username,))
        conn.commit()
        if conn.total_changes > 0:
            result = "Update Sucessfull&url=/update"
        else:
            result = "Update Error&url=/update"
        return result

def register_new_user(session,username,fullname,password,permission,picture):
        from main import app
        conn = sqlite3.connect('db.sqlite', check_same_thread=False)
        cursor = conn.cursor()
        if session['permission'] == "admin":
            cursor.execute("SELECT * FROM users WHERE username=? or fullname=?", (username,fullname,))
            user = cursor.fetchone()
            if user:
                 return redirect("/result?result=Already exists&url=/register")
            password_hash = hashlib.sha256(password.encode()).hexdigest()
            cursor.execute('''
            INSERT INTO users (username, fullname, password, permission, picture)
            SELECT ?, ?, ?, ?, ?
            WHERE NOT EXISTS (SELECT 1 FROM users where username = ? or fullname = ?)
            ''', (username, fullname, password_hash, permission, picture, username, fullname))
            conn.commit()
            conn.close()
            return redirect("/result?result=Successfull Register&url=/register")
        else:
            return redirect("/result?result=You aren't admin&url=/register")

def delete_profile(session,username):
        from main import app
        conn = sqlite3.connect('db.sqlite', check_same_thread=False)
        cursor = conn.cursor()
        if session['permission'] == "admin":
            cursor.execute("DELETE FROM users WHERE username=?", (username,))
            conn.commit()

            if conn.total_changes > 0:
                 conn.close()
                 return "Delete Successfull&url=/delete"
            else:
                 conn.close()
                 return "Error&url=/delete"
        else:
            return "You aren't admin&url=/delete"
        

def register_new_score(type, text, score):
        from main import app
        
        conn = sqlite3.connect('db.sqlite', check_same_thread=False)
        cursor = conn.cursor()
        
        cursor.execute("SELECT MAX(id) FROM score")    
        score_last_id = cursor.fetchone()[0]
        if not score_last_id:
             score_last_id=0

        if type != "all":
            cursor.execute('''
            INSERT INTO score (id,text, type, score)
            SELECT ?,?, ?, ?
            WHERE NOT EXISTS (SELECT 1 FROM score where text = ? AND type = ?)
            ''', (score_last_id+1,text, type, score, text, type,))
            conn.commit(),
            if conn.total_changes > 0:
                conn.close()
                return redirect("success")
        else:
            cursor.execute("DELETE FROM score WHERE text=?", (text,))
            conn.commit()
            cursor.execute('''
            INSERT INTO score (id,text, type, score)
            SELECT ?,?, ?, ?
            WHERE NOT EXISTS (SELECT 1 FROM score where text = ? AND type = ?)
            ''', (score_last_id+1,text, "subject", score, text, "subject",))
            cursor.execute('''
            INSERT INTO score (id,text, type, score)
            SELECT ?,?, ?, ?
            WHERE NOT EXISTS (SELECT 1 FROM score where text = ? AND type = ?)
            ''', (score_last_id+2,text, "body", score, text, "body",))
            cursor.execute('''
            INSERT INTO score (id,text, type, score)
            SELECT ?, ?, ?, ?
            WHERE NOT EXISTS (SELECT 1 FROM score where text = ? AND type = ?)
            ''', (score_last_id+3,text, "url", score, text, "url",))
            conn.commit()
            if conn.total_changes > 0:
                conn.close()
                return redirect("success")
        return redirect("/result?result=Error To Register&url=/forms")
        

def delete_score(session, id):
        conn = sqlite3.connect('db.sqlite', check_same_thread=False)
        cursor = conn.cursor()
        if session['permission'] == "admin":
            cursor.execute("DELETE FROM score WHERE id=?", (id,))
            conn.commit()
            
            if conn.total_changes > 0:
                 conn.close()
                 return "success"
            else:
                 conn.close()
                 return "Error&url=/forms"
        else:
            return "You aren't admin&url=/forms"
        

def new_email(subject,body,urls):
        conn = sqlite3.connect('db.sqlite', check_same_thread=False)
        cursor = conn.cursor()
        cursor.execute('''
        INSERT INTO emails (subject, body)
        SELECT ?, ?
        WHERE NOT EXISTS (SELECT 1 FROM emails where subject = ?)
        ''', (subject, body, subject,))
        conn.commit()
        cursor.execute("SELECT MAX(id) FROM emails")    
        score_last_id = cursor.fetchone()[0]
        # Converter os urls em uma lista de tuplas para corresponder aos espaços reservados na consulta
        url_tuples = [(url, score_last_id) for url in urls]

        # Usar o executemany com os argumentos corretos (consulta e dados)
        cursor.executemany("INSERT OR IGNORE INTO urls (url, email_id) VALUES (?, ?)", url_tuples)
        conn.commit()
        conn.close()


def update_action(delete,quarantine):
        from main import app
        conn = sqlite3.connect('db.sqlite', check_same_thread=False)
        cursor = conn.cursor()
            
        cursor.execute("UPDATE action SET score=? WHERE action=?", (delete, "delete"))
        cursor.execute("UPDATE action SET score=? WHERE action=?", (quarantine, "quarantine"))
        conn.commit()
        if conn.total_changes > 0:
            result = "Update Sucessfull&url=/score_action"
        else:
            result = "Update Error&url=/score_action"
        return result