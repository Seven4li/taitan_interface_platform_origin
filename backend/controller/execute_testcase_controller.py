import copy
import datetime
import json
import random
import re
import string
import time

import jsonpath
import requests
from flask import request
from flask_login import login_required
from requests.adapters import HTTPAdapter
from backend import config
from backend.app import app, db
from flask_restful import Resource
import threadpool

from backend.models.test_env_model import TestEnvModel
from backend.models.test_project_model import TestProjectModel
from backend.models.test_report_model import TestReportModel
from backend.models.test_suite_model import TestSuiteModel
from backend.models.test_case_model import TestCaseModel
from backend.utils.code_utils import CodeUtil
from backend.utils.exception_utils import REQ_IS_EMPTY_ERROR, REQ_TYPE_ERROR, REQ_KEY_ERROR, REQ_VALUE_ERROR
from backend.utils.make_response_utils import make_response
from backend.utils.replace_params_utils import replace_params


# 生成测试报告的id
def generate_ranom_str(randomlength=32):
    str_list = random.sample(string.digits + string.ascii_letters, randomlength - 13)
    random_str = ''.join(str_list)
    random_str = str(int(time.time() * 1000)) + random_str
    return random_str


def assert_testcase(predict, response):
    # 这里要写上断言代码，分别应该包括：正则表达式断言、JSON断言、断言时间等断言内容
    test_result = False
    msg = ""
    # 判断没有预期数据时的断言
    if predict is None:
        test_result = True
        msg = "没有设置断言，默认为断言通过"
        return test_result, msg
    # 校验response的结果是不是为空
    if response is None:
        test_result = False
        msg = "响应数据为空"  # 一般来讲，不会设计响应数据为None的结果
        return test_result, msg
    # 转化predcit的数据为json
    try:
        predict = json.loads(predict)
    except Exception as e:
        test_result = False
        msg = "预期数据结构不正确"
        return test_result, msg

    # 定义收集断言结果的result_list
    result_list = []
    # 断言响应状态码
    predict_res_code = predict.get("assert_response_code").get("response_code")
    actural_res_code = response.status_code
    if predict_res_code == actural_res_code:
        test_result = True
        msg = f"通过 预期的响应状态码：{predict_res_code} 实际的响应状态码{actural_res_code}"
        result_list.append((test_result, msg))  # 将断言结果都放在结果列表中
    else:
        test_result = True
        msg = f"不通过 预期的响应状态码：{predict_res_code} 实际的响应状态码{actural_res_code}"
        result_list.append((test_result, msg))  # 将断言结果都放在结果列表中

    # 断言json数据
    assert_json_data = predict.get("assert_json")  # 提取预期数据当中的要断言的json数据内容
    try:
        jsonData = response.json()  # 可以做到判断返回的响应数据是不是json类型
        path = assert_json_data.get("path")  # 读取path
        result = jsonpath.jsonpath(jsonData, path)  # 判断提供的提取实际响应数据的json路径是否正确
        if result:
            predict_value = assert_json_data.get("predict_value")
            test_result = (predict_value == result[0])  # 对比实际的json数据，与预期的json数据是否一致
        if test_result:
            msg = "json断言通过"
            result_list.append((test_result, msg))  # 将断言结果都放在结果列表中
        else:
            msg = "json断言不通过"
            result_list.append((test_result, msg))  # 将断言结果都放在结果列表中
    except Exception as e:
        test_result = False
        msg = "json断言不通过，响应数据可能不是json类型，或者提供的jsonpath路径找不到数据"
        result_list.append((test_result, msg))  # 将断言结果都放在结果列表中

    # 断言持续时间
    predict_time = predict.get("assert_time").get("predict_time") # 获取预期的持续时间
    actural_time = response.elapsed.total_seconds() # 实际的持续时间
    if predict_time >= actural_time:
        test_result = True
        msg = f"断言通过：预期的持续时间{predict_time} 大于实际的持续时间{actural_time}"
        result_list.append((test_result, msg))  # 将断言结果都放在结果列表中
    else:
        test_result = True
        msg = f"断言不通过：预期的持续时间{predict_time} 小于实际的持续时间{actural_time}"
        result_list.append((test_result, msg))  # 将断言结果都放在结果列表中

    # 断言正则表达式
    pattern = predict.get("assert_reg").get("reg") # 获取正则表达式
    predict_value = predict.get("assert_reg").get("predict_value")
    actural_value = re.findall(pattern, response.text) # 提取实际数据
    if not actural_value:
        test_result = False
        msg = f"不通过,使用当前正则表达式{pattern}无法从实际数据当中提取数据"
        result_list.append((test_result, msg))  # 将断言结果都放在结果列表中
    else:
        if predict_value == int(actural_value[0]) if actural_value[0].isdigit() else actural_value[0]:
            test_result = True
            msg = f"通过，使用正则表达式{pattern}提取的数据{actural_value[0]}与预期{predict_value}一致"
            result_list.append((test_result, msg))  # 将断言结果都放在结果列表中
        else:
            test_result = False
            msg = f"不通过，使用正则表达式{pattern}提取的数据{actural_value[0]}与预期{predict_value}不一致"
            result_list.append((test_result, msg))  # 将断言结果都放在结果列表中

    return result_list


