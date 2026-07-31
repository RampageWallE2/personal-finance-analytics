from datetime import date
from decimal import Decimal, InvalidOperation

from sqlalchemy.exc import SQLAlchemyError

from extensions import db
from models.transaction import Transaction


class TransactionService:

    VALID_TYPES = {"income", "expense"}

    @staticmethod
    def _parse_amount(value):
        try:
            amount = Decimal(str(value))
        except (InvalidOperation, TypeError, ValueError):
            raise ValueError("El monto debe ser un número válido")

        if amount <= 0:
            raise ValueError("El monto debe ser mayor que cero")

        return amount.quantize(Decimal("0.01"))

    @staticmethod
    def _parse_date(value):
        if not value:
            raise ValueError("La fecha de la transacción es obligatoria")

        try:
            return date.fromisoformat(value)
        except (TypeError, ValueError):
            raise ValueError(
                "La fecha debe utilizar el formato YYYY-MM-DD"
            )

    @staticmethod
    def _find_owned_transaction(user_id, transaction_id):
        return Transaction.query.filter_by(
            id=transaction_id,
            user_id=user_id
        ).first()

    @staticmethod
    def create(user_id, data):
        required_fields = [
            "amount",
            "type",
            "category",
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

        transaction_type = str(
            data.get("type")
        ).strip().lower()

        if transaction_type not in TransactionService.VALID_TYPES:
            return {
                "message": (
                    "El tipo debe ser 'income' o 'expense'"
                )
            }, 400

        category = str(
            data.get("category")
        ).strip().lower()

        if not category:
            return {
                "message": "La categoría es obligatoria"
            }, 400

        try:
            amount = TransactionService._parse_amount(
                data.get("amount")
            )

            transaction_date = TransactionService._parse_date(
                data.get("transaction_date")
            )
        except ValueError as error:
            return {
                "message": str(error)
            }, 400

        transaction = Transaction(
            user_id=user_id,
            amount=amount,
            transaction_type=transaction_type,
            category=category,
            description=(
                str(data.get("description")).strip()
                if data.get("description") else None
            ),
            merchant=(
                str(data.get("merchant")).strip()
                if data.get("merchant") else None
            ),
            payment_method=(
                str(data.get("payment_method")).strip().lower()
                if data.get("payment_method") else None
            ),
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
        query = Transaction.query.filter_by(
            user_id=user_id
        )

        transaction_type = filters.get("type")
        category = filters.get("category")
        start_date = filters.get("start_date")
        end_date = filters.get("end_date")

        if transaction_type:
            transaction_type = transaction_type.strip().lower()

            if transaction_type not in TransactionService.VALID_TYPES:
                return {
                    "message": (
                        "El tipo debe ser 'income' o 'expense'"
                    )
                }, 400

            query = query.filter(
                Transaction.transaction_type == transaction_type
            )

        if category:
            query = query.filter(
                Transaction.category == category.strip().lower()
            )

        try:
            if start_date:
                query = query.filter(
                    Transaction.transaction_date >=
                    date.fromisoformat(start_date)
                )

            if end_date:
                query = query.filter(
                    Transaction.transaction_date <=
                    date.fromisoformat(end_date)
                )
        except ValueError:
            return {
                "message": (
                    "Las fechas deben utilizar el formato YYYY-MM-DD"
                )
            }, 400

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
        transaction = TransactionService._find_owned_transaction(
            user_id,
            transaction_id
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
        transaction = TransactionService._find_owned_transaction(
            user_id,
            transaction_id
        )

        if transaction is None:
            return {
                "message": "Transacción no encontrada"
            }, 404

        allowed_fields = {
            "amount",
            "type",
            "category",
            "description",
            "merchant",
            "payment_method",
            "transaction_date"
        }

        if not any(field in data for field in allowed_fields):
            return {
                "message": "No se enviaron campos para actualizar"
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
        except ValueError as error:
            return {
                "message": str(error)
            }, 400

        if "type" in data:
            transaction_type = str(data.get("type")).strip().lower()

            if transaction_type not in TransactionService.VALID_TYPES:
                return {
                    "message": (
                        "El tipo debe ser 'income' o 'expense'"
                    )
                }, 400

            transaction.transaction_type = transaction_type

        if "category" in data:
            category = str(
                data.get("category")
            ).strip().lower()

            if not category:
                return {
                    "message": "La categoría no puede estar vacía"
                }, 400

            transaction.category = category

        if "description" in data:
            transaction.description = (
                str(data.get("description")).strip()
                if data.get("description") else None
            )

        if "merchant" in data:
            transaction.merchant = (
                str(data.get("merchant")).strip()
                if data.get("merchant") else None
            )

        if "payment_method" in data:
            transaction.payment_method = (
                str(data.get("payment_method")).strip().lower()
                if data.get("payment_method") else None
            )

        try:
            db.session.commit()
        except SQLAlchemyError:
            db.session.rollback()

            return {
                "message": "No se pudo actualizar la transacción"
            }, 500

        return {
            "message": "Transacción actualizada correctamente",
            "transaction": transaction.to_dict()
        }, 200

    @staticmethod
    def delete(user_id, transaction_id):
        transaction = TransactionService._find_owned_transaction(
            user_id,
            transaction_id
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