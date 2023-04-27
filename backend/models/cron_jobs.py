import datetime

from backend.app import db


class CronJobsModel(db.Model):
    __tablename__ = 'cron_jobs'  # 设置表名
    # 字段
    id = db.Column(db.String(191), unique=True, primary_key=True)
    next_run_time = db.Column(db.Float(25), unique=False, nullable=True)
    job_state = db.Column(db.BLOB, unique=False, nullable=True)
    cron_name = db.Column(db.String(100))  # 定时任务的名称
    create_time = db.Column(db.DateTime, default=datetime.datetime.now(), nullable=True)

    def __repr__(self):
        return '<CronJobsModel> %r' % self.id
