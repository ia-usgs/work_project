import os
from flask import Flask, redirect, url_for, session, request, jsonify, render_template
from flask_login import LoginManager, current_user, login_user, logout_user, login_required
from oauthlib.oauth2 import WebApplicationClient
import requests

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

# Flask app setup
app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY") or "SUPER SECRET"

# Flask-Login setup
login_manager = LoginManager(app)
login_manager.init_app(app)

# OAuth2 client setup
client = WebApplicationClient(os.getenv("CLIENT_ID"))

# Dummy user database
users = {}

# User session management setup
@login_manager.user_loader
def load_user(user_id):
    return users.get(user_id)

# Flask routes
@app.route('/')
def index():
    if current_user.is_authenticated:
        return render_template('dashboard.html', user=current_user)
    else:
        return '<a href="/login">Login</a>'

@app.route('/login')
def login():
    # Find out what URL to hit for Keycloak login
    request_uri = client.prepare_request_uri(
        os.getenv("AUTH_URI"),
        redirect_uri=request.base_url + "/callback",
        scope=["openid", "email", "profile"],
    )
    return redirect(request_uri)

@app.route('/login/callback')
def callback():
    # Get authorization code Keycloak sent back to you
    code = request.args.get("code")

    # Prepare and send a request to get tokens
    token_url, headers, body = client.prepare_token_request(
        os.getenv("TOKEN_URI"),
        authorization_response=request.url,
        redirect_url=request.base_url,
        code=code
    )
    token_response = requests.post(
        token_url,
        headers=headers,
        data=body,
        auth=(os.getenv("CLIENT_ID"), os.getenv("CLIENT_SECRET")),
    )

    # Parse the tokens!
    client.parse_request_body_response(json.dumps(token_response.json()))

    # Now that you have tokens (access_token and optionally refresh_token),
    # you need to get the user's profile and create a user session
    userinfo_response = requests.get(
        os.getenv("USERINFO_URI"),
        headers={'Authorization': 'Bearer ' + token_response.json()["access_token"]}
    )

    userinfo = userinfo_response.json()
    unique_id = userinfo["sub"]
    users[unique_id] = userinfo  # This could be more complex in a real app

    # Begin user session by logging the user in
    login_user(users[unique_id])

    return redirect(url_for("index"))

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for("index"))

if __name__ == "__main__":
    port = int(os.environ.get('FLASK_PORT', 8080))
    app.run(port=port, host='0.0.0.0', ssl_context="adhoc", debug=True)  # SSL context for HTTPS
