import datetime
import json
import mimetypes

from flask import request, Response
from flask_login import login_required
from werkzeug.datastructures import Headers

from backend.app import app, db
from flask_restful import Resource

from backend.models.test_project_model import TestProjectModel
from backend.models.test_suite_model import TestSuiteModel
from backend.utils.code_utils import CodeUtil
from backend.utils.excel_utils import ExcelUtils
from backend.utils.exception_utils import REQ_IS_EMPTY_ERROR, REQ_TYPE_ERROR, REQ_KEY_ERROR, REQ_VALUE_ERROR
from backend.utils.make_response_utils import make_response


class TestSuiteController:
    excel_utils = ExcelUtils()  # 实例化excel工具类

    @classmethod
    def add_suite(cls, suite_data):
        # 添加测试套件
        project_id = suite_data.get("project_id")
        project_data = TestProjectModel.query.filter_by(id=project_id, isDeleted=0).first()
        if not project_data:
            app.logger.info(f"测试计划id为{project_id}的数据，在数据库当中查询不到")
            return None
        data = TestSuiteModel(**suite_data)
        db.session.add(data)
        db.session.commit()
        db.session.close()
        return True

    @classmethod
    def query_suite_by_id(cls, id):
        # 查询测试套件详情
        suite_detail_data = TestSuiteModel.query.filter_by(id=id, isDeleted=0).first()
        app.logger.info(f"查询的测试套件id为：{id}的详情数据为：{suite_detail_data}")
        if suite_detail_data is None:
            return []
        app.logger.info(f"查询的测试套件id为：{id}的详情数据转化为json后：{suite_detail_data.to_dict()}")
        return suite_detail_data.to_dict()

    @classmethod
    def query_suite_by_name(cls, project_id, suite_name):
        # 根据测试套件的名称，搜索测试套件
        suite_search_data = TestSuiteModel.query.filter(
            TestSuiteModel.project_id == project_id,
            TestSuiteModel.suite_name.like(f'%{suite_name}%'),
            TestSuiteModel.isDeleted == 0).all()  # []
        app.logger.info(f"根据测试套件名称 [{suite_name}] 搜索出来的数据有：{suite_search_data}")

        response_list = []
        for suite_data in suite_search_data:
            suite_dictdata = suite_data.to_dict()  # 把model中的数据转化成dict
            suite_dictdata.update({"create_time": str(suite_dictdata.get("create_time"))})  # 修改创建时间对象为字符串对象
            if suite_dictdata.get("update_time"):
                suite_dictdata.update({"update_time": str(suite_dictdata.get("update_time"))})
            response_list.append(suite_dictdata)
        app.logger.info(f"根据测试套件名称 [{suite_name}] 搜索出来的数据并转化为json后：{response_list}")
        return response_list

    @classmethod
    def query_list(cls, project_id, page=1, size=10):
        all_data = TestSuiteModel.query \
            .filter(TestSuiteModel.isDeleted == 0) \
            .filter(TestSuiteModel.project_id == project_id) \
            .slice((page - 1) * size, page * size) \
            .all()
        app.logger.info(f"查询出的测试套件列表数据为：{all_data}")
        response_list = []
        for suite_data in all_data:
            suite_dictdata = suite_data.to_dict()  # 把model中的数据转化成dict
            suite_dictdata.update({"create_time": str(suite_dictdata.get("create_time"))})  # 修改创建时间对象为字符串对象
            if suite_dictdata.get("update_time"):
                suite_dictdata.update({"update_time": str(suite_dictdata.get("update_time"))})
            response_list.append(suite_dictdata)
        app.logger.info(f"查询出的测试套件列表数据并转化为json为：{all_data}")
        return response_list

    @classmethod
    def modify_suite(cls, suite_id, project_id, suite_name, description):
        # 先校验测试计划有没有被删除
        project_data = TestProjectModel.query.filter_by(id=project_id, isDeleted=0).first()
        if not project_data:
            app.logger.info(f"测试计划id为{project_id}的数据，在数据库当中查询不到")
            return None
        origin_data = TestSuiteModel.query.filter_by(id=suite_id, project_id=project_id,
                                                     isDeleted=0).first()  # 根据id查询出之前的数据
        if not origin_data:
            return None

        origin_suite_name = origin_data.suite_name  # 读取数据库中的测试计划名称
        origin_description = origin_data.description  # 读取数据库中的测试计划的备注
        modify_data = {
            "suite_name": suite_name if suite_name else origin_suite_name,
            "description": description if description else origin_description
        }

        if suite_name or description:  # 外部传入的project_name和description至少要有一个不为空才能触发修改，才能有时间的修改
            update_time = str(datetime.datetime.now())
            modify_data.update({"update_time": update_time})
        TestSuiteModel.query.filter_by(id=suite_id, project_id=project_id, isDeleted=0).update(modify_data)
        db.session.commit()
        db.session.close()
        return modify_data

    @classmethod
    def delete_suite(cls, id, project_id):
        # 根据id查询要删除的数据
        origin_data = TestSuiteModel.query.filter_by(id=id, project_id=project_id, isDeleted=0).first()
        if not origin_data:
            return None
        isDeleted = {
            "isDeleted": 1
        }
        TestSuiteModel.query.filter_by(id=id, isDeleted=0).update(isDeleted)
        db.session.commit()
        db.session.close()

    @classmethod
    def export_case(cls, export_data):
        suite_id_list = export_data.get("suite_id_list").split(',')  # 读取要导出的用例列表
        export_data_list = []  # 要导出的数据列表
        for suite_id in suite_id_list:
            case_data = TestSuiteModel.query.filter_by(id=suite_id, isDeleted=0).first()
            if case_data:
                export_data_list.append(case_data.to_dict())  # 把用例对象转化为字典对象
            else:
                app.logger.info(f"要导出的suite_id：{suite_id}不存在，跳过该条用例")
                continue

        output = cls.excel_utils.export_data(export_data_list) # 把要导出的用例传递给export_data方法，得到要导出的输出流
        return output

    @classmethod
    def import_case(cls, file):

        # 读取要导入的文件名
        file_object = file.get('file') # 获取request.files当中的file文件
        filename = file_object.filename # 获取文件名
        app.logger.info(f"导入的文件名为：{filename}")
        if not filename.split('.')[1] == 'xls':
            app.logger.info(f"导入的文件名不是xls")
            return False
        # 从文件中，把所有用例数据都读入到内存
        suite_data_list = cls.excel_utils.import_case(file_object)
        # 转化case_data_list为json
        suite_data_list = json.loads(suite_data_list)
        app.logger.info(f"从文件中读取的要导入的数据为：{suite_data_list}")
        # 处理数据，
        suite_data_list = cls.excel_utils.foramt_data(suite_data_list)
        # 把数据保存到数据库当中
        response_list = []
        for suite_data in suite_data_list:
            response_list.append({"id": int(suite_data.get("id")), "suite_name": suite_data.get("suite_name")})
            data = TestSuiteModel(**suite_data)
            db.session.add(data)
            db.session.commit()
            db.session.close()
        app.logger.info(f"返回响应数据为：{response_list}")
        return response_list

    @classmethod
    def switch_status(cls, suite_data):
        suite_id = suite_data.get("id")
        suite_object = TestSuiteModel.query.filter_by(id=suite_id, isDeleted=0)
        suite_data_model = suite_object.first()
        app.logger.info(f"{suite_data_model}")
        if not suite_data_model:
            app.logger.info(f"要执行的用例不存在")
            return False
        if suite_data_model.status == "1":
            # 禁用
            modify_data = {
                "status": "0"
            }
        else:
            # 启用
            modify_data = {
                "status": "1"
            }
        app.logger.info(f"{modify_data}")
        suite_object.update(modify_data)
        db.session.commit()
        db.session.close()

        # 返回结果
        response_data = {
            "id": suite_data.get("id"),
            "status": modify_data.get("status")
        }
        app.logger.info(f"{response_data}")
        return response_data


