from flask import Flask, redirect, url_for, render_template, session, request
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, login_user, logout_user, login_required, UserMixin
from oauthlib.oauth2 import WebApplicationClient
import os

# Load environment variables
from dotenv import load_dotenv
import requests
load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.urandom(24)
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv("DATABASE_URL")
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

print("Database URL: ", os.getenv("DATABASE_URL"))

db = SQLAlchemy(app)
login_manager = LoginManager(app)
client = WebApplicationClient(os.getenv("CLIENT_ID"))

# Define user loader
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Define a simple User model
class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(250), nullable=False)

@app.route('/')
@login_required
def index():
    tables = db.engine.table_names()  # List of all tables in the database
    return render_template('index.html', tables=tables)

@app.route('/login')
def login():
    # Keycloak login URL preparation
    redirect_uri = url_for('login_callback', _external=True)
    request_uri = client.prepare_request_uri(
        os.getenv("AUTH_URI"),
        redirect_uri=redirect_uri,
        scope=["openid", "profile", "email"]
    )
    return redirect(request_uri)

@app.route('/login_callback')
def login_callback():
    # Exchange authorization code for token
    token_response = client.prepare_token_request(
        os.getenv("TOKEN_URI"),
        authorization_response=request.url,
        redirect_uri=url_for('login_callback', _external=True)
    )
    token_url, headers, body = token_response
    token_data = requests.post(token_url, headers=headers, data=body,
                               auth=(os.getenv("CLIENT_ID"), os.getenv("CLIENT_SECRET"))).json()

    # Use token to get user info
    userinfo_response = requests.get(
        os.getenv("USERINFO_URI"),
        headers={'Authorization': f"Bearer {token_data['access_token']}"}
    )
    userinfo = userinfo_response.json()
    user = User.query.filter_by(username=userinfo['preferred_username']).first()
    if not user:
        user = User(username=userinfo['preferred_username'])
        db.session.add(user)
        db.session.commit()
    
    login_user(user)  # Log the user in using Flask-Login
    return redirect(url_for('index'))

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

if __name__ == '__main__':
    db.create_all()
    app.run(ssl_context="adhoc")  # SSL context for HTTPS, useful during development
