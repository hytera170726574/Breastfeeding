from flask import Blueprint, request, jsonify, render_template
from app import db
import logging
from app.models.models import User, Baby
from app.schemas.schemas import UserCreate, UserLogin, UserResponse, BabyResponse
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from werkzeug.security import check_password_hash

auth_bp = Blueprint('auth_bp', __name__)
logger = logging.getLogger(__name__)
@auth_bp.route('/register', methods=['POST'])
def register():
    try:
        # 打印收到的请求，便于调试
        logger.info(f"Register request json: {request.get_json()}")

        # 验证输入数据
        user_data = UserCreate(**request.get_json())

        # 检查用户是否已存在
        if User.query.filter_by(username=user_data.username).first():
            return jsonify({'success': False, 'message': '用户名已存在'}), 400

        if User.query.filter_by(email=user_data.email).first():
            return jsonify({'success': False, 'message': '邮箱已被注册'}), 400

        # 创建新用户
        user = User(username=user_data.username, email=user_data.email)
        user.set_password(user_data.password)

        db.session.add(user)
        db.session.commit()

        # 返回用户信息（包含 success 字段以兼容前端判断）
        user_response = UserResponse.from_orm(user)
        return jsonify({
            'success': True,
            'message': '用户注册成功',
            'user': user_response.dict()
        }), 201

    except Exception as e:
        db.session.rollback()
        logger.exception('注册出错')
        return jsonify({'success': False, 'message': str(e)}), 400




@auth_bp.route('/login', methods=['POST'])
def login():
    try:
        # 验证输入数据
        login_data = UserLogin(**request.json)

        # 查找用户（通过用户名）
        user = User.query.filter_by(username=login_data.username).first()

        # 验证用户和密码
        if not user or not user.check_password(login_data.password):
            return jsonify({'error': '用户名或密码错误'}), 401

        # 创建访问令牌
        access_token = create_access_token(identity=user.id)
        user_response = UserResponse.from_orm(user)

        # 如果用户设置了默认宝宝，一并返回该宝宝信息，便于客户端在登录后立即使用
        default_baby_data = None
        if user.default_baby_id:
            baby = Baby.query.filter_by(id=user.default_baby_id, user_id=user.id).first()
            if baby:
                default_baby_data = BabyResponse.from_orm(baby).dict()

        return jsonify({
            'message': '登录成功',
            'access_token': access_token,
            'user': user_response.dict(),
            'default_baby': default_baby_data
        }), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 400
    
@auth_bp.route('/loginPage', methods=['GET'])
def login_page():
    return render_template('auth.html')

@auth_bp.route('/dashboard', methods=['GET'])
def dashboard_page():
    return render_template('dashboard.html')


@auth_bp.route('/logout', methods=['POST'])
@jwt_required()
def logout():
    try:
        # For now we don't maintain a token revocation list. Client should delete the token.
        identity = get_jwt_identity()
        logger.info(f"Logout requested by user: {identity}")
        return jsonify({'message': '已退出登录'}), 200
    except Exception as e:
        logger.exception('Logout error')
        return jsonify({'error': str(e)}), 500