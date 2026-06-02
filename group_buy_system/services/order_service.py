from models import db
from models.order import Order
from models.order_item import OrderItem
from models.group_item import GroupItem
from services.inventory_service import inventory_service
from datetime import datetime, timedelta

class OrderService:

    def create_order(self, user_id, group_buy_id, items):
        # 1秒内防重复
        recent = Order.query.filter(
            Order.group_buy_id == group_buy_id,
            Order.user_id == user_id,
            Order.create_time >= datetime.now() - timedelta(seconds=1)
        ).first()
        if recent:
            return None, "操作过于频繁，请稍后再试"

        # 检查拼单是否存在、是否已截止、是否可下单
        from models.group_buy import GroupBuy
        group = GroupBuy.query.get(group_buy_id)
        if not group:
            return None, "拼单不存在"
        if datetime.now() >= group.deadline:
            return None, "拼单已截止，无法下单"
        if group.status != 'active':
            return None, "拼单当前不可下单"

        for item in items:
            success, msg = inventory_service.check_stock(item['item_id'], item['quantity'])
            if not success:
                return None, msg

        total_price = 0
        order_items_data = []
        for item in items:
            group_item = GroupItem.query.get(item['item_id'])
            subtotal = float(group_item.price) * item['quantity']
            total_price += subtotal
            order_items_data.append({
                'group_item': group_item,
                'quantity': item['quantity'],
                'subtotal': subtotal
            })

        order = Order(
            group_buy_id=group_buy_id,
            user_id=user_id,
            total_price=total_price,
            status='pending'
        )
        db.session.add(order)
        db.session.flush()

        for data in order_items_data:
            order_item = OrderItem(
                order_id=order.id,
                group_item_id=data['group_item'].id,
                quantity=data['quantity'],
                subtotal=data['subtotal']
            )
            db.session.add(order_item)
            inventory_service.deduct_stock(data['group_item'].id, data['quantity'])

        db.session.commit()

        # 发起人下单自动确认
        if user_id == group.creator_id:
            order.status = 'confirmed'
            db.session.commit()

        # 检查售空并可能进入等待确认
        from services import group_service
        group_service.check_sold_out_and_start_confirmation(group_buy_id)

        return order, "订单创建成功"

    def cancel_order(self, order_id, is_group_cancel=False):
        order = Order.query.get(order_id)
        if not order:
            return False, "订单不存在"
        if order.status not in ['pending', 'confirmed']:
            return False, "订单状态无法取消"
        for order_item in order.order_items:
            inventory_service.restore_stock(order_item.group_item_id, order_item.quantity)
        if is_group_cancel:
            order.status = 'group_cancelled'
        else:
            order.status = 'cancelled'
        order.cancel_time = datetime.now()
        db.session.commit()
        return True, "订单已取消"

    def get_user_orders(self, user_id, page=1, per_page=10):
        pagination = Order.query.filter_by(user_id=user_id).order_by(Order.create_time.desc()).paginate(page=page, per_page=per_page, error_out=False)
        return pagination.items, pagination

    def get_order_by_id(self, order_id):
        return Order.query.get(order_id)

    def get_all_orders(self, page=1, per_page=10, status=None):
        query = Order.query
        if status:
            query = query.filter_by(status=status)
        pagination = query.order_by(Order.create_time.desc()).paginate(page=page, per_page=per_page, error_out=False)
        return pagination.items, pagination

    def get_order_statistics(self):
        total_orders = Order.query.count()
        pending_orders = Order.query.filter_by(status='pending').count()
        completed_orders = Order.query.filter_by(status='completed').count()
        cancelled_orders = Order.query.filter(Order.status.in_(['cancelled', 'group_cancelled'])).count()
        from models import db
        total_sales = db.session.query(db.func.sum(Order.total_price)).filter(Order.status == 'completed').scalar() or 0
        return {
            'total': total_orders,
            'pending': pending_orders,
            'completed': completed_orders,
            'cancelled': cancelled_orders,
            'total_sales': float(total_sales)
        }

    def confirm_order(self, order_id):
        order = Order.query.get(order_id)
        if order and order.status == 'pending':
            order.status = 'completed'
            db.session.commit()
            return True
        return False

    def confirm_participation(self, order_id):
        order = Order.query.get(order_id)
        if not order:
            return False, "订单不存在"
        if order.status != 'pending':
            return False, "订单已确认或已取消"
        group = order.group_buy
        if group.status != 'waiting_confirmation':
            return False, "当前拼单不在等待确认阶段"
        order.status = 'confirmed'
        db.session.commit()
        from services import group_service
        if group_service.check_all_participants_confirmed(group.id):
            group.status = 'procuring'
            db.session.commit()
        return True, "确认成功，等待发起人采购"

    def confirm_receipt(self, order_id):
        order = Order.query.get(order_id)
        if not order:
            return False, "订单不存在"
        if order.status != 'confirmed':
            return False, "订单未处于待取货状态"
        group = order.group_buy
        if group.status != 'shipped':
            return False, "发起人尚未标记送达，请耐心等待"
        order.status = 'completed'
        db.session.commit()
        all_completed = not Order.query.filter(
            Order.group_buy_id == group.id,
            Order.status != 'completed'
        ).first()
        if all_completed:
            group.status = 'completed'
            db.session.commit()
        return True, "取货确认成功"

# 单例
order_service = OrderService()