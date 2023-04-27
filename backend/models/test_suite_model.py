import datetime
from backend.app import db


class TestSuiteModel(db.Model):
    __tablename__ = 'test_suite'  # 定义表名是test_suite

    id = db.Column(db.INTEGER, autoincrement=True)
    suite_name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.String(500), nullable=True)

    project_id = db.Column(db.INTEGER,db.ForeignKey('test_project.id'), nullable=True) # 外键关联测试计划的id
    project = db.relationship('TestProjectModel', backref=db.backref('test_suite', lazy='dynamic')) # 关联测试计划

    isDeleted = db.Column(db.String(1), default='0')
    status = db.Column(db.String(1), default='1', nullable=True)
    create_time = db.Column(db.DateTime, default=datetime.datetime.now(), nullable=True)
    update_time = db.Column(db.DateTime, nullable=True)
    operation = db.Column(db.String(20), nullable=True)

    db.PrimaryKeyConstraint(id)

    def __repr__(self):
        return '<TestSuiteModel> %r' % self.suite_name

    def to_dict(self):
        return {tcm.name: getattr(self, tcm.name) for tcm in TestSuiteModel.__table__.columns}
