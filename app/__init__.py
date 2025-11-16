import os
from flask import Flask, send_from_directory, abort
from werkzeug.exceptions import NotFound
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_jwt_extended import JWTManager
from flask_cors import CORS
from config import Config

# 初始化扩展
db = SQLAlchemy()
migrate = Migrate()
jwt = JWTManager()

def create_app(config_class=Config):
    # Ensure Flask serves static files from the project-level 'static' directory
    static_folder_path = os.path.join(os.path.dirname(__file__), '..', 'static')
    app = Flask(__name__, static_folder=static_folder_path, template_folder='templates')
    app.config.from_object(config_class)

    # 初始化扩展
    db.init_app(app)
    migrate.init_app(app, db)
    jwt.init_app(app)
    CORS(app)

    # 注册全局错误处理
    from app.utils.errors import register_error_handlers
    register_error_handlers(app)

    # 确保模型被加载以便 SQLAlchemy 元数据就绪（尤其用于迁移自动生成）
    from app.models import models  # noqa: F401

    # 注册蓝图
    from app.routes import auth_bp, baby_bp, feeding_bp, diaper_bp, sleep_bp, measurement_bp, stats_bp
    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    app.register_blueprint(baby_bp, url_prefix='/api/baby')
    app.register_blueprint(feeding_bp, url_prefix='/api/feeding')
    app.register_blueprint(diaper_bp, url_prefix='/api/diaper')
    app.register_blueprint(sleep_bp, url_prefix='/api/sleep')
    app.register_blueprint(measurement_bp, url_prefix='/api/measurement')
    app.register_blueprint(stats_bp, url_prefix='/api/stats')

    # 在生产环境中使用打包后的前端资源 (frontend/dist)
    frontend_dist = os.path.join(os.path.dirname(__file__), '..', 'frontend', 'dist')

    @app.route('/', defaults={'path': ''})
    @app.route('/<path:path>')
    def serve_frontend(path: str):
        """为除 /api/* 以外的请求提供前端构建产物。"""
        if path.startswith('api/'):
            abort(404)

        if not os.path.isdir(frontend_dist):
            abort(404)

        if path:
            full_path = os.path.join(frontend_dist, path)
            if os.path.exists(full_path):
                return send_from_directory(frontend_dist, path)
            # 如果请求的是具体文件（如 .js/.css）但不存在，直接返回 404，避免返回 HTML 导致 MIME 报错
            if '.' in os.path.basename(path):
                abort(404)

        return send_from_directory(frontend_dist, 'index.html')

    # 创建表
    with app.app_context():
        db.create_all()

    return app