class TestSuiteService(Resource):
    decorators = [login_required]

    def get(self):
        if not request.args:
            raise REQ_IS_EMPTY_ERROR()
        if not request.args.get("type"):
            raise REQ_KEY_ERROR()
        project_id = request.args.get("project_id")
        if not project_id:  # 校验project_id有没有传递
            raise REQ_KEY_ERROR()
        if not project_id.isdigit():  # 校验project_id是不是数字
            raise REQ_VALUE_ERROR()
        action_type = request.args.get("type")
        if action_type == "query_detail":
            if not request.args.get("id"):
                raise REQ_KEY_ERROR()
            response_data = TestSuiteController.query_suite_by_id(request.args.get("id"))
            if len(response_data) < 1:
                return make_response(status=CodeUtil.SUCCESS, data=response_data)
            response_data.update({"create_time": str(response_data.get("create_time"))})
            if response_data.get("update_time"):  # 如果修改时间不为空，那么把修改时间转化为字符串类型
                response_data.update({"update_time": str(response_data.get("update_time"))})
            app.logger.info(f"把日期对象转化为字符串之后，的结果为：{response_data}")
            return make_response(status=CodeUtil.SUCCESS, data=response_data)
        if action_type == "search":
            if not request.args.get("suite_name"):
                raise REQ_KEY_ERROR()
            response_data = TestSuiteController.query_suite_by_name(project_id, request.args.get("suite_name"))
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
            response_data = TestSuiteController.query_list(project_id, page, size)
            total_count = len(response_data)
            return make_response(status=CodeUtil.SUCCESS,
                                 data=response_data,
                                 total_count=total_count,
                                 page=page,
                                 size=size)
        if request.args.get("operation") == "export":
            # 进行导出操作
            result = TestSuiteController.export_case(request.args)
            if result:
                return make_response(status=CodeUtil.SUCCESS)
            else:
                return make_response(status=CodeUtil.FAIL)
        # 如果没有满足的if条件，那么返回json数据的结果
        return make_response(status=CodeUtil.SUCCESS)

    def post(self):
        if not request.data and not request.form:  # 判断有没有传递raw数据和表单数据
            raise REQ_IS_EMPTY_ERROR()


        if request.data: # 如果有传递raw数据，那么执行添加操作
            if not request.is_json: # 校验是不是json数据
                raise REQ_TYPE_ERROR()
            suite_name = request.get_json().get("suite_name")
            if not suite_name:
                raise REQ_KEY_ERROR()
            project_id = request.get_json().get("project_id")
            if not project_id:
                raise REQ_KEY_ERROR()
            if not isinstance(suite_name, str):
                raise REQ_VALUE_ERROR()
            if not isinstance(project_id, int):
                raise REQ_VALUE_ERROR()
            suite_data = request.get_json()  # 接受前端传入的数据，只能传json数据

            result = TestSuiteController.add_suite(suite_data)
            if result:
                return make_response(status=CodeUtil.SUCCESS, data=suite_data)
            else:
                return make_response(status=CodeUtil.FAIL)
        if request.form: # 如果传递了是表单数据，那么认为是要做导入和导出操作
            if request.form.get("operation").upper() == "EXPORT": # 导出
                # 进行导出操作
                output = TestSuiteController.export_case(request.form)
                # 把输出流返回给客户端
                response = Response()  # 定义响应数据
                response.data = output.getvalue()  # 把数据流的数据赋值给响应数据的data属性
                # 定义要导出的文件名
                output_filename = 'export.xls'
                # 分析文件名
                mimetype_tuple = mimetypes.guess_type(output_filename)
                app.logger.info(f"要导出的文件类型是：{mimetype_tuple}")
                headers = Headers({
                    'Content-Type': mimetype_tuple[0],
                    'Content-Length': len(response.data),
                    'Content-Transfer-Encoding': 'binary'
                })
                response.headers = headers
                return response  # 返回响应数据
            if request.form.get("operation").upper() == "IMPORT": # 导入
                # 获取客户端传递的文件流
                file = request.files
                # 执行导入操作
                result = TestSuiteController.import_case(file)
                if result:
                    return make_response(status=CodeUtil.SUCCESS, data=result)
                else:
                    return make_response(status=CodeUtil.FAIL)

        return make_response(status=CodeUtil.FAIL)

    def put(self):
        if not request.data:
            raise REQ_IS_EMPTY_ERROR()
        if not request.is_json:
            raise REQ_TYPE_ERROR()
        if not request.get_json().get("id"):
            raise REQ_KEY_ERROR()
        if not request.get_json().get("project_id"):
            raise REQ_KEY_ERROR()

        id = request.get_json().get("id")  # 测试套件的id
        project_id = request.get_json().get("project_id")  # 测试计划的id
        suite_name = request.get_json().get("suite_name")
        description = request.get_json().get("description")

        response_data = TestSuiteController.modify_suite(id, project_id, suite_name, description)
        return make_response(status=CodeUtil.SUCCESS, data=response_data)

    def delete(self):
        if not request.data:
            raise REQ_IS_EMPTY_ERROR()
        if not request.is_json:
            raise REQ_TYPE_ERROR()
        if not request.get_json().get("id"):
            raise REQ_KEY_ERROR()
        if not request.get_json().get("project_id"):
            raise REQ_KEY_ERROR()

        id = request.get_json().get("id")  # suite的id
        project_id = request.get_json().get("project_id")  # 测试计划的id

        TestSuiteController.delete_suite(id, project_id)
        return make_response(status=CodeUtil.SUCCESS, data=None)

    def patch(self):
        app.logger.info(f"传入的禁用启用的测试套件为：{request.get_json()}")
        result = TestSuiteController.switch_status(request.get_json())
        if result:
            return make_response(status=CodeUtil.SUCCESS, data=result)
        else:
            return make_response(status=CodeUtil.FAIL)
