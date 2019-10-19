from time import time

from flask import make_response, render_template
from flask_restful import Resource

from models.confirmation import ConfirmationModel
from models.user import UserModel
from schemas.confirmation import ConfirmationSchema

NOT_FOUND = "Confirmation reference not found"
EXPIRED = "The link has expired"
ALREADY_CONFIRMED = "Registration has already been confirmed"


class Confirmation(Resource):
    @classmethod
    def get(cls, confirmation_id: str):
        confirmation = ConfirmationModel.find_by_id(confirmation_id)
        if not confirmation:        # does not exist
            return {"message": NOT_FOUND}, 404

        if confirmation.expired:    # has expired
            return {"message": EXPIRED}

        if confirmation.confirmed:  # is confirmed
            return {"message": ALREADY_CONFIRMED}

        confirmation.confirmed = True
        confirmation.save_to_db()

        headers = {"Content-Type": "text/html"}
        return make_response(
            render_template("confirmation_page.html", email=confirmation.user.username), 200, headers
        )


confirmation_schema = ConfirmationSchema()


class ConfirmationByUser(Resource):
    @classmethod
    def get(cls, user_id: int):
        """returns confirmations of a given user. Use for testing"""
        user = UserModel.find_by_id(user_id)
        if user:
            return {
                "current_time": int(time()),
                "confirmation": [
                    confirmation_schema.dump(each)
                    for each in user.confirmation.order_by(ConfirmationModel.expire_at)
                ]
            }

    @classmethod
    def post(cls):
        """post to resend the confirmation email"""
        pass