from flask import render_template, request, redirect, url_for, flash, session
from flask_login import login_required, current_user
from routes import user_bp
from services import user_service, auth_service, group_service, order_service
from utils.auth import login_required_with_message, admin_required
from utils.common import save_upload_file


@user_bp.route('/')
def index():
    """首页"""
    categories = group_service.get_categories()
    page = request.args.get('page', 1, type=int)
    category_id = request.args.get('category_id', type=int)
    keyword = request.args.get('keyword', '')

    groups, pagination = group_service.get_active_groups(page, category_id=category_id, keyword=keyword)

    # 获取公告
    from models.notice import Notice
    notices = Notice.query.order_by(Notice.create_time.desc()).limit(5).all()

    return render_template('index.html', groups=groups, pagination=pagination,
                           categories=categories, current_category=category_id,
                           keyword=keyword, notices=notices)


@user_bp.route('/login', methods=['GET', 'POST'])
def login():
    """用户登录"""
    if current_user.is_authenticated:
        return redirect(url_for('user_routes.index'))

    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        selected_role = request.form.get('role')  # 'user' 或 'admin'

        user, msg = user_service.login(username, password)
        if user:
            # 额外校验角色是否匹配
            if selected_role == 'admin' and user.role != 'admin':
                flash('您选择的身份是管理员，但该账号不是管理员，请切换身份或使用管理员账号', 'danger')
                return render_template('login.html')
            if selected_role == 'user' and user.role != 'user':
                flash('您选择的身份是普通用户，但该账号是管理员，请切换身份或使用普通账号', 'danger')
                return render_template('login.html')

            auth_service.authenticate(user)
            next_page = request.args.get('next')
            flash(msg, 'success')
            # 根据角色重定向到不同首页（可选）
            if user.role == 'admin':
                return redirect(next_page or url_for('admin_routes.dashboard'))
            return redirect(next_page or url_for('user_routes.index'))
        else:
            flash(msg, 'danger')

    return render_template('login.html')

@user_bp.route('/register', methods=['GET', 'POST'])
def register():
    """用户注册"""
    if current_user.is_authenticated:
        return redirect(url_for('user_routes.index'))

    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        nickname = request.form.get('nickname')
        phone = request.form.get('phone')

        if password != confirm_password:
            flash('两次密码输入不一致', 'danger')
            return render_template('register.html')

        user, msg = user_service.register(username, password, nickname, phone)
        if user:
            flash(msg, 'success')
            return redirect(url_for('user_routes.login'))
        else:
            flash(msg, 'danger')

    return render_template('register.html')


@user_bp.route('/logout')
@login_required
def logout():
    """用户登出"""
    auth_service.logout()
    flash('已退出登录', 'info')
    return redirect(url_for('user_routes.index'))


@user_bp.route('/profile')
@login_required_with_message
def profile():
    """个人中心"""
    my_groups, group_pagination = group_service.get_groups_by_creator(current_user.id)
    return render_template('profile.html', user=current_user, my_groups=my_groups, group_pagination=group_pagination)


@user_bp.route('/change_password', methods=['POST'])
@login_required
def change_password():
    """修改密码"""
    old_password = request.form.get('old_password')
    new_password = request.form.get('new_password')

    success, msg = user_service.change_password(current_user.id, old_password, new_password)
    flash(msg, 'success' if success else 'danger')
    return redirect(url_for('user_routes.profile'))


@user_bp.route('/my_orders')
@login_required_with_message
def my_orders():
    """我的订单"""
    page = request.args.get('page', 1, type=int)
    orders, pagination = order_service.get_user_orders(current_user.id, page)
    return render_template('my_orders.html', orders=orders, pagination=pagination)