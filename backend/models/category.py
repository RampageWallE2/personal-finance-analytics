from sqlalchemy.sql import func

from extensions import db


class Category(db.Model):
    __tablename__ = "categories"

    __table_args__ = (
        db.CheckConstraint(
            "category_type IN ('income', 'expense')",
            name="ck_categories_type"
        ),
        db.UniqueConstraint(
            "user_id",
            "name",
            "category_type",
            name="uq_categories_user_name_type"
        ),
        db.Index(
            "ix_categories_user_type",
            "user_id",
            "category_type"
        ),
    )

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    user_id = db.Column(
        db.Integer,
        db.ForeignKey(
            "users.id",
            ondelete="CASCADE"
        ),
        nullable=False,
        index=True
    )

    name = db.Column(
        db.String(80),
        nullable=False
    )

    category_type = db.Column(
        db.String(10),
        nullable=False
    )

    created_at = db.Column(
        db.DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )

    updated_at = db.Column(
        db.DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False
    )

    user = db.relationship(
        "User",
        back_populates="categories"
    )

    transactions = db.relationship(
        "Transaction",
        back_populates="category",
        passive_deletes=True
    )

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "name": self.name,
            "type": self.category_type,
            "created_at": (
                self.created_at.isoformat()
                if self.created_at else None
            ),
            "updated_at": (
                self.updated_at.isoformat()
                if self.updated_at else None
            )
        }