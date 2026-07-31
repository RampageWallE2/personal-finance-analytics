from flask import Blueprint, jsonify, request
from flask_jwt_extended import (
    get_jwt_identity,
    jwt_required
)

from services.category_service import CategoryService


categories_bp = Blueprint(
    "categories",
    __name__,
    url_prefix="/categories"
)


def get_current_user_id():
    return int(get_jwt_identity())


@categories_bp.route("/", methods=["POST"], strict_slashes=False)
@jwt_required()
def create_category():
    user_id = get_current_user_id()
    data = request.get_json(silent=True) or {}

    response, status = CategoryService.create(
        user_id,
        data
    )

    return jsonify(response), status


@categories_bp.route("/", methods=["GET"], strict_slashes=False)
@jwt_required()
def get_categories():
    user_id = get_current_user_id()

    filters = {
        "type": request.args.get("type")
    }

    response, status = CategoryService.get_all(
        user_id,
        filters
    )

    return jsonify(response), status


@categories_bp.route("/<int:category_id>", methods=["GET"])
@jwt_required()
def get_category(category_id):
    user_id = get_current_user_id()

    response, status = CategoryService.get_by_id(
        user_id,
        category_id
    )

    return jsonify(response), status


@categories_bp.route("/<int:category_id>", methods=["PUT", "PATCH"])
@jwt_required()
def update_category(category_id):
    user_id = get_current_user_id()
    data = request.get_json(silent=True) or {}

    response, status = CategoryService.update(
        user_id,
        category_id,
        data
    )

    return jsonify(response), status


@categories_bp.route("/<int:category_id>", methods=["DELETE"])
@jwt_required()
def delete_category(category_id):
    user_id = get_current_user_id()

    response, status = CategoryService.delete(
        user_id,
        category_id
    )

    return jsonify(response), status