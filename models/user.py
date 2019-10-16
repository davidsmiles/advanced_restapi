from typing import List

from db import db

from flask import request, url_for
from requests import Request, post

MAILGUN_DOMAIN = "sandbox5bf2b915fd6d4873b6ce4f765558f0a4.mailgun.org"
MAILGUN_API_KEY = "b58aa70ad5ce95e80536d44a8225a14b-9c988ee3-3e87ce1c"
FROM_TITLE = "Stores REST API"
FROM_EMAIL = "ugberodavid@gmail.com"


class UserModel(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), nullable=False, unique=True)
    password = db.Column(db.String(80), nullable=False)
    email = db.Column(db.String(80), nullable=False, unique=True)
    activated = db.Column(db.Boolean, default=False)

    @classmethod
    def find_by_username(cls, username: str) -> List["UserModel"]:
        return cls.query.filter_by(username=username).first()

    @classmethod
    def find_by_email(cls, email: str) -> List["UserModel"]:
        return cls.query.filter_by(email=email).first()

    @classmethod
    def find_by_id(cls, _id: int) -> List["UserModel"]:
        return cls.query.filter_by(id=_id).first()

    def send_confirmation_email(self) -> Request:
        link = request.url_root[0:-1] + url_for("userconfirm", user_id=self.id)

        return post(
            f"https://api.mailgun.net/v3/{MAILGUN_DOMAIN}/messages",
            auth=("api", MAILGUN_API_KEY),
            data={
                "from": f"{FROM_TITLE} {FROM_EMAIL}",
                "to": self.email,
                "subject": "Registration confirmation",
                "text": f"Please click the link to confirm your registration: {link}"
            },
        )

    def save_to_db(self) -> None:
        db.session.add(self)
        db.session.commit()

    def delete_from_db(self) -> None:
        db.session.delete(self)
        db.session.commit()
