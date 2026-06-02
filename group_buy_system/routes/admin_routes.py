from flask import render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required
from routes import admin_bp
from services import user_service, group_service, order_service
from utils.auth import admin_required
from models.notice import Notice
from models import db
from datetime import datetime


@admin_bp.route('/')
@login_required
@admin_required
def dashboard():
    """管理后台首页"""
    user_stats = user_service.get_user_statistics()
    order_stats = order_service.get_order_statistics()
    group_stats = {
        'total': group_service.get_all_groups()[1].total,
        'active': group_service.get_active_groups(1, 10000)[1].total if group_service.get_active_groups(1, 10000)[
            1] else 0
    }

    return render_template('admin/dashboard.html', user_stats=user_stats, order_stats=order_stats,
                           group_stats=group_stats)


@admin_bp.route('/users')
@login_required
@admin_required
def users():
    """用户管理"""
    page = request.args.get('page', 1, type=int)
    users, pagination = user_service.get_all_users(page)
    return render_template('admin/users.html', users=users, pagination=pagination)


@admin_bp.route('/users/<int:user_id>/toggle_status', methods=['POST'])
@login_required
@admin_required
def toggle_user_status(user_id):
    """封禁/解封用户"""
    user = user_service.get_user_by_id(user_id)
    if user and user.id == 1:  # 保护admin账号
        flash('不能操作管理员账号', 'danger')
        return redirect(url_for('admin_routes.users'))

    new_status = 1 if user.status == 0 else 0
    user_service.update_user_status(user_id, new_status)
    flash(f'用户状态已更新', 'success')
    return redirect(url_for('admin_routes.users'))


@admin_bp.route('/users/<int:user_id>/delete', methods=['POST'])
@login_required
@admin_required
def delete_user(user_id):
    """删除用户"""
    user = user_service.get_user_by_id(user_id)
    if user and user.id == 1:
        flash('不能删除管理员账号', 'danger')
        return redirect(url_for('admin_routes.users'))

    if user_service.delete_user(user_id):
        flash('用户已删除', 'success')
    else:
        flash('删除失败', 'danger')
    return redirect(url_for('admin_routes.users'))


@admin_bp.route('/groups')
@login_required
@admin_required
def groups():
    """拼单管理"""
    page = request.args.get('page', 1, type=int)
    status = request.args.get('status', '')
    groups, pagination = group_service.get_all_groups(page, status=status if status else None)
    return render_template('admin/groups.html', groups=groups, pagination=pagination, current_status=status)


@admin_bp.route('/groups/<int:group_id>/delete', methods=['POST'])
@login_required
@admin_required
def delete_group(group_id):
    """删除拼单"""
    if group_service.delete_group(group_id):
        flash('拼单已删除', 'success')
    else:
        flash('删除失败', 'danger')
    return redirect(url_for('admin_routes.groups'))


@admin_bp.route('/orders')
@login_required
@admin_required
def orders():
    """订单管理"""
    page = request.args.get('page', 1, type=int)
    status = request.args.get('status', '')
    orders, pagination = order_service.get_all_orders(page, status=status if status else None)
    return render_template('admin/orders.html', orders=orders, pagination=pagination, current_status=status)


@admin_bp.route('/notices', methods=['GET', 'POST'])
@login_required
@admin_required
def notices():
    """公告管理"""
    if request.method == 'POST':
        action = request.form.get('action')

        if action == 'add':
            title = request.form.get('title')
            content = request.form.get('content')
            notice = Notice(title=title, content=content)
            db.session.add(notice)
            db.session.commit()
            flash('公告已发布', 'success')

        elif action == 'delete':
            notice_id = request.form.get('notice_id', type=int)
            notice = Notice.query.get(notice_id)
            if notice:
                db.session.delete(notice)
                db.session.commit()
                flash('公告已删除', 'success')

    all_notices = Notice.query.order_by(Notice.create_time.desc()).all()
    return render_template('admin/notices.html', notices=all_notices)


@admin_bp.route('/statistics')
@login_required
@admin_required
def statistics():
    """数据统计"""
    from sqlalchemy import func
    from models.order import Order
    from models.group_buy import GroupBuy

    # 月度订单统计
    monthly_orders = db.session.query(
        func.date_format(Order.create_time, '%Y-%m').label('month'),
        func.count(Order.id).label('count'),
        func.sum(Order.total_price).label('total')
    ).filter(Order.status == 'completed').group_by('month').order_by('month').limit(12).all()

    # 分类统计
    from models.category import Category
    from models.group_buy import GroupBuy
    category_stats = db.session.query(
        Category.name,
        func.count(GroupBuy.id).label('count')
    ).outerjoin(GroupBuy, Category.id == GroupBuy.category_id).group_by(Category.id).all()

    return render_template('admin/statistics.html', monthly_orders=monthly_orders, category_stats=category_stats)