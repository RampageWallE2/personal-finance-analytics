from flask import Blueprint, jsonify, request
from flask_jwt_extended import (
    get_jwt_identity,
    jwt_required
)

from services.transaction_service import TransactionService


transactions_bp = Blueprint(
    "transactions",
    __name__,
    url_prefix="/transactions"
)


def get_current_user_id():
    return int(get_jwt_identity())


@transactions_bp.route("/", methods=["POST"], strict_slashes=False)
@jwt_required()
def create_transaction():
    user_id = get_current_user_id()
    data = request.get_json(silent=True) or {}

    response, status = TransactionService.create(
        user_id,
        data
    )

    return jsonify(response), status


@transactions_bp.route("/", methods=["GET"], strict_slashes=False)
@jwt_required()
def get_transactions():
    user_id = get_current_user_id()

    filters = {
        "type": request.args.get("type"),
        "category": request.args.get("category"),
        "start_date": request.args.get("start_date"),
        "end_date": request.args.get("end_date")
    }

    response, status = TransactionService.get_all(
        user_id,
        filters
    )

    return jsonify(response), status


@transactions_bp.route("/<int:transaction_id>", methods=["GET"])
@jwt_required()
def get_transaction(transaction_id):
    user_id = get_current_user_id()

    response, status = TransactionService.get_by_id(
        user_id,
        transaction_id
    )

    return jsonify(response), status


@transactions_bp.route("/<int:transaction_id>", methods=["PUT", "PATCH"])
@jwt_required()
def update_transaction(transaction_id):
    user_id = get_current_user_id()
    data = request.get_json(silent=True) or {}

    response, status = TransactionService.update(
        user_id,
        transaction_id,
        data
    )

    return jsonify(response), status


@transactions_bp.route("/<int:transaction_id>", methods=["DELETE"])
@jwt_required()
def delete_transaction(transaction_id):
    user_id = get_current_user_id()

    response, status = TransactionService.delete(
        user_id,
        transaction_id
    )

    return jsonify(response), status