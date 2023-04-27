# -*- encoding=utf-8 -*-
import datetime
import pickle
from datetime import timedelta

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.date import DateTrigger
from pytz import timezone

from backend.app import db, app
from backend.controller.execute_testcase_controller import ExecuteTestCaseController

from apscheduler.triggers.interval import IntervalTrigger
from backend.models.cron_jobs import CronJobsModel


def _deal_crondata(cron_detail_data):
    blob_data = cron_detail_data.job_state  # 提取数据库中的job_state的数据，它是一个blob数据
    result = pickle.loads(blob_data)  # 使用pickle解析blob数据
    app.logger.info(f"pickle.loads(blob_data): {result}")
    # 获取要返回的触发器数据
    trigger = result.get("trigger")
    app.logger.info(f"触发器trriger的类型为：{type(trigger)}")

    cron_type = None
    interval_time = None
    start_date = None
    timezone = "Asia/Shanghai"
    run_date = None
    if issubclass(type(trigger), DateTrigger):
        cron_type = 'date'
        run_date = str(trigger.run_date)
    if issubclass(type(trigger), IntervalTrigger):
        app.logger.info(f"进入了IntervalTrigger条件")
        cron_type = 'interval'
        interval_time = str(trigger.interval.total_seconds())  # 获取间隔时间
        start_date = str(trigger.start_date)  # 获取开始时间
        timezone = str(trigger.timezone)  # 获取时区域
    response_data = {
        "cron_id": cron_detail_data.id,
        "cron_name": cron_detail_data.cron_name,
        "project_id": result.get("args")[0].get("project_id"),
        "project_name": result.get("args")[0].get("project_name"),
        "env_id": result.get("args")[0].get("env_id"),
        "suite_id_list": result.get("args")[0].get("suite_id_list"),
        "executionMode": result.get("args")[0].get("executionMode"),
        "trigger": {
            "cron_type": cron_type,
            "interval_time": interval_time,
            "start_date": start_date,
            "timezone": timezone,
            "run_date": run_date
        },
        "next_run_time": str(result.get("next_run_time"))
    }
    return response_data

