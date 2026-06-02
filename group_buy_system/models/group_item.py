from models import db


class GroupItem(db.Model):
    __tablename__ = 'group_item'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    group_buy_id = db.Column(db.Integer, db.ForeignKey('group_buy.id'), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    price = db.Column(db.Numeric(10, 2), nullable=False)
    stock = db.Column(db.Integer, nullable=False, default=0)
    remain_stock = db.Column(db.Integer, nullable=False, default=0)
    image = db.Column(db.String(200))

    # 关联关系
    order_items = db.relationship('OrderItem', backref='group_item', lazy=True)

    def to_dict(self):
        return {
            'id': self.id,
            'group_buy_id': self.group_buy_id,
            'name': self.name,
            'price': float(self.price),
            'stock': self.stock,
            'remain_stock': self.remain_stock,
            'image': self.image
        }