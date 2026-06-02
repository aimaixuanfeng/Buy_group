import os
import uuid
from werkzeug.utils import secure_filename
from flask import current_app


def allowed_file(filename):
    """检查文件扩展名是否允许"""
    return '.' in filename and \
        filename.rsplit('.', 1)[1].lower() in current_app.config['ALLOWED_EXTENSIONS']


def save_upload_file(file, subfolder=''):
    """保存上传的文件，返回保存路径"""
    if not file or not allowed_file(file.filename):
        return None

    # 生成唯一文件名
    ext = file.filename.rsplit('.', 1)[1].lower()
    filename = f"{uuid.uuid4().hex}.{ext}"

    # 构建保存路径
    upload_dir = current_app.config['UPLOAD_FOLDER']
    if subfolder:
        upload_dir = os.path.join(upload_dir, subfolder)
        os.makedirs(upload_dir, exist_ok=True)

    filepath = os.path.join(upload_dir, filename)
    file.save(filepath)

    # 返回相对路径
    relative_path = f"/static/uploads/{subfolder}/{filename}" if subfolder else f"/static/uploads/{filename}"
    return relative_path


def format_price(price):
    """格式化价格"""
    return f"¥{float(price):.2f}"