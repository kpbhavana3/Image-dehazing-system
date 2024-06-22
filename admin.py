from flask import Flask, render_template, g
import sqlite3

app = Flask(__name__)
app.secret_key = 'supersecretkey'
DATABASE = 'database.db'

def get_db():
    if 'db' not in g:
        g.db = sqlite3.connect(DATABASE)
        g.db.row_factory = sqlite3.Row
    return g.db

@app.teardown_appcontext
def close_db(exception):
    db = g.pop('db', None)
    if db is not None:
        db.close()

@app.route('/')
def home():
    return render_template('index_admin.html')

@app.route('/user_uploads')
def user_uploads():
    db = get_db()
    cursor = db.cursor()
    cursor.execute('''
        SELECT users.username, users.email, images.original_path, images.dehazed_path, images.upload_time
        FROM users
        JOIN images ON users.id = images.user_id
        ORDER BY images.upload_time DESC
    ''')
    uploads = cursor.fetchall()
    return render_template('user_uploads.html', uploads=uploads)

if __name__ == '__main__':
    app.run(debug=True)
