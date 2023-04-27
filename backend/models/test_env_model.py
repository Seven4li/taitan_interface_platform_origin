import datetime

from backend.app import db


class TestEnvModel(db.Model):
    __tablename__ = 'test_env'  # ���������test_env

    id = db.Column(db.INTEGER, autoincrement=True) # ������id
    env_name = db.Column(db.String(100), nullable=False) # ����������
    description = db.Column(db.String(500), nullable=True) # ����������

    isDeleted = db.Column(db.String(1), default='0')
    status = db.Column(db.String(1), default='1', nullable=True)
    create_time = db.Column(db.DateTime, default=datetime.datetime.now(), nullable=True)
    update_time = db.Column(db.DateTime, nullable=True)
    operation = db.Column(db.String(20), nullable=True)
    db.PrimaryKeyConstraint(id)

    def __repr__(self):
        return '<TestEnvModel> %r' % self.env_name

    def to_dict(self):
        return {tcm.name: getattr(self, tcm.name) for tcm in TestEnvModel.__table__.columns}
