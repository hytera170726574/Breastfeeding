from flask import jsonify
from marshmallow import ValidationError
import logging

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def register_error_handlers(app):
    """注册全局错误处理处理器"""

    @app.errorhandler(400)
    def bad_request(error):
        return jsonify({'error': '请求参数错误'}), 400

    @app.errorhandler(401)
    def unauthorized(error):
        return jsonify({'error': '未授权访问'}), 401

    @app.errorhandler(403)
    def forbidden(error):
        return jsonify({'error': '禁止访问'}), 403

    @app.errorhandler(404)
    def not_found(error):
        return jsonify({'error': '资源未找到'}), 404

    @app.errorhandler(405)
    def method_not_allowed(error):
        return jsonify({'error': '方法不被允许'}), 405

    @app.errorhandler(500)
    def internal_error(error):
        logger.error(f"内部服务器错误: {str(error)}")
        return jsonify({'error': '服务器内部错误'}), 500

    @app.errorhandler(ValidationError)
    def handle_validation_error(error):
        return jsonify({'error': '数据验证失败', 'details': error.messages}), 400

    @app.errorhandler(Exception)
    def handle_unexpected_error(error):
        logger.error(f"未处理的异常: {str(error)}")
        return jsonify({'error': '服务器发生未知错误'}), 500