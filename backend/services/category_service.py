from sqlalchemy import func
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

from extensions import db
from models.category import Category
from models.transaction import Transaction


class CategoryService:

    VALID_TYPES = {"income", "expense"}

    @staticmethod
    def _normalize_name(value):
        if not isinstance(value, str):
            raise ValueError(
                "El nombre de la categoría debe ser texto"
            )

        # Elimina espacios iniciales, finales y espacios repetidos.
        name = " ".join(value.split())

        if not name:
            raise ValueError(
                "El nombre de la categoría es obligatorio"
            )

        if len(name) > 80:
            raise ValueError(
                "El nombre no puede superar los 80 caracteres"
            )

        return name

    @staticmethod
    def _normalize_type(value):
        if not isinstance(value, str):
            raise ValueError(
                "El tipo de categoría es obligatorio"
            )

        category_type = value.strip().lower()

        if category_type not in CategoryService.VALID_TYPES:
            raise ValueError(
                "El tipo debe ser 'income' o 'expense'"
            )

        return category_type

    @staticmethod
    def _find_owned_category(user_id, category_id):
        return Category.query.filter_by(
            id=category_id,
            user_id=user_id
        ).first()

    @staticmethod
    def _find_duplicate(
        user_id,
        name,
        category_type,
        excluded_category_id=None
    ):
        query = Category.query.filter(
            Category.user_id == user_id,
            Category.category_type == category_type,
            func.lower(Category.name) == name.lower()
        )

        if excluded_category_id is not None:
            query = query.filter(
                Category.id != excluded_category_id
            )

        return query.first()

    @staticmethod
    def create(user_id, data):
        required_fields = [
            "name",
            "type"
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
            name = CategoryService._normalize_name(
                data.get("name")
            )

            category_type = CategoryService._normalize_type(
                data.get("type")
            )

        except ValueError as error:
            return {
                "message": str(error)
            }, 400

        duplicate = CategoryService._find_duplicate(
            user_id=user_id,
            name=name,
            category_type=category_type
        )

        if duplicate is not None:
            return {
                "message": (
                    "Ya existe una categoría con ese nombre y tipo"
                )
            }, 409

        category = Category(
            user_id=user_id,
            name=name,
            category_type=category_type
        )

        try:
            db.session.add(category)
            db.session.commit()

        except IntegrityError:
            db.session.rollback()

            return {
                "message": (
                    "Ya existe una categoría con ese nombre y tipo"
                )
            }, 409

        except SQLAlchemyError:
            db.session.rollback()

            return {
                "message": "No se pudo crear la categoría"
            }, 500

        return {
            "message": "Categoría creada correctamente",
            "category": category.to_dict()
        }, 201

    @staticmethod
    def get_all(user_id, filters=None):
        filters = filters or {}

        query = Category.query.filter_by(
            user_id=user_id
        )

        category_type = filters.get("type")

        if category_type:
            try:
                category_type = CategoryService._normalize_type(
                    category_type
                )

            except ValueError as error:
                return {
                    "message": str(error)
                }, 400

            query = query.filter(
                Category.category_type == category_type
            )

        categories = query.order_by(
            Category.category_type.asc(),
            Category.name.asc()
        ).all()

        return {
            "count": len(categories),
            "categories": [
                category.to_dict()
                for category in categories
            ]
        }, 200

    @staticmethod
    def get_by_id(user_id, category_id):
        category = CategoryService._find_owned_category(
            user_id,
            category_id
        )

        if category is None:
            return {
                "message": "Categoría no encontrada"
            }, 404

        return {
            "category": category.to_dict()
        }, 200

    @staticmethod
    def update(user_id, category_id, data):
        category = CategoryService._find_owned_category(
            user_id,
            category_id
        )

        if category is None:
            return {
                "message": "Categoría no encontrada"
            }, 404

        allowed_fields = {
            "name",
            "type"
        }

        if not any(
            field in data
            for field in allowed_fields
        ):
            return {
                "message": (
                    "No se enviaron campos para actualizar"
                )
            }, 400

        new_name = category.name
        new_type = category.category_type

        try:
            if "name" in data:
                new_name = CategoryService._normalize_name(
                    data.get("name")
                )

            if "type" in data:
                new_type = CategoryService._normalize_type(
                    data.get("type")
                )

        except ValueError as error:
            return {
                "message": str(error)
            }, 400

        # El tipo de la categoría determina si sus transacciones
        # son ingresos o gastos. No debe cambiarse si ya está en uso.
        if new_type != category.category_type:
            has_transactions = Transaction.query.filter_by(
                category_id=category.id
            ).first()

            if has_transactions is not None:
                return {
                    "message": (
                        "No se puede cambiar el tipo de una "
                        "categoría que tiene transacciones"
                    )
                }, 409

        duplicate = CategoryService._find_duplicate(
            user_id=user_id,
            name=new_name,
            category_type=new_type,
            excluded_category_id=category.id
        )

        if duplicate is not None:
            return {
                "message": (
                    "Ya existe una categoría con ese nombre y tipo"
                )
            }, 409

        category.name = new_name
        category.category_type = new_type

        try:
            db.session.commit()

        except IntegrityError:
            db.session.rollback()

            return {
                "message": (
                    "Ya existe una categoría con ese nombre y tipo"
                )
            }, 409

        except SQLAlchemyError:
            db.session.rollback()

            return {
                "message": "No se pudo actualizar la categoría"
            }, 500

        return {
            "message": "Categoría actualizada correctamente",
            "category": category.to_dict()
        }, 200

    @staticmethod
    def delete(user_id, category_id):
        category = CategoryService._find_owned_category(
            user_id,
            category_id
        )

        if category is None:
            return {
                "message": "Categoría no encontrada"
            }, 404

        has_transactions = Transaction.query.filter_by(
            category_id=category.id
        ).first()

        if has_transactions is not None:
            return {
                "message": (
                    "No se puede eliminar una categoría "
                    "que tiene transacciones"
                )
            }, 409

        try:
            db.session.delete(category)
            db.session.commit()

        except IntegrityError:
            db.session.rollback()

            return {
                "message": (
                    "La categoría está siendo utilizada "
                    "y no puede eliminarse"
                )
            }, 409

        except SQLAlchemyError:
            db.session.rollback()

            return {
                "message": "No se pudo eliminar la categoría"
            }, 500

        return {
            "message": "Categoría eliminada correctamente"
        }, 200