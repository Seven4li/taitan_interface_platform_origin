import datetime

from backend.app import db


class TestReportModel(db.Model):
    __tablename__ = 'report_summerise'  # 定义报告的表名是report_summerise

    id = db.Column(db.INTEGER, autoincrement=True)
    reportName = db.Column(db.String(100), nullable=False)
    reportId = db.Column(db.String(100), nullable=False)
    project_id = db.Column(db.INTEGER, autoincrement=True)
    project_name = db.Column(db.String(100), nullable=True)
    testCount = db.Column(db.INTEGER, nullable=True)
    passCount = db.Column(db.INTEGER, nullable=True)
    failedCount = db.Column(db.INTEGER, nullable=True)
    passRate = db.Column(db.String(20), nullable=True)
    conclusion = db.Column(db.String(20), nullable=True)
    total_time = db.Column(db.String(100), nullable=True)
    comFrom = db.Column(db.String(100), nullable=True)
    case_data = db.Column(db.JSON, nullable=True)
    create_time = db.Column(db.DateTime, default=datetime.datetime.now(), nullable=True)
    update_time = db.Column(db.DateTime, nullable=True)
    db.PrimaryKeyConstraint(id)

    def __repr__(self):
        return '<TestReportModel> %r' % self.project_name

    def to_dict(self):
        return {tcm.name: getattr(self, tcm.name) for tcm in TestReportModel.__table__.columns}

