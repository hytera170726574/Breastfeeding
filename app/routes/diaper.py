from flask import Blueprint, request, jsonify
from app import db
from app.models.models import Diaper
from app.schemas.schemas import DiaperCreate, DiaperUpdate, DiaperResponse
from app.utils.helpers import get_current_user, success_response, error_response, parse_iso_datetime
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

        # 如果提供了时间戳或备注，使用它们；否则使用默认值
        if diaper_data.timestamp:
            diaper.timestamp = diaper_data.timestamp
        if getattr(diaper_data, 'notes', None) is not None:
            diaper.notes = diaper_data.notes

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

        # 基础查询（先按 baby_id 和可选类型过滤）
        base_q = Diaper.query.filter_by(baby_id=baby_id)
        if diaper_type and diaper_type in ['wet', 'dirty']:
            base_q = base_q.filter_by(diaper_type=diaper_type)

        # 解析日期范围：支持 YYYY-MM-DD 或 ISO 时间。如果两者都未提供，默认取今日 00:00 到现在
        start_datetime = None
        end_datetime = None
        try:
            if start_date:
                s = start_date
                if len(s) == 10 and s.count('-') == 2:
                    s = s + 'T00:00:00'
                start_datetime = parse_iso_datetime(s)
            if end_date:
                e = end_date
                if len(e) == 10 and e.count('-') == 2:
                    e = e + 'T23:59:59.999'
                end_datetime = parse_iso_datetime(e)
        except ValueError:
            return error_response('开始/结束日期格式错误，应为 YYYY-MM-DD 或 ISO 格式', 400)

        from datetime import datetime as _dt
        if start_datetime is None and end_datetime is None:
            # 默认：今天的本地日期窗口（以 UTC 存储的 naive 时间为准）
            now = _dt.utcnow()
            start_datetime = now.replace(hour=0, minute=0, second=0, microsecond=0)
            end_datetime = now
        elif start_datetime is None and end_datetime is not None:
            # 如果只提供 end，则把 start 设为当天 00:00
            s = end_datetime
            start_datetime = s.replace(hour=0, minute=0, second=0, microsecond=0)
        elif end_datetime is None and start_datetime is not None:
            # 如果只提供 start，则把 end 设为 now
            end_datetime = _dt.utcnow()

        # 在 base 查询上应用时间过滤
        filtered_q = base_q.filter(Diaper.timestamp >= start_datetime, Diaper.timestamp <= end_datetime)

        # 支持简单分页参数 limit/offset（可选）
        try:
            limit = int(request.args.get('limit', 1000))
            offset = int(request.args.get('offset', 0))
        except Exception:
            return error_response('limit/offset 必须为整数', 400)

        total = filtered_q.count()
        diapers = filtered_q.order_by(Diaper.timestamp.asc()).offset(offset).limit(limit).all()
        diapers_data = [DiaperResponse.from_orm(diaper).dict() for diaper in diapers]

        # 返回列表（data 仍为数组以兼容前端），并在 meta 中包含分页信息
        payload = {
            'items': diapers_data,
            'meta': {
                'total': total,
                'limit': limit,
                'offset': offset
            }
        }
        return jsonify({'message': '获取大小便记录成功', 'data': diapers_data, 'meta': payload['meta']}), 200

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

        # 基础查询
        base_q = Diaper.query.filter_by(baby_id=baby.id)
        if diaper_type and diaper_type in ['wet', 'dirty']:
            base_q = base_q.filter_by(diaper_type=diaper_type)

        # 解析并应用时间范围（与上方实现保持一致）
        start_datetime = None
        end_datetime = None
        try:
            if start_date:
                s = start_date
                if len(s) == 10 and s.count('-') == 2:
                    s = s + 'T00:00:00'
                start_datetime = parse_iso_datetime(s)
            if end_date:
                e = end_date
                if len(e) == 10 and e.count('-') == 2:
                    e = e + 'T23:59:59.999'
                end_datetime = parse_iso_datetime(e)
        except ValueError:
            return error_response('开始/结束日期格式错误，应为 YYYY-MM-DD 或 ISO 格式', 400)

        from datetime import datetime as _dt
        if start_datetime is None and end_datetime is None:
            now = _dt.utcnow()
            start_datetime = now.replace(hour=0, minute=0, second=0, microsecond=0)
            end_datetime = now
        elif start_datetime is None and end_datetime is not None:
            start_datetime = end_datetime.replace(hour=0, minute=0, second=0, microsecond=0)
        elif end_datetime is None and start_datetime is not None:
            end_datetime = _dt.utcnow()

        filtered_q = base_q.filter(Diaper.timestamp >= start_datetime, Diaper.timestamp <= end_datetime)

        try:
            limit = int(request.args.get('limit', 1000))
            offset = int(request.args.get('offset', 0))
        except Exception:
            return error_response('limit/offset 必须为整数', 400)

        total = filtered_q.count()
        diapers = filtered_q.order_by(Diaper.timestamp.asc()).offset(offset).limit(limit).all()
        diapers_data = [DiaperResponse.from_orm(diaper).dict() for diaper in diapers]

        return jsonify({'message': '获取大小便记录成功', 'data': diapers_data, 'meta': {'total': total, 'limit': limit, 'offset': offset}}), 200

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