class CronUtil:
    # 定义调度器
    scheduler = BackgroundScheduler({
        'apscheduler.jobstores.default': {
            'type': 'sqlalchemy',
            'url': 'mysql+pymysql://root:123456@10.1.201.231:3307/taitan_interface_platform?charset=utf8',
            'tablename': 'cron_jobs'
        },
        'apscheduler.executors.default': {
            'class': 'apscheduler.executors.pool:ThreadPoolExecutor',
            'max_workers': '20'
        },
        'apscheduler.executors.processpool': {
            'type': 'processpool',
            'max_workers': '5'
        },
        'apscheduler.job_defaults.coalesce': 'false',
        'apscheduler.job_defaults.max_instances': '10',
        'apscheduler.timezone': timezone('Asia/Shanghai'),
    })

    @classmethod
    # 实现添加定时任务
    def add_cron(cls, func, cron_data):
        cron_type = cron_data.get("cronTab").get("cronType")  # 获取触发器
        # 定义执行测试套件所需要的数据
        testsuite_data = {
            "project_id": cron_data.get("project_id"),
            "env_id": cron_data.get("env_id"),
            "project_name": cron_data.get("project_name"),
            "suite_id_list": cron_data.get("suite_id_list"),
            "executionMode": cron_data.get("executionMode")
        }
        # 定义要返回的job
        job = None
        if cron_type == 'date':
            # 获取指定的日期
            run_date = cron_data.get("cronTab").get("date_list").get("run_date")
            # 添加触发器类型为date的job
            job = cls.scheduler.add_job(func,
                                        trigger='date',
                                        run_date=run_date,
                                        args=(testsuite_data,),
                                        replace_existing=True, coalesce=True)
            app.logger.info(f"添加date类型的触发器，调度器add_job之后，返回的job中的job.id的值为：{job.id}")

        if cron_type == 'interval':
            # 获取触发的间隔事件
            seconds = cron_data.get("cronTab").get("interval_list").get("seconds")
            # 添加触发器类型为intervale的job
            job = cls.scheduler.add_job(func,
                                        trigger='interval',
                                        seconds=int(seconds),
                                        args=(testsuite_data,),
                                        replace_existing=True, coalesce=True)
            app.logger.info(f"添加interval类型的触发器，调度器add_job之后，返回的job中的job.id的值为：{job.id}")

        if cron_type == 'cron':
            # 添加触发器类型为cron的job
            pass

        # 添加定时任务的名称
        cron_name = cron_data.get("cron_name")  # 获取定时任务的名称
        create_time = str(datetime.datetime.now()) # 获取当前的时间
        CronJobsModel.query.filter_by(id=job.id).update({"cron_name": cron_name,
                                                         "create_time":create_time})  # 添加定时任务的名称和时间
        db.session.commit()
        db.session.close()
        return job

    @classmethod
    # 实现修改定时任务
    # scheduler.modify_job(job_id="xxx", trigger="xxx", args=(testsuite_data,))
    def update_cron(cls, cron_data):
        cron_id = cron_data.get("id")  # 获取定时任务的id
        cron_type = cron_data.get("cronTab").get("cronType")  # 获取要修改的触发器
        modify_data = {
            "project_id": cron_data.get("project_id"),
            "env_id": cron_data.get("env_id"),
            "project_name": cron_data.get("project_name"),
            "suite_id_list": cron_data.get("suite_id_list"),
            "executionMode": cron_data.get("executionMode")
        }
        # 定义修改之后的job
        job = None
        if cron_type == 'date':
            run_date = cron_data.get("cronTab").get("date_list").get("run_date")  # 执行的指定日期
            job = cls.scheduler.modify_job(job_id=cron_id,
                                           trigger=DateTrigger(run_date=run_date),
                                           args=(modify_data,)
                                           )

        if cron_type == 'interval':
            seconds = cron_data.get("cronTab").get("interval_list").get("seconds")  # 获取触发间隔的秒
            job = cls.scheduler.modify_job(job_id=cron_id,
                                           trigger=IntervalTrigger(seconds=int(seconds)),
                                           args=(modify_data,)
                                           )

        if cron_type == 'cron':
            pass

        cls.scheduler.pause_job(job_id=cron_id)  # 暂停定时任务
        job = cls.scheduler.resume_job(job_id=cron_id)  # 恢复定时任务，通过暂停和恢复，更新定时任务的内部时间
        app.logger.info(f"修改定时任务触发间隔、传递给作业的参数的结果为：{job}")
        # 修改定时任务名称
        cron_name = cron_data.get("cron_name")  # 获取定时任务的名称
        CronJobsModel.query.filter_by(id=job.id).update({"cron_name": cron_name})  # 添加定时任务的名称
        db.session.commit()
        db.session.close()
        return job

    # 查询定时任务详情
    @classmethod
    def query_detail_cron(cls, cron_id):
        # 根据cron_id查询数据库中的结果
        cron_deatail_data = CronJobsModel.query.filter_by(id=cron_id).first()
        app.logger.info(f"查询定时任务详情的数据为：{cron_deatail_data}")
        # 提取结果，并组合成需要的响应数据
        response_data = _deal_crondata(cron_deatail_data) # 使用封装的处理cron_data数据的方法，来构造要返回的响应数据
        return response_data

    # 查询定时任务列表
    @classmethod
    def query_list(cls, page=1, size=10):
        all_data = CronJobsModel.query \
            .slice((page - 1) * size, page * size) \
            .all()
        app.logger.info(f"查询的定时任务列表为：{all_data}")
        response_list = []
        for cron_data in all_data:
            # 提取结果，并组合成需要的响应数据
            response_data = _deal_crondata(cron_data)  # 使用封装的处理cron_data数据的方法，来构造要返回的响应数据
            response_list.append(response_data)
        app.logger.info(f"查询的定时任务列表转化为json之后：{response_list}")  # 把job_state中的所需要的数据提取出来，放在字典中
        return response_list

    # 搜索定时任务
    @classmethod
    def query_cron_by_name(cls, cron_name):
        # 根据定时任务名称，搜索测定时任务
        cron_data_list = CronJobsModel.query.filter(CronJobsModel.cron_name.like(f'%{cron_name}%')).all()
        app.logger.info(f"根据定时任务名称 [{cron_name}] 搜索出来的数据有：{cron_data_list}")
        response_list = []
        for cron_data in cron_data_list:
            # 提取结果，并组合成需要的响应数据
            response_data = _deal_crondata(cron_data)  # 使用封装的处理cron_data数据的方法，来构造要返回的响应数据
            response_list.append(response_data)
        app.logger.info(f"搜索的定时任务列表转化为json之后：{response_list}")  # 把job_state中的所需要的数据提取出来，放在字典中

        return response_list

    # 开始定时任务
    @classmethod
    def start_cron(cls, paused=False):
        app.logger.info(f"开始定时任务")
        cls.scheduler.start(paused=paused)  # paused=True时，会启动所有定时任务，但是定时任务的状态是暂停状态

    # 暂停定时任务
    @classmethod
    def pause_cron(cls, job_id=None):
        if job_id is None:
            app.logger.info("暂停所有定时任务")
            cls.scheduler.pause()  # 暂停全部定时任务
        else:
            app.logger.info(f"暂停指定的定时任务id的任务：{job_id}")
            cls.scheduler.pause_job(job_id=job_id)  # 暂停指定的定时任务id的任务

    # 恢复定时任务
    @classmethod
    def resume_job(cls, job_id=None):
        if job_id is None:
            app.logger.info("恢复所有定时任务")
            cls.scheduler.resume()  # 恢复全部定时任务
        else:
            app.logger.info(f"恢复指定的定时任务：{job_id}")
            cls.scheduler.resume_job(job_id=job_id)  # 恢复指定的定时任务

    # 关闭定时任务
    @classmethod
    def shutdown_cron(cls, wait=True):
        app.logger.info("关闭定时任务")
        cls.scheduler.shutdown(wait=wait)  # wait=True 要等待定时任务执行完成后，再shutdown

    # 删除定时任务
    @classmethod
    def delete_cron(cls, job_id=None):
        if job_id is None:
            app.logger.info("删除所有定时任务")
            cls.scheduler.remove_all_jobs()  # 删除所有定时任务
        else:
            app.logger.info(f"删除指定的定时任务：{job_id}")
            cls.scheduler.remove_job(job_id=job_id)  # 删除指定的定时任务

    # 查询job
    @classmethod
    def get_job(cls, job_id=None):
        if job_id is None:
            return cls.scheduler.get_jobs()
        else:
            return cls.scheduler.get_job(job_id=job_id)


if __name__ == '__main__':
    # result = CronUtil.query_detail_cron("e715da20ab5142309959e381ea7a9997")
    # print("result ", result)
    # result = CronUtil.query_list(page=1,size=10)
    # print(result)
    # 搜索
    result = CronUtil.query_cron_by_name("定时任务")
    print("result:", result)
