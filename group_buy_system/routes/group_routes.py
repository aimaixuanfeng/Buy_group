from flask import render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from routes import group_bp
from services import group_service, order_service, inventory_service
from utils.auth import login_required_with_message
from utils.common import save_upload_file
from datetime import datetime
import json


@group_bp.route('/publish', methods=['GET', 'POST'])
@login_required_with_message
def publish():
    categories = group_service.get_categories()
    if request.method == 'POST':
        title = request.form.get('title')
        description = request.form.get('description')
        category_id = request.form.get('category_id', type=int)
        pickup_location = request.form.get('pickup_location')
        deadline_str = request.form.get('deadline')
        items_json = request.form.get('items_json')
        image = None
        if 'image' in request.files:
            file = request.files['image']
            if file.filename:
                image = save_upload_file(file, 'groups')
        items_data = json.loads(items_json) if items_json else []
        if not items_data:
            flash('请至少添加一个商品项', 'danger')
            return render_template('publish.html', categories=categories)

        # 校验截止时间不能早于当前时间
        deadline = None
        if deadline_str:
            try:
                deadline = datetime.strptime(deadline_str, '%Y-%m-%dT%H:%M')
                if deadline <= datetime.now():
                    flash('截止时间必须晚于当前时间', 'danger')
                    return render_template('publish.html', categories=categories)
            except ValueError:
                flash('截止时间格式错误', 'danger')
                return render_template('publish.html', categories=categories)

        try:
            group = group_service.create_group(
                creator_id=current_user.id,
                title=title,
                description=description,
                category_id=category_id,
                pickup_location=pickup_location,
                deadline=deadline,
                image=image,
                items_data=items_data
            )
        except ValueError as e:
            flash(str(e), 'danger')
            return render_template('publish.html', categories=categories)

        flash('拼单发布成功！', 'success')
        return redirect(url_for('group_routes.detail', group_id=group.id))
    return render_template('publish.html', categories=categories)


@group_bp.route('/detail/<int:group_id>')
def detail(group_id):
    group = group_service.get_group_by_id(group_id)
    if not group:
        flash('拼单不存在', 'danger')
        return redirect(url_for('user_routes.index'))
    user_order = None
    if current_user.is_authenticated:
        from models.order import Order
        user_order = Order.query.filter_by(group_buy_id=group_id, user_id=current_user.id, status='pending').first()
    return render_template('detail.html', group=group, user_order=user_order)


@group_bp.route('/participants/<int:group_id>')
@login_required
def participants(group_id):
    group = group_service.get_group_by_id(group_id)
    if not group or group.creator_id != current_user.id:
        flash('无权查看', 'danger')
        return redirect(url_for('user_routes.index'))
    from models.order import Order
    orders = Order.query.filter(Order.group_buy_id == group_id,
                                Order.status.in_(['pending', 'confirmed', 'completed'])).all()
    participants_data = []
    for order in orders:
        items = []
        for item in order.order_items:
            items.append({
                'name': item.group_item.name,
                'quantity': item.quantity,
                'subtotal': float(item.subtotal)
            })
        participants_data.append({
            'user_nickname': order.user.nickname,
            'order_id': order.id,
            'total_price': float(order.total_price),
            'status': order.status,
            'items': items,
            'create_time': order.create_time.strftime('%Y-%m-%d %H:%M')
        })
    return render_template('participants.html', group=group, participants=participants_data)


