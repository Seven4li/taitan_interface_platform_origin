import datetime

from backend.app import db


class UserModel(db.Model):
    __tablename__ = 'users'  # ���������users

    id = db.Column(db.INTEGER, autoincrement=True)  # ����id
    username = db.Column(db.String(100), nullable=False)  # �û���
    password = db.Column(db.String(100), nullable=True)  # ����
    nick_name = db.Column(db.String(100), nullable=True)  # �ǳ�
    role_id = db.Column(db.String(10), nullable=True)  # ��ɫ

    isDeleted = db.Column(db.String(1), default='0')  # ɾ��״̬
    status = db.Column(db.String(1), default='1', nullable=True)  # ����״̬
    create_time = db.Column(db.DateTime, default=datetime.datetime.now(), nullable=True)  # ����ʱ��
    update_time = db.Column(db.DateTime, nullable=True)  # �޸�ʱ��

    db.PrimaryKeyConstraint(id)

    def __repr__(self):
        return '<UserModel> %r' % self.username

    def to_dict(self):
        return {tcm.name: getattr(self, tcm.name) for tcm in UserModel.__table__.columns}
