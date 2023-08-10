from flask import Flask, render_template, request, jsonify, session, redirect, send_from_directory
from threading import Thread
import hashlib, db, base64, os, sqlite3
from datetime import timedelta
import db, json
import get_emails
import calendar
from datetime import datetime
app = Flask(__name__)
app.secret_key = 'SECRET5521521'
app.config['UPLOAD_FOLDER'] = "static/Uploads"
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(minutes=3000)
app.config['IMAGES_FOLDER'] = "static/images"
app.static_folder = 'static'
app.template_folder = 'templates'


#####################################################
#####################################################
#####################################################
###################### PAGES ########################
#####################################################
#####################################################
#####################################################

#LOGIN PAGE, CREATES THE SESSION IF AUTHENTICATED (LOGIN: ROOT, PASSWORD: 123456)
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        password_hash = hashlib.sha256(password.encode()).hexdigest()

        conn = sqlite3.connect('db.sqlite', check_same_thread=False)
        c = conn.cursor()

        c.execute("SELECT * FROM users WHERE username=? AND password=?", (username, password_hash))
        user = c.fetchone()
        conn.close()

        if user:
            session['username'] = user[1]
            session['fullname'] = user[2]
            session['permission'] = user[4]
            session['picture'] = user[5]
            session.permanent = True
            return redirect("/home")

        else:
            return redirect("/home")
    
    if 'username' in session:
        return redirect('/home')

    return render_template('account/login.html')


@app.route('/')
def none():
    if 'username' in session:
        return redirect('/chart')
    return redirect('/login')

@app.route('/home')
def home():
    if 'username' in session:
        return redirect('/chart')
    return redirect('/login')

@app.route('/profile', methods=['GET', 'POST'])
def profile():
    if 'username' in session:
        if request.method == 'POST':

            username = request.form.get('username',None)
            fullname = request.form.get('fullname',None)
            password = request.form.get('password',None)
            newpassword = request.form.get('newpassword',None)
            picture = request.files.get('picture',None)
            result = db.update_profile(session,username,fullname,password,newpassword,picture)
            if result:
                return result       
        return render_template("layout-nav-head.html", fullname=session['fullname'], picture=session['picture'] , permission=session['permission'], content=render_template('profile.html',username=session['username'],picture=session['picture'],fullname=session['fullname']) )
    return redirect('/login')

@app.route('/logout')
def logout():
    if 'username' in session:
        session.clear()
        return redirect('/login')
    return redirect('/login')

@app.route('/table')
def table():
    if 'username' in session:
        return render_template("layout-nav-head.html", fullname=session['fullname'], picture=session['picture'] , permission=session['permission'],  content=render_template('table.html'))
    return redirect('/login')

@app.route('/chart')
def chart():
    if 'username' in session:
        conn = sqlite3.connect('db.sqlite')
        cursor = conn.cursor()
        cursor.execute("SELECT count(*) FROM emails where status = 'Quarantined' AND strftime('%m', timestamp) = strftime('%m', 'now');")
        quarantined = cursor.fetchone()
        cursor.execute("SELECT count(*) FROM emails where status = 'Deleted' AND strftime('%m', timestamp) = strftime('%m', 'now');")
        deleted = cursor.fetchone()
        cursor.execute("SELECT count(*) FROM emails where status is NULL AND strftime('%m', timestamp) = strftime('%m', 'now');")
        onlyscore = cursor.fetchone()
        cursor.execute("SELECT strftime('%m', timestamp) AS month, COUNT(*) AS count FROM emails WHERE strftime('%Y', timestamp) = strftime('%Y', 'now') GROUP BY month ORDER BY month DESC;")
        action_per_month = cursor.fetchall()

        month_number_to_abbr = {i: calendar.month_abbr[i] for i in range(1, 13)}
        result_dict = {month_number_to_abbr[int(month)]: count for month, count in action_per_month}
        for month_number in range(1, 13):
            if month_number_to_abbr[month_number] not in result_dict:
                result_dict[month_number_to_abbr[month_number]] = 0
        action_per_month = sorted(result_dict.items(), key=lambda x: list(calendar.month_abbr).index(x[0]))
        months_list = [month for month, _ in action_per_month]
        values_list = [count for _, count in action_per_month]
        cursor.close()
        conn.close()
        piechart=[quarantined[0],deleted[0],onlyscore[0]]
        return render_template("layout-nav-head.html", fullname=session['fullname'], picture=session['picture'] , permission=session['permission'],  content=render_template('chart.html',piechart=piechart,month=datetime.now().strftime('%h'),months_list=json.dumps(months_list),values_list=values_list))
    return redirect('/login')

@app.route('/score', methods=['GET', 'POST'])
def score():
    if 'username' in session:
        if request.method == 'POST': 
            db.register_new_score(request.form['flexRadioDefault'],request.form['text'],request.form['score'])
        conn = sqlite3.connect('db.sqlite')
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM score")
        data = cursor.fetchall()
        cursor.close()
        conn.close()

        return render_template("layout-nav-head.html", fullname=session['fullname'], picture=session['picture'] , permission=session['permission'], content=render_template('score.html'))
    return redirect('/login')

@app.route('/faq')
def faq():
    if 'username' in session:
        return render_template("layout-nav-head.html", fullname=session['fullname'], picture=session['picture'] , permission=session['permission'],  content=render_template('faq.html'))
    return redirect('/login')

