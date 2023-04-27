# -*- encoding=utf-8 -*-
import datetime

from flask import request
from flask_login import login_required

from backend.app import app, db
from flask_restful import Resource

from backend.models.test_env_model import TestEnvModel
from backend.models.test_env_params_model import TestEnvParamsModel
from backend.utils.code_utils import CodeUtil
from backend.utils.exception_utils import REQ_IS_EMPTY_ERROR, REQ_TYPE_ERROR, REQ_KEY_ERROR, REQ_VALUE_ERROR
from backend.utils.make_response_utils import make_response


class TestEnvParamsController:
    def __init__(self):
        pass

    @classmethod
    def add_env_params(cls, env_params_data):
        env_params_data = {
            "params_key": env_params_data.get("params_name"),
            "params_value": env_params_data.get("params_value"),
            "description": env_params_data.get("description"),
            "env_id": env_params_data.get("env_id")
        }

        # 添加环境
        data = TestEnvParamsModel(**env_params_data)
        db.session.add(data)
        db.session.commit()
        db.session.close()

    @classmethod
    def query_env_by_id(cls, env_id, id):
        # 查询环境变量的详情
        env_params_detail_data = TestEnvParamsModel.query.filter_by(id=id,
                                                                    isDeleted=0,
                                                                    env_id=env_id).first()
        app.logger.info(f"查询环境变量的环境变量id：{id}的详情数据为：{env_params_detail_data}")
        if env_params_detail_data is None:
            return []
        app.logger.info(f"查询环境变量的环境变量id：{id}的详情数据转化为json后：{env_params_detail_data.to_dict()}")
        return env_params_detail_data.to_dict()

    @classmethod
    def query_envparams_by_name(cls, env_id, env_params_key):
        # 根据环境变量的名称，搜索环境变量
        env_params_search_data = TestEnvParamsModel.query.filter(
            TestEnvParamsModel.params_key.like(f'%{env_params_key}%'),
            TestEnvParamsModel.isDeleted == 0,
            TestEnvParamsModel.env_id == env_id
        ).all()  # []
        app.logger.info(f"根据环境变量名称 [{env_params_key}] 搜索出来的数据有：{env_params_search_data}")

        response_list = []
        for env_params_data in env_params_search_data:
            env_params_dictdata = env_params_data.to_dict()  # 把model中的数据转化成dict
            env_params_dictdata.update({"params_name": env_params_dictdata.pop("params_key")}) # 根据接口文档，调整params_key为params_name
            env_params_dictdata.update({"create_time": str(env_params_dictdata.get("create_time"))})  # 修改创建时间对象为字符串对象
            if env_params_dictdata.get("update_time"):
                env_params_dictdata.update({"update_time": str(env_params_dictdata.get("update_time"))})
            response_list.append(env_params_dictdata)
        app.logger.info(f"根据环境变量名称 [{env_params_key}] 搜索出来的数据并转化为json后：{response_list}")
        return response_list

    @classmethod
    def query_list(cls, env_id, page=1, size=10):
        all_data = TestEnvParamsModel.query \
            .filter(TestEnvParamsModel.isDeleted == 0,
                    TestEnvParamsModel.env_id == env_id) \
            .slice((page - 1) * size, page * size) \
            .all()
        app.logger.info(f"查询出的环境变量列表数据为：{all_data}")
        response_list = []
        for env_params_data in all_data:
            env_params_dictdata = env_params_data.to_dict()  # 把model中的数据转化成dict
            env_params_dictdata.update({"params_name": env_params_dictdata.pop("params_key")}) # 根据接口文档，调整params_key为params_name
            env_params_dictdata.update({"create_time": str(env_params_dictdata.get("create_time"))})  # 修改创建时间对象为字符串对象
            if env_params_dictdata.get("update_time"):
                env_params_dictdata.update({"update_time": str(env_params_dictdata.get("update_time"))})
            response_list.append(env_params_dictdata)
        app.logger.info(f"查询出的环境变量列表数据为并转化为json为：{response_list}")
        return response_list

    @classmethod
    def modify_env_params(cls, id, params_key, params_value, description, env_id):
        origin_data = TestEnvParamsModel.query.filter_by(id=id, isDeleted=0,
                                                         env_id=env_id).first()  # 根据id查询出之前的数据
        if not origin_data:
            return None
        origin_params_key = origin_data.params_key  # 读取数据库中的环境变量的变量名
        origin_params_value = origin_data.params_value  # 读取数据库中的环境变量的变量值
        origin_description = origin_data.description  # 读取数据库中的环境的备注
        modify_data = {
            "params_key": params_key if params_key else origin_params_key,
            "params_value": params_value if params_value else origin_params_value,
            "description": description if description else origin_description
        }
        if params_key or params_value or description:  # 三个参数必须传递一个
            update_time = str(datetime.datetime.now())
            modify_data.update({"update_time": update_time})
        TestEnvParamsModel.query.filter_by(id=id, isDeleted=0).update(modify_data)
        db.session.commit()
        db.session.close()

        return modify_data

    @classmethod
    def delete_env_params(cls, id):
        # 根据id查询要删除的数据
        origin_data = TestEnvParamsModel.query.filter_by(id=id, isDeleted=0).first()
        if not origin_data:
            return None
        isDeleted = {
            "isDeleted": 1
        }
        TestEnvParamsModel.query.filter_by(id=id, isDeleted=0).update(isDeleted)
        db.session.commit()
        db.session.close()


