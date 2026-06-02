from flask import Blueprint

user_bp = Blueprint('user_routes', __name__, url_prefix='/')
group_bp = Blueprint('group_routes', __name__, url_prefix='/group')
order_bp = Blueprint('order_routes', __name__, url_prefix='/order')
admin_bp = Blueprint('admin_routes', __name__, url_prefix='/admin')