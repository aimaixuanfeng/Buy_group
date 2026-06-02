from models import db
from models.group_buy import GroupBuy
from models.group_item import GroupItem
from models.category import Category
from models.order import Order
from services.order_service import order_service
from datetime import datetime
import logging


class GroupService:

    def create_group(self, creator_id, title, description, category_id, pickup_location, deadline, image, items_data):
        # 校验截止时间不能早于当前时间
        if deadline and deadline <= datetime.now():
            raise ValueError("截止时间必须晚于当前时间")

        group = GroupBuy(
            creator_id=creator_id,
            title=title,
            description=description,
            category_id=category_id,
            pickup_location=pickup_location,
            deadline=deadline,
            image=image,
            status='active'
        )
        db.session.add(group)
        db.session.flush()
        for item in items_data:
            group_item = GroupItem(
                group_buy_id=group.id,
                name=item['name'],
                price=float(item['price']),
                stock=int(item['stock']),
                remain_stock=int(item['stock'])
            )
            db.session.add(group_item)
        db.session.commit()
        return group

    def update_group(self, group_id, **kwargs):
        group = GroupBuy.query.get(group_id)
        if not group:
            return None

        # 如果更新截止时间，需要校验
        if 'deadline' in kwargs and kwargs['deadline'] is not None:
            if kwargs['deadline'] <= datetime.now():
                raise ValueError("截止时间必须晚于当前时间")

        allowed_fields = ['title', 'description', 'pickup_location', 'deadline', 'image']
        for field in allowed_fields:
            if field in kwargs and kwargs[field] is not None:
                setattr(group, field, kwargs[field])
        db.session.commit()
        return group

    def cancel_group(self, group_id, cancel_reason=''):
        group = GroupBuy.query.get(group_id)
        if not group or group.status != 'active':
            return False, "拼单不存在或状态异常"
        orders = Order.query.filter_by(group_buy_id=group_id, status='pending').all()
        for order in orders:
            order_service.cancel_order(order.id, is_group_cancel=True)
        group.status = 'cancelled'
        group.cancel_reason = cancel_reason
        group.cancel_time = datetime.now()
        db.session.commit()
        return True, "拼单已取消"

    def delete_group(self, group_id):
        group = GroupBuy.query.get(group_id)
        if group:
            db.session.delete(group)
            db.session.commit()
            return True
        return False

    def get_active_groups(self, page=1, per_page=10, category_id=None, keyword=None):
        query = GroupBuy.query.filter(GroupBuy.status == 'active')
        if category_id:
            query = query.filter_by(category_id=category_id)
        if keyword:
            query = query.filter(GroupBuy.title.contains(keyword) | GroupBuy.description.contains(keyword))
        query = query.order_by(GroupBuy.create_time.desc())
        pagination = query.paginate(page=page, per_page=per_page, error_out=False)
        return pagination.items, pagination

    def get_group_by_id(self, group_id):
        return GroupBuy.query.get(group_id)

    def get_groups_by_creator(self, creator_id, page=1, per_page=10):
        pagination = GroupBuy.query.filter_by(creator_id=creator_id).order_by(GroupBuy.create_time.desc()).paginate(
            page=page, per_page=per_page, error_out=False)
        return pagination.items, pagination

    def get_categories(self):
        return Category.query.all()

    def get_all_groups(self, page=1, per_page=10, status=None):
        query = GroupBuy.query
        if status:
            query = query.filter_by(status=status)
        pagination = query.order_by(GroupBuy.create_time.desc()).paginate(page=page, per_page=per_page, error_out=False)
        return pagination.items, pagination

    # ========== 核心新增方法 ==========
    def check_sold_out_and_start_confirmation(self, group_id):
        """检查是否全部售空，并在截止时间前进入等待确认"""
        group = self.get_group_by_id(group_id)
        now = datetime.now()
        # 关键：如果已经超过截止时间，不允许进入等待确认
        if group.status != 'active' or now >= group.deadline:
            return False
        all_sold_out = all(item.remain_stock == 0 for item in group.items)
        if all_sold_out:
            group.status = 'waiting_confirmation'
            group.sold_out_time = now
            db.session.commit()
            # 没有其他参与者则直接进入采购
            self.try_auto_advance_to_procuring(group_id)
            return True
        return False

    def try_auto_advance_to_procuring(self, group_id):
        """如果拼单在等待确认阶段且没有其他参与者需要确认，直接进入采购"""
        group = self.get_group_by_id(group_id)
        if group.status != 'waiting_confirmation':
            return False
        other_orders = Order.query.filter(
            Order.group_buy_id == group_id,
            Order.user_id != group.creator_id
        ).all()
        if not other_orders:
            group.status = 'procuring'
            db.session.commit()
            return True
        all_confirmed = all(o.status == 'confirmed' for o in other_orders)
        if all_confirmed:
            group.status = 'procuring'
            db.session.commit()
            return True
        return False

    def confirm_procurement(self, group_id, photo_path):
        group = self.get_group_by_id(group_id)
        if not group or group.status != 'procuring':
            return False, "当前状态不能上传采购截图"
        group.add_procurement_photo(photo_path)
        return True, "采购截图已添加"

    def mark_shipped(self, group_id):
        group = self.get_group_by_id(group_id)
        if not group or group.status != 'procuring':
            return False, "当前状态不能标记送达"
        group.status = 'shipped'
        group.shipped_time = datetime.now()
        db.session.commit()
        return True, "已标记送达，请通知参与者确认取货"

    def check_all_participants_confirmed(self, group_id):
        group = self.get_group_by_id(group_id)
        if not group:
            return False
        other_orders = Order.query.filter(
            Order.group_buy_id == group_id,
            Order.user_id != group.creator_id
        ).all()
        if not other_orders:
            return True
        for order in other_orders:
            if order.status != 'confirmed':
                return False
        return True

    def process_expired_groups(self):
        """统一的定时任务：先处理超时active拼单失败，再处理超时waiting_confirmation自动确认"""
        now = datetime.now()
        failed_count = 0
        confirmed_count = 0
        try:
            # 第一步：超时的active拼单 -> failed
            active_expired = GroupBuy.query.filter(
                GroupBuy.status == 'active',
                GroupBuy.deadline < now
            ).all()
            for g in active_expired:
                g.status = 'failed'
                failed_count += 1

            # 第二步：超时的waiting_confirmation拼单 -> 自动确认所有pending订单
            waiting_expired = GroupBuy.query.filter(
                GroupBuy.status == 'waiting_confirmation',
                GroupBuy.deadline < now
            ).all()
            for g in waiting_expired:
                pending_orders = Order.query.filter(
                    Order.group_buy_id == g.id,
                    Order.status == 'pending',
                    Order.user_id != g.creator_id
                ).all()
                for order in pending_orders:
                    order.status = 'confirmed'
                    confirmed_count += 1
                # 确认后检查是否所有参与者都已确认
                if self.check_all_participants_confirmed(g.id):
                    g.status = 'procuring'
            db.session.commit()
            if failed_count > 0 or confirmed_count > 0:
                logging.info(f"[定时任务] 处理过期拼单：失败{failed_count}个，自动确认{confirmed_count}个订单")
        except Exception as e:
            db.session.rollback()
            logging.error(f"[定时任务] 处理失败：{e}")
        return failed_count, confirmed_count