@group_bp.route('/edit/<int:group_id>', methods=['GET', 'POST'])
@login_required_with_message
def edit_group(group_id):
    group = group_service.get_group_by_id(group_id)
    if not group or group.creator_id != current_user.id:
        flash('无权编辑该拼单', 'danger')
        return redirect(url_for('user_routes.index'))
    if group.status != 'active':
        flash('拼单已结束，无法编辑', 'warning')
        return redirect(url_for('group_routes.detail', group_id=group_id))
    categories = group_service.get_categories()
    if request.method == 'POST':
        title = request.form.get('title')
        description = request.form.get('description')
        pickup_location = request.form.get('pickup_location')
        deadline_str = request.form.get('deadline')

        # 校验截止时间
        deadline = None
        if deadline_str:
            try:
                deadline = datetime.strptime(deadline_str, '%Y-%m-%dT%H:%M')
                if deadline <= datetime.now():
                    flash('截止时间必须晚于当前时间', 'danger')
                    return render_template('edit_group.html', group=group, categories=categories)
            except ValueError:
                flash('截止时间格式错误', 'danger')
                return render_template('edit_group.html', group=group, categories=categories)

        image = group.image
        if 'image' in request.files:
            file = request.files['image']
            if file.filename:
                image = save_upload_file(file, 'groups')

        try:
            group_service.update_group(group_id, title=title, description=description, pickup_location=pickup_location,
                                       deadline=deadline, image=image)
        except ValueError as e:
            flash(str(e), 'danger')
            return render_template('edit_group.html', group=group, categories=categories)

        flash('拼单信息已更新', 'success')
        return redirect(url_for('group_routes.detail', group_id=group_id))
    return render_template('edit_group.html', group=group, categories=categories)


@group_bp.route('/cancel/<int:group_id>', methods=['POST'])
@login_required
def cancel_group(group_id):
    group = group_service.get_group_by_id(group_id)
    if not group or group.creator_id != current_user.id:
        flash('无权操作', 'danger')
        return redirect(url_for('user_routes.index'))
    cancel_reason = request.form.get('cancel_reason', '')
    success, msg = group_service.cancel_group(group_id, cancel_reason)
    flash(msg, 'success' if success else 'danger')
    return redirect(url_for('user_routes.profile'))


@group_bp.route('/add_to_order/<int:group_id>', methods=['POST'])
@login_required
def add_to_order(group_id):
    data = request.get_json()
    if not data:
        return jsonify({'success': False, 'message': '无效的请求数据'})
    items = data.get('items', [])
    items = [item for item in items if item.get('quantity', 0) > 0]
    if not items:
        return jsonify({'success': False, 'message': '请至少选择一件商品'})
    order, msg = order_service.create_order(current_user.id, group_id, items)
    if order:
        return jsonify({'success': True, 'redirect': url_for('order_routes.order_detail', order_id=order.id)})
    else:
        return jsonify({'success': False, 'message': msg})


@group_bp.route('/check_stock', methods=['POST'])
def check_stock():
    data = request.get_json()
    item_id = data.get('item_id')
    quantity = data.get('quantity', 1)
    success, msg = inventory_service.check_stock(item_id, quantity)
    remain = inventory_service.get_item_stock(item_id)['remain_stock'] if success else None
    return jsonify({'success': success, 'message': msg, 'remain_stock': remain})


# ========== 新增：发起人操作路由 ==========
@group_bp.route('/confirm_procurement/<int:group_id>', methods=['POST'])
@login_required
def confirm_procurement(group_id):
    group = group_service.get_group_by_id(group_id)
    if not group or group.creator_id != current_user.id:
        flash('无权限', 'danger')
        return redirect(url_for('group_routes.detail', group_id=group_id))
    if 'procurement_photo' not in request.files:
        flash('请上传采购截图', 'danger')
        return redirect(url_for('group_routes.detail', group_id=group_id))
    file = request.files['procurement_photo']
    if file.filename:
        photo_path = save_upload_file(file, 'procurement')
        success, msg = group_service.confirm_procurement(group_id, photo_path)
        flash(msg, 'success' if success else 'danger')
    else:
        flash('请选择图片', 'danger')
    return redirect(url_for('group_routes.detail', group_id=group_id))


@group_bp.route('/mark_shipped/<int:group_id>', methods=['POST'])
@login_required
def mark_shipped(group_id):
    success, msg = group_service.mark_shipped(group_id)
    flash(msg, 'success' if success else 'danger')
    return redirect(url_for('group_routes.detail', group_id=group_id))