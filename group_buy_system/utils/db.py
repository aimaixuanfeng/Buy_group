from models import db


def init_db(app):
    """初始化数据库"""
    with app.app_context():
        db.create_all()
        # 初始化默认分类
        init_categories()
        # 创建默认管理员账号
        create_admin()


def init_categories():
    """初始化默认分类"""
    from models.category import Category

    categories = ['奶茶饮品', '外卖美食', '水果生鲜', '日用品', '学习用品', '其他']
    for cat_name in categories:
        if not Category.query.filter_by(name=cat_name).first():
            category = Category(name=cat_name)
            db.session.add(category)
    db.session.commit()


def create_admin():
    """创建默认管理员"""
    from models.user import User
    from werkzeug.security import generate_password_hash

    admin = User.query.filter_by(username='admin').first()
    if not admin:
        admin = User(
            username='admin',
            password=generate_password_hash('admin123'),
            nickname='系统管理员',
            phone='13800000000',
            role='admin',
            status=1
        )
        db.session.add(admin)
        db.session.commit()