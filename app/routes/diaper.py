from flask import Blueprint, request, jsonify
from app import db
from app.models.models import Diaper
from app.schemas.schemas import DiaperCreate, DiaperUpdate, DiaperResponse
from app.utils.helpers import get_current_user, success_response, error_response
from flask_jwt_extended import jwt_required
from datetime import datetime

diaper_bp = Blueprint('diaper_bp', __name__)

@diaper_bp.route('/', methods=['POST'])
@jwt_required()
def create_diaper():
    try:
        # 获取当前用户
        current_user = get_current_user()
        if not current_user:
            return error_response('用户未登录', 401)

        # 验证输入数据
        diaper_data = DiaperCreate(**request.json)

        # 验证婴儿权限
        from app.models.models import Baby
        baby = Baby.query.filter_by(id=diaper_data.baby_id, user_id=current_user.id).first()
        if not baby:
            return error_response('无权限访问该婴儿记录', 403)

        # 创建大小便记录
        diaper = Diaper(
            diaper_type=diaper_data.diaper_type,
            baby_id=diaper_data.baby_id
        )

        # 如果提供了时间戳，使用它；否则使用当前时间
        if diaper_data.timestamp:
            diaper.timestamp = diaper_data.timestamp

        db.session.add(diaper)
        db.session.commit()

        return success_response('大小便记录创建成功', DiaperResponse.from_orm(diaper).dict(), 201)

    except Exception as e:
        db.session.rollback()
        return error_response(f'创建大小便记录失败: {str(e)}')

@diaper_bp.route('/<int:baby_id>', methods=['GET'])
@jwt_required()
def get_diapers(baby_id):
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
        diaper_type = request.args.get('type')  # 'wet', 'dirty', 或 None(全部)

        # 构建查询
        query = Diaper.query.filter_by(baby_id=baby_id).order_by(Diaper.timestamp.desc())

        # 按类型过滤
        if diaper_type and diaper_type in ['wet', 'dirty']:
            query = query.filter_by(diaper_type=diaper_type)

        # 按日期范围过滤
        if start_date:
            try:
                start_datetime = datetime.fromisoformat(start_date)
                query = query.filter(Diaper.timestamp >= start_datetime)
            except ValueError:
                return error_response('开始日期格式错误，应为 ISO 格式 (YYYY-MM-DDTHH:MM:SS)', 400)

        if end_date:
            try:
                end_datetime = datetime.fromisoformat(end_date)
                query = query.filter(Diaper.timestamp <= end_datetime)
            except ValueError:
                return error_response('结束日期格式错误，应为 ISO 格式 (YYYY-MM-DDTHH:MM:SS)', 400)

        # 执行查询
        diapers = query.all()
        diapers_data = [DiaperResponse.from_orm(diaper) for diaper in diapers]

        return success_response('获取大小便记录成功', diapers_data, 200)

    except Exception as e:
        return error_response(f'获取大小便记录失败: {str(e)}')

@diaper_bp.route('/default-baby', methods=['GET'])
@jwt_required()
def get_diapers_for_default_baby():
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
        diaper_type = request.args.get('type')  # 'wet', 'dirty', 或 None(全部)

        # 构建查询
        query = Diaper.query.filter_by(baby_id=baby.id).order_by(Diaper.timestamp.desc())

        # 按类型过滤
        if diaper_type and diaper_type in ['wet', 'dirty']:
            query = query.filter_by(diaper_type=diaper_type)

        # 按日期范围过滤
        if start_date:
            try:
                start_datetime = datetime.fromisoformat(start_date)
                query = query.filter(Diaper.timestamp >= start_datetime)
            except ValueError:
                return error_response('开始日期格式错误，应为 ISO 格式 (YYYY-MM-DDTHH:MM:SS)', 400)

        if end_date:
            try:
                end_datetime = datetime.fromisoformat(end_date)
                query = query.filter(Diaper.timestamp <= end_datetime)
            except ValueError:
                return error_response('结束日期格式错误，应为 ISO 格式 (YYYY-MM-DDTHH:MM:SS)', 400)

        # 执行查询
        diapers = query.all()
        diapers_data = [DiaperResponse.from_orm(diaper) for diaper in diapers]

        return success_response('获取大小便记录成功', diapers_data, 200)

    except Exception as e:
        return error_response(f'获取大小便记录失败: {str(e)}')

@diaper_bp.route('/<int:diaper_id>', methods=['PUT'])
@jwt_required()
def update_diaper(diaper_id):
    try:
        # 获取当前用户
        current_user = get_current_user()
        if not current_user:
            return error_response('用户未登录', 401)

        # 获取大小便记录
        diaper = Diaper.query.filter_by(id=diaper_id).first()
        if not diaper:
            return error_response('大小便记录不存在', 404)

        # 验证用户是否有权限访问该婴儿的记录
        baby = diaper.baby
        if baby.user_id != current_user.id:
            return error_response('无权限访问该记录', 403)

        # 验证输入数据
        update_data = DiaperUpdate(**request.json)

        # 更新记录
        if update_data.diaper_type is not None:
            diaper.diaper_type = update_data.diaper_type
        if update_data.timestamp is not None:
            diaper.timestamp = update_data.timestamp
        if update_data.notes is not None:
            diaper.notes = update_data.notes

        db.session.commit()

        return success_response('大小便记录更新成功', DiaperResponse.from_orm(diaper).dict(), 200)

    except Exception as e:
        db.session.rollback()
        return error_response(f'更新大小便记录失败: {str(e)}')

@diaper_bp.route('/<int:diaper_id>', methods=['DELETE'])
@jwt_required()
def delete_diaper(diaper_id):
    try:
        # 获取当前用户
        current_user = get_current_user()
        if not current_user:
            return error_response('用户未登录', 401)

        # 获取大小便记录
        diaper = Diaper.query.filter_by(id=diaper_id).first()
        if not diaper:
            return error_response('大小便记录不存在', 404)

        # 验证用户是否有权限访问该婴儿的记录
        baby = diaper.baby
        if baby.user_id != current_user.id:
            return error_response('无权限访问该记录', 403)

        # 删除记录
        db.session.delete(diaper)
        db.session.commit()

        return success_response(message='大小便记录删除成功', status_code=200)

    except Exception as e:
        db.session.rollback()
        return error_response(f'删除大小便记录失败: {str(e)}')