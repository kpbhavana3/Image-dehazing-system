from flask import Flask, render_template, request, redirect, url_for, flash, session, g, send_from_directory
from werkzeug.utils import secure_filename, safe_join
import os
import cv2
import numpy as np
import sqlite3
import image_dehazer

app = Flask(__name__)
app.secret_key = 'supersecretkey'
DATABASE = 'database.db'
UPLOAD_FOLDER = 'static/uploads'
DEHAZED_FOLDER = 'static/dehazed_images'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['DEHAZED_FOLDER'] = DEHAZED_FOLDER
app.config['ALLOWED_EXTENSIONS'] = {'png', 'jpg', 'jpeg', 'gif'}  # Add more if needed

# Ensure upload and dehazed directories exist
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)
if not os.path.exists(DEHAZED_FOLDER):
    os.makedirs(DEHAZED_FOLDER)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

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
    return render_template('index.html')

@app.route('/upload', methods=['GET', 'POST'])
def upload_file():
    if request.method == 'POST':
        if 'file' not in request.files:
            flash('No file part')
            return redirect(request.url)

        file = request.files['file']

        if file.filename == '':
            flash('No selected file')
            return redirect(request.url)

        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            original_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(original_path)

            # Dehaze the uploaded image
            img = cv2.imread(original_path)
            if img is not None:
                dehazed_img, _ = image_dehazer.remove_haze(img)
                dehazed_filename = f"dehazed_{filename}"
                dehazed_path = os.path.join(app.config['DEHAZED_FOLDER'], dehazed_filename)
                cv2.imwrite(dehazed_path, dehazed_img)

                # Save image paths to the database
                db = get_db()
                user_id = get_user_id(session['email'])
                cursor = db.cursor()
                cursor.execute('''INSERT INTO images (user_id, original_path, dehazed_path) VALUES (?, ?, ?)''',
                               (user_id, original_path, dehazed_path))
                db.commit()

                flash('Image dehazed successfully!')
                return redirect(url_for('view_image', filename=dehazed_filename))
            else:
                flash('Error processing image. Please try again.')
                return redirect(request.url)
        else:
            flash('Invalid file type. Allowed types are: png, jpg, jpeg, gif')
            return redirect(request.url)

    return render_template('upload.html')

@app.route('/login', methods=['POST'])
def login():
    email = request.form.get('email')
    password = request.form.get('password')

    if not email or not password:
        flash('Email and password are required')
        return redirect(url_for('home'))

    db = get_db()
    cursor = db.cursor()
    cursor.execute('SELECT * FROM users WHERE email = ?', (email,))
    user = cursor.fetchone()

    if user and user['password'] == password:
        session['email'] = email
        flash('Login successful!')
        return redirect(url_for('dehaze'))
    else:
        flash('Invalid credentials')
        return redirect(url_for('home'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')

        if not username or not email or not password:
            flash('All fields are required')
            return redirect(url_for('register'))

        db = get_db()
        cursor = db.cursor()
        try:
            cursor.execute('INSERT INTO users (username, password, email) VALUES (?, ?, ?)', (username, password, email))
            db.commit()
            flash('Registration successful! Please login.')
            return redirect(url_for('home'))
        except sqlite3.IntegrityError:
            flash('Username or email already exists. Please choose a different username or email.')
            return redirect(url_for('register'))

    return render_template('register.html')

@app.route('/forgot', methods=['GET'])
def forgot():
    return 'Forgot Password functionality not yet implemented'

@app.route('/dehaze', methods=['GET', 'POST'])
def dehaze():
    if request.method == 'POST':
        if 'image' not in request.files:
            flash('No file part')
            return redirect(request.url)

        file = request.files['image']

        if file.filename == '':
            flash('No selected file')
            return redirect(request.url)

        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            original_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(original_path)

            img = cv2.imread(original_path)
            if img is not None:
                dehazed_img, _ = image_dehazer.remove_haze(img)
                dehazed_filename = f"dehazed_{filename}"
                dehazed_path = os.path.join(app.config['DEHAZED_FOLDER'], dehazed_filename)
                cv2.imwrite(dehazed_path, dehazed_img)

                # Save image paths to the database
                db = get_db()
                user_id = get_user_id(session['email'])
                cursor = db.cursor()
                cursor.execute('''INSERT INTO images (user_id, original_path, dehazed_path) VALUES (?, ?, ?)''',
                               (user_id, original_path, dehazed_path))
                db.commit()

                flash('Image dehazed successfully!')
                return redirect(url_for('view_image', filename=dehazed_filename))
            else:
                flash('Error processing image. Please try again.')
                return redirect(request.url)
        else:
            flash('Invalid file type. Allowed types are: png, jpg, jpeg, gif')
            return redirect(request.url)

    return render_template('upload.html')

@app.route('/view_image/<filename>')
def view_image(filename):
    return render_template('view_image.html', filename=filename)

@app.route('/download_image/<filename>')
def download_image(filename):
    file_path = safe_join(DEHAZED_FOLDER, filename)
    return send_from_directory(DEHAZED_FOLDER, filename, as_attachment=True)

def process_image(filepath):
    image = cv2.imread(filepath)

    image = histogram_equalization(image)

    image = apply_clahe(image)

    image = gamma_correction(image, gamma=1.2)

    cv2.imwrite(filepath, image)
    return filepath

def histogram_equalization(image):
    yuv = cv2.cvtColor(image, cv2.COLOR_BGR2YUV)
    yuv[:, :, 0] = cv2.equalizeHist(yuv[:, :, 0])
    result = cv2.cvtColor(yuv, cv2.COLOR_YUV2BGR)
    return result

def apply_clahe(image):
    lab = cv2.cvtColor(image, cv2.COLOR_BGR2LAB)
    clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8))
    lab[:, :, 0] = clahe.apply(lab[:, :, 0])
    result = cv2.cvtColor(lab, cv2.COLOR_LAB2BGR)
    return result

def gamma_correction(image, gamma=1.0):
    inv_gamma = 1.0 / gamma
    table = np.array([((i / 255.0) ** inv_gamma) * 255 for i in range(256)]).astype("uint8")
    return cv2.LUT(image, table)

def get_user_id(email):
    db = get_db()
    cursor = db.cursor()
    cursor.execute('SELECT id FROM users WHERE email = ?', (email,))
    user = cursor.fetchone()
    return user['id']

if __name__ == '__main__':
    app.run(debug=False,host='0.0.0.0')
