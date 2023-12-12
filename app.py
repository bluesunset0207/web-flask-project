from flask import Flask, render_template, session, url_for, request, redirect, flash
import pymysql
import re
from werkzeug.utils import secure_filename
import os
from flask import send_from_directory
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)

UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif', 'pptx', 'hwp', 'hwpx', 'docx'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql://blue:vkfksshdmf0207@db/flasksql'  # DB 접속 정보
db = SQLAlchemy(app)
class Posts(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False)
    content = db.Column(db.Text, nullable=False)
    filename = db.Column(db.String(255), nullable=True)

class Users(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(64), nullable=False)
    email = db.Column(db.String(50), unique=True, nullable=False)

with app.app_context():
    db.create_all()

app.secret_key = 'sample_secret'

def connectsql():
    conn = pymysql.connect(host='db', port=3306, user = 'root', passwd = 'vkfksshdmf0207', db = 'flasksql', charset='utf8')
    return conn

@app.route('/')
def index():
    if 'username' in session:
        username = session['username']

        return render_template('index.html', username = username)
    else:
        username = None
        return render_template('index.html', username = username )

@app.route('/board')
def board():
    conn = connectsql()
    cursor = conn.cursor(pymysql.cursors.DictCursor)
    query = "SELECT id, title, content FROM posts ORDER BY id DESC"
    cursor.execute(query)
    post = cursor.fetchall()
    
    cursor.close()
    conn.close()

    return render_template('board.html', post = post)

@app.route('/board/read/<id>')
def read(id):
    if 'username' in session:
        username = session['username']

        conn = connectsql()
        cursor = conn.cursor(pymysql.cursors.DictCursor)
        query = "SELECT id, title, content, username, filename FROM posts WHERE id = %s"
        value = id
        cursor.execute(query, value)
        post = cursor.fetchone()

        isadmin = session['username'] == 'admin'
        iswriter = False
        if post['username'] == username:
            iswriter = True
        conn.commit()

        query = "SELECT * FROM comments WHERE post_id = %s ORDER BY id DESC"
        cursor.execute(query, id)
        comments = cursor.fetchall()

        query = "SELECT * FROM recommend WHERE post_id = %s AND username = %s"
        cursor.execute(query, (id, username))
        recommended = cursor.fetchone()

        cursor.close()
        conn.close()
        return render_template('read.html', post = post, iswriter = iswriter, comments = comments, recommended = recommended, isadmin = isadmin)
    else:
        redirect(url_for('login'))

@app.route('/board/edit/<id>', methods=['GET', 'POST'])
def edit(id):
    if request.method == 'POST':
        if 'username' in session:
            username = session['username']
 
            edittitle = request.form['title']
            editcontent = request.form['content']

            conn = connectsql()
            cursor = conn.cursor()
            query = "UPDATE posts SET title = %s, content = %s WHERE id = %s"
            value = (edittitle, editcontent, id)
            cursor.execute(query, value)
            conn.commit()
            cursor.close()
            conn.close()
    
        return redirect(url_for('board'))
    else:
        username = session['username']
        conn = connectsql()
        cursor = conn.cursor(pymysql.cursors.DictCursor)
        query = "SELECT id, title, content, username FROM posts WHERE id = %s"
        value = id
        cursor.execute(query, value)
        post = cursor.fetchone()
        cursor.close()
        conn.close()
        if username == post['username']:
            return render_template('edit.html', post = post)
        else:
            return redirect(url_for('board'))

@app.route('/board/delete/<id>')
def delete(id):
    if 'username' in session:
        username = session['username']
        conn = connectsql()
        cursor = conn.cursor()
        query = "SELECT username FROM posts WHERE id = %s"
        value = id
        cursor.execute(query, value)
        data = [post[0] for post in cursor.fetchall()]
        cursor.close()
        conn.close()
        
        isadmin = session['username'] == 'admin'

        if username in data or isadmin:
            conn = connectsql()
            cursor = conn.cursor()
            query = "DELETE FROM posts WHERE id = %s"
            value = id
            cursor.execute(query, value)
            conn.commit()
            cursor.close()
            conn.close()
            return redirect(url_for('board'))
        
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS
        
