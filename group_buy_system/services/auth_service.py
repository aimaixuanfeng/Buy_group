from flask_login import login_user, logout_user, current_user


class AuthService:

    def authenticate(self, user):
        """登录认证"""
        if user:
            login_user(user, remember=True)
            return True
        return False

    def logout(self):
        """登出"""
        logout_user()

    def is_admin(self):
        """检查当前用户是否为管理员"""
        return current_user.is_authenticated and current_user.role == 'admin'

    def get_current_user(self):
        """获取当前用户"""
        return current_user if current_user.is_authenticated else None