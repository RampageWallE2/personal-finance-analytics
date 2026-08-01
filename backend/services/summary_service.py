from datetime import date
from decimal import Decimal

from sqlalchemy import case, func
from sqlalchemy.exc import SQLAlchemyError

from extensions import db
from models.category import Category
from models.transaction import Transaction


class SummaryService:

    @staticmethod
    def _parse_optional_date(value, field_name):
        if value in (None, ""):
            return None

        try:
            return date.fromisoformat(str(value))
        except (TypeError, ValueError):
            raise ValueError(
                f"{field_name} debe utilizar el formato YYYY-MM-DD"
            )

    @staticmethod
    def _apply_date_filters(
        query,
        start_date=None,
        end_date=None
    ):
        if start_date:
            query = query.filter(
                Transaction.transaction_date >= start_date
            )

        if end_date:
            query = query.filter(
                Transaction.transaction_date <= end_date
            )

        return query

    @staticmethod
    def _format_amount(value):
        amount = Decimal(value or 0)

        return format(
            amount.quantize(Decimal("0.01")),
            ".2f"
        )

    @staticmethod
    def get_summary(user_id, filters=None):
        filters = filters or {}

        try:
            start_date = SummaryService._parse_optional_date(
                filters.get("start_date"),
                "La fecha inicial"
            )

            end_date = SummaryService._parse_optional_date(
                filters.get("end_date"),
                "La fecha final"
            )

        except ValueError as error:
            return {
                "message": str(error)
            }, 400

        if (
            start_date is not None
            and end_date is not None
            and start_date > end_date
        ):
            return {
                "message": (
                    "La fecha inicial no puede ser "
                    "posterior a la fecha final"
                )
            }, 400

        try:
            totals_query = (
                db.session.query(
                    func.coalesce(
                        func.sum(
                            case(
                                (
                                    Category.category_type == "income",
                                    Transaction.amount
                                ),
                                else_=0
                            )
                        ),
                        0
                    ).label("total_income"),

                    func.coalesce(
                        func.sum(
                            case(
                                (
                                    Category.category_type == "expense",
                                    Transaction.amount
                                ),
                                else_=0
                            )
                        ),
                        0
                    ).label("total_expense"),

                    func.count(
                        Transaction.id
                    ).label("transaction_count")
                )
                .join(
                    Category,
                    Transaction.category_id == Category.id
                )
                .filter(
                    Transaction.user_id == user_id,
                    Category.user_id == user_id
                )
            )

            totals_query = SummaryService._apply_date_filters(
                totals_query,
                start_date,
                end_date
            )

            totals = totals_query.one()

            total_income = Decimal(
                totals.total_income or 0
            )

            total_expense = Decimal(
                totals.total_expense or 0
            )

            balance = total_income - total_expense

            categories_query = (
                db.session.query(
                    Category.id.label("category_id"),
                    Category.name.label("category_name"),
                    Category.category_type.label("category_type"),
                    func.coalesce(
                        func.sum(Transaction.amount),
                        0
                    ).label("total"),
                    func.count(
                        Transaction.id
                    ).label("transaction_count")
                )
                .join(
                    Transaction,
                    Transaction.category_id == Category.id
                )
                .filter(
                    Category.user_id == user_id,
                    Transaction.user_id == user_id
                )
            )

            categories_query = (
                SummaryService._apply_date_filters(
                    categories_query,
                    start_date,
                    end_date
                )
            )

            category_rows = (
                categories_query
                .group_by(
                    Category.id,
                    Category.name,
                    Category.category_type
                )
                .order_by(
                    Category.category_type.asc(),
                    func.sum(Transaction.amount).desc(),
                    Category.name.asc()
                )
                .all()
            )

        except SQLAlchemyError:
            db.session.rollback()

            return {
                "message": (
                    "No se pudo generar el resumen financiero"
                )
            }, 500

        income_by_category = []
        expenses_by_category = []

        for row in category_rows:
            category_data = {
                "category_id": row.category_id,
                "name": row.category_name,
                "total": SummaryService._format_amount(
                    row.total
                ),
                "transaction_count": row.transaction_count
            }

            if row.category_type == "income":
                income_by_category.append(category_data)
            else:
                expenses_by_category.append(category_data)

        return {
            "period": {
                "start_date": (
                    start_date.isoformat()
                    if start_date else None
                ),
                "end_date": (
                    end_date.isoformat()
                    if end_date else None
                )
            },
            "total_income": SummaryService._format_amount(
                total_income
            ),
            "total_expense": SummaryService._format_amount(
                total_expense
            ),
            "balance": SummaryService._format_amount(
                balance
            ),
            "transaction_count": totals.transaction_count,
            "income_by_category": income_by_category,
            "expenses_by_category": expenses_by_category
        }, 200