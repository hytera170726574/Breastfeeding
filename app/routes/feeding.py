from flask import Blueprint, request, jsonify
from app import db
from app.models.models import Feeding
from app.schemas.schemas import FeedingCreate, BottleFeedingCreate, BreastFeedingStart, BreastFeedingEnd, FeedingUpdate, FeedingResponse
from app.utils.helpers import get_current_user, success_response, error_response
from flask_jwt_extended import jwt_required
from datetime import datetime

feeding_bp = Blueprint('feeding_bp', __name__)

@feeding_bp.route('/', methods=['POST'])
@jwt_required()
def create_feeding():
    try:
        # 获取当前用户
        current_user = get_current_user()
        if not current_user:
            return error_response('用户未登录', 401)

        # 验证输入数据
        feeding_data = FeedingCreate(**request.json)

        # 验证婴儿权限
        from app.models.models import Baby
        baby = Baby.query.filter_by(id=feeding_data.baby_id, user_id=current_user.id).first()
        if not baby:
            return error_response('无权限访问该婴儿记录', 403)

        # 创建喂养记录
        feeding = Feeding(
            feeding_type=feeding_data.feeding_type,
            start_time=feeding_data.start_time,
            bottle_ml=feeding_data.bottle_ml or 0,
            baby_id=feeding_data.baby_id
        )

        # 如果是母乳喂养且有开始时间，初始化breast_ml为0
        if feeding_data.feeding_type == 'breast' and feeding_data.start_time:
            feeding.breast_ml = 0

        db.session.add(feeding)
        db.session.commit()

        return success_response('喂养记录创建成功', FeedingResponse.from_orm(feeding).dict(), 201)
    except Exception as e:
        db.session.rollback()
        return error_response(f'创建喂养记录失败: {str(e)}')

@feeding_bp.route('/bottle', methods=['POST'])
@jwt_required()
def create_bottle_feeding():
    try:
        # 获取当前用户
        current_user = get_current_user()
        if not current_user:
            return error_response('用户未登录', 401)

        # 验证输入数据
        feeding_data = BottleFeedingCreate(**request.json)

        # 验证婴儿权限
        from app.models.models import Baby
        baby = Baby.query.filter_by(id=feeding_data.baby_id, user_id=current_user.id).first()
        if not baby:
            return error_response('无权限访问该婴儿记录', 403)

        # 创建奶粉喂养记录
        feeding = Feeding(
            feeding_type='bottle',
            bottle_ml=feeding_data.bottle_ml,
            start_time=feeding_data.timestamp,
            baby_id=feeding_data.baby_id
        )

        db.session.add(feeding)
        db.session.commit()

        return success_response('奶粉喂养记录创建成功', FeedingResponse.from_orm(feeding).dict(), 201)

    except Exception as e:
        db.session.rollback()
        return error_response(f'创建奶粉喂养记录失败: {str(e)}')

@feeding_bp.route('/breast/start', methods=['POST'])
@jwt_required()
def start_breast_feeding():
    try:
        # 获取当前用户
        current_user = get_current_user()
        if not current_user:
            return error_response('用户未登录', 401)

        # 验证输入数据
        feeding_data = BreastFeedingStart(**request.json)

        # 验证婴儿权限
        from app.models.models import Baby
        baby = Baby.query.filter_by(id=feeding_data.baby_id, user_id=current_user.id).first()
        if not baby:
            return error_response('无权限访问该婴儿记录', 403)

        # 创建母乳喂养开始记录
        feeding = Feeding(
            feeding_type='breast',
            start_time=feeding_data.start_time,
            baby_id=feeding_data.baby_id,
            breast_ml=0  # 初始化为0，结束时计算
        )

        db.session.add(feeding)
        db.session.commit()

        return success_response('母乳喂养开始记录成功', FeedingResponse.from_orm(feeding).dict(), 201)

    except Exception as e:
        db.session.rollback()
        return error_response(f'记录母乳喂养开始时间失败: {str(e)}')

@feeding_bp.route('/breast/<int:feeding_id>/end', methods=['PUT'])
@jwt_required()
def end_breast_feeding(feeding_id):
    try:
        # 获取当前用户
        current_user = get_current_user()
        if not current_user:
            return error_response('用户未登录', 401)

        # 获取喂养记录
        feeding = Feeding.query.filter_by(id=feeding_id).first()
        if not feeding:
            return error_response('喂养记录不存在', 404)

        # 验证用户是否有权限访问该婴儿的记录
        baby = feeding.baby
        if baby.user_id != current_user.id:
            return error_response('无权限访问该记录', 403)

        # 验证是否为母乳喂养记录
        if feeding.feeding_type != 'breast':
            return error_response('该记录不是母乳喂养记录', 400)

        # 验证输入数据
        end_data = BreastFeedingEnd(**request.json)

        # 更新结束时间和估算母乳量
        feeding.end_time = end_data.end_time
        if end_data.notes:
            feeding.notes = end_data.notes

        # 估算母乳喂养量
        feeding.estimate_breast_ml()

        db.session.commit()

        return success_response('母乳喂养结束记录成功', FeedingResponse.from_orm(feeding).dict(), 200)

    except Exception as e:
        db.session.rollback()
        return error_response(f'记录母乳喂养结束时间失败: {str(e)}')

