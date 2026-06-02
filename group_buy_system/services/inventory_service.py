from models import db
from models.group_item import GroupItem

class InventoryService:
    def check_stock(self, item_id, quantity):
        item = GroupItem.query.get(item_id)
        if not item:
            return False, "商品不存在"
        if item.remain_stock < quantity:
            return False, f"库存不足，剩余 {item.remain_stock} 件"
        return True, "库存充足"

    def deduct_stock(self, item_id, quantity):
        item = GroupItem.query.get(item_id)
        if not item or item.remain_stock < quantity:
            return False
        item.remain_stock -= quantity
        db.session.commit()
        return True

    def restore_stock(self, item_id, quantity):
        item = GroupItem.query.get(item_id)
        if not item:
            return False
        item.remain_stock += quantity
        if item.remain_stock > item.stock:
            item.remain_stock = item.stock
        db.session.commit()
        return True

    def get_item_stock(self, item_id):
        item = GroupItem.query.get(item_id)
        if item:
            return {'id': item.id, 'name': item.name, 'stock': item.stock, 'remain_stock': item.remain_stock}
        return None

# 创建单例实例
inventory_service = InventoryService()