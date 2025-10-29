from flask import Blueprint, request, jsonify
from app import db
from app.models.models import Baby, Feeding, Diaper, Sleep, Measurement, MilkInventory, MilkPump, DirectBreastfeeding, BottleBreastFeeding, FormulaFeeding
from app.schemas.schemas import BabyCreate, BabyUpdate, BabyResponse
from app.utils.helpers import get_current_user, success_response, error_response
from flask_jwt_extended import jwt_required
import logging

logger = logging.getLogger(__name__)

baby_bp = Blueprint('baby_bp', __name__)

@baby_bp.route('/createBaby', methods=['POST'])
@jwt_required()
def create_baby():
    print("开始创建婴儿")
    try:
        # 获取当前用户
        print("获取当前用户")
        current_user = get_current_user()
        if not current_user:
            return error_response('用户未登录', 401)

        # # 检查用户拥有的婴儿数量（限制免费用户最多2个婴儿）
        # baby_count = Baby.query.filter_by(user_id=current_user.id).count()
        # if baby_count >= 200:
        #     return error_response('免费账户最多只能创建2个婴儿信息，如需更多请升级到高级账户', 403)
        # all_baby_count = Baby.query.all().count()
        # 验证输入数据
        print("获取当前用户1")
        baby_data = BabyCreate(**request.json)
        print("获取当前用户2")
        logger.info(f"Received baby data: {baby_data}")
        print("baby_data:", baby_data)
        # 创建婴儿记录
        from datetime import datetime
        timestamp = datetime.now().timestamp()
        baby = Baby(
            name=baby_data.name,
            birth_date=baby_data.birth_date,
            gender=baby_data.gender,
            user_id=current_user.id,
            created_at = db.func.now(),
            id =current_user.id+int(timestamp)
        )
        logger.info(f"Creating baby for user id: {current_user.id}")
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
        logger.info(f"current user id is : {current_user.id if current_user else 'Unknown'}")
        # print("current user id is :",current_user)
        if not current_user:
            return error_response('用户未登录', 401)

        # 获取该用户的所有婴儿
        babies = Baby.query.filter_by(user_id=current_user.id).all()
        babies_data = []
        for baby in babies:
            baby_data = {
                "id": baby.id,
                "name": baby.name,
                "gender": baby.gender,
                "birth_date": baby.birth_date.isoformat() if baby.birth_date else None,
                "user_id": baby.user_id
            }
            babies_data.append(baby_data)
        baby_jsondata ={
            "data":babies_data
        }
        # logger.info(babies_data.json())
        return success_response(message='获取婴儿信息成功', data=babies_data, status_code=200)

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

        return success_response('获取婴儿信息成功', BabyResponse.from_orm(baby).dict(), status_code=200)

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

        return success_response('婴儿信息更新成功', BabyResponse.from_orm(baby).dict(), status_code=200)

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

        return success_response('婴儿信息删除成功', status_code=200)

    except Exception as e:
        db.session.rollback()
        return error_response(f'删除婴儿信息失败: {str(e)}')


@baby_bp.route('/<int:baby_id>/purge', methods=['DELETE'])
@jwt_required()
def purge_baby_and_all_data(baby_id):
    """彻底删除指定婴儿及其所有关联数据（喂养、大小便、睡眠、测量、库存等）。

    规则：
    - 如果这是该用户的最后一个宝宝，不允许删除。
    - 如果删除的是默认宝宝，自动选择该用户的另一个宝宝作为新的默认（如果存在）。
    - 返回删除结果或错误信息。
    """
    try:
        current_user = get_current_user()
        if not current_user:
            return error_response('用户未登录', 401)

        # 验证婴儿是否存在且属于当前用户
        baby = Baby.query.filter_by(id=baby_id, user_id=current_user.id).first()
        if not baby:
            return error_response('婴儿信息不存在或无权限访问', 404)

        # 检查该用户还有多少个宝宝
        total = Baby.query.filter_by(user_id=current_user.id).count()
        if total <= 1:
            return error_response('无法删除：这是您账户中的最后一个宝宝', 400)

        # 如果要删除的是默认宝宝，先选择另一个宝宝作为默认
        if current_user.default_baby_id == baby_id:
            other = Baby.query.filter(Baby.user_id == current_user.id, Baby.id != baby_id).first()
            if other:
                current_user.default_baby_id = other.id
            else:
                current_user.default_baby_id = None

        # 删除关联数据（逐表删除以避免外键约束问题）
        Feeding.query.filter_by(baby_id=baby_id).delete(synchronize_session=False)
        Diaper.query.filter_by(baby_id=baby_id).delete(synchronize_session=False)
        Sleep.query.filter_by(baby_id=baby_id).delete(synchronize_session=False)
        Measurement.query.filter_by(baby_id=baby_id).delete(synchronize_session=False)
        MilkInventory.query.filter_by(baby_id=baby_id).delete(synchronize_session=False)
        MilkPump.query.filter_by(baby_id=baby_id).delete(synchronize_session=False)
        DirectBreastfeeding.query.filter_by(baby_id=baby_id).delete(synchronize_session=False)
        BottleBreastFeeding.query.filter_by(baby_id=baby_id).delete(synchronize_session=False)
        FormulaFeeding.query.filter_by(baby_id=baby_id).delete(synchronize_session=False)

        # 最后删除 Baby 记录
        db.session.delete(baby)
        db.session.commit()

        logger.info(f"用户 {current_user.id} 已删除婴儿 {baby_id} 及其关联数据")
        return success_response('婴儿及其所有数据已删除', status_code=200)

    except Exception as e:
        db.session.rollback()
        return error_response(f'删除婴儿及其数据失败: {str(e)}')

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

        # 记录当前值以便排查
        logger.info(f"用户 {current_user.id} - 旧 default_baby_id = {current_user.default_baby_id}")

        # 设置为默认婴儿
        current_user.default_baby_id = baby_id
        db.session.commit()

        # 确认已写回数据库（刷新对象）并记录新值
        logger.info(f"用户 {current_user.id} - 新 default_baby_id = {current_user.default_baby_id}")

        # 返回设置后的婴儿对象作为权威信息，便于客户端更新
        return success_response(message=f'已将 {baby.name} 设置为默认婴儿', data=BabyResponse.from_orm(baby).dict(), status_code=200)

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

        # 记录当前用户默认宝宝以便排查
        logger.info(f"获取默认宝宝请求 - 用户 {current_user.id} 当前 default_baby_id = {current_user.default_baby_id}")

        # 获取默认婴儿
        if current_user.default_baby_id:
            baby = Baby.query.filter_by(id=current_user.default_baby_id, user_id=current_user.id).first()
            if baby:
                logger.info(f"返回默认宝宝 id={baby.id} name={baby.name} for user {current_user.id}")
                return success_response('获取默认婴儿成功', BabyResponse.from_orm(baby).dict(), status_code=200)

        return error_response('未设置默认婴儿', 404)

    except Exception as e:
        return error_response(f'获取默认婴儿失败: {str(e)}')