class TestEnvParamsService(Resource):
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
            response_data = TestEnvParamsController.query_env_by_id(request.args.get("env_id"),
                                                                    request.args.get("id"))
            if len(response_data) < 1:
                return make_response(status=CodeUtil.SUCCESS, data=response_data)
            if isinstance(response_data,dict):
                response_data.update({"params_name": response_data.pop("params_key")}) # 根据接口文档，调整params_key为params_name
            response_data.update({"create_time": str(response_data.get("create_time"))})
            if response_data.get("update_time"):  # 如果修改时间不为空，那么把修改时间转化为字符串类型
                response_data.update({"update_time": str(response_data.get("update_time"))})
            app.logger.info(f"把日期对象转化为字符串之后，的结果为：{response_data}")
            return make_response(status=CodeUtil.SUCCESS, data=response_data)
        if action_type == "search":
            if not request.args.get("params_name"):
                raise REQ_KEY_ERROR()
            response_data = TestEnvParamsController.query_envparams_by_name(request.args.get("env_id"),
                                                                            request.args.get("params_name"))
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
            env_id = request.args.get("env_id")  # 获取要查询的环境变量列表的环境id
            response_data = TestEnvParamsController.query_list(env_id, page, size)
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
        params_key = request.get_json().get("params_name")
        if not params_key:
            raise REQ_KEY_ERROR()
        if not isinstance(params_key, str):
            raise REQ_VALUE_ERROR()
        env_params_data = request.json  # 接受前端传入的数据，只能传json数据
        TestEnvParamsController.add_env_params(env_params_data)
        return make_response(status=CodeUtil.SUCCESS, data=env_params_data)

    def put(self):
        if not request.data:
            raise REQ_IS_EMPTY_ERROR()
        if not request.is_json:
            raise REQ_TYPE_ERROR()
        if not request.get_json().get("id"):
            raise REQ_KEY_ERROR()

        id = request.get_json().get("id")
        params_key = request.get_json().get("params_key")
        params_value = request.get_json().get("params_value")
        description = request.get_json().get("description")

        response_data = TestEnvParamsController.modify_env_params(id, params_key, params_value, description,
                                                                  request.get_json().get("env_id"))
        return make_response(status=CodeUtil.SUCCESS, data=response_data)

    def delete(self):
        if not request.data:
            raise REQ_IS_EMPTY_ERROR()
        if not request.is_json:
            raise REQ_TYPE_ERROR()
        if not request.get_json().get("id"):
            raise REQ_KEY_ERROR()

        id = request.get_json().get("id")

        TestEnvParamsController.delete_env_params(id)
        return make_response(status=CodeUtil.SUCCESS, data=None)
