from flask import Flask, render_template, request, make_response, current_app
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import inspect
from flask_caching import Cache

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root@localhost:3306/used_car_database'
app.config['CACHE_TYPE'] = 'simple'
app.config['CACHE_DEFAULT_TIMEOUT'] = 300
db = SQLAlchemy(app)
cache = Cache(app)

@app.route('/')
@cache.cached(timeout=300)
def index():
    inspector = inspect(db.engine)
    tables = inspector.get_table_names()
    return render_template('index.html', tables=tables)

if __name__ == '__main__':
    app.run(debug=True)
