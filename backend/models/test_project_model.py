import datetime

from backend.app import db


class TestProjectModel(db.Model):
    __tablename__ = 'test_project'  # 定义表名是test_project

    id = db.Column(db.INTEGER, autoincrement=True)
    project_name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.String(500), nullable=True)

    isDeleted = db.Column(db.String(1), default='0')
    status = db.Column(db.String(1), default='1', nullable=True)
    create_time = db.Column(db.DateTime, default=datetime.datetime.now(), nullable=True)
    update_time = db.Column(db.DateTime, nullable=True)
    operation = db.Column(db.String(20), nullable=True)
    db.PrimaryKeyConstraint(id)

    def __repr__(self):
        return '<TestProjectModel> %r' % self.project_name

    def to_dict(self):
        return {tcm.name: getattr(self, tcm.name) for tcm in TestProjectModel.__table__.columns}
