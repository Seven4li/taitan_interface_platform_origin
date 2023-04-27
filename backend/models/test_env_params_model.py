import datetime

from backend.app import db


class TestEnvParamsModel(db.Model):
    __tablename__ = 'test_env_params'  # ���������test_env

    id = db.Column(db.INTEGER, autoincrement=True) # �����������id
    params_key = db.Column(db.String(100), nullable=False) # ������
    params_value = db.Column(db.String(100), nullable=False)  # ����ֵ
    description = db.Column(db.String(500), nullable=True) # ����������

    env_id = db.Column(db.INTEGER, db.ForeignKey('test_env.id'), nullable=True)  # �����������������id
    environment = db.relationship('TestEnvModel', backref=db.backref('test_env', lazy='dynamic')) # ��������


    isDeleted = db.Column(db.String(1), default='0')
    status = db.Column(db.String(1), default='1', nullable=True)
    create_time = db.Column(db.DateTime, default=datetime.datetime.now(), nullable=True)
    update_time = db.Column(db.DateTime, nullable=True)
    operation = db.Column(db.String(20), nullable=True)
    db.PrimaryKeyConstraint(id)

    def __repr__(self):
        return '<TestEnvParamsModel> %r' % self.params_key

    def to_dict(self):
        return {tcm.name: getattr(self, tcm.name) for tcm in TestEnvParamsModel.__table__.columns}
