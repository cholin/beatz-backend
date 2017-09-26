import flask_sqlalchemy
import flask_restless
from flask import Flask, request, abort, jsonify
from sqlalchemy.orm import validates
from itsdangerous import TimestampSigner, SignatureExpired
from urlextract import URLExtract
from werkzeug.security import safe_str_cmp

app = Flask(__name__)
app.config.from_envvar('SETTINGS')

db = flask_sqlalchemy.SQLAlchemy(app)
signer = TimestampSigner(app.config['SECRET_KEY'])


class Post(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user = db.Column(db.Unicode)
    date = db.Column(db.DateTime)
    msg = db.Column(db.Unicode, unique=True, index=True)

    @validates('msg')
    def validate_msg(self, key, value):
        extractor = URLExtract()
        urls = extractor.find_urls(value)
        assert len(urls) > 0
        return value


@app.after_request
def add_cors_headers(resp):
    resp.headers['Access-Control-Allow-Origin'] = '*'
    resp.headers['Access-Control-Allow-Headers'] = 'Content-Type, X-Secret, X-Token'
    return resp


@app.route('/auth')
def auth():
    secret = request.headers.get('X-Secret', '')
    if not safe_str_cmp(secret, app.config['MASTER_TOKEN']):
        abort(401)

    data = signer.sign(secret.encode())
    value, timestamp, signature = data.split(signer.sep.encode())
    token = signer.sep.encode().join([timestamp, signature]).decode()
    return jsonify(token=token)


def check_token(**kwargs):
    token = request.headers.get('X-Token').encode()
    if token:
        value = b'.'.join([app.config['MASTER_TOKEN'].encode(), token])
        try:
            signer.unsign(value, max_age=60*60)
        except SignatureExpired:
            raise flask_restless.ProcessingException(code=401)


db.create_all()

manager = flask_restless.APIManager(app, flask_sqlalchemy_db=db)
blueprint = manager.create_api_blueprint(Post,
                validation_exceptions=[AssertionError],
                methods=['GET', 'POST', 'OPTIONS'],
                preprocessors={
                    'GET_SINGLE': [check_token],
                    'GET_MANY': [check_token],
                    'POST': [check_token]
                }
            )
blueprint.after_request(add_cors_headers)
app.register_blueprint(blueprint)


if __name__ == "__main__":
    app.run("0.0.0.0", port=8080)