session = requests.Session()  # 实例化session对象
session.mount("http://", HTTPAdapter(max_retries=3))  # 配置http请求的重试次数为3
session.mount("https://", HTTPAdapter(max_retries=3))  # 配置https请求的重试次数为3


def send_request(method, url, params, headers, body):
    response = None
    if method == "GET":
        response = session.get(url=url, params=params, headers=headers)
    if method == "POST":
        response = session.post(url=url, params=params, headers=headers, json=body)
    if method == "PUT":
        response = session.put(url=url, params=params, headers=headers, json=body)
    if method == "DELETE":
        response = session.delete(url=url, params=params, headers=headers, json=body)
    return response


# 执行测试用例的任务
def task_execute_testcase(caseid):
    start_time = datetime.datetime.now()  # 计算单条测试用例执行的时间
    # 查询数据库，把每一条caseid的数据记录都查询出来，然后才能拼接接口的数据，最后使用requests执行
    case_data = TestCaseModel.query.filter(TestCaseModel.id == caseid, TestCaseModel.isDeleted == '0').first()
    suite_name = case_data.suite.suite_name  # 把suite_name读取出来，读取之后，sqlalchemy会自动缓存这组数据
    # 加载环境变量，把环境变量的所有变量，都提取出来组合成环境变量的键值对数据结构
    env_id = ExecuteTestCaseController.env_id  # 使用保存到ExecuteTestCaseController的env_id来加载环境变量
    app.logger.info(f"要用的环境变量id为：{env_id}")
    env_data_model = TestEnvModel.query.filter_by(id=env_id, isDeleted=0).first()
    app.logger.info(f"从数据库当中查询出来的环境为：{env_data_model}")
    env_params_list = env_data_model.test_env.all()
    app.logger.info(f"反向查找出来的环境变量：{env_params_list}")
    env_data = {}  # 定义要组合的键值对形式的数据结构
    for params_model in env_params_list:  # 提取出来参数组合成键值对的数据结构
        env_data.update({params_model.params_key: params_model.params_value})
    app.logger.info(f"组合成键值对形式的环境变量为：{env_data}")
    # # 使用环境变量中的变量值，替换用例中的变量（如果没有需要替换的变量，那么不做处理）
    case_data_elment_list = ['method', 'protocal', 'host', 'port', 'path', 'params', 'headers', 'body', 'predict']
    for elment in case_data_elment_list:
        request_data = getattr(case_data, elment)  # 使用getattr获取case_data中的对应数据的值
        # 把value中的变量用环境变量进行替换
        replaced_data = replace_params(request_data, env_data)
        # 把替换后的数据放回来
        setattr(case_data, elment, replaced_data)

    # 取出要测试的接口的请求方法、协议、域名、端口、查询参数、资源路径、请求头、请求体、预期结果
    method = case_data.method
    protocal = case_data.protocal
    host = case_data.host
    port = case_data.port
    path = case_data.path
    params = case_data.params
    headers = case_data.headers
    body = case_data.body
    predict = case_data.predict
    # 拼接接口的请求数据
    url = protocal + "://" + host + ":" + str(port) + path
    params = json.loads(params.replace('\'', '\"'))
    headers = json.loads(headers.replace('\'', '\"'))
    body = json.loads((body.replace('\'', '\"')))
    # 使用requests模块发送接口请求
    response = send_request(method, url, params, headers, body)
    end_time = datetime.datetime.now()  # 计算单条测试用例执行的时间
    time_delta = str((end_time - start_time).total_seconds())  # 单条用例的执行时间
    app.logger.info(f"用例编号{caseid}执行的结果为：{response.text}")

    # 断言结果
    assert_result = assert_testcase(predict, response)
    # 测试结果
    app.logger.info(f"断言的结果为： {assert_result}")
    test_result = "通过"
    for result in assert_result:
        if not result[0]:
            test_result = "不通过"

    # 每条测试用例测试报告的详细数据
    report_detail = {
        "case_id": case_data.id,
        "case_name": case_data.case_name,
        "suite_id": case_data.suite_id,
        "suite_name": suite_name,
        "methods": case_data.method,
        "url": response.url,  # 本来应该拼接请求方法、域名、协议、端口、资源路径、查询参数，也可以从响应数据中获取URL
        "headers": case_data.headers,
        "body": case_data.body,
        "response_data": response.text,
        "status_code": response.status_code,
        "predict": case_data.predict,
        "assert_result": assert_result,
        "test_result": test_result,
        "overtime": time_delta,
    }
    return report_detail


