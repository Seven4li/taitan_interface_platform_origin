#! -*- encoding=utf-8 -*-
import datetime

from flask import request, jsonify
from flask_login import UserMixin, login_user, logout_user, login_required

from backend.app import app, db, login_manager
from flask_restful import Resource
from backend.models.user_model import UserModel
from backend.utils.code_utils import CodeUtil
from backend.utils.exception_utils import REQ_IS_EMPTY_ERROR, REQ_TYPE_ERROR, REQ_KEY_ERROR, REQ_VALUE_ERROR
from backend.utils.make_response_utils import make_response


@login_manager.user_loader
def user_load(username):
    user = UserController.query_user(username)
    if user:
        curr_user = UserController()
        curr_user.username = username
        return curr_user


class UserController(UserMixin):
    @classmethod
    def add_user(cls, user_data):
        # 添加用户
        data = UserModel(**user_data)
        db.session.add(data)
        db.session.commit()
        db.session.close()

    @classmethod
    def query_user(cls, username):
        user = UserModel.query.filter_by(username=username, isDeleted=0).first()
        app.logger.info(f"当前登陆的用户为：{user}")
        if user:
            return user.to_dict()
        return {}

    @classmethod
    def get_nick_name(cls, username):
        user = UserModel.query.filter_by(username=username, isDeleted=0).first()
        nick_name = user.nick_name
        if nick_name:
            return nick_name
        else:
            return '未知用户'

    @classmethod
    def modify_user(cls, user_data):
        id = user_data.pop("id")  # 去除id这个值，并传递给变量id
        origin_data = UserModel.query.filter_by(id=id, isDeleted=0).first()
        if not origin_data:
            return None

        UserModel.query.filter_by(id=id, isDeleted=0).update(user_data)
        db.session.commit()
        db.session.close()

    @classmethod
    def delete_user(cls, id):
        # 根据id查询要删除的数据
        origin_data = UserModel.query.filter_by(id=id, isDeleted=0).first()
        if not origin_data:
            return None
        isDeleted = {
            "isDeleted": 1
        }
        UserModel.query.filter_by(id=id, isDeleted=0).update(isDeleted)
        db.session.commit()
        db.session.close()


class UserService(Resource):
    def get(self):
        pass

    def post(self):
        if not request.data:
            raise REQ_IS_EMPTY_ERROR()
        if not request.is_json:
            raise REQ_TYPE_ERROR()
        username = request.get_json().get("username")
        if not username:
            raise REQ_KEY_ERROR()
        if not isinstance(username, str):
            raise REQ_VALUE_ERROR()
        user_data = request.json  # 接受前端传入的数据，只能传json数据
        UserController.add_user(user_data)
        return make_response(status=CodeUtil.SUCCESS, data=user_data)

    @login_required
    def put(self):
        if not request.data:
            raise REQ_IS_EMPTY_ERROR()
        if not request.is_json:
            raise REQ_TYPE_ERROR()
        UserController.modify_user(request.get_json())
        return make_response(status=CodeUtil.SUCCESS, data=request.get_json())

    @login_required
    def delete(self):
        if not request.data:
            raise REQ_IS_EMPTY_ERROR()
        if not request.is_json:
            raise REQ_TYPE_ERROR()
        id = request.get_json().get("id")
        UserController.delete_user(id)
        return make_response(status=CodeUtil.SUCCESS, data={"id": id})


class LoginService(Resource):

    def post(self):
        if not request.data:
            raise REQ_IS_EMPTY_ERROR()
        if not request.is_json:
            raise REQ_TYPE_ERROR()
        app.logger.info(f"给登陆接口传入的请求数据为：{request.data}")

        username = request.get_json().get("username")  # 获取登陆的用户名
        password = request.get_json().get("password")  # 获取密码

        user = UserController.query_user(username)  # 对比用户名，并获取User对象
        if user and user['password'] == password:
            current_user = UserController()
            current_user.id = username
            login_user(current_user, remember=True)  # 进行登陆，记录session
            nick_name = UserController.get_nick_name(username)
            return make_response(status=CodeUtil.SUCCESS, data={"nick_name": nick_name})
        else:
            return make_response(status=CodeUtil.FAIL, data=None)


class LogoutService(Resource):

    def post(self):
        # 退出登陆
        result = logout_user()
        # 返回结果
        if result:
            return make_response(status=CodeUtil.SUCCESS)
        else:
            return make_response(status=CodeUtil.FAIL)
