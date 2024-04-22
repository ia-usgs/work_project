import json
import os

from flask import Flask, jsonify, render_template, redirect, request, url_for
from flask_sqlalchemy import SQLAlchemy
from keycloak import KeycloakOpenID

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://admin:kali@172.30.153.109/irvindb'
db = SQLAlchemy(app)

keycloak_client = KeycloakOpenID(
    server_url="https://keycloak-ekho-sso-dev.apps.ocpshareddev.gc1.myngc.com/auth/",
    client_id="irvintest",
    realm_name="developer", 
    verify=False
)


@app.route('/')
def index():
    return render_template('login.html')


@app.route('/login')
def login():
    return render_template('login.html')

@app.route('/keycloak-login')
def keycloak_login():
    redirect_url = url_for('authorize', _external=True)
    print("Generated redirect_uri:", redirect_url)  # Debugging output
    auth_url = keycloak_client.auth_url(redirect_uri=redirect_url)
    print("Authorization URL:", auth_url)  # Debugging output
    return redirect(auth_url)

    

@app.route('/authorize')
def authorize():
    try:
        code = request.args.get('code')
        if not code:
            return jsonify({'error': 'No authorization code provided'}), 400

         # Exchange the authorization code for a token
        token_response = keycloak_client.token(code=code)
        # Assuming token_response is a dict that could have an 'error' key.
        if 'access_token' not in token_response:
            print(f"Failed to retrieve access token: {token_response}")
            return jsonify(token_response), 401

        print(f"Authorization code received: {code}")
        token = keycloak_client.token(code=code)
        print(f"Token received: {token}")

        user_info = keycloak_client.userinfo(token['access_token'])
        return jsonify(user_info)

    except Exception as e:
        print(f"Error during token exchange or user info retrieval: {str(e)}")
        return jsonify({'error': str(e)}), 500
    error = request.args.get('error')
    if error:
        error_description = request.args.get('error_description')
        return jsonify({'error': error, 'error_description': error_description}), 400
    code = request.args.get('code')
    token = keycloak_client.token(code=code)
    user_info = keycloak_client.userinfo(token['access_token'])
    if isinstance(user_info, bytes):
        user_info = json.loads(user_info.decode('utf-8'))
    username = user_info['preferred_username']
    user_id = int(ord(username[0]) - ord('0'))
    return jsonify({'user_id': user_id})

class User(db.Model):
    # The __tablename__ attribute sets the name of the database table
    # to 'users'.
    __tablename__ = 'users'

    # The 'id' column is the primary key of the 'users' table.
    # It is an integer column.
    id = db.Column(db.Integer, primary_key=True)

    # The 'name' column stores the name of the user.
    # It is a string column with a maximum length of 50 characters.
    name = db.Column(db.String(50), doc="Name of the user.")

    # The 'age' column stores the age of the user.
    # It is a string column with a maximum length of 50 characters.
    age = db.Column(db.String(50), doc="Age of the user.")

    # The 'address' column stores the address of the user.
    # It is a string column with a maximum length of 50 characters.
    address = db.Column(db.String(50), doc="Address of the user.")

    # The 'salary' column stores the salary of the user.
    # It is a string column with a maximum length of 50 characters.
    salary = db.Column(db.String(50), doc="Salary of the user.")


@app.route('/table_data/users')
def table_data():
    users = User.query.all()
    table_data = []
    for user in users:
        table_data.append({
            'id': user.id,
            'name': user.name, 
            'age': user.age, 
            'address': user.address, 
            'salary': user.salary
        })
    return jsonify(table_data)

if __name__ == '__main__':
    port = int(os.environ.get('FLASK_PORT', 8080))
    app.run(port=port, host='0.0.0.0', debug=True)
