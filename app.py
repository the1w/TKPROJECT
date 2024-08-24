from flask import Flask, render_template, redirect, url_for, flash, request, abort, jsonify, send_file, session
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from flask_mail import Mail, Message
from flask_babel import Babel, _
from werkzeug.security import generate_password_hash, check_password_hash
from itsdangerous import URLSafeTimedSerializer
from datetime import datetime, timedelta
import os
import qrcode
from io import BytesIO
import logging

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY') or 'your-secret-key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///app.db'
app.config['MAIL_SERVER'] = 'smtp-relay.brevo.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = '7ad7b0001@smtp-brevo.com'
app.config['MAIL_PASSWORD'] = '482ZY7c9zqT0RxXa'
app.config['MAIL_DEFAULT_SENDER'] = '7ad7b0001@smtp-brevo.com'
app.config['BABEL_DEFAULT_LOCALE'] = 'lt'

db = SQLAlchemy(app)
login_manager = LoginManager(app)
mail = Mail(app)
babel = Babel(app)

# Set up logging
logging.basicConfig(filename='app.log', level=logging.INFO)

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128))
    nfc_tags = db.relationship('NFCTag', backref='owner', lazy='dynamic')

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def get_reset_token(self, expires_sec=1800):
        s = URLSafeTimedSerializer(app.config['SECRET_KEY'])
        return s.dumps({'user_id': self.id})

    @staticmethod
    def verify_reset_token(token, expires_sec=1800):
        s = URLSafeTimedSerializer(app.config['SECRET_KEY'])
        try:
            user_id = s.loads(token, max_age=expires_sec)['user_id']
        except:
            return None
        return User.query.get(user_id)

class NFCTag(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    tag_id = db.Column(db.String(100), unique=True, nullable=False)
    redirect_url = db.Column(db.String(500), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

def get_locale():
    return session.get('lang', request.accept_languages.best_match(['en', 'lt']))

babel.init_app(app, locale_selector=get_locale)

@app.context_processor
def inject_get_locale():
    return dict(get_locale=get_locale)

@app.route('/set_language/<lang>')
def set_language(lang):
    session['lang'] = lang
    return redirect(request.referrer or url_for('index'))

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        user = User(username=username, email=email)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        flash(_('Registration successful. Please log in.'))
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        user = User.query.filter_by(username=request.form['username']).first()
        if user and user.check_password(request.form['password']):
            login_user(user)
            return redirect(url_for('dashboard'))
        flash(_('Invalid username or password'))
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

@app.route('/dashboard')
@login_required
def dashboard():
    tags = current_user.nfc_tags.all()
    return render_template('dashboard.html', tags=tags)

@app.route('/add_tag', methods=['POST'])
@login_required
def add_tag():
    tag_id = request.form['tag_id']
    redirect_url = request.form['redirect_url']
    tag = NFCTag(tag_id=tag_id, redirect_url=redirect_url, owner=current_user)
    db.session.add(tag)
    db.session.commit()
    flash(_('NFC Tag added successfully'))
    return redirect(url_for('dashboard'))

@app.route('/edit_tag/<int:id>', methods=['POST'])
@login_required
def edit_tag(id):
    tag = NFCTag.query.get_or_404(id)
    if tag.owner != current_user:
        abort(403)
    tag.redirect_url = request.form['redirect_url']
    db.session.commit()
    flash(_('NFC Tag updated successfully'))
    return redirect(url_for('dashboard'))

@app.route('/delete_tag/<int:id>', methods=['POST'])
@login_required
def delete_tag(id):
    tag = NFCTag.query.get_or_404(id)
    if tag.owner != current_user:
        abort(403)
    db.session.delete(tag)
    db.session.commit()
    flash(_('NFC Tag deleted successfully'))
    return redirect(url_for('dashboard'))

@app.route('/redirect/<tag_id>')
def nfc_redirect(tag_id):
    tag = NFCTag.query.filter_by(tag_id=tag_id).first_or_404()
    return redirect(tag.redirect_url)

@app.route('/reset_password', methods=['GET', 'POST'])
def reset_request():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    if request.method == 'POST':
        user = User.query.filter_by(email=request.form['email']).first()
        if user:
            try:
                send_reset_email(user)
                flash(_('An email has been sent with instructions to reset your password.'))
                logging.info(f"Password reset email sent to {user.email}")
            except Exception as e:
                flash(_('An error occurred while sending the password reset email. Please try again later.'))
                logging.error(f"Failed to send password reset email to {user.email}. Error: {str(e)}")
        else:
            flash(_('No account found with that email address.'))
            logging.warning(f"Password reset attempted for non-existent email: {request.form['email']}")
        return redirect(url_for('login'))
    return render_template('reset_request.html')

@app.route('/reset_password/<token>', methods=['GET', 'POST'])
def reset_token(token):
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    user = User.verify_reset_token(token)
    if user is None:
        flash(_('That is an invalid or expired token'))
        return redirect(url_for('reset_request'))
    if request.method == 'POST':
        user.set_password(request.form['password'])
        db.session.commit()
        flash(_('Your password has been updated! You are now able to log in'))
        logging.info(f"Password reset successful for user: {user.email}")
        return redirect(url_for('login'))
    return render_template('reset_token.html')

def send_reset_email(user):
    token = user.get_reset_token()
    msg = Message('Password Reset Request',
                  sender=app.config['MAIL_DEFAULT_SENDER'],
                  recipients=[user.email])
    msg.body = f'''To reset your password, visit the following link:
{url_for('reset_token', token=token, _external=True)}

If you did not make this request then simply ignore this email and no changes will be made.
'''
    mail.send(msg)

@app.route('/qr_code/<tag_id>')
def qr_code(tag_id):
    url = url_for('nfc_redirect', tag_id=tag_id, _external=True)
    img = qrcode.make(url)
    img_io = BytesIO()
    img.save(img_io, 'PNG')
    img_io.seek(0)
    return send_file(img_io, mimetype='image/png')

def create_tables():
    with app.app_context():
        db.create_all()

if __name__ == '__main__':
    create_tables()
    app.run(debug=True)