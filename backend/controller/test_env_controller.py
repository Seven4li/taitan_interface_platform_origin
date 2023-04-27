# -*- encoding=utf-8 -*-
import datetime
from flask import request
from flask_login import login_required

from backend.app import app, db
from flask_restful import Resource
from backend.models.test_env_model import TestEnvModel
from backend.utils.code_utils import CodeUtil
from backend.utils.exception_utils import REQ_IS_EMPTY_ERROR, REQ_TYPE_ERROR, REQ_KEY_ERROR, REQ_VALUE_ERROR
from backend.utils.make_response_utils import make_response


class TestEnvController:
    def __init__(self):
        pass

    @classmethod
    def add_env(cls, env_data):
        env_data = {
            "env_name": env_data.get("env_name"),
            "description": env_data.get("description"),
        }

        # 添加环境
        data = TestEnvModel(**env_data)
        db.session.add(data)
        db.session.commit()
        db.session.close()

    @classmethod
    def query_env_by_id(cls, id):
        # 查询环境的详情
        env_detail_data = TestEnvModel.query.filter_by(id=id, isDeleted=0).first()
        app.logger.info(f"查询环境的环境id：{id}的详情数据为：{env_detail_data}")
        if env_detail_data is None:
            return []
        app.logger.info(f"查询环境的环境id：{id}的详情数据转化为json后：{env_detail_data.to_dict()}")
        return env_detail_data.to_dict()

    @classmethod
    def query_env_by_name(cls, env_name):
        # 根据环境的名称，搜索环境
        env_search_data = TestEnvModel.query.filter(
            TestEnvModel.env_name.like(f'%{env_name}%'),
            TestEnvModel.isDeleted == 0).all()  # []
        app.logger.info(f"根据环境名称 [{env_name}] 搜索出来的数据有：{env_search_data}")

        response_list = []
        for env_data in env_search_data:
            env_dictdata = env_data.to_dict()  # 把model中的数据转化成dict
            env_dictdata.update({"create_time": str(env_dictdata.get("create_time"))})  # 修改创建时间对象为字符串对象
            if env_dictdata.get("update_time"):
                env_dictdata.update({"update_time": str(env_dictdata.get("update_time"))})
            response_list.append(env_dictdata)
        app.logger.info(f"根据环境名称 [{env_name}] 搜索出来的数据并转化为json后：{response_list}")
        return response_list

    @classmethod
    def query_list(cls, page=1, size=10):
        all_data = TestEnvModel.query \
            .filter(TestEnvModel.isDeleted == 0) \
            .slice((page - 1) * size, page * size) \
            .all()
        app.logger.info(f"查询出的环境列表数据为：{all_data}")
        response_list = []
        for env_data in all_data:
            env_dictdata = env_data.to_dict()  # 把model中的数据转化成dict
            env_dictdata.update({"create_time": str(env_dictdata.get("create_time"))})  # 修改创建时间对象为字符串对象
            if env_dictdata.get("update_time"):
                env_dictdata.update({"update_time": str(env_dictdata.get("update_time"))})
            response_list.append(env_dictdata)
        app.logger.info(f"查询出的环境列表数据为并转化为json为：{all_data}")
        return response_list

    @classmethod
    def modify_env(cls, id, env_name, description):
        origin_data = TestEnvModel.query.filter_by(id=id, isDeleted=0).first()  # 根据id查询出之前的数据
        if not origin_data:
            return None
        origin_env_name = origin_data.env_name  # 读取数据库中的环境名称
        origin_description = origin_data.description  # 读取数据库中的环境的备注
        modify_data = {
            "env_name": env_name if env_name else origin_env_name,
            "description": description if description else origin_description
        }
        if env_name or description:  # 外部传入的env_name和description至少要有一个不为空才能触发修改，才能有时间的修改
            update_time = str(datetime.datetime.now())
            modify_data.update({"update_time": update_time})
        TestEnvModel.query.filter_by(id=id, isDeleted=0).update(modify_data)
        db.session.commit()
        db.session.close()

        return modify_data

    @classmethod
    def delete_env(cls, id):
        # 根据id查询要删除的数据
        origin_data = TestEnvModel.query.filter_by(id=id, isDeleted=0).first()
        if not origin_data:
            return None
        isDeleted = {
            "isDeleted": 1
        }
        TestEnvModel.query.filter_by(id=id, isDeleted=0).update(isDeleted)
        db.session.commit()
        db.session.close()


