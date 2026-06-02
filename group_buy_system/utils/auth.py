from flask_login import LoginManager, current_user
from functools import wraps
from flask import flash, redirect, url_for

login_manager = LoginManager()

@login_manager.user_loader
def load_user(user_id):
    from models.user import User
    return User.query.get(int(user_id))

def admin_required(f):
    """管理员权限装饰器"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role != 'admin':
            flash('需要管理员权限访问', 'danger')
            return redirect(url_for('user_routes.index'))
        return f(*args, **kwargs)
    return decorated_function

def login_required_with_message(f):
    """带消息的登录要求"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            flash('请先登录', 'warning')
            return redirect(url_for('user_routes.login'))
        return f(*args, **kwargs)
    return decorated_function