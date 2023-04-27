from backend.app import db, api, app
from backend.models.test_project_model import TestProjectModel
from backend.models.test_suite_model import TestSuiteModel
from backend.models.test_case_model import TestCaseModel
from backend.models.test_report_model import TestReportModel
from backend.models.cron_jobs import CronJobsModel
from backend.models.test_env_model import TestEnvModel
from backend.models.test_env_params_model import TestEnvParamsModel
from backend.models.user_model import UserModel
from backend.controller.test_helloworld import IndexService
from backend.controller.test_project_controller import TestProjectService
from backend.controller.test_suite_controller import TestSuiteService
from backend.controller.test_case_controller import TestCaseService
from backend.controller.execute_testcase_controller import ExecuteTestCaseService
from backend.controller.cron_job_controller import CronJobService
from backend.controller.test_env_controller import TestEnvService
from backend.controller.test_env_params_controller import TestEnvParamsService
from backend.controller.user_controller import UserService, LoginService, LogoutService
from backend.controller.test_report_controller import TestReportService

if __name__ == '__main__':
    # db.drop_all()
    db.create_all()
    # 由于CronUtil中使用了db和app，所以先让db和app运行之后，再导入CronUtil，这样能够避免循环导包出现的问题
    import backend.utils.cron_utils
    # 启动定时任务
    backend.utils.cron_utils.CronUtil.start_cron()
    # 创建路由
    api.add_resource(IndexService, '/')
    api.add_resource(TestProjectService, '/api/testproject')
    api.add_resource(TestSuiteService, '/api/testsuite')
    api.add_resource(TestCaseService, '/api/testcase')
    api.add_resource(ExecuteTestCaseService, '/api/run/testcase')
    api.add_resource(CronJobService, '/api/cron')
    api.add_resource(TestEnvService, '/api/env')
    api.add_resource(TestEnvParamsService, '/api/env/params')
    api.add_resource(UserService, '/api/user')
    api.add_resource(LoginService, '/api/login')
    api.add_resource(LogoutService, '/api/logout')
    api.add_resource(TestReportService, '/api/test_report')
    # 启动flask
    app.run(debug=True, use_reloader=True)
