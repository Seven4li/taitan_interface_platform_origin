import datetime

from backend.app import db


class UserModel(db.Model):
    __tablename__ = 'users'  # 定义表名是users

    id = db.Column(db.INTEGER, autoincrement=True)  # 主键id
    username = db.Column(db.String(100), nullable=False)  # 用户名
    password = db.Column(db.String(100), nullable=True)  # 密码
    nick_name = db.Column(db.String(100), nullable=True)  # 昵称
    role_id = db.Column(db.String(10), nullable=True)  # 角色

    isDeleted = db.Column(db.String(1), default='0')  # 删除状态
    status = db.Column(db.String(1), default='1', nullable=True)  # 禁用状态
    create_time = db.Column(db.DateTime, default=datetime.datetime.now(), nullable=True)  # 创建时间
    update_time = db.Column(db.DateTime, nullable=True)  # 修改时间

    db.PrimaryKeyConstraint(id)

    def __repr__(self):
        return '<UserModel> %r' % self.username

    def to_dict(self):
        return {tcm.name: getattr(self, tcm.name) for tcm in UserModel.__table__.columns}
