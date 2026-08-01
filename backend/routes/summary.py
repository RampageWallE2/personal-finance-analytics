from flask import Blueprint, jsonify, request
from flask_jwt_extended import (
    get_jwt_identity,
    jwt_required
)

from services.summary_service import SummaryService


summary_bp = Blueprint("summary", __name__, url_prefix="/summary")


def get_current_user_id():
    return int(get_jwt_identity())


@summary_bp.route("/", methods=["GET"], strict_slashes=False)
@jwt_required()
def get_financial_summary():
    user_id = get_current_user_id()

    filters = {
        "start_date": request.args.get("start_date"),
        "end_date": request.args.get("end_date")
    }

    response, status = SummaryService.get_summary(
        user_id,
        filters
    )

    return jsonify(response), status