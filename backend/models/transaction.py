from sqlalchemy.sql import func

from extensions import db


class Transaction(db.Model):
    __tablename__ = "transactions"

    __table_args__ = (
        db.CheckConstraint(
            "amount > 0",
            name="ck_transactions_amount_positive"
        ),
        db.CheckConstraint(
            "transaction_type IN ('income', 'expense')",
            name="ck_transactions_type"
        ),
    )

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    amount = db.Column(
        db.Numeric(12, 2),
        nullable=False
    )

    transaction_type = db.Column(
        db.String(10),
        nullable=False
    )

    category = db.Column(
        db.String(80),
        nullable=False,
        index=True
    )

    description = db.Column(
        db.String(255),
        nullable=True
    )

    merchant = db.Column(
        db.String(120),
        nullable=True
    )

    payment_method = db.Column(
        db.String(30),
        nullable=True
    )

    transaction_date = db.Column(
        db.Date,
        nullable=False,
        index=True
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
        back_populates="transactions"
    )

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "amount": format(self.amount, ".2f"),
            "type": self.transaction_type,
            "category": self.category,
            "description": self.description,
            "merchant": self.merchant,
            "payment_method": self.payment_method,
            "transaction_date": self.transaction_date.isoformat(),
            "created_at": (
                self.created_at.isoformat()
                if self.created_at else None
            ),
            "updated_at": (
                self.updated_at.isoformat()
                if self.updated_at else None
            )
        }