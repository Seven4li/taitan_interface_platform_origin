# -*- encoding=utf-8 -*-
from flask import request
from flask_login import login_required
from flask_restful import Resource

from backend.app import app
from backend.controller.execute_testcase_controller import ExecuteTestCaseController
from backend.utils.code_utils import CodeUtil
from backend.utils.cron_utils import CronUtil
from backend.utils.exception_utils import REQ_IS_EMPTY_ERROR, REQ_TYPE_ERROR, REQ_KEY_ERROR
from backend.utils.make_response_utils import make_response


class CronJobController:

    @classmethod
    # 新增定时任务
    def add_cron(cls, cron_data):
        job = CronUtil.add_cron(ExecuteTestCaseController.execute_testsuite, cron_data)
        return job

    @classmethod
    # 查询定时任务的详情数据：
    def query_detail(cls, cron_id):
        return CronUtil.query_detail_cron(cron_id)

    @classmethod
    # 搜索定时任务
    def search_cron_by_cronname(cls, cron_name):
        return CronUtil.query_cron_by_name(cron_name)

    @classmethod
    # 查询定时任务列表
    def query_list(cls, page=1, size=10):
        return CronUtil.query_list(page, size)

    @classmethod
    # 修改定时任务
    def modify_cron(cls, cron_data):
        return CronUtil.update_cron(cron_data)

    @classmethod
    # 删除定时任务
    def delete_cron(cls, cron_id):
        return CronUtil.delete_cron(cron_id)


class CronJobService(Resource):
    decorators = [login_required]

    # 查询类操作
    def get(self):
        if not request.args:
            raise REQ_IS_EMPTY_ERROR()
        if not request.args.get("type"):
            raise REQ_KEY_ERROR()

        action_type = request.args.get("type")
        if action_type == "query_detail":
            cron_id = request.args.get("cron_id")  # 获取cron_id
            response_data = CronJobController.query_detail(cron_id)  # 根据cron_id查询定时任务详情
            return make_response(status=CodeUtil.SUCCESS, data=response_data)
        if action_type == "search":
            cron_name = request.args.get("cron_name")  # 获取cron_name
            response_data = CronJobController.search_cron_by_cronname(cron_name)
            return make_response(status=CodeUtil.SUCCESS, data=response_data)
        if action_type == "query_list":
            page = request.args.get("page")
            if page:  # 如果传入了page，那么判断page是不是数字，如果不是数字直接返回查询的空结果
                if page.isdigit():
                    page = int(page)
                else:
                    return make_response(status=CodeUtil.SUCCESS, data=[])
            size = request.args.get("size")
            response_data = CronJobController.query_list(page=1, size=10)
            total_count = len(response_data)
            return make_response(status=CodeUtil.SUCCESS,
                                 data=response_data,
                                 total_count=total_count,
                                 page=page,
                                 size=size)
        # 如果没有满足的if条件，那么返回json数据的结果
        return make_response(status=CodeUtil.SUCCESS)

    # 新增
    def post(self):
        # 公共校验
        if not request.data:
            raise REQ_IS_EMPTY_ERROR()
        if not request.is_json:
            raise REQ_TYPE_ERROR()
        # 添加定时任务
        job = CronJobController.add_cron(request.get_json())
        app.logger.info(f"CronJobService中添加定时任务返回的job为：{job}")
        return make_response(status=CodeUtil.SUCCESS, data=request.get_json())

    # 修改定时任务
    def put(self):
        if not request.data:
            raise REQ_IS_EMPTY_ERROR()
        if not request.is_json:
            raise REQ_TYPE_ERROR()

        # 调用Controller的修改定时任务方法
        job = CronJobController.modify_cron(request.get_json())
        app.logger.info(f"修改定时任务的结果为：{job}")
        return make_response(status=CodeUtil.SUCCESS, data=request.get_json())

    # 删除
    def delete(self):
        if not request.data:
            raise REQ_IS_EMPTY_ERROR()
        if not request.is_json:
            raise REQ_TYPE_ERROR()

        # 删除定时任务
        cron_id = request.get_json().get("cron_id")  # 获取要删除的cron_id
        CronJobController.delete_cron(cron_id)  # 删除定时任务
        return make_response(status=CodeUtil.SUCCESS, data=None)

    # 暂停/恢复定时任务
    def patch(self):
        if not request.data:
            raise REQ_IS_EMPTY_ERROR()
        if not request.is_json:
            raise REQ_TYPE_ERROR()
        action = request.get_json().get("action")  # 获取要进行的动作
        cron_id = request.get_json().get("cron_id")
        app.logger.info(f"暂停和恢复定时任务的cron_id: {cron_id}")
        # 根据action来判断对定时任务状态进行操作
        if action == 0:
            CronUtil.resume_job()  # 恢复全部定时任务
            app.logger.info(f"恢复全部定时任务后的结果为：{CronUtil.scheduler.state}")
        if action == 1:
            CronUtil.resume_job(job_id=cron_id)  # 指定id进行恢复,可以查看对应cron_id的next_run_time有没有恢复即可
        if action == 2:
            CronUtil.pause_cron(job_id=cron_id)  # 指定id进行暂停，可以查看对应cron_id的next_run_time有没有被删除即可
        if action == 3:
            CronUtil.pause_cron()  # 暂停全部定时任务
            app.logger.info(f"暂停全部定时任务后的结果为：{CronUtil.scheduler.state}")
        return make_response(status=CodeUtil.SUCCESS, data=None)