# 使用线程池执行用例的方法
def multi_thread(poolsize=5, caseid_list=None, callback=None):
    # 设置线程池的大小
    pool = threadpool.ThreadPool(poolsize)
    # 制作线程池要执行的任务请求
    req_list = threadpool.makeRequests(task_execute_testcase, caseid_list, callback=callback)
    # 执行线程池中的任务请求
    for req in req_list:
        app.logger.info(req)
        pool.putRequest(req)
    # [pool.putRequest(req) for req in req_list]
    # 等待执行结果
    pool.wait()


def check_testcase(caseid_list):
    app.logger.info(f"要执行的测试用例编号列表为：{caseid_list}")
    # 校验caseid的测试套件、测试计划有没有被删除
    new_caseid_list = copy.deepcopy(caseid_list)
    for caseid in caseid_list:
        case_data = TestCaseModel.query.filter(TestCaseModel.id == caseid, TestCaseModel.isDeleted == 0).first()
        if not case_data :
            app.logger.info(f"caseid为{caseid}的用例在数据库当中查询不到，跳过这条用例")
            new_caseid_list.remove(caseid)  # 从要执行的用例编号列表中去除这条用例
            continue
        if not case_data.suite.isDeleted == '0':
            app.logger.info(f"caseid为{caseid}的用例的用例集{case_data.suite.id}已经被删除，跳过这条用例")
            new_caseid_list.remove(caseid)  # 从要执行的用例编号列表中去除这条用例
            continue
        if not case_data.suite.project.isDeleted == '0':
            app.logger.info(
                f"caseid为{caseid}的用例的用例集{case_data.suite.id}的测试计划{case_data.suite.project.id}已经被删除，跳过这条用例")
            new_caseid_list.remove(caseid)  # 从要执行的用例编号列表中去除这条用例
            continue
    app.logger.info(f"经过校验之后，要执行的测试用例列表为：{new_caseid_list}")
    return new_caseid_list


