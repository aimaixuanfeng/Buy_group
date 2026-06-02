from models import db
from datetime import datetime


class Order(db.Model):
    __tablename__ = 'orders'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    group_buy_id = db.Column(db.Integer, db.ForeignKey('group_buy.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    total_price = db.Column(db.Numeric(10, 2), nullable=False)
    status = db.Column(db.String(20), default='pending')
    # 状态: pending(待确认), confirmed(已确认参与), completed(已完成), cancelled, group_cancelled
    cancel_time = db.Column(db.DateTime)
    create_time = db.Column(db.DateTime, default=datetime.now)

    order_items = db.relationship('OrderItem', backref='order', lazy=True, cascade='all, delete-orphan')

    def to_dict(self):
        return {
            'id': self.id,
            'group_buy_id': self.group_buy_id,
            'group_title': self.group_buy.title if self.group_buy else '',
            'user_id': self.user_id,
            'user_name': self.user.nickname if self.user else '',
            'total_price': float(self.total_price),
            'status': self.status,
            'create_time': self.create_time.strftime('%Y-%m-%d %H:%M:%S')
        }