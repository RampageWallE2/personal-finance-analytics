from extensions import db
from sqlalchemy.sql import func

class User(db.Model):

    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)

    username = db.Column(
        db.String(80), 
        nullable=False
    )

    email = db.Column(
        db.String(120), 
        unique=True, 
        nullable=False
    )

    password = db.Column(
        db.String(255), 
        nullable=False
    )

    created_at = db.Column(
        db.DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )

    transactions = db.relationship(
        "Transaction",
        back_populates="user",
        cascade="all, delete-orphan",
        passive_deletes=True
    )

    def to_dict(self):
                                                                                                                 
        return {
            "id": self.id,
            "username": self.username,
            "email": self.email,
            "created_at" : self.created_at
        }