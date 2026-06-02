from services.user_service import UserService
from services.group_service import GroupService
from services.order_service import OrderService
from services.inventory_service import inventory_service  # 直接导入实例
from services.auth_service import AuthService

user_service = UserService()
group_service = GroupService()
order_service = OrderService()
inventory_service = inventory_service
auth_service = AuthService()

__all__ = [
    'user_service',
    'group_service',
    'order_service',
    'inventory_service',
    'auth_service'
]