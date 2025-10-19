from functools import wraps
from flask import jsonify
from flask_jwt_extended import verify_jwt_in_request, get_jwt_identity
from app.models.models import User, Baby

def validate_json(f):
    """验证JSON请求数据装饰器"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        from flask import request
        if not request.is_json:
            return jsonify({'error': '请求必须为JSON格式'}), 400
        return f(*args, **kwargs)
    return decorated_function

def validate_baby_ownership(f):
    """验证用户对婴儿的所有权装饰器"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # 验证JWT
        try:
            verify_jwt_in_request()
        except Exception:
            return jsonify({'error': '无效的访问令牌'}), 401

        # 获取当前用户
        user_id = get_jwt_identity()
        current_user = User.query.get(user_id)
        if not current_user:
            return jsonify({'error': '用户不存在'}), 404

        # 获取婴儿ID（从URL参数或请求体中）
        baby_id = kwargs.get('baby_id') or request.json.get('baby_id')
        if not baby_id:
            return jsonify({'error': '缺少婴儿ID参数'}), 400

        # 验证婴儿所有权
        baby = Baby.query.filter_by(id=baby_id, user_id=current_user.id).first()
        if not baby:
            return jsonify({'error': '婴儿不存在或无权限访问'}), 403

        return f(*args, **kwargs)
    return decorated_function

def validate_date_range(start_date, end_date):
    """验证日期范围"""
    if start_date > end_date:
        return False, "开始日期不能晚于结束日期"

    # 限制时间范围不超过1年
    if (end_date - start_date).days > 365:
        return False, "时间范围不能超过1年"

    return True, ""

def validate_positive_number(value, field_name):
    """验证正数"""
    if value is not None and value <= 0:
        return False, f"{field_name}必须为正数"
    return True, ""