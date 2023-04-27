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
from backend.models.test_case_model import TestCaseModel
from backend.utils.code_utils import CodeUtil
from backend.utils.excel_utils import ExcelUtils
from backend.utils.exception_utils import REQ_IS_EMPTY_ERROR, REQ_TYPE_ERROR, REQ_KEY_ERROR, REQ_VALUE_ERROR
from backend.utils.make_response_utils import make_response


class TestCaseController:
    excel_utils = ExcelUtils()  # 实例化excel工具类

    @classmethod
    def add_case(cls, case_data):
        # 添加测试用例
        suite_id = case_data.get("suite_id")
        suite_data = TestSuiteModel.query.filter_by(id=suite_id, isDeleted=0).first()
        if not suite_data:
            app.logger.info(f"测试套件id为{suite_id}的数据，在数据库当中查询不到")
            return None

        # 通过suite_id查询project的删除状态
        project_isDeleted = TestSuiteModel.query \
            .filter(TestSuiteModel.id == suite_id, TestSuiteModel.isDeleted == 0) \
            .first() \
            .project \
            .isDeleted

        if not project_isDeleted == '0':  # 判断这个project是不是被删除了，如果被删除了，那么不添加测试用例
            app.logger.info(f"测试套件编号：{suite_id}对应的project已经被删除")
            return None
        case_data = {
            "case_name": case_data.get("case_name"),
            "method": case_data.get("request_method"),
            "protocal": case_data.get("request_protocol"),
            "host": case_data.get("request_host"),
            "port": case_data.get("request_port"),
            "path": case_data.get("request_path"),
            "params": json.dumps(case_data.get("request_params")) if case_data.get("request_params") else None,
            "headers": json.dumps(case_data.get("request_headers")) if case_data.get("request_headers") else None,
            "body": json.dumps(case_data.get("request_body")) if case_data.get("request_body") else '{}',
            "description": case_data.get("description"),
            "predict": json.dumps(case_data.get("predict")) if case_data.get("predict") else None,
            "suite_id": case_data.get("suite_id"),
            "isDeleted": case_data.get("isDeleted"),
            "status": case_data.get("status")
        }
        app.logger.info(f"添加测试用例的数据为：{case_data}")

        data = TestCaseModel(**case_data)
        db.session.add(data)
        db.session.commit()
        db.session.close()
        return case_data

    @classmethod
    def query_testase_by_id(cls, suite_id, id):
        test_suite_data = TestSuiteModel.query.filter(TestSuiteModel.id == suite_id,
                                                      TestSuiteModel.isDeleted == 0).first()
        if not test_suite_data:
            app.logger.info("该用例对应的测试套件id为{suite_id}的数据不存在")
            return []
        if not test_suite_data.project.isDeleted == '0':
            app.logger.info("该用例对应的测试计划的数据不存在")
            return []
        # 查询测试用例详情
        testcase_detail_data = TestCaseModel.query.filter_by(id=id, isDeleted=0).first()
        app.logger.info(f"查询的测试用例id为：{id}的详情数据为：{testcase_detail_data}")
        if testcase_detail_data is None:
            return []
        response_list = []

        testcase_detail_data = testcase_detail_data.to_dict()
        app.logger.info(f"查询的测试用例id为：{id}的详情数据转化为json后：{testcase_detail_data}")
        testcase_detail_data.update({"create_time": str(testcase_detail_data.get("create_time"))})  # 转化修改时间为字符串
        update_time = testcase_detail_data.get("update_time")  # 转化修改时间为字符串
        testcase_detail_data.update({"update_time": str(update_time) if update_time else None})
        return testcase_detail_data

    @classmethod
    def query_testcase_by_name(cls, suite_id, case_name):
        # 校验测试套件和计划有没有被删除，如果被删除了返回空列表
        test_suite_data = TestSuiteModel.query.filter(TestSuiteModel.id == suite_id,
                                                      TestSuiteModel.isDeleted == 0).first()
        if not test_suite_data:
            app.logger.info("该用例对应的测试套件id为{suite_id}的数据不存在")
            return []
        if not test_suite_data.project.isDeleted == '0':
            app.logger.info("该用例对应的测试计划的数据不存在")
            return []
        # 根据测试计划的名称，搜索测试计划
        testcase_search_data = TestCaseModel.query.filter(
            TestCaseModel.case_name.like(f'%{case_name}%'),
            TestCaseModel.isDeleted == 0).all()  # []
        app.logger.info(f"根据测试用例名称 [{case_name}] 搜索出来的数据有：{testcase_search_data}")

        response_list = []
        for testcase_data in testcase_search_data:
            testcase_dictdata = testcase_data.to_dict()  # 把model中的数据转化成dict
            testcase_dictdata.update({"create_time": str(testcase_dictdata.get("create_time"))})  # 修改创建时间对象为字符串对象
            if testcase_dictdata.get("update_time"):
                testcase_dictdata.update({"update_time": str(testcase_dictdata.get("update_time"))})
            response_list.append(testcase_dictdata)
        app.logger.info(f"根据测试用例名称 [{case_name}] 搜索出来的数据并转化为json后：{response_list}")
        return response_list

    @classmethod
    def query_list(cls, suite_id, page=1, size=10):
        # 校验测试套件和计划有没有被删除，如果被删除了返回空列表
        test_suite_data = TestSuiteModel.query.filter(TestSuiteModel.id == suite_id,
                                                      TestSuiteModel.isDeleted == 0).first()
        if not test_suite_data:
            app.logger.info("该用例对应的测试套件id为{suite_id}的数据不存在")
            return []
        if not test_suite_data.project.isDeleted == '0':
            app.logger.info("该用例对应的测试计划的数据不存在")
            return []
        # 查询测试用例列表
        all_data = TestCaseModel.query \
            .filter(TestCaseModel.isDeleted == 0,
                    TestCaseModel.suite_id == suite_id) \
            .slice((page - 1) * size, page * size) \
            .all()
        app.logger.info(f"查询出的测试用例列表数据为：{all_data}")
        response_list = []
        for testcase_data in all_data:
            testcase_dictdata = testcase_data.to_dict()  # 把model中的数据转化成dict
            testcase_dictdata.update({"create_time": str(testcase_dictdata.get("create_time"))})  # 修改创建时间对象为字符串对象
            if testcase_dictdata.get("update_time"):
                testcase_dictdata.update({"update_time": str(testcase_dictdata.get("update_time"))})
            response_list.append(testcase_dictdata)
        app.logger.info(f"查询出的测试计划列表数据并转化为json为：{all_data}")
        return response_list

    @classmethod
    def modify_testcase(cls, modify_data):
        # 读取测试用例的id和测试套件的id
        id = modify_data.get("id")
        suite_id = modify_data.get("suite_id")
        # 校验测试套件和计划有没有被删除，如果被删除了返回空列表
        test_suite_data = TestSuiteModel.query.filter(TestSuiteModel.id == suite_id,
                                                      TestSuiteModel.isDeleted == 0).first()
        if not test_suite_data:
            app.logger.info("该用例对应的测试套件id为{suite_id}的数据不存在")
            return []
        if not test_suite_data.project.isDeleted == '0':
            app.logger.info("该用例对应的测试计划的数据不存在")
            return []

        origin_data = TestCaseModel.query.filter_by(id=id, suite_id=suite_id, isDeleted=0).first()  # 根据id查询出之前的数据
        if not origin_data:
            return None

        modify_data = {
            "case_name": modify_data.get("case_name") if not modify_data.get(
                "case_name") is None else origin_data.case_name,
            "method": modify_data.get("request_method") if not modify_data.get(
                "request_method") is None else origin_data.method,
            "protocal": modify_data.get("request_protocol") if not modify_data.get(
                "request_protocol") is None else origin_data.protocal,
            "host": modify_data.get("request_host") if not modify_data.get(
                "request_host") is None else origin_data.host,
            "port": modify_data.get("request_port") if not modify_data.get(
                "request_port") is None else origin_data.port,
            "path": modify_data.get("request_path") if not modify_data.get(
                "request_path") is None else origin_data.path,
            "params": str(modify_data.get("request_params")) if not modify_data.get("request_params") is None else origin_data.params,
            "headers": str(modify_data.get("request_headers")) if not modify_data.get(
                "request_headers") is None else origin_data.headers,
            "body": str(modify_data.get("request_body")) if not modify_data.get(
                "request_body") is None else origin_data.body,
            "description": modify_data.get("description") if not modify_data.get(
                "description") is None else origin_data.description,
            "predict": str(modify_data.get("predict")) if not modify_data.get(
                "predict") is None else origin_data.predict,
            "update_time": str(datetime.datetime.now())
        }

        TestCaseModel.query.filter_by(id=id, suite_id=suite_id, isDeleted=0).update(modify_data)
        db.session.commit()
        db.session.close()

        return modify_data

    @classmethod
    def delete_testcase(cls, delete_data):
        id = delete_data.get("id")  # 取出测试用例的id
        suite_id = delete_data.get("suite_id")  # 取出测试套件的id
        # 校验测试套件和计划有没有被删除，如果被删除了返回空列表
        test_suite_data = TestSuiteModel.query.filter(TestSuiteModel.id == suite_id,
                                                      TestSuiteModel.isDeleted == 0).first()
        if not test_suite_data:
            app.logger.info("该用例对应的测试套件id为{suite_id}的数据不存在")
            return []
        if not test_suite_data.project.isDeleted == '0':
            app.logger.info("该用例对应的测试计划的数据不存在")
            return []
        # 根据id查询要删除的数据
        origin_data = TestCaseModel.query.filter_by(id=id, suite_id=suite_id, isDeleted=0).first()
        if not origin_data:
            return None
        isDeleted = {
            "isDeleted": 1
        }
        TestCaseModel.query.filter_by(id=id, suite_id=suite_id, isDeleted=0).update(isDeleted)
        db.session.commit()
        db.session.close()

    @classmethod
    def copy_case(cls, case_data):
        # 复制用例就是先查出这条用例，然后去除主键，再插入到数据当中
        testcase_model = TestCaseModel.query.filter_by(id=case_data.get("id"),
                                                       isDeleted=0,
                                                       suite_id=case_data.get("suite_id")).first()
        # 校验用例是否存在
        if not testcase_model:
            app.logger.info(f"要复制的用例不存在{case_data.get(id)}的数据不存在")
            return []
        # 校验用例对应的测试套件和测试计划是否存在
        if not testcase_model.suite.isDeleted:
            app.logger.info(f"要复制的用例{case_data.get(id)}的测试套件已经被删除")
            return []
        if not testcase_model.suite.project.isDeleted:
            app.logger.info(f"要复制的用例{case_data.get(id)}的测试计划已经被删除")
            return []

        case_data_dict = {
            "case_name": testcase_model.case_name + " copy",
            "method": testcase_model.method,
            "protocal": testcase_model.protocal,
            "host": testcase_model.host,
            "port": testcase_model.port,
            "path": testcase_model.path,
            "params": testcase_model.params,
            "headers": testcase_model.headers,
            "body": testcase_model.body,
            "description": testcase_model.description,
            "predict": testcase_model.predict,
            "suite_id": testcase_model.suite_id,
            "suite": testcase_model.suite,
            "isDeleted": testcase_model.isDeleted,
            "status": testcase_model.status,
            "create_time": testcase_model.create_time,
            "update_time": testcase_model.update_time,
            "operation": testcase_model.operation
        }
        copy_case_data = TestCaseModel(**case_data_dict)
        db.session.add(copy_case_data)
        db.session.commit()
        db.session.close()

        return True

    @classmethod
    def export_case(cls, export_data):
        case_id_list = export_data.get("case_id_list").split(',')  # 读取要导出的用例列表
        export_data_list = []  # 要导出的数据列表
        for case_id in case_id_list:
            case_data = TestCaseModel.query.filter_by(id=case_id, isDeleted=0).first()
            if case_data:
                export_data_list.append(case_data.to_dict())  # 把用例对象转化为字典对象
            else:
                app.logger.info(f"要导出的case_id：{case_id}不存在，跳过该条用例")
                continue
        result = cls.excel_utils.export_data(export_data_list)
        return result

    @classmethod
    def import_case(cls, file):
        # 读取要导入的文件名
        file_object = file.get('file')  # 获取request.files当中的file文件
        filename = file_object.filename  # 获取文件名
        app.logger.info(f"导入的文件名为：{filename}")
        if not filename.split('.')[1] == 'xls':
            app.logger.info(f"导入的文件名不是xls")
            return False
        # 从文件中，把所有用例数据都读入到内存
        case_data_list = cls.excel_utils.import_case(file_object)
        # 转化case_data_list为json
        case_data_list = json.loads(case_data_list)
        app.logger.info(f"从文件中读取的要导入的数据为：{case_data_list}")
        # 处理数据，
        case_data_list = cls.excel_utils.foramt_data(case_data_list)
        # 把数据保存到数据库当中
        response_list = []
        for case_data in case_data_list:
            response_list.append({"id": int(case_data.get("id")), "case_name": case_data.get("case_name")})
            data = TestCaseModel(**case_data)
            db.session.add(data)
            db.session.commit()
            db.session.close()
        app.logger.info(f"返回响应数据为：{response_list}")
        return response_list

    @classmethod
    def switch_status(cls, case_data):
        case_id = case_data.get("id")
        case_object = TestCaseModel.query.filter_by(id=case_id, isDeleted=0)
        case_data_model = case_object.first()
        app.logger.info(f"{case_data_model}")
        if not case_data_model:
            app.logger.info(f"要执行的用例不存在")
            return False
        if case_data_model.status == "1":
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
        case_object.update(modify_data)
        db.session.commit()
        db.session.close()

        # 返回结果
        response_data = {
            "id": case_data.get("id"),
            "status": modify_data.get("status")
        }
        app.logger.info(f"{response_data}")
        return response_data


