from flask import request, jsonify, make_response, render_template
from flask_restful import Resource, reqparse
from marshmallow import ValidationError, EXCLUDE
from werkzeug.security import safe_str_cmp
from flask_jwt_extended import (
    create_access_token,
    create_refresh_token,
    jwt_refresh_token_required,
    get_jwt_identity,
    jwt_required,
    get_raw_jwt,
)

from schemas.user import UserSchema
from models.user import UserModel
from blacklist import BLACKLIST

ALREADY_EXISTS = "A user with that username already exists."
ERROR_CREATING = "An error occurred while creating the store."
USER_CREATED = "User created successfully."
USER_NOT_FOUND = "User not found"
USER_DELETED = "User deleted."
USER_LOGGED_OUT = "User <id={}> successfully logged out."
INVALID_CREDENTIALS = "Invalid Credentials!"
USER_CONFIRMED_ERROR = "You have not confirmed registration. Please check your email <{}>"
USER_ACTIVATED = "User {} has been activated."

user_schema = UserSchema(unknown=EXCLUDE)


class UserRegister(Resource):
    @classmethod
    def post(cls):
        json = request.get_json()
        user = user_schema.load(json)

        if UserModel.find_by_username(user.username):
            return {"message": ALREADY_EXISTS}, 400

        user.save_to_db()

        return {"message": USER_CREATED}, 201


class User(Resource):
    """
    This resource can be useful when testing our Flask app. We may not want to expose it to public users, but for the
    sake of demonstration in this course, it can be useful when we are manipulating data regarding the users.
    """

    @classmethod
    def get(cls, user_id: int):
        user = UserModel.find_by_id(user_id)
        if not user:
            return {"message": USER_NOT_FOUND}, 404
        return user_schema.dump(user), 200

    @classmethod
    def delete(cls, user_id: int):
        user = UserModel.find_by_id(user_id)
        if not user:
            return {"message": USER_NOT_FOUND}, 404
        user.delete_from_db()
        return {"message": USER_DELETED}, 200


class UserLogin(Resource):
    @classmethod
    def post(cls):
        json = request.get_json()
        data = user_schema.load(json)

        user = UserModel.find_by_username(data.username)

        # this is what the `authenticate()` function did in security.py
        if user and safe_str_cmp(user.password, data.password):
            if user.activated:
                # identity= is what the identity() function did in security.py—now stored in the JWT
                access_token = create_access_token(identity=user.id, fresh=True)
                refresh_token = create_refresh_token(user.id)
                return {"access_token": access_token, "refresh_token": refresh_token}, 200
            return {"message": USER_CONFIRMED_ERROR.format(user.username)}, 400

        return {"message": INVALID_CREDENTIALS}, 401


class UserLogout(Resource):
    @classmethod
    @jwt_required
    def post(cls):
        jti = get_raw_jwt()["jti"]  # jti is "JWT ID", a unique identifier for a JWT.
        user_id = get_jwt_identity()
        BLACKLIST.add(jti)
        return {"message": USER_LOGGED_OUT.format(user_id)}, 200


class TokenRefresh(Resource):
    @classmethod
    @jwt_refresh_token_required
    def post(cls):
        current_user = get_jwt_identity()
        new_token = create_access_token(identity=current_user, fresh=False)
        return {"access_token": new_token}, 200


class UserConfirm(Resource):
    @classmethod
    def get(cls, user_id: int):
        user = UserModel.find_by_id(user_id)
        if not user:
            return {"message": USER_NOT_FOUND}

        user.activated = True
        user.save_to_db()
        headers = {"Content-Type": "text/html"}
        return make_response(render_template("confirmation_page.html", email=user.username), 200, headers)

