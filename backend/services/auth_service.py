from flask_jwt_extended import create_access_token
from services.category_service import CategoryService
from extensions import db, bcrypt
from models.user import User
from sqlalchemy.exc import IntegrityError, SQLAlchemyError 

class AuthService:

    @staticmethod
    def register(data):

        username = data.get("username")
        email = data.get("email")
        password = data.get("password")

        if not username or not email or not password:

            return {
                "message": "Todos los campos son obligatorios"
            }, 400

        existing_user = User.query.filter_by(email=email).first()

        if existing_user:

            return {
                "message": "El correo ya está registrado"
            }, 409

        hashed_password = bcrypt.generate_password_hash(password).decode("utf-8")

        user = User(
            username=username,
            email=email,
            password=hashed_password
        )


        try:
            db.session.add(user)
            db.session.flush()

            categories = (
                CategoryService.create_default_categories(
                    user_id=user.id
                )
            )

            db.session.commit()

        except IntegrityError:
            db.session.rollback()

            return {
                "message": "El usuario ya existe"
            }, 409

        except SQLAlchemyError:
            db.session.rollback()

            return {
                "message": "No se pudo registrar el usuario"
            }, 500
        
        return {
            "message": "Usuario registrado correctamente",
            "user": user.to_dict()
        }, 201

    @staticmethod
    def login(data):

        email = data.get("email")
        password = data.get("password")

        if not email or not password:

            return {
                "message": "Todos los campos son obligatorios"
            }, 401

        email = email.strip().lower()

        user = User.query.filter_by(email=email).first()

        if user is None: 
            return {
                "message": "Credenciales incorrectas"
            }, 401

        password_is_valid = bcrypt.check_password_hash(
            user.password,
            password
        )

        if not password_is_valid:
            return {
                "message": "Credenciales incorrectas"
            }, 401

        access_token = create_access_token(
            identity=str(user.id)
        )

        return {
            "message": "Inicio de sesión correcto",
            "access_token": access_token,
            "user": user.to_dict()
        }, 200