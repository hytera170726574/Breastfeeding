from flask import Flask
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
    app = Flask(__name__)
    app.config.from_object(config_class)

    # 初始化扩展
    db.init_app(app)
    migrate.init_app(app, db)
    jwt.init_app(app)
    CORS(app)

    # 注册全局错误处理
    from app.utils.errors import register_error_handlers
    register_error_handlers(app)

    # 注册蓝图
    from app.routes import auth_bp, baby_bp, feeding_bp, diaper_bp, sleep_bp, measurement_bp, stats_bp
    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    app.register_blueprint(baby_bp, url_prefix='/api/baby')
    app.register_blueprint(feeding_bp, url_prefix='/api/feeding')
    app.register_blueprint(diaper_bp, url_prefix='/api/diaper')
    app.register_blueprint(sleep_bp, url_prefix='/api/sleep')
    app.register_blueprint(measurement_bp, url_prefix='/api/measurement')
    app.register_blueprint(stats_bp, url_prefix='/api/stats')

    # 创建表
    with app.app_context():
        db.create_all()

    return app