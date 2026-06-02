from models import db
from models.user import User
from werkzeug.security import generate_password_hash, check_password_hash


class UserService:

    def register(self, username, password, nickname, phone):
        """用户注册"""
        # 检查用户名是否已存在
        if User.query.filter_by(username=username).first():
            return None, "用户名已存在"

        user = User(
            username=username,
            password=generate_password_hash(password),
            nickname=nickname,
            phone=phone
        )
        db.session.add(user)
        db.session.commit()
        return user, "注册成功"

    def login(self, username, password):
        """用户登录验证"""
        user = User.query.filter_by(username=username).first()
        if user and check_password_hash(user.password, password):
            if user.status == 0:
                return None, "账号已被封禁"
            return user, "登录成功"
        return None, "用户名或密码错误"

    def change_password(self, user_id, old_password, new_password):
        """修改密码"""
        user = User.query.get(user_id)
        if not user or not check_password_hash(user.password, old_password):
            return False, "原密码错误"

        user.password = generate_password_hash(new_password)
        db.session.commit()
        return True, "密码修改成功"

    def get_user_by_id(self, user_id):
        """根据ID获取用户"""
        return User.query.get(user_id)

    def get_all_users(self, page=1, per_page=10):
        """获取所有用户（分页）"""
        pagination = User.query.order_by(User.create_time.desc()).paginate(page=page, per_page=per_page,
                                                                           error_out=False)
        return pagination.items, pagination

    def update_user_status(self, user_id, status):
        """更新用户状态（封禁/解封）"""
        user = User.query.get(user_id)
        if user:
            user.status = status
            db.session.commit()
            return True
        return False

    def delete_user(self, user_id):
        """删除用户"""
        user = User.query.get(user_id)
        if user:
            db.session.delete(user)
            db.session.commit()
            return True
        return False

    def get_user_statistics(self):
        """获取用户统计"""
        total_users = User.query.count()
        active_users = User.query.filter_by(status=1).count()
        admin_users = User.query.filter_by(role='admin').count()
        return {
            'total': total_users,
            'active': active_users,
            'admin': admin_users
        }