from flask import Blueprint, request, jsonify
from app import db
from app.models.models import Baby
from app.schemas.schemas import BabyCreate, BabyUpdate, BabyResponse
from app.utils.helpers import get_current_user, success_response, error_response
from flask_jwt_extended import jwt_required

baby_bp = Blueprint('baby_bp', __name__)

@baby_bp.route('/', methods=['POST'])
@jwt_required()
def create_baby():
    print("开始创建婴儿")
    try:
        # 获取当前用户
        print("获取当前用户")
        current_user = get_current_user()
        if not current_user:
            return error_response('用户未登录', 401)

        # 检查用户拥有的婴儿数量（限制免费用户最多2个婴儿）
        baby_count = Baby.query.filter_by(user_id=current_user.id).count()
        if baby_count >= 200:
            return error_response('免费账户最多只能创建2个婴儿信息，如需更多请升级到高级账户', 403)

        # 验证输入数据
        baby_data = BabyCreate(**request.json)
        # 创建婴儿记录
        baby = Baby(
            name=baby_data.name,
            birth_date=baby_data.birth_date,
            gender=baby_data.gender,
            user_id=current_user.id,
            # id = baby_count +1
        )
        # baby.jsonify()
        db.session.add(baby)
        db.session.commit()

        return success_response(message='婴儿信息创建成功',data= BabyResponse.from_orm(baby).dict(), status_code=201)

    except Exception as e:
        db.session.rollback()
        return error_response(f'创建婴儿信息失败: {str(e)}')

@baby_bp.route('/', methods=['GET'])
@jwt_required()
def get_babies():
    try:
        # 获取当前用户
        current_user = get_current_user()
        if not current_user:
            return error_response('用户未登录', 401)

        # 获取该用户的所有婴儿
        babies = Baby.query.filter_by(user_id=current_user.id).all()
        print(babies)
        babies_data = []
        for baby in range(babies):
            baby_data = {
                "id": baby.id,
                "name": baby.name,
                "gender": baby.gender,
                "birthdate": baby.birth_date.isoformat() if baby.birthdate else None,
                "user": baby.user
            }
            babies_data.append(baby_data)
        # babies_data = [BabyResponse.from_orm(baby) for baby in babies]
        return success_response(message='获取婴儿信息成功',data= babies_data), 200

    except Exception as e:
        return error_response(f'获取婴儿信息失败: {str(e)}')

@baby_bp.route('/<int:baby_id>', methods=['GET'])
@jwt_required()
def get_baby(baby_id):
    try:
        # 获取当前用户
        current_user = get_current_user()
        if not current_user:
            return error_response('用户未登录', 401)

        # 获取婴儿信息并检查权限
        baby = Baby.query.filter_by(id=baby_id, user_id=current_user.id).first()
        if not baby:
            return error_response('婴儿信息不存在或无权限访问', 404)

        return success_response('获取婴儿信息成功', BabyResponse.from_orm(baby).dict()), 200

    except Exception as e:
        return error_response(f'获取婴儿信息失败: {str(e)}')

@baby_bp.route('/<int:baby_id>', methods=['PUT'])
@jwt_required()
def update_baby(baby_id):
    try:
        # 获取当前用户
        current_user = get_current_user()
        if not current_user:
            return error_response('用户未登录', 401)

        # 获取婴儿信息并检查权限
        baby = Baby.query.filter_by(id=baby_id, user_id=current_user.id).first()
        if not baby:
            return error_response('婴儿信息不存在或无权限访问', 404)

        # 验证输入数据
        update_data = BabyUpdate(**request.json)

        # 更新婴儿信息
        if update_data.name is not None:
            baby.name = update_data.name
        if update_data.birth_date is not None:
            baby.birth_date = update_data.birth_date

        db.session.commit()

        return success_response('婴儿信息更新成功', BabyResponse.from_orm(baby).dict()), 200

    except Exception as e:
        db.session.rollback()
        return error_response(f'更新婴儿信息失败: {str(e)}')

@baby_bp.route('/<int:baby_id>', methods=['DELETE'])
@jwt_required()
def delete_baby(baby_id):
    try:
        # 获取当前用户
        current_user = get_current_user()
        if not current_user:
            return error_response('用户未登录', 401)

        # 获取婴儿信息并检查权限
        baby = Baby.query.filter_by(id=baby_id, user_id=current_user.id).first()
        if not baby:
            return error_response('婴儿信息不存在或无权限访问', 404)

        # 如果删除的是默认婴儿，清除默认婴儿设置
        if current_user.default_baby_id == baby_id:
            current_user.default_baby_id = None

        # 删除婴儿记录
        db.session.delete(baby)
        db.session.commit()

        return success_response('婴儿信息删除成功'), 200

    except Exception as e:
        db.session.rollback()
        return error_response(f'删除婴儿信息失败: {str(e)}')

@baby_bp.route('/<int:baby_id>/set-default', methods=['POST'])
@jwt_required()
def set_default_baby(baby_id):
    try:
        # 获取当前用户
        current_user = get_current_user()
        if not current_user:
            return error_response('用户未登录', 401)

        # 检查婴儿是否存在且属于当前用户
        baby = Baby.query.filter_by(id=baby_id, user_id=current_user.id).first()
        if not baby:
            return error_response('婴儿信息不存在或无权限访问', 404)

        # 设置为默认婴儿
        current_user.default_baby_id = baby_id
        db.session.commit()

        return success_response(message=f'已将 {baby.name} 设置为默认婴儿',status_code=200)

    except Exception as e:
        db.session.rollback()
        return error_response(f'设置默认婴儿失败: {str(e)}')

@baby_bp.route('/default', methods=['GET'])
@jwt_required()
def get_default_baby():
    try:
        # 获取当前用户
        current_user = get_current_user()
        if not current_user:
            return error_response('用户未登录', 401)

        # 获取默认婴儿
        if current_user.default_baby_id:
            baby = Baby.query.filter_by(id=current_user.default_baby_id, user_id=current_user.id).first()
            if baby:
                return success_response('获取默认婴儿成功', BabyResponse.from_orm(baby).dict()), 200

        return error_response('未设置默认婴儿'), 404

    except Exception as e:
        return error_response(f'获取默认婴儿失败: {str(e)}')