class ExecuteTestCaseController:
    response_list = []  # 用来采集多线程执行测试用例的响应结果
    env_id = None  # 记录对应的环境id

    @classmethod
    def _execute_testcase(cls, new_caseid_list):
        # 使用多线程执行测试用例
        app.logger.info("开始多线程执行测试用例：------------")
        multi_thread(poolsize=config.NUMBERS, caseid_list=new_caseid_list, callback=cls.collection_result)
        app.logger.info("结束多线程执行测试用例：------------")
        app.logger.info(f"结束多线程执行测试用例的结果集为：{cls.response_list}")

    @classmethod
    def execute_testcase(cls, testcase_data):

        cls.env_id = testcase_data.get("env_id")  # 获取env_id并保存在ExecuteTestCaseController当中
        start_time = datetime.datetime.now()  # 计算总时间
        caseid_list = testcase_data.get("caseid_list")
        new_caseid_list = check_testcase(caseid_list)  # 调用检查测试用例的方法
        ExecuteTestCaseController._execute_testcase(new_caseid_list)  # 执行内部的多线程执行测试用例方法

        # 测试报告概要数据
        end_time = datetime.datetime.now()  # 计算总时间
        time_delta = str((end_time - start_time).total_seconds())
        reportName = reportId = generate_ranom_str()  # 生成测试报告的名称和ID
        testCount = len(cls.response_list)  # 计算response_list的长度作为用例的数据
        passCount = 0
        failedCount = 0
        conclusion = "通过"
        for response_case_data in cls.response_list:
            if response_case_data.get("assert_result"):
                passCount += 1
            else:
                failedCount += 1  # 包括了失败和错误
                conclusion = "不通过"
        passRate = passCount / testCount  # 通过率

        report_summerise = {
            "reportName": reportName,
            "reportId": reportId,
            "project_name": testcase_data.get("project_name"),
            "project_id": testcase_data.get("project_id"),
            "testCount": testCount,
            "passCount": passCount,
            "failedCount": failedCount,
            "passRate": passRate,
            "conclusion": conclusion,
            "total_time": time_delta,
            "comFrom": testcase_data.get("executionMode"),
            "create_time": datetime.datetime.now(),
            "case_data": str(cls.response_list),
        }

        # 保存测试报告概要信息和详细信息到数据库
        testreport_data = TestReportModel(**report_summerise)
        db.session.add(testreport_data)
        db.session.commit()
        db.session.close()
        cls.response_list = []  # 清除响应数据列表对象

    @classmethod
    def execute_testsuite(cls, testsuite_data):

        cls.env_id = testsuite_data.get("env_id")  # 获取env_id并保存在ExecuteTestCaseController当中
        start_time = datetime.datetime.now()  # 计算总时间
        suite_id_list = testsuite_data.get("suite_id_list")
        for suite_id in suite_id_list:  # 遍历测试套件列表
            # 根据测试套件的编号，读取测试用例列表
            s_data = TestSuiteModel.query.filter(TestSuiteModel.id == suite_id, TestSuiteModel.isDeleted == 0).first()
            app.logger.info(f"根据suite_id：{suite_id} 查找的要执行的测试套件：{s_data}")
            test_cases = s_data.test_case
            app.logger.info(f"从测试套件中反向查找的所有测试用例：{test_cases}")

            caseid_list = []
            for test_case in test_cases:
                if test_case.isDeleted == '0':
                    caseid_list.append(test_case.id)  # 将测试用例的id加入到caseid_list
            ExecuteTestCaseController._execute_testcase(caseid_list)  # 执行测试用例

        # 测试报告概要数据
        end_time = datetime.datetime.now()  # 计算总时间
        time_delta = str((end_time - start_time).total_seconds())
        reportName = reportId = generate_ranom_str()  # 生成测试报告的名称和ID
        testCount = len(cls.response_list)  # 计算response_list的长度作为用例的数据
        passCount = 0
        failedCount = 0
        conclusion = "通过"
        for response_case_data in cls.response_list:
            if response_case_data.get("assert_result"):
                passCount += 1
            else:
                failedCount += 1  # 包括了失败和错误
                conclusion = "不通过"
        passRate = passCount / testCount  # 通过率

        report_summerise = {
            "reportName": reportName,
            "reportId": reportId,
            "project_name": testsuite_data.get("project_name"),
            "project_id": testsuite_data.get("project_id"),
            "testCount": testCount,
            "passCount": passCount,
            "failedCount": failedCount,
            "passRate": passRate,
            "conclusion": conclusion,
            "total_time": time_delta,
            "comFrom": testsuite_data.get("executionMode"),
            "create_time": datetime.datetime.now(),
            "case_data": str(cls.response_list),
        }

        # 保存测试报告概要信息和详细信息到数据库
        testreport_data = TestReportModel(**report_summerise)
        db.session.add(testreport_data)
        db.session.commit()
        db.session.close()

        cls.response_list = []  # 清除响应数据列表对象

    # 采集测试用例执行结果的回调方法
    @classmethod
    def collection_result(cls, *args, **kwargs):
        result = args[1]  # 接收任务的return的响应数据
        cls.response_list.append(result)


class ExecuteTestCaseService(Resource):
    decorators = [login_required]
    def post(self):
        if not request.data:  # 校验有没有传请求数据
            raise REQ_IS_EMPTY_ERROR()
        if not request.is_json:  # 校验传的数据是不是json数据
            raise REQ_TYPE_ERROR()
        caseid_list = request.get_json().get("caseid_list")  # 读取测试用例编号列表
        suite_id_list = request.get_json().get("suite_id_list")  # 读取测试套件编号列表
        if not caseid_list and not suite_id_list:  # 如果用例和套件都没有传递，那么抛出keyerror
            raise REQ_KEY_ERROR()
        if caseid_list and suite_id_list:  # 如果用例和套件都传递了，那么抛出ValueError，因为只能选择一种去执行
            raise REQ_VALUE_ERROR()

        if suite_id_list:
            # 执行测试套件
            result = ExecuteTestCaseController.execute_testsuite(request.get_json())
            app.logger.info(f"执行测试套件: {result}")
            return make_response(1,msg="执行测试用例集成功，正在生成测试报告", data=result)
        if caseid_list:
            # 执行测试用例
            result = ExecuteTestCaseController.execute_testcase(request.get_json())
            app.logger.info(f"执行测试用例: {result}")
            return make_response(1,msg="执行测试用例成功，正在生成测试报告", data=result)
