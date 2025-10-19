from flask import jsonify
from flask_jwt_extended import get_jwt_identity
from app.models.models import User, Baby

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
    response = {'message': message}
    if data:
        response['data'] = data
    return jsonify(response), status_code