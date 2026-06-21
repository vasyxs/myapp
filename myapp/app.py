from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import sqlite3

app = Flask(__name__)
app.secret_key = 'supersecretkey123' 

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    reviews = db.relationship('Review', backref='user', lazy=True)

class Review(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    movie = db.Column(db.String(100), nullable=False)
    rating = db.Column(db.Integer, nullable=False)
    text = db.Column(db.Text, nullable=False)
    date = db.Column(db.DateTime, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

with app.app_context():
    db.create_all()

@app.route('/')
def index():
    reviews = Review.query.order_by(Review.date.desc()).all()
    return render_template('index.html', reviews=reviews)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        confirm = request.form['confirm_password']
        
        if password != confirm:
            flash('Пароли не совпадают!', 'error')
            return render_template('register.html')
        
        if len(password) < 4:
            flash('Пароль должен быть длиннее 4 символов', 'error')
            return render_template('register.html')
        
        user_exists = User.query.filter_by(username=username).first()
        if user_exists:
            flash('Это имя уже занято!', 'error')
            return render_template('register.html')
        
        email_exists = User.query.filter_by(email=email).first()
        if email_exists:
            flash('Эта почта уже используется!', 'error')
            return render_template('register.html')
        
        hashed = generate_password_hash(password)
        new_user = User(username=username, email=email, password=hashed)
        db.session.add(new_user)
        db.session.commit()
        
        flash('Регистрация прошла успешно! Теперь войдите.', 'success')
        return redirect(url_for('login'))
    
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        
        user = User.query.filter_by(email=email).first()
        
        if user and check_password_hash(user.password, password):
            session['user_id'] = user.id
            session['username'] = user.username
            flash(f'Привет, {user.username}!', 'success')
            return redirect(url_for('index'))
        else:
            flash('Неверная почта или пароль!', 'error')
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('Вы вышли из аккаунта', 'info')
    return redirect(url_for('index'))

@app.route('/profile')
def profile():
    if 'user_id' not in session:
        flash('Сначала войдите в аккаунт!', 'error')
        return redirect(url_for('login'))
    
    user = User.query.get(session['user_id'])
    reviews = Review.query.filter_by(user_id=user.id).order_by(Review.date.desc()).all()
    return render_template('profile.html', user=user, reviews=reviews)

@app.route('/add', methods=['GET', 'POST'])
def add_review():
    if 'user_id' not in session:
        flash('Сначала войдите!', 'error')
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        movie = request.form['movie']
        rating = request.form['rating']
        text = request.form['text']
        
        if not movie or not text:
            flash('Заполните все поля!', 'error')
            return render_template('add.html')
        
        new_review = Review(
            movie=movie,
            rating=int(rating),
            text=text,
            user_id=session['user_id']
        )
        db.session.add(new_review)
        db.session.commit()
        flash('Отзыв добавлен!', 'success')
        return redirect(url_for('profile'))
    
    return render_template('add.html')

@app.route('/delete/<int:id>')
def delete_review(id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    review = Review.query.get(id)
    if review and review.user_id == session['user_id']:
        db.session.delete(review)
        db.session.commit()
        flash('Отзыв удален', 'success')
    else:
        flash('Нельзя удалить чужой отзыв!', 'error')
    
    return redirect(url_for('profile'))

if __name__ == '__main__':
    app.run(debug=True)