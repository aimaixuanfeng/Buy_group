from models import db


class OrderItem(db.Model):
    __tablename__ = 'order_item'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    order_id = db.Column(db.Integer, db.ForeignKey('orders.id'), nullable=False)
    group_item_id = db.Column(db.Integer, db.ForeignKey('group_item.id'), nullable=False)
    quantity = db.Column(db.Integer, nullable=False, default=1)
    subtotal = db.Column(db.Numeric(10, 2), nullable=False)

    def to_dict(self):
        return {
            'id': self.id,
            'order_id': self.order_id,
            'group_item_id': self.group_item_id,
            'item_name': self.group_item.name if self.group_item else '',
            'price': float(self.group_item.price) if self.group_item else 0,
            'quantity': self.quantity,
            'subtotal': float(self.subtotal)
        }