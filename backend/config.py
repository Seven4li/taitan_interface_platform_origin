import os

# 日志等级
CRITICAL = 50
ERROR = 40
WARNING = 30
INFO = 20
DEBUG = 10
LOG_LEVEL = INFO

# 项目路径
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
print("当前路径为：", BASE_DIR)

# 数据库连接配置
DB_PROTOCAL = 'mysql'
DB_DRIVER = 'pymysql'
USERNAME = 'root'
PASSWORD = '123456'
HOST = '10.1.201.231'
PORT = '3307'
DATABASE = 'taitan_interface_platform'

# 测试平台执行测试用例启动的线程数量
NUMBERS = 5

# 报告详情的模板
_report_detail = {
    "case_id": None,
    "case_name": None,
    "suite_id": None,
    "suite_name": None,
    "methods": None,
    "url": None,  # 本来应该拼接请求方法、域名、协议、端口、资源路径、查询参数，也可以从响应数据中获取URL
    "headers": None,
    "body": None,
    "response_data": None,
    "status_code": None,
    "predict": None,
    "assert_result": None,
    "test_result": None,
    "overtime": None,
}

# 报告概要的模板
_report_summerise = {
    "reportName": None,
    "reportId": None,
    "project_name": None,
    "project_id": None,
    "testCount": None,
    "passCount": None,
    "failedCount": None,
    "passRate": None,
    "conclusion": None,
    "total_time": None,
    "comFrom": None,
    "create_time": None,
    "case_data": None,
}
