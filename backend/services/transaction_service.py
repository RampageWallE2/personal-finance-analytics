from datetime import date
from decimal import Decimal, InvalidOperation

from sqlalchemy import func
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import joinedload

from extensions import db
from models.category import Category
from models.transaction import Transaction


class TransactionService:

    VALID_TYPES = {"income", "expense"}

    @staticmethod
    def _parse_amount(value):
        try:
            amount = Decimal(str(value))
        except (InvalidOperation, TypeError, ValueError):
            raise ValueError(
                "El monto debe ser un número válido"
            )

        if amount <= 0:
            raise ValueError(
                "El monto debe ser mayor que cero"
            )

        return amount.quantize(Decimal("0.01"))

    @staticmethod
    def _parse_date(value):
        if not value:
            raise ValueError(
                "La fecha de la transacción es obligatoria"
            )

        try:
            return date.fromisoformat(str(value))
        except (TypeError, ValueError):
            raise ValueError(
                "La fecha debe utilizar el formato YYYY-MM-DD"
            )

    @staticmethod
    def _parse_category_id(value):
        if value in (None, ""):
            raise ValueError(
                "La categoría es obligatoria"
            )

        if isinstance(value, bool):
            raise ValueError(
                "El identificador de categoría no es válido"
            )

        try:
            category_id = int(value)
        except (TypeError, ValueError):
            raise ValueError(
                "El identificador de categoría no es válido"
            )

        if category_id <= 0:
            raise ValueError(
                "El identificador de categoría no es válido"
            )

        return category_id

    @staticmethod
    def _parse_optional_text(
        value,
        field_name,
        max_length,
        lowercase=False
    ):
        if value is None:
            return None

        text = str(value).strip()

        if not text:
            return None

        if len(text) > max_length:
            raise ValueError(
                f"{field_name} no puede superar "
                f"los {max_length} caracteres"
            )

        if lowercase:
            text = text.lower()

        return text

    @staticmethod
    def _find_owned_category(user_id, category_id):
        return Category.query.filter_by(
            id=category_id,
            user_id=user_id
        ).first()

    @staticmethod
    def _find_owned_transaction(user_id, transaction_id):
        return (
            Transaction.query
            .options(
                joinedload(Transaction.category)
            )
            .filter_by(
                id=transaction_id,
                user_id=user_id
            )
            .first()
        )

    @staticmethod
    def create(user_id, data):
        required_fields = [
            "amount",
            "category_id",
            "transaction_date"
        ]

        missing_fields = [
            field
            for field in required_fields
            if data.get(field) in (None, "")
        ]

        if missing_fields:
            return {
                "message": "Faltan campos obligatorios",
                "fields": missing_fields
            }, 400

        try:
            amount = TransactionService._parse_amount(
                data.get("amount")
            )

            transaction_date = TransactionService._parse_date(
                data.get("transaction_date")
            )

            category_id = (
                TransactionService._parse_category_id(
                    data.get("category_id")
                )
            )

            description = (
                TransactionService._parse_optional_text(
                    data.get("description"),
                    "La descripción",
                    255
                )
            )

            merchant = (
                TransactionService._parse_optional_text(
                    data.get("merchant"),
                    "El comercio",
                    120
                )
            )

            payment_method = (
                TransactionService._parse_optional_text(
                    data.get("payment_method"),
                    "El método de pago",
                    30,
                    lowercase=True
                )
            )

        except ValueError as error:
            return {
                "message": str(error)
            }, 400

        category = TransactionService._find_owned_category(
            user_id,
            category_id
        )

        if category is None:
            return {
                "message": "Categoría no encontrada"
            }, 404

        transaction = Transaction(
            user_id=user_id,
            category_id=category.id,
            amount=amount,
            description=description,
            merchant=merchant,
            payment_method=payment_method,
            transaction_date=transaction_date
        )

        try:
            db.session.add(transaction)
            db.session.commit()

        except SQLAlchemyError:
            db.session.rollback()

            return {
                "message": "No se pudo crear la transacción"
            }, 500

        return {
            "message": "Transacción creada correctamente",
            "transaction": transaction.to_dict()
        }, 201

    @staticmethod
    def get_all(user_id, filters):
        query = (
            Transaction.query
            .join(
                Category,
                Transaction.category_id == Category.id
            )
            .options(
                joinedload(Transaction.category)
            )
            .filter(
                Transaction.user_id == user_id,
                Category.user_id == user_id
            )
        )

        transaction_type = filters.get("type")
        category_id = filters.get("category_id")
        category_name = filters.get("category")
        start_date = filters.get("start_date")
        end_date = filters.get("end_date")

        if transaction_type:
            transaction_type = (
                transaction_type
                .strip()
                .lower()
            )

            if transaction_type not in TransactionService.VALID_TYPES:
                return {
                    "message": (
                        "El tipo debe ser 'income' o 'expense'"
                    )
                }, 400

            query = query.filter(
                Category.category_type == transaction_type
            )

        if category_id:
            try:
                parsed_category_id = (
                    TransactionService._parse_category_id(
                        category_id
                    )
                )
            except ValueError as error:
                return {
                    "message": str(error)
                }, 400

            query = query.filter(
                Transaction.category_id == parsed_category_id
            )

        # Se conserva temporalmente para que funcione el filtro
        # actual de tu ruta: ?category=alimentación
        if category_name:
            normalized_category_name = (
                str(category_name)
                .strip()
                .lower()
            )

            if normalized_category_name:
                query = query.filter(
                    func.lower(Category.name) ==
                    normalized_category_name
                )

        try:
            parsed_start_date = (
                date.fromisoformat(start_date)
                if start_date else None
            )

            parsed_end_date = (
                date.fromisoformat(end_date)
                if end_date else None
            )

        except (TypeError, ValueError):
            return {
                "message": (
                    "Las fechas deben utilizar "
                    "el formato YYYY-MM-DD"
                )
            }, 400

        if (
            parsed_start_date
            and parsed_end_date
            and parsed_start_date > parsed_end_date
        ):
            return {
                "message": (
                    "La fecha inicial no puede ser "
                    "posterior a la fecha final"
                )
            }, 400

        if parsed_start_date:
            query = query.filter(
                Transaction.transaction_date >=
                parsed_start_date
            )

        if parsed_end_date:
            query = query.filter(
                Transaction.transaction_date <=
                parsed_end_date
            )

        transactions = query.order_by(
            Transaction.transaction_date.desc(),
            Transaction.id.desc()
        ).all()

        return {
            "count": len(transactions),
            "transactions": [
                transaction.to_dict()
                for transaction in transactions
            ]
        }, 200

    @staticmethod
    def get_by_id(user_id, transaction_id):
        transaction = (
            TransactionService._find_owned_transaction(
                user_id,
                transaction_id
            )
        )

        if transaction is None:
            return {
                "message": "Transacción no encontrada"
            }, 404

        return {
            "transaction": transaction.to_dict()
        }, 200

    @staticmethod
    def update(user_id, transaction_id, data):
        transaction = (
            TransactionService._find_owned_transaction(
                user_id,
                transaction_id
            )
        )

        if transaction is None:
            return {
                "message": "Transacción no encontrada"
            }, 404

        allowed_fields = {
            "amount",
            "category_id",
            "description",
            "merchant",
            "payment_method",
            "transaction_date"
        }

        received_allowed_fields = (
            allowed_fields.intersection(data.keys())
        )

        if not received_allowed_fields:
            return {
                "message": (
                    "No se enviaron campos para actualizar"
                )
            }, 400

        try:
            if "amount" in data:
                transaction.amount = (
                    TransactionService._parse_amount(
                        data.get("amount")
                    )
                )

            if "transaction_date" in data:
                transaction.transaction_date = (
                    TransactionService._parse_date(
                        data.get("transaction_date")
                    )
                )

            if "category_id" in data:
                category_id = (
                    TransactionService._parse_category_id(
                        data.get("category_id")
                    )
                )

                category = (
                    TransactionService._find_owned_category(
                        user_id,
                        category_id
                    )
                )

                if category is None:
                    return {
                        "message": "Categoría no encontrada"
                    }, 404

                transaction.category_id = category.id
                transaction.category = category

            if "description" in data:
                transaction.description = (
                    TransactionService._parse_optional_text(
                        data.get("description"),
                        "La descripción",
                        255
                    )
                )

            if "merchant" in data:
                transaction.merchant = (
                    TransactionService._parse_optional_text(
                        data.get("merchant"),
                        "El comercio",
                        120
                    )
                )

            if "payment_method" in data:
                transaction.payment_method = (
                    TransactionService._parse_optional_text(
                        data.get("payment_method"),
                        "El método de pago",
                        30,
                        lowercase=True
                    )
                )

        except ValueError as error:
            return {
                "message": str(error)
            }, 400

        try:
            db.session.commit()

        except SQLAlchemyError:
            db.session.rollback()

            return {
                "message": (
                    "No se pudo actualizar la transacción"
                )
            }, 500

        return {
            "message": "Transacción actualizada correctamente",
            "transaction": transaction.to_dict()
        }, 200

    @staticmethod
    def delete(user_id, transaction_id):
        transaction = (
            TransactionService._find_owned_transaction(
                user_id,
                transaction_id
            )
        )

        if transaction is None:
            return {
                "message": "Transacción no encontrada"
            }, 404

        try:
            db.session.delete(transaction)
            db.session.commit()

        except SQLAlchemyError:
            db.session.rollback()

            return {
                "message": "No se pudo eliminar la transacción"
            }, 500

        return {
            "message": "Transacción eliminada correctamente"
        }, 200