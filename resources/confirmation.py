import traceback
from time import time

from flask import make_response, render_template
from flask_restful import Resource

from models.confirmation import ConfirmationModel
from models.user import UserModel
from resources.user import USER_NOT_FOUND
from schemas.confirmation import ConfirmationSchema

NOT_FOUND = "Confirmation reference not found"
EXPIRED = "The link has expired"
ALREADY_CONFIRMED = "Registration has already been confirmed"
RESEND_SUCCESSFUL = "E-mail confirmation successfully resent."
RESEND_FAIL = "There was a problem resending the email. Please try again."


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
    def post(cls, user_id: int):
        """post to resend the confirmation email"""
        user = UserModel.find_by_id(user_id)
        if not user:
            return {"message": USER_NOT_FOUND}, 404
        try:
            confirmation = user.most_recent_confirmation
            if confirmation:    # confirmation exists
                if confirmation.confirmed:  # already confirmed
                    return {"message": ALREADY_CONFIRMED}
                confirmation.force_to_expire()

            new_confirmation = ConfirmationModel(user_id)
            new_confirmation.save_to_db()

            # user.send_confirmation_email()

            return {"message": RESEND_SUCCESSFUL}
        except:
            traceback.print_exc()
            return {"message": RESEND_FAIL}