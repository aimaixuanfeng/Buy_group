from models import db
from datetime import datetime
import json

class GroupBuy(db.Model):
    __tablename__ = 'group_buy'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    category_id = db.Column(db.Integer, db.ForeignKey('category.id'), nullable=False)
    creator_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    pickup_location = db.Column(db.String(200), nullable=False)
    deadline = db.Column(db.DateTime, nullable=False)
    status = db.Column(db.String(20), default='active')
    # 状态: active, waiting_confirmation, procuring, shipped, completed, failed, cancelled
    cancel_reason = db.Column(db.String(200))
    cancel_time = db.Column(db.DateTime)
    image = db.Column(db.String(200))
    create_time = db.Column(db.DateTime, default=datetime.now)

    all_confirmed = db.Column(db.Boolean, default=False)
    procurement_photos = db.Column(db.Text, default='[]')  # 存储JSON数组
    shipped_time = db.Column(db.DateTime)
    sold_out_time = db.Column(db.DateTime)

    items = db.relationship('GroupItem', backref='group_buy', lazy=True, cascade='all, delete-orphan')
    orders = db.relationship('Order', backref='group_buy', lazy=True)

    def get_procurement_photos(self):
        if self.procurement_photos:
            try:
                return json.loads(self.procurement_photos)
            except:
                return []
        return []

    def add_procurement_photo(self, photo_path):
        photos = self.get_procurement_photos()
        photos.append(photo_path)
        self.procurement_photos = json.dumps(photos)
        db.session.commit()

    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'category_id': self.category_id,
            'category_name': self.category.name if self.category else '',
            'creator_id': self.creator_id,
            'creator_name': self.creator.nickname if self.creator else '',
            'pickup_location': self.pickup_location,
            'deadline': self.deadline.strftime('%Y-%m-%d %H:%M:%S'),
            'status': self.status,
            'image': self.image,
            'create_time': self.create_time.strftime('%Y-%m-%d %H:%M:%S'),
            'all_confirmed': self.all_confirmed,
            'procurement_photos': self.get_procurement_photos(),
            'shipped_time': self.shipped_time.strftime('%Y-%m-%d %H:%M:%S') if self.shipped_time else None,
            'sold_out_time': self.sold_out_time.strftime('%Y-%m-%d %H:%M:%S') if self.sold_out_time else None
        }