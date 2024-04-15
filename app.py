import json
import os

from flask import Flask, jsonify, render_template, redirect, request, url_for
from flask_sqlalchemy import SQLAlchemy
from keycloak import KeycloakOpenID

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://admin:kali@localhost/irvindb'
db = SQLAlchemy(app)

keycloak_client = KeycloakOpenID(
    server_url="https://pacer-dev.northgrum.com",
    client_id="pacer-dev",
    realm_name="developer",
    client_secret_key="redhatsso"
)


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/login')
def login():
    return render_template('login.html')

@app.route('/keycloak-login')
def keycloak_login():
    well_known = keycloak_client.well_known()
    print(type(well_known), well_known)  # Add this line for debugging
    redirect_url = url_for('authorize', _external=True)
    return redirect(keycloak_client.auth_url(redirect_uri=redirect_url))

    

@app.route('/authorize', methods=['GET'])
def authorize():
    code = request.args.get('code')
    token = keycloak_client.token(code=code)
    user_info = keycloak_client.userinfo(token['access_token'])
    if isinstance(user_info, bytes):
        user_info = json.loads(user_info.decode('utf-8'))
    username = user_info['preferred_username']
    user_id = int(ord(username[0]) - ord('0'))
    return jsonify({'user_id': user_id})

class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50))
    email = db.Column(db.String(50))

@app.route('/table_data/users')
def table_data():
    users = User.query.all()
    table_data = []
    for user in users:
        table_data.append({
            'id': user.id,
            'name': user.name,
            'email': user.email
        })
    return jsonify(table_data)

if __name__ == '__main__':
    port = int(os.environ.get('FLASK_PORT', 8080))
    app.run(port=port, host='0.0.0.0', debug=True)
