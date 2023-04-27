import datetime
from backend.app import db


class TestCaseModel(db.Model):
    __tablename__ = 'test_case'  # 定义表名是test_case

    id = db.Column(db.INTEGER, autoincrement=True)
    case_name = db.Column(db.String(100), nullable=False)
    method = db.Column(db.String(20), nullable=False)  # 接口的请求方法
    protocal = db.Column(db.String(20), default="HTTP", nullable=False)  # 协议
    host = db.Column(db.String(50), nullable=False)  # 域名
    port = db.Column(db.INTEGER, nullable=True)  # 端口
    path = db.Column(db.String(100), default='/', nullable=True)  # 资源路径
    params = db.Column(db.String(100), nullable=True)  # 查询参数
    headers = db.Column(db.String(500), nullable=True)  # 请求头
    body = db.Column(db.String(500), nullable=True)  # 请求体
    description = db.Column(db.String(500), nullable=True)  # 描述信息

    predict = db.Column(db.String(500), nullable=True)  # 预期数据

    suite_id = db.Column(db.INTEGER, db.ForeignKey('test_suite.id'), nullable=True)  # 外键关联测试计划的id
    suite = db.relationship('TestSuiteModel', backref=db.backref('test_case', lazy='dynamic'))  # 关联测试计划

    isDeleted = db.Column(db.String(1), default='0')
    status = db.Column(db.String(1), default='1', nullable=True)
    create_time = db.Column(db.DateTime, default=datetime.datetime.now(), nullable=True)
    update_time = db.Column(db.DateTime, nullable=True)
    operation = db.Column(db.String(20), nullable=True)

    db.PrimaryKeyConstraint(id)

    def __repr__(self):
        return '<TestCaseModel> %r' % self.case_name

    def to_dict(self):
        return {tcm.name: getattr(self, tcm.name) for tcm in TestCaseModel.__table__.columns}