class TestEnvService(Resource):
    decorators = [login_required]
    def get(self):
        if not request.args:
            raise REQ_IS_EMPTY_ERROR()
        if not request.args.get("type"):
            raise REQ_KEY_ERROR()
        action_type = request.args.get("type")
        if action_type == "query_detail":
            if not request.args.get("id"):
                raise REQ_KEY_ERROR()
            response_data = TestEnvController.query_env_by_id(request.args.get("id"))
            if len(response_data) < 1:
                return make_response(status=CodeUtil.SUCCESS, data=response_data)
            response_data.update({"create_time": str(response_data.get("create_time"))})
            if response_data.get("update_time"):  # 如果修改时间不为空，那么把修改时间转化为字符串类型
                response_data.update({"update_time": str(response_data.get("update_time"))})
            app.logger.info(f"把日期对象转化为字符串之后，的结果为：{response_data}")
            return make_response(status=CodeUtil.SUCCESS, data=response_data)
        if action_type == "search":
            if not request.args.get("env_name"):
                raise REQ_KEY_ERROR()
            response_data = TestEnvController.query_env_by_name(request.args.get("env_name"))
            return make_response(status=CodeUtil.SUCCESS, data=response_data)
        if action_type == "query_list":
            page = request.args.get("page")
            if page:  # 如果传入了page，那么判断page是不是数字，如果不是数字直接返回查询的空结果
                if page.isdigit():
                    page = int(page)
                else:
                    return make_response(status=CodeUtil.SUCCESS, data=[])
            size = request.args.get("size")
            if size:  # 如果传入了size，那么判断size是不是数字，如果不是数字直接返回查询的空结果
                if size.isdigit():
                    size = int(size)
                else:
                    return make_response(status=CodeUtil.SUCCESS, data=[])
            response_data = TestEnvController.query_list(page, size)
            total_count = len(response_data)
            return make_response(status=CodeUtil.SUCCESS,
                                 data=response_data,
                                 total_count=total_count,
                                 page=page,
                                 size=size)
        # 如果没有满足的if条件，那么返回json数据的结果
        return make_response(status=CodeUtil.SUCCESS)

    def post(self):
        if not request.data:
            raise REQ_IS_EMPTY_ERROR()
        if not request.is_json:
            raise REQ_TYPE_ERROR()
        env_name = request.get_json().get("env_name")
        if not env_name:
            raise REQ_KEY_ERROR()
        if not isinstance(env_name, str):
            raise REQ_VALUE_ERROR()
        env_data = request.json  # 接受前端传入的数据，只能传json数据
        TestEnvController.add_env(env_data)
        return make_response(status=CodeUtil.SUCCESS, data=env_data)

    def put(self):
        if not request.data:
            raise REQ_IS_EMPTY_ERROR()
        if not request.is_json:
            raise REQ_TYPE_ERROR()
        if not request.get_json().get("id"):
            raise REQ_KEY_ERROR()

        id = request.get_json().get("id")
        env_name = request.get_json().get("env_name")
        description = request.get_json().get("description")

        response_data = TestEnvController.modify_env(id, env_name, description)
        return make_response(status=CodeUtil.SUCCESS, data=response_data)

    def delete(self):
        if not request.data:
            raise REQ_IS_EMPTY_ERROR()
        if not request.is_json:
            raise REQ_TYPE_ERROR()
        if not request.get_json().get("id"):
            raise REQ_KEY_ERROR()

        id = request.get_json().get("id")

        TestEnvController.delete_env(id)
        return make_response(status=CodeUtil.SUCCESS, data=None)
