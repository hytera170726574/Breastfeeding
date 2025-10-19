from flask import Blueprint, request, jsonify,render_template,Flask
from app import db
from app.models.models import User
from app.schemas.schemas import UserCreate, UserLogin, UserResponse
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from werkzeug.security import check_password_hash

auth_bp = Blueprint('auth_bp', __name__)
app = Flask(__name__)
@auth_bp.route('/register', methods=['POST'])
def register():
    try:
        # 验证输入数据
        user_data = UserCreate(**request.json)

        # 检查用户是否已存在
        if User.query.filter_by(username=user_data.username).first():
            return jsonify({'error': '用户名已存在'}), 400

        if User.query.filter_by(email=user_data.email).first():
            return jsonify({'error': '邮箱已被注册'}), 400

        # 创建新用户
        user = User(username=user_data.username, email=user_data.email)
        user.set_password(user_data.password)

        db.session.add(user)
        db.session.commit()

        # 返回用户信息
        user_response = UserResponse.from_orm(user)
        return jsonify({
            'message': '用户注册成功',
            'user': user_response.dict()
        }), 201

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 400




@auth_bp.route('/login', methods=['POST'])
def login():
    try:
        # 验证输入数据
        login_data = UserLogin(**request.json)

        # 查找用户
        user = User.query.filter_by(username=login_data.username).first()

        # 验证用户和密码
        if not user or not user.check_password(login_data.password):
            return jsonify({'error': '用户名或密码错误'}), 401

        # 创建访问令牌
        access_token = create_access_token(identity=user.id)
        user_response = UserResponse.from_orm(user)

        return jsonify({
            'message': '登录成功',
            'access_token': access_token,
            'user': user_response.dict()
        }), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 400
    
@auth_bp.route('/loginPage', methods=['GET'])
def login_page():
    return render_template('auth.html')

@auth_bp.route('/dashboard', methods=['GET'])
def dashboard_page():
    return render_template('dashboard.html')