@app.route('/board/write', methods=['GET', 'POST'])
def write():
    if request.method == 'POST':
        if 'username' in session:
            username = session['username']
            
            title = request.form['title']
            content = request.form['content']
            file = request.files['file']
            filename = None

            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))

            conn = connectsql()
            cursor = conn.cursor()
            query = "INSERT INTO posts (title, content, username, filename) values (%s, %s, %s, %s)"
            value = (title, content, username, filename)
            cursor.execute(query, value)
            conn.commit()
            cursor.close()
            conn.close()

            return redirect('/')
        else:
            return redirect(url_for('login'))
    else:
        if 'username' in session:
            return render_template ('write.html')
        else:
            return redirect(url_for('login'))

@app.route('/download/<filename>')
def download(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename, as_attachment=True)

@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect(url_for('index'))

@app.route('/login', methods=['GET','POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        conn = connectsql()
        cursor = conn.cursor()
        query = "SELECT * FROM users WHERE username = %s AND password = %s"
        value = (username, password)
        cursor.execute(query, value)
        data = cursor.fetchall()
        cursor.close()
        conn.close()

        if data:
            session['username'] = request.form['username']
            session['password'] = request.form['password']
            return redirect(url_for('index'))
        else:
            return redirect(url_for('login'))
    else:
        return render_template ('login.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        email = request.form['email']

        if not validate_password(password):
            flash("비밀번호는 최소 8자리 이상이어야 하며, 대문자, 소문자, 숫자, 특수 문자를 최소 1개 이상 포함해야 합니다.", "error")
            return render_template('signup.html', username=username, email=email)
        
        conn = connectsql()
        cursor = conn.cursor()
        query = "SELECT * FROM users WHERE email = %s"
        value = email
        cursor.execute(query, value)
        findemail = (cursor.fetchall())

        query = "SELECT * FROM users WHERE username = %s"
        value = username
        cursor.execute(query, value)
        findusername = (cursor.fetchall())
        
        if findemail:
            return render_template('registError.html', error = 'email')
        elif findusername:
            return render_template('registError.html', error = 'username') 
        else:
            query = "INSERT INTO users (username, password, email) values (%s, %s, %s)"
            value = (username, password, email)
            cursor.execute(query, value)
            data = cursor.fetchall()
            conn.commit()
            return redirect('/')
        cursor.close()
        conn.close()
    else:
        return render_template('signup.html')        

def validate_password(password):
    if len(password) < 8:
        return False
    if not re.search("[a-z]", password):
        return False
    if not re.search("[0-9]", password):
        return False
    return True


@app.route('/comment/<id>', methods=['POST'])
def comment(id):
    if 'username' not in session:
        return redirect(url_for('login'))
    
    username = session['username']
    content = request.form.get('content')

    conn = connectsql()
    cursor = conn.cursor()
    query = "INSERT INTO comments (post_id, username, content) VALUES (%s, %s, %s)"
    value = (id, username, content)
    cursor.execute(query, value)
    conn.commit()
    cursor.close()
    conn.close()
    
    return redirect(url_for('read', id=id))

@app.route('/recommend/<id>', methods=['POST'])
def recommend(id):
    if 'username' not in session:
        return redirect(url_for('login'))
    
    username = session['username']

    conn = connectsql()
    cursor = conn.cursor()
    
    query = "SELECT * FROM recommend WHERE post_id = %s AND username = %s"
    cursor.execute(query, (id, username))
    recommended = cursor.fetchone()
    
    if not recommended:
        query = "INSERT INTO recommend (post_id, username) VALUES (%s, %s)"
        cursor.execute(query, (id, username))
    
    conn.commit()
    cursor.close()
    conn.close()
    
    return redirect(url_for('read', id=id))

@app.route('/search')
def search():
    search_type = request.args.get('search_type')
    query = request.args.get('query')
    
    conn = connectsql()
    cursor = conn.cursor(pymysql.cursors.DictCursor)
    
    if search_type == 'title':
        cursor.execute("SELECT * FROM posts WHERE title LIKE %s", ('%' + query + '%',))
    elif search_type == 'content':
        cursor.execute("SELECT * FROM posts WHERE content LIKE %s", ('%' + query + '%',))
    
    posts = cursor.fetchall()
    conn.close()
    
    return render_template('search_results.html', posts=posts)

if __name__ == '__main__':
    app.run(debug=True)

