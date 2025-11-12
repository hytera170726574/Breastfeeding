from flask import jsonify
from flask_jwt_extended import get_jwt_identity
from app.models.models import User, Baby
from datetime import datetime, timezone


def parse_iso_datetime(s: str) -> datetime:
    """Parse ISO datetime strings robustly.

    Accepts strings with trailing 'Z' (UTC) or with offsets. Returns a
    naive UTC datetime (tzinfo removed) suitable for comparing with DB
    datetimes stored as naive UTC.
    Raises ValueError on invalid format.
    """
    if not s:
        raise ValueError('empty datetime string')
    # Handle 'Z' suffix (RFC3339) which Python's fromisoformat doesn't accept
    if s.endswith('Z'):
        s = s[:-1] + '+00:00'
    dt = datetime.fromisoformat(s)
    # If dt is timezone-aware, convert to UTC and drop tzinfo to keep naive datetimes
    if dt.tzinfo is not None:
        dt = dt.astimezone(timezone.utc).replace(tzinfo=None)
    return dt

def get_current_user():
    """获取当前登录用户"""
    user_id = get_jwt_identity()
    return User.query.get(user_id)

def get_baby_with_permission_check(baby_id, user_id):
    """检查用户是否有权限访问指定的婴儿"""
    baby = Baby.query.filter_by(id=baby_id, user_id=user_id).first()
    return baby

def error_response(message, status_code=400):
    """标准化错误响应"""
    return jsonify({'error': message}), status_code

def success_response(message, data=None, status_code=200):
    """标准化成功响应"""
    response = {
        'message': message,
        'data': data,
    }
    return jsonify(response), status_code