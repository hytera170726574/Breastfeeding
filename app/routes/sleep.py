from flask import Blueprint, request, jsonify
from app import db
from app.models.models import Sleep
from app.schemas.schemas import SleepCreate, SleepUpdate, SleepResponse
from app.utils.helpers import get_current_user, success_response, error_response
from flask_jwt_extended import jwt_required
from datetime import datetime

sleep_bp = Blueprint('sleep_bp', __name__)

@sleep_bp.route('/start', methods=['POST'])
@jwt_required()
def start_sleep():
    try:
        # 获取当前用户
        current_user = get_current_user()
        if not current_user:
            return error_response('用户未登录', 401)

        # 验证输入数据
        sleep_data = SleepCreate(**request.json)

        # 验证婴儿权限
        from app.models.models import Baby
        baby = Baby.query.filter_by(id=sleep_data.baby_id, user_id=current_user.id).first()
        if not baby:
            return error_response('无权限访问该婴儿记录', 403)

        # 创建睡眠开始记录
        sleep = Sleep(
            start_time=sleep_data.start_time,
            baby_id=sleep_data.baby_id
        )

        db.session.add(sleep)
        db.session.commit()

        return success_response('睡眠开始记录成功', SleepResponse.from_orm(sleep).dict(), 201)

    except Exception as e:
        db.session.rollback()
        return error_response(f'记录睡眠开始时间失败: {str(e)}')

@sleep_bp.route('/<int:sleep_id>/end', methods=['PUT'])
@jwt_required()
def end_sleep(sleep_id):
    try:
        # 获取当前用户
        current_user = get_current_user()
        if not current_user:
            return error_response('用户未登录', 401)

        # 获取睡眠记录
        sleep = Sleep.query.filter_by(id=sleep_id).first()
        if not sleep:
            return error_response('睡眠记录不存在', 404)

        # 验证用户是否有权限访问该婴儿的记录
        baby = sleep.baby
        if baby.user_id != current_user.id:
            return error_response('无权限访问该记录', 403)

        # 验证输入数据
        update_data = SleepUpdate(**request.json)

        # 更新结束时间
        if update_data.end_time is not None:
            sleep.end_time = update_data.end_time
        if update_data.notes is not None:
            sleep.notes = update_data.notes

        db.session.commit()

        return success_response('睡眠结束记录成功', SleepResponse.from_orm(sleep).dict(), 200)

    except Exception as e:
        db.session.rollback()
        return error_response(f'记录睡眠结束时间失败: {str(e)}')

@sleep_bp.route('/<int:baby_id>', methods=['GET'])
@jwt_required()
def get_sleeps(baby_id):
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

        # 构建查询
        query = Sleep.query.filter_by(baby_id=baby_id).order_by(Sleep.start_time.desc())

        # 按日期范围过滤
        if start_date:
            try:
                start_datetime = datetime.fromisoformat(start_date)
                query = query.filter(Sleep.start_time >= start_datetime)
            except ValueError:
                return error_response('开始日期格式错误，应为 ISO 格式 (YYYY-MM-DDTHH:MM:SS)', 400)

        if end_date:
            try:
                end_datetime = datetime.fromisoformat(end_date)
                query = query.filter(Sleep.start_time <= end_datetime)
            except ValueError:
                return error_response('结束日期格式错误，应为 ISO 格式 (YYYY-MM-DDTHH:MM:SS)', 400)

        # 执行查询
        sleeps = query.all()
        sleeps_data = [SleepResponse.from_orm(sleep) for sleep in sleeps]

        return success_response('获取睡眠记录成功', sleeps_data, 200)

    except Exception as e:
        return error_response(f'获取睡眠记录失败: {str(e)}')

@sleep_bp.route('/default-baby', methods=['GET'])
@jwt_required()
def get_sleeps_for_default_baby():
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

        # 构建查询
        query = Sleep.query.filter_by(baby_id=baby.id).order_by(Sleep.start_time.desc())

        # 按日期范围过滤
        if start_date:
            try:
                start_datetime = datetime.fromisoformat(start_date)
                query = query.filter(Sleep.start_time >= start_datetime)
            except ValueError:
                return error_response('开始日期格式错误，应为 ISO 格式 (YYYY-MM-DDTHH:MM:SS)', 400)

        if end_date:
            try:
                end_datetime = datetime.fromisoformat(end_date)
                query = query.filter(Sleep.start_time <= end_datetime)
            except ValueError:
                return error_response('结束日期格式错误，应为 ISO 格式 (YYYY-MM-DDTHH:MM:SS)', 400)

        # 执行查询
        sleeps = query.all()
        sleeps_data = [SleepResponse.from_orm(sleep) for sleep in sleeps]

        return success_response('获取睡眠记录成功', sleeps_data, 200)

    except Exception as e:
        return error_response(f'获取睡眠记录失败: {str(e)}')

@sleep_bp.route('/<int:sleep_id>', methods=['PUT'])
@jwt_required()
def update_sleep(sleep_id):
    try:
        # 获取当前用户
        current_user = get_current_user()
        if not current_user:
            return error_response('用户未登录', 401)

        # 获取睡眠记录
        sleep = Sleep.query.filter_by(id=sleep_id).first()
        if not sleep:
            return error_response('睡眠记录不存在', 404)

        # 验证用户是否有权限访问该婴儿的记录
        baby = sleep.baby
        if baby.user_id != current_user.id:
            return error_response('无权限访问该记录', 403)

        # 验证输入数据
        update_data = SleepUpdate(**request.json)

        # 更新记录
        if update_data.start_time is not None:
            sleep.start_time = update_data.start_time
        if update_data.end_time is not None:
            sleep.end_time = update_data.end_time
        if update_data.notes is not None:
            sleep.notes = update_data.notes

        db.session.commit()

        return success_response('睡眠记录更新成功', SleepResponse.from_orm(sleep).dict(), 200)
    except Exception as e:
        db.session.rollback()
        return error_response(f'更新睡眠记录失败: {str(e)}')

@sleep_bp.route('/<int:sleep_id>', methods=['DELETE'])
@jwt_required()
def delete_sleep(sleep_id):
    try:
        # 获取当前用户
        current_user = get_current_user()
        if not current_user:
            return error_response('用户未登录', 401)

        # 获取睡眠记录
        sleep = Sleep.query.filter_by(id=sleep_id).first()
        if not sleep:
            return error_response('睡眠记录不存在', 404)

        # 验证用户是否有权限访问该婴儿的记录
        baby = sleep.baby
        if baby.user_id != current_user.id:
            return error_response('无权限访问该记录', 403)

        # 删除记录
        db.session.delete(sleep)
        db.session.commit()

        return success_response(message='睡眠记录删除成功', status_code=200)

    except Exception as e:
        db.session.rollback()
        return error_response(f'删除睡眠记录失败: {str(e)}')