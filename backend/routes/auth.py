from flask import Blueprint, request, jsonify
from services.auth_service import AuthService
from flask_jwt_extended import jwt_required, get_jwt_identity

from extensions import db
from models.user import User

auth_bp = Blueprint("auth", __name__, url_prefix="/auth")


@auth_bp.route("/register", methods=["POST"])
def register():

    data = request.get_json(silent=True) or {}

    response, status = AuthService.register(data)

    return jsonify(response), status

@auth_bp.route("/login", methods=["POST"])
def login():

    data = request.get_json(silent=True) or {}

    response, status = AuthService.login(data)

    return jsonify(response), status

@auth_bp.route("/profile", methods=["GET"])
@jwt_required()
def profile():
    user_id = get_jwt_identity()

    user = db.session.get(User, int(user_id))

    if user is None: 
        return jsonify({
            "message": "Usuario no encontrado"
        }), 404

    return jsonify({
        "message": "Token valido",
        "user": user.to_dict()
    }), 200