@feeding_bp.route('/<int:baby_id>', methods=['GET'])
@jwt_required()
def get_feedings(baby_id):
    try:
        # 获取当前用户
        current_user = get_current_user()
        if not current_user:
            return error_response('用户未登录', 401)

        # 验证用户是否有权限访问该婴儿的记录
        from app.models.models import Baby
        baby = Baby.query.filter_by(id=baby_id, user_id=current_user.id).first()
        if not baby:
            return error_response('无权限访问该婴儿记录', 403)

        # 获取查询参数
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        feeding_type = request.args.get('type')  # 'breast', 'bottle', 或 None(全部)

        # 构建查询
        query = Feeding.query.filter_by(baby_id=baby_id).order_by(Feeding.start_time.desc())

        # 按喂养类型过滤
        if feeding_type and feeding_type in ['breast', 'bottle']:
            query = query.filter_by(feeding_type=feeding_type)

        # 按日期范围过滤
        if start_date:
            try:
                start_datetime = datetime.fromisoformat(start_date)
                query = query.filter(Feeding.start_time >= start_datetime)
            except ValueError:
                return error_response('开始日期格式错误，应为 ISO 格式 (YYYY-MM-DDTHH:MM:SS)', 400)

        if end_date:
            try:
                end_datetime = datetime.fromisoformat(end_date)
                query = query.filter(Feeding.start_time <= end_datetime)
            except ValueError:
                return error_response('结束日期格式错误，应为 ISO 格式 (YYYY-MM-DDTHH:MM:SS)', 400)

        # 执行查询
        feedings = query.all()
        feedings_data = [FeedingResponse.from_orm(feeding) for feeding in feedings]

        return success_response('获取喂养记录成功', feedings_data, 200)

    except Exception as e:
        return error_response(f'获取喂养记录失败: {str(e)}')

@feeding_bp.route('/default-baby', methods=['GET'])
@jwt_required()
def get_feedings_for_default_baby():
    try:
        # 获取当前用户
        current_user = get_current_user()
        if not current_user:
            return error_response('用户未登录', 401)

        # 检查是否有默认婴儿
        if not current_user.default_baby_id:
            return error_response('未设置默认婴儿', 404)

        # 验证用户是否有权限访问该婴儿的记录
        from app.models.models import Baby
        baby = Baby.query.filter_by(id=current_user.default_baby_id, user_id=current_user.id).first()
        if not baby:
            return error_response('无权限访问该婴儿记录', 403)

        # 获取查询参数
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        feeding_type = request.args.get('type')  # 'breast', 'bottle', 或 None(全部)

        # 构建查询
        query = Feeding.query.filter_by(baby_id=baby.id).order_by(Feeding.start_time.desc())

        # 按喂养类型过滤
        if feeding_type and feeding_type in ['breast', 'bottle']:
            query = query.filter_by(feeding_type=feeding_type)

        # 按日期范围过滤
        if start_date:
            try:
                start_datetime = datetime.fromisoformat(start_date)
                query = query.filter(Feeding.start_time >= start_datetime)
            except ValueError:
                return error_response('开始日期格式错误，应为 ISO 格式 (YYYY-MM-DDTHH:MM:SS)', 400)

        if end_date:
            try:
                end_datetime = datetime.fromisoformat(end_date)
                query = query.filter(Feeding.start_time <= end_datetime)
            except ValueError:
                return error_response('结束日期格式错误，应为 ISO 格式 (YYYY-MM-DDTHH:MM:SS)', 400)

        # 执行查询
        feedings = query.all()
        feedings_data = [FeedingResponse.from_orm(feeding) for feeding in feedings]

        return success_response('获取喂养记录成功', feedings_data, 200)

    except Exception as e:
        return error_response(f'获取喂养记录失败: {str(e)}')

@feeding_bp.route('/<int:feeding_id>', methods=['PUT'])
@jwt_required()
def update_feeding(feeding_id):
    try:
        # 获取当前用户
        current_user = get_current_user()
        if not current_user:
            return error_response('用户未登录', 401)

        # 获取喂养记录
        feeding = Feeding.query.filter_by(id=feeding_id).first()
        if not feeding:
            return error_response('喂养记录不存在', 404)

        # 验证用户是否有权限访问该婴儿的记录
        baby = feeding.baby
        if baby.user_id != current_user.id:
            return error_response('无权限访问该记录', 403)

        # 验证输入数据
        update_data = FeedingUpdate(**request.json)

        # 更新记录
        if update_data.feeding_type is not None:
            feeding.feeding_type = update_data.feeding_type
        if update_data.start_time is not None:
            feeding.start_time = update_data.start_time
        if update_data.end_time is not None:
            feeding.end_time = update_data.end_time
        if update_data.bottle_ml is not None:
            feeding.bottle_ml = update_data.bottle_ml
        if update_data.breast_ml is not None:
            feeding.breast_ml = update_data.breast_ml
        if update_data.notes is not None:
            feeding.notes = update_data.notes

        db.session.commit()

        return success_response('喂养记录更新成功', FeedingResponse.from_orm(feeding).dict(), 200)

    except Exception as e:
        db.session.rollback()
        return error_response(f'更新喂养记录失败: {str(e)}')

@feeding_bp.route('/<int:feeding_id>', methods=['DELETE'])
@jwt_required()
def delete_feeding(feeding_id):
    try:
        # 获取当前用户
        current_user = get_current_user()
        if not current_user:
            return error_response('用户未登录', 401)

        # 获取喂养记录
        feeding = Feeding.query.filter_by(id=feeding_id).first()
        if not feeding:
            return error_response('喂养记录不存在', 404)

        # 验证用户是否有权限访问该婴儿的记录
        baby = feeding.baby
        if baby.user_id != current_user.id:
            return error_response('无权限访问该记录', 403)

        # 删除记录
        db.session.delete(feeding)
        db.session.commit()

        return success_response(message='喂养记录删除成功', status_code=200)

    except Exception as e:
        db.session.rollback()
        return error_response(f'删除喂养记录失败: {str(e)}')