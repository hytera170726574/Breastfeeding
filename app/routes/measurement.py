from flask import Blueprint, request, jsonify
from app import db
from app.models.models import Measurement
from app.schemas.schemas import MeasurementCreate, MeasurementUpdate, MeasurementResponse
from app.utils.helpers import get_current_user, success_response, error_response, parse_iso_datetime
from flask_jwt_extended import jwt_required

measurement_bp = Blueprint('measurement_bp', __name__)

@measurement_bp.route('/', methods=['POST'])
@jwt_required()
def create_measurement():
    try:
        # 获取当前用户
        current_user = get_current_user()
        if not current_user:
            return error_response('用户未登录', 401)

        # 验证输入数据
        measurement_data = MeasurementCreate(**request.json)

        # 验证婴儿权限
        from app.models.models import Baby
        baby = Baby.query.filter_by(id=measurement_data.baby_id, user_id=current_user.id).first()
        if not baby:
            return error_response('无权限访问该婴儿记录', 403)

        # 检查同一天是否已有记录
        existing_measurement = Measurement.query.filter_by(
            baby_id=measurement_data.baby_id,
            measurement_date=measurement_data.measurement_date
        ).first()

        if existing_measurement:
            return error_response('该日期已存在测量记录，请使用更新功能', 400)

        # 创建体重身长记录
        measurement = Measurement(
            weight_kg=measurement_data.weight_kg,
            height_cm=measurement_data.height_cm,
            measurement_date=measurement_data.measurement_date,
            notes=measurement_data.notes,
            baby_id=measurement_data.baby_id
        )

        db.session.add(measurement)
        db.session.commit()

        return success_response('测量记录创建成功', MeasurementResponse.from_orm(measurement)), 201

    except Exception as e:
        db.session.rollback()
        return error_response(f'创建测量记录失败: {str(e)}')

@measurement_bp.route('/<int:baby_id>', methods=['GET'])
@jwt_required()
def get_measurements(baby_id):
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
        query = Measurement.query.filter_by(baby_id=baby_id).order_by(Measurement.measurement_date.desc())

        # 按日期范围过滤
        if start_date:
            try:
                start_date_obj = parse_iso_datetime(start_date).date()
                query = query.filter(Measurement.measurement_date >= start_date_obj)
            except ValueError:
                return error_response('开始日期格式错误，应为 ISO 格式 (YYYY-MM-DD)', 400)

        if end_date:
            try:
                end_date_obj = parse_iso_datetime(end_date).date()
                query = query.filter(Measurement.measurement_date <= end_date_obj)
            except ValueError:
                return error_response('结束日期格式错误，应为 ISO 格式 (YYYY-MM-DD)', 400)

        # 执行查询
        measurements = query.all()
        measurements_data = [MeasurementResponse.from_orm(measurement) for measurement in measurements]

        return success_response('获取测量记录成功', measurements_data), 200

    except Exception as e:
        return error_response(f'获取测量记录失败: {str(e)}')

@measurement_bp.route('/default-baby', methods=['GET'])
@jwt_required()
def get_measurements_for_default_baby():
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
        query = Measurement.query.filter_by(baby_id=baby.id).order_by(Measurement.measurement_date.desc())

        # 按日期范围过滤
        if start_date:
            try:
                start_date_obj = parse_iso_datetime(start_date).date()
                query = query.filter(Measurement.measurement_date >= start_date_obj)
            except ValueError:
                return error_response('开始日期格式错误，应为 ISO 格式 (YYYY-MM-DD)', 400)

        if end_date:
            try:
                end_date_obj = parse_iso_datetime(end_date).date()
                query = query.filter(Measurement.measurement_date <= end_date_obj)
            except ValueError:
                return error_response('结束日期格式错误，应为 ISO 格式 (YYYY-MM-DD)', 400)

        # 执行查询
        measurements = query.all()
        measurements_data = [MeasurementResponse.from_orm(measurement) for measurement in measurements]

        return success_response('获取测量记录成功', measurements_data), 200

    except Exception as e:
        return error_response(f'获取测量记录失败: {str(e)}')

@measurement_bp.route('/<int:measurement_id>', methods=['PUT'])
@jwt_required()
def update_measurement(measurement_id):
    try:
        # 获取当前用户
        current_user = get_current_user()
        if not current_user:
            return error_response('用户未登录', 401)

        # 获取测量记录
        measurement = Measurement.query.filter_by(id=measurement_id).first()
        if not measurement:
            return error_response('测量记录不存在', 404)

        # 验证用户是否有权限访问该婴儿的记录
        baby = measurement.baby
        if baby.user_id != current_user.id:
            return error_response('无权限访问该记录', 403)

        # 验证输入数据
        update_data = MeasurementUpdate(**request.json)

        # 更新记录
        if update_data.weight_kg is not None:
            measurement.weight_kg = update_data.weight_kg
        if update_data.height_cm is not None:
            measurement.height_cm = update_data.height_cm
        if update_data.measurement_date is not None:
            measurement.measurement_date = update_data.measurement_date
        if update_data.notes is not None:
            measurement.notes = update_data.notes

        db.session.commit()

        return success_response('测量记录更新成功', MeasurementResponse.from_orm(measurement)), 200

    except Exception as e:
        db.session.rollback()
        return error_response(f'更新测量记录失败: {str(e)}')

@measurement_bp.route('/<int:measurement_id>', methods=['DELETE'])
@jwt_required()
def delete_measurement(measurement_id):
    try:
        # 获取当前用户
        current_user = get_current_user()
        if not current_user:
            return error_response('用户未登录', 401)

        # 获取测量记录
        measurement = Measurement.query.filter_by(id=measurement_id).first()
        if not measurement:
            return error_response('测量记录不存在', 404)

        # 验证用户是否有权限访问该婴儿的记录
        baby = measurement.baby
        if baby.user_id != current_user.id:
            return error_response('无权限访问该记录', 403)

        # 删除记录
        db.session.delete(measurement)
        db.session.commit()

        return success_response('测量记录删除成功'), 200

    except Exception as e:
        db.session.rollback()
        return error_response(f'删除测量记录失败: {str(e)}')