class TestCaseService(Resource):
    decorators = [login_required]

    def get(self):
        if not request.args:  # 校验有没有传数据
            raise REQ_IS_EMPTY_ERROR()
        if not request.args.get("type"):  # 校验传的数据中，有没有type
            raise REQ_KEY_ERROR()

        action_type = request.args.get("type")  # 取出type的值
        if action_type == "query_detail":
            if not request.args.get("suite_id"):
                raise REQ_KEY_ERROR()
            if not request.args.get("id"):
                raise REQ_KEY_ERROR()
            if not request.args.get("suite_id").isdigit():
                raise REQ_VALUE_ERROR()
            if not request.args.get("id").isdigit():
                raise REQ_VALUE_ERROR()

            response_data = TestCaseController.query_testase_by_id(request.args.get("suite_id"), request.args.get("id"))
            return make_response(status=CodeUtil.SUCCESS, data=response_data)
        if action_type == "search":
            if not request.args.get("case_name"):
                raise REQ_KEY_ERROR()
            if not request.args.get("suite_id"):
                raise REQ_KEY_ERROR()
            if not request.args.get("suite_id").isdigit():
                raise REQ_VALUE_ERROR()

            response_data = TestCaseController.query_testcase_by_name(request.args.get("suite_id"),
                                                                      request.args.get("case_name"))
            return make_response(status=CodeUtil.SUCCESS, data=response_data)
        if action_type == "query_list":
            if not request.args.get("suite_id"):
                raise REQ_KEY_ERROR()
            if not request.args.get("suite_id").isdigit():
                raise REQ_VALUE_ERROR()
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
            response_data = TestCaseController.query_list(request.args.get("suite_id"), page, size)
            total_count = len(response_data)
            return make_response(status=CodeUtil.SUCCESS,
                                 data=response_data,
                                 total_count=total_count,
                                 page=page,
                                 size=size)

        # 如果没有满足的if条件，那么返回json数据的结果
        return make_response(status=CodeUtil.SUCCESS)

    def post(self):
        if not request.data and not request.form:  # 如果没有传递raw和表单数据，那么就提示必须传递数据
            raise REQ_IS_EMPTY_ERROR()

        if request.data:  # 如果传递了raw数据，那么认为是在做复制或者新增操作
            if request.get_json().get("operation").upper() == "COPY":
                # 执行复制的动作
                result = TestCaseController.copy_case(request.get_json())
                if result:  # 返回结果
                    return make_response(status=CodeUtil.SUCCESS)
                else:
                    return make_response(status=CodeUtil.FAIL)
            if request.get_json().get("operation").upper() == "ADD":
                case_name = request.get_json().get("case_name")
                if not case_name:
                    raise REQ_KEY_ERROR()
                suite_id = request.get_json().get("suite_id")
                if not suite_id:
                    raise REQ_KEY_ERROR()
                # if not isinstance(suite_id, int): # 接口文档规定必须是字符串，所以不需要校验整型
                #     raise REQ_VALUE_ERROR()
                # 执行新增操作
                method = request.get_json().get("request_method")
                if not method:
                    raise REQ_KEY_ERROR()
                if not method in ['GET', 'POST', 'PUT', 'DELETE', 'PATCH']:
                    raise REQ_VALUE_ERROR()
                result = TestCaseController.add_case(request.get_json())  # 执行添加
                if result:  # 返回结果
                    return make_response(status=CodeUtil.SUCCESS, data=result)
                else:
                    return make_response(status=CodeUtil.FAIL)
        if request.form:  # 如果传递了表单数据，那么认为是在做导入或者导出操作
            if request.form.get("operation").upper() == "IMPORT":
                # 执行导入操作
                # 获取客户端传递的文件流
                file = request.files
                result = TestCaseController.import_case(file)
                if result:
                    return make_response(status=CodeUtil.SUCCESS, data=result)
                else:
                    return make_response(status=CodeUtil.FAIL)
            if request.form.get("operation").upper() == "EXPORT":
                # 执行导出操作
                # 进行导出操作
                output = TestCaseController.export_case(request.form)
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
        return make_response(status=CodeUtil.FAIL)

    def put(self):
        if not request.data:
            raise REQ_IS_EMPTY_ERROR()
        if not request.is_json:
            raise REQ_TYPE_ERROR()
        if not request.get_json().get("id"):
            raise REQ_KEY_ERROR()
        if not request.get_json().get("suite_id"):
            raise REQ_KEY_ERROR()
        if not request.get_json().get("suite_id").isdigit():
            raise REQ_VALUE_ERROR()
        if not request.get_json().get("id").isdigit():
            raise REQ_VALUE_ERROR()

        response_data = TestCaseController.modify_testcase(request.get_json())
        return make_response(status=CodeUtil.SUCCESS, data=response_data)

    def delete(self):
        if not request.data:
            raise REQ_IS_EMPTY_ERROR()
        if not request.is_json:
            raise REQ_TYPE_ERROR()
        if not request.get_json().get("id"):
            raise REQ_KEY_ERROR()
        if not request.get_json().get("suite_id"):
            raise REQ_KEY_ERROR()
        if not request.get_json().get("suite_id").isdigit():
            raise REQ_VALUE_ERROR()
        if not request.get_json().get("id").isdigit():
            raise REQ_VALUE_ERROR()

        TestCaseController.delete_testcase(request.get_json())
        return make_response(status=CodeUtil.SUCCESS, data=None)

    def patch(self):
        app.logger.info(f"传入的禁用启用的用例为：{request.get_json()}")
        result = TestCaseController.switch_status(request.get_json())
        if result:
            return make_response(status=CodeUtil.SUCCESS, data=result)
        else:
            return make_response(status=CodeUtil.FAIL)
