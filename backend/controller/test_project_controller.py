import datetime

import flask_login
from flask import request
from flask_login import login_required

from backend.app import app, db
from flask_restful import Resource

from backend.models.test_project_model import TestProjectModel
from backend.utils.code_utils import CodeUtil
from backend.utils.exception_utils import REQ_IS_EMPTY_ERROR, REQ_TYPE_ERROR, REQ_KEY_ERROR, REQ_VALUE_ERROR
from backend.utils.make_response_utils import make_response


class TestProjectController:
    def __init__(self):
        pass

    @classmethod
    def add_project(cls, project_data):
        # 添加测试计划
        data = TestProjectModel(**project_data)
        db.session.add(data)
        db.session.commit()
        db.session.close()

    @classmethod
    def query_project_by_id(cls, id):
        # 查询测试计划详情
        project_detail_data = TestProjectModel.query.filter_by(id=id, isDeleted=0).first()
        app.logger.info(f"查询的测试计划id为：{id}的详情数据为：{project_detail_data}")
        if project_detail_data is None:
            return []
        app.logger.info(f"查询的测试计划id为：{id}的详情数据转化为json后：{project_detail_data.to_dict()}")
        return project_detail_data.to_dict()

    @classmethod
    def query_project_by_name(cls, project_name):
        # 根据测试计划的名称，搜索测试计划
        project_search_data = TestProjectModel.query.filter(
            TestProjectModel.project_name.like(f'%{project_name}%'),
            TestProjectModel.isDeleted == 0).all()  # []
        app.logger.info(f"根据测试计划名称 [{project_name}] 搜索出来的数据有：{project_search_data}")

        response_list = []
        for project_data in project_search_data:
            project_dictdata = project_data.to_dict()  # 把model中的数据转化成dict
            project_dictdata.update({"create_time": str(project_dictdata.get("create_time"))})  # 修改创建时间对象为字符串对象
            if project_dictdata.get("update_time"):
                project_dictdata.update({"update_time": str(project_dictdata.get("update_time"))})
            response_list.append(project_dictdata)
        app.logger.info(f"根据测试计划名称 [{project_name}] 搜索出来的数据并转化为json后：{response_list}")
        return response_list

    @classmethod
    def query_list(cls, page=1, size=10):
        all_data = TestProjectModel.query \
            .filter(TestProjectModel.isDeleted == 0) \
            .slice((page - 1) * size, page * size) \
            .all()
        app.logger.info(f"查询出的测试计划列表数据为：{all_data}")
        response_list = []
        for project_data in all_data:
            project_dictdata = project_data.to_dict()  # 把model中的数据转化成dict
            project_dictdata.update({"create_time": str(project_dictdata.get("create_time"))})  # 修改创建时间对象为字符串对象
            if project_dictdata.get("update_time"):
                project_dictdata.update({"update_time": str(project_dictdata.get("update_time"))})
            response_list.append(project_dictdata)
        app.logger.info(f"查询出的测试计划列表数据并转化为json为：{all_data}")
        return response_list

    @classmethod
    def modify_project(cls, id, project_name, description):
        origin_data = TestProjectModel.query.filter_by(id=id, isDeleted=0).first()  # 根据id查询出之前的数据
        if not origin_data:
            return None
        origin_project_name = origin_data.project_name  # 读取数据库中的测试计划名称
        origin_description = origin_data.description  # 读取数据库中的测试计划的备注
        modify_data = {
            "project_name": project_name if project_name else origin_project_name,
            "description": description if description else origin_description
        }

        if project_name or description:  # 外部传入的project_name和description至少要有一个不为空才能触发修改，才能有时间的修改
            update_time = str(datetime.datetime.now())
            modify_data.update({"update_time": update_time})
        TestProjectModel.query.filter_by(id=id, isDeleted=0).update(modify_data)
        db.session.commit()
        db.session.close()

        return modify_data

    @classmethod
    def delete_project(cls, id):
        # 根据id查询要删除的数据
        origin_data = TestProjectModel.query.filter_by(id=id, isDeleted=0).first()
        if not origin_data:
            return None
        isDeleted = {
            "isDeleted": 1
        }
        TestProjectModel.query.filter_by(id=id, isDeleted=0).update(isDeleted)
        db.session.commit()
        db.session.close()

class TestProjectService(Resource):
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
            response_data = TestProjectController.query_project_by_id(request.args.get("id"))
            if len(response_data) < 1:
                return make_response(status=CodeUtil.SUCCESS, data=response_data)
            response_data.update({"create_time": str(response_data.get("create_time"))})
            if response_data.get("update_time"):  # 如果修改时间不为空，那么把修改时间转化为字符串类型
                response_data.update({"update_time": str(response_data.get("update_time"))})
            app.logger.info(f"把日期对象转化为字符串之后，的结果为：{response_data}")
            return make_response(status=CodeUtil.SUCCESS, data=response_data)
        if action_type == "search":
            if not request.args.get("project_name"):
                raise REQ_KEY_ERROR()
            response_data = TestProjectController.query_project_by_name(request.args.get("project_name"))
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
            response_data = TestProjectController.query_list(page, size)
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
        project_name = request.get_json().get("project_name")
        if not project_name:
            raise REQ_KEY_ERROR()
        if not isinstance(project_name, str):
            raise REQ_VALUE_ERROR()
        project_data = request.json  # 接受前端传入的数据，只能传json数据
        TestProjectController.add_project(project_data)
        return make_response(status=CodeUtil.SUCCESS, data=project_data)

    def put(self):
        if not request.data:
            raise REQ_IS_EMPTY_ERROR()
        if not request.is_json:
            raise REQ_TYPE_ERROR()
        if not request.get_json().get("id"):
            raise REQ_KEY_ERROR()

        id = request.get_json().get("id")
        project_name = request.get_json().get("project_name")
        description = request.get_json().get("description")

        response_data = TestProjectController.modify_project(id, project_name, description)
        return make_response(status=CodeUtil.SUCCESS, data=response_data)

    def delete(self):
        if not request.data:
            raise REQ_IS_EMPTY_ERROR()
        if not request.is_json:
            raise REQ_TYPE_ERROR()
        if not request.get_json().get("id"):
            raise REQ_KEY_ERROR()

        id = request.get_json().get("id")

        TestProjectController.delete_project(id)
        return make_response(status=CodeUtil.SUCCESS, data=None)

