from flask import Flask, jsonify
from config import Config
from extensions import db, bcrypt, migrate, jwt

# Importar rutas
from routes.auth import auth_bp
from routes.transactions import transactions_bp
from routes.categories import categories_bp
from routes.summary import summary_bp

# Importar modelos
from models.user import User
from models.transaction import Transaction
from models.category import Category

app = Flask(__name__)

app.config.from_object(Config)

db.init_app(app)
bcrypt.init_app(app)
migrate.init_app(app, db)
jwt.init_app(app)

app.register_blueprint(auth_bp)
app.register_blueprint(transactions_bp)
app.register_blueprint(categories_bp)
app.register_blueprint(summary_bp)


@app.route("/", methods=["GET"])
def index():
    return jsonify({
        "status": "ok",
        "message": "Servidor listo y funcionando correctamente"
    }), 200

@jwt.invalid_token_loader
def invalid_token_callback(reason):
    return jsonify({
        "message": "El token no es válido"
    }), 401


@jwt.unauthorized_loader
def missing_token_callback(reason):
    return jsonify({
        "message": "Debes enviar un token de acceso"
    }), 401


@jwt.expired_token_loader
def expired_token_callback(jwt_header, jwt_payload):
    return jsonify({
        "message": "El token ha expirado"
    }), 401


if __name__ == "__main__":
    app.run(debug=True)