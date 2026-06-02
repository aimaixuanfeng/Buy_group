from flask import Flask
from config import Config
from models import db
from utils.auth import login_manager
from utils.db import init_db
import os
from flask_apscheduler import APScheduler

scheduler = APScheduler()



def process_expired_groups():
    with app.app_context():
        from services import group_service
        failed_count, confirmed_count = group_service.process_expired_groups()
        print(f"[定时任务] 处理过期拼单：失败{failed_count}个，自动确认{confirmed_count}个订单")


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

    db.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = 'user_routes.login'
    login_manager.login_message = '请先登录'

    from routes.user_routes import user_bp
    from routes.group_routes import group_bp
    from routes.order_routes import order_bp
    from routes.admin_routes import admin_bp
    app.register_blueprint(user_bp)
    app.register_blueprint(group_bp)
    app.register_blueprint(order_bp)
    app.register_blueprint(admin_bp)

    with app.app_context():
        init_db(app)

    if not app.debug or os.environ.get('WERKZEUG_RUN_MAIN') == 'true':
        scheduler.init_app(app)
        scheduler.add_job(
            id='process_expired_groups',
            func=process_expired_groups,
            trigger='interval',
            minutes=1
        )
        scheduler.start()
        print("[系统] 定时任务已启动，每分钟检查一次过期拼单")

    return app


if __name__ == '__main__':
    app = create_app()
    app.run(debug=True, host='0.0.0.0', port=5000)