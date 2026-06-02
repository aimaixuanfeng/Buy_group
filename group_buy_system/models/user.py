from models import db
from datetime import datetime
from flask_login import UserMixin


class User(UserMixin, db.Model):
    __tablename__ = 'user'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    nickname = db.Column(db.String(50), nullable=False)
    phone = db.Column(db.String(20), nullable=False)
    avatar = db.Column(db.String(200), default='/static/images/default_avatar.png')
    role = db.Column(db.String(20), default='user')  # user, admin
    status = db.Column(db.Integer, default=1)  # 1:正常 0:封禁
    create_time = db.Column(db.DateTime, default=datetime.now)

    # 关联关系
    group_buys = db.relationship('GroupBuy', backref='creator', lazy=True, foreign_keys='GroupBuy.creator_id')
    orders = db.relationship('Order', backref='user', lazy=True)

    def to_dict(self):
        return {
            'id': self.id,
            'username': self.username,
            'nickname': self.nickname,
            'phone': self.phone,
            'avatar': self.avatar,
            'role': self.role,
            'status': self.status,
            'create_time': self.create_time.strftime('%Y-%m-%d %H:%M:%S')
        }