@app.route('/result')
def result():
    if 'username' in session:
        return render_template("layout-nav-head.html", fullname=session['fullname'], picture=session['picture'] , permission=session['permission'],  content=render_template('result.html'))
    return redirect('/login')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if 'username' in session:
        if request.method == 'POST':   
            username = request.form.get('username',None)
            fullname = request.form.get('fullname',None)
            password = request.form.get('password',None)
            permission = request.form.get('permission',None)
            picture = request.files.get('picture',None)
            if session and username and fullname and password and permission and picture:
                result = db.register_new_user(session,username,fullname,password,permission,picture)
            else: 
                result = db.register_new_user(session,username,fullname,password,permission,app.config['IMAGES_FOLDER'] + "/default.png")
            if result:
                return result   
        conn = sqlite3.connect('db.sqlite')
        cursor = conn.cursor()
        cursor.execute("SELECT username, fullname, password, permission, picture FROM users")
        data = cursor.fetchall()

        cursor.close()
        conn.close()
        return render_template("layout-nav-head.html", fullname=session['fullname'], picture=session['picture'] , permission=session['permission'], content=render_template('account/register.html', users=data))
    return redirect('/login')


@app.route('/update', methods=['GET', 'POST'])
def update():
    if 'username' in session:
        if request.method == 'POST': 
            if session['permission'] == "admin":

                username = request.form.get('username',None)
                fullname = request.form.get('fullname',None)
                password = request.form.get('password',None)
                permission = request.form.get('permission',None)
                picture = request.files.get('picture',None)
                result = db.update_users(session,username,fullname,password,permission,picture)
                response_data = {'result': result}
                response = jsonify(response_data)
                return response       
            else:
                result = "You aren't admin"
                response_data = {'result':  result}
                response = jsonify(response_data)
                return response
        conn = sqlite3.connect('db.sqlite')
        cursor = conn.cursor()
        cursor.execute("SELECT username, fullname, password, permission, picture FROM users WHERE username !=?",(session['username'],))
        data = cursor.fetchall()
        cursor.close()
        conn.close()
        return render_template("layout-nav-head.html", fullname=session['fullname'], picture=session['picture'] , permission=session['permission'], content=render_template('account/update.html', users=data))
    return redirect('/login')

@app.route('/delete', methods=['GET', 'POST'])
def delete():
    if 'username' in session:
        if request.method == 'POST': 
            if session['permission'] == "admin":
                username = request.form.get('username',None)
                if session['username'] == username:
                                    return json.dumps({'result': "You can't delete yourself&url=/delete"})
                result = db.delete_profile(session,username)
                return json.dumps({'result': result})
            else:
                return json.dumps({'result': "You aren't admin&url=/delete"})
        conn = sqlite3.connect('db.sqlite')
        cursor = conn.cursor()
        cursor.execute("SELECT username, fullname, password, permission, picture FROM users WHERE username !=?",(session['username'],))
        data = cursor.fetchall()
        cursor.close()
        return render_template("layout-nav-head.html", fullname=session['fullname'], picture=session['picture'] , permission=session['permission'], content=render_template('account/delete.html', users=data))
    return redirect('/login')

@app.route('/score_action', methods=["POST","GET"])
def score_action():
    if 'username' in session:
        if request.method == 'POST':   
            data = request.get_json()
            type = data.get('flexRadioDefault')
            wildcardregex = data.get('text')
            score = data.get('score')
            result = db.register_new_score(type,wildcardregex,score)
            if result == "sucess":
                return jsonify({"message": "sucess"})
            return jsonify({"message": "result"})
        conn = sqlite3.connect('db.sqlite')
        cursor = conn.cursor()
        cursor.execute("SELECT action, score FROM action")
        data = cursor.fetchall()
        cursor.close()
        return render_template("layout-nav-head.html", fullname=session['fullname'], picture=session['picture'] , permission=session['permission'], content=render_template('score-action.html', delete=data[0][1], quarantine=data[1][1]))
 
    return redirect('/login')


#####################################################
#####################################################
#####################################################
#################### FUNCTIONS ######################
#####################################################
#####################################################
#####################################################

@app.route('/delete_row', methods=['POST'])
def delete_row():
    rowId = request.form['id']
    response = db.delete_score(session,rowId)
    return jsonify({'message': response})


@app.route('/score_table')
def score_table():
    if 'username' in session:
        conn = sqlite3.connect('db.sqlite')
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM score")
        data = cursor.fetchall()
        cursor.close()
        conn.close()
        return jsonify(data)
    

@app.route('/found_table')
def found_table():
    if 'username' in session:
        conn = sqlite3.connect('db.sqlite')
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM emails")
        data = cursor.fetchall()
        cursor.close()
        conn.close()
        return jsonify(data)
    

@app.route('/save_score', methods=["POST"])
def save_score():
    if 'username' in session:
        if request.method == 'POST':   
            data = request.get_json()
            type = data.get('flexRadioDefault')
            wildcardregex = data.get('text')
            score = data.get('score')
            result = db.register_new_score(type,wildcardregex,score)
            if result == "sucess":
                return jsonify({"message": "sucess"})
            return jsonify({"message": "result"})
            
    return redirect('/login')

            
@app.route('/save_action', methods=["POST"])
def save_action():
    if 'username' in session:
        if request.method == 'POST':   
            data = request.get_json()
            delete = data.get('delete')
            quarantine = data.get('quarantine')
            result = db.update_action(delete,quarantine)
            return jsonify({"message": result})
    return redirect('/login')


@app.route('/find_body', methods=["POST"])
def find_body():
    if 'username' in session:
        data = request.get_json()
        subject_id = data.get('subject_id')
        conn = sqlite3.connect('db.sqlite')
        cursor = conn.cursor()
        cursor.execute("SELECT body FROM emails where id = {}".format(subject_id))
        data = cursor.fetchall()
        cursor.close()
        conn.close()
        return jsonify({"message": data})



if __name__ == "__main__":
    thread_print = Thread(target=get_emails.extract_data)
    thread_print.start()
    app.run(debug=False)

