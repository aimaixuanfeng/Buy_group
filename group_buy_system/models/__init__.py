from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

# 导入所有模型，确保创建表时被注册
from models.user import User
from models.category import Category
from models.group_buy import GroupBuy
from models.group_item import GroupItem
from models.order import Order
from models.order_item import OrderItem
from models.notice import Notice