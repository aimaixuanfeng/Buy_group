from flask import render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from routes import order_bp
from services import order_service
from utils.auth import login_required_with_message

@order_bp.route('/detail/<int:order_id>')
@login_required
def order_detail(order_id):
    order = order_service.get_order_by_id(order_id)
    if not order or order.user_id != current_user.id:
        flash('订单不存在', 'danger')
        return redirect(url_for('user_routes.my_orders'))
    return render_template('order_detail.html', order=order)

@order_bp.route('/cancel/<int:order_id>', methods=['POST'])
@login_required
def cancel_order(order_id):
    order = order_service.get_order_by_id(order_id)
    if not order or order.user_id != current_user.id:
        return jsonify({'success': False, 'message': '订单不存在或无权操作'})
    success, msg = order_service.cancel_order(order_id)
    return jsonify({'success': success, 'message': msg})

@order_bp.route('/confirm/<int:order_id>', methods=['POST'])
@login_required
def confirm_order(order_id):
    from models.order import Order
    from models.group_buy import GroupBuy
    order = Order.query.get(order_id)
    if not order:
        flash('订单不存在', 'danger')
        return redirect(url_for('user_routes.my_orders'))
    group = GroupBuy.query.get(order.group_buy_id)
    if not group or group.creator_id != current_user.id:
        flash('仅拼单发起人可确认收货', 'danger')
        return redirect(url_for('user_routes.my_orders'))
    success = order_service.confirm_order(order_id)
    flash('订单已完成' if success else '操作失败', 'success' if success else 'danger')
    return redirect(url_for('group_routes.detail', group_id=order.group_buy_id))

# ========== 新增参与者确认路由 ==========
@order_bp.route('/confirm_participation/<int:order_id>', methods=['POST'])
@login_required
def confirm_participation(order_id):
    order = order_service.get_order_by_id(order_id)
    if not order or order.user_id != current_user.id:
        return jsonify({'success': False, 'message': '无权操作'})
    success, msg = order_service.confirm_participation(order_id)
    return jsonify({'success': success, 'message': msg})

@order_bp.route('/confirm_receipt/<int:order_id>', methods=['POST'])
@login_required
def confirm_receipt(order_id):
    order = order_service.get_order_by_id(order_id)
    if not order or order.user_id != current_user.id:
        return jsonify({'success': False, 'message': '无权操作'})
    success, msg = order_service.confirm_receipt(order_id)
    return jsonify({'success': success, 'message': msg})