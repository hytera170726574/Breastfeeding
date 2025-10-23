from flask import Blueprint, request, jsonify
from app import db
from app.models.models import (
    Feeding,
    MilkInventory,
    MilkPump,
    DirectBreastfeeding,
    BottleBreastFeeding,
    FormulaFeeding,
)
from app.schemas.schemas import (
    FeedingCreate,
    BottleFeedingCreate,
    BreastFeedingStart,
    BreastFeedingEnd,
    FeedingUpdate,
    FeedingResponse,
    MilkPumpCreate,
    BottleBreastCreate,
    MilkInventoryResponse,
    DirectBreastStart,
    DirectBreastEnd,
    DirectBreastResponse,
    FormulaFeedingCreate,
    FormulaFeedingResponse,
    BottleBreastResponse,
)
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

@feeding_bp.route('/breastToPump', methods=['POST'])
@jwt_required()
def breast_to_pump():
    """记录吸奶时间和吸奶量，并累加剩余母乳量"""
    try:
        current_user = get_current_user()
        if not current_user:
            return error_response('用户未登录', 401)

        data = MilkPumpCreate(**request.json)

        # 权限校验
        from app.models.models import Baby
        baby = Baby.query.filter_by(id=data.baby_id, user_id=current_user.id).first()
        if not baby:
            return error_response('无权限访问该婴儿记录', 403)

        # 创建吸奶记录
        pump = MilkPump(
            baby_id=data.baby_id,
            start_time=data.start_time,
            end_time=data.end_time,
            volume_ml=data.volume_ml,
            notes=data.notes
        )
        db.session.add(pump)

        # 更新或创建余量
        inv = MilkInventory.query.filter_by(baby_id=data.baby_id).first()
        if not inv:
            inv = MilkInventory(baby_id=data.baby_id, remaining_ml=0)
            db.session.add(inv)
        inv.remaining_ml = (inv.remaining_ml or 0) + data.volume_ml
        inv.updated_at = datetime.utcnow()

        db.session.commit()

        return success_response('吸奶记录成功，余量已更新', {
            'pump_id': pump.id,
            'baby_id': data.baby_id,
            'volume_ml': data.volume_ml,
            'remaining_ml': inv.remaining_ml
        }, 201)
    except Exception as e:
        db.session.rollback()
        return error_response(f'记录吸奶失败: {str(e)}')

@feeding_bp.route('/breastBottle', methods=['POST'])
@jwt_required()
def breast_bottle_feed():
    """记录瓶喂母乳并扣减剩余母乳量"""
    try:
        current_user = get_current_user()
        if not current_user:
            return error_response('用户未登录', 401)

        data = BottleBreastCreate(**request.json)

        # 权限校验
        from app.models.models import Baby
        baby = Baby.query.filter_by(id=data.baby_id, user_id=current_user.id).first()
        if not baby:
            return error_response('无权限访问该婴儿记录', 403)

        inv = MilkInventory.query.filter_by(baby_id=data.baby_id).first()
        if not inv:
            inv = MilkInventory(baby_id=data.baby_id, remaining_ml=0)
            db.session.add(inv)
            db.session.flush()

        if (inv.remaining_ml or 0) < data.volume_ml:
            return error_response('剩余母乳量不足', 400)

        # 创建瓶喂记录（使用 Feeding 表，标记为 bottle）
        feeding = Feeding(
            feeding_type='bottle',
            start_time=data.timestamp,
            bottle_ml=data.volume_ml,
            baby_id=data.baby_id,
        )
        db.session.add(feeding)

        # 扣减余量
        inv.remaining_ml = (inv.remaining_ml or 0) - data.volume_ml
        inv.updated_at = datetime.utcnow()

        db.session.commit()

        return success_response('瓶喂母乳记录成功，余量已更新', {
            'feeding_id': feeding.id,
            'baby_id': data.baby_id,
            'volume_ml': data.volume_ml,
            'remaining_ml': inv.remaining_ml
        }, 201)
    except Exception as e:
        db.session.rollback()
        return error_response(f'记录瓶喂母乳失败: {str(e)}')

@feeding_bp.route('/breast/remaining/<int:baby_id>', methods=['GET'])
@jwt_required()
def get_breast_remaining(baby_id):
    try:
        current_user = get_current_user()
        if not current_user:
            return error_response('用户未登录', 401)

        from app.models.models import Baby
        baby = Baby.query.filter_by(id=baby_id, user_id=current_user.id).first()
        if not baby:
            return error_response('无权限访问该婴儿记录', 403)

        inv = MilkInventory.query.filter_by(baby_id=baby_id).first()
        remaining = inv.remaining_ml if inv else 0
        updated_at = (inv.updated_at if inv else datetime.utcnow())
        resp = MilkInventoryResponse(baby_id=baby_id, remaining_ml=remaining, updated_at=updated_at)
        return success_response('获取剩余母乳量成功', resp.dict(), 200)
    except Exception as e:
        return error_response(f'获取剩余母乳量失败: {str(e)}')

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

# ================== 新独立接口：亲喂 ==================
@feeding_bp.route('/direct/start', methods=['POST'])
@jwt_required()
def direct_breast_start():
    try:
        current_user = get_current_user()
        if not current_user:
            return error_response('用户未登录', 401)

        data = DirectBreastStart(**request.json)
        from app.models.models import Baby
        baby = Baby.query.filter_by(id=data.baby_id, user_id=current_user.id).first()
        if not baby:
            return error_response('无权限访问该婴儿记录', 403)

        rec = DirectBreastfeeding(
            baby_id=data.baby_id,
            start_time=data.start_time,
            side=data.side,
            notes=data.notes,
        )
        db.session.add(rec)
        db.session.commit()

        return success_response('亲喂开始记录成功', DirectBreastResponse.from_orm(rec).dict(), 201)
    except Exception as e:
        db.session.rollback()
        return error_response(f'记录亲喂开始失败: {str(e)}')

@feeding_bp.route('/direct/<int:rec_id>/end', methods=['PUT'])
@jwt_required()
def direct_breast_end(rec_id):
    try:
        current_user = get_current_user()
        if not current_user:
            return error_response('用户未登录', 401)

        rec = DirectBreastfeeding.query.filter_by(id=rec_id).first()
        if not rec:
            return error_response('亲喂记录不存在', 404)
        baby = rec.baby
        if baby.user_id != current_user.id:
            return error_response('无权限访问该记录', 403)

        data = DirectBreastEnd(**request.json)
        rec.end_time = data.end_time
        if data.notes is not None:
            rec.notes = data.notes

        db.session.commit()
        return success_response('亲喂结束记录成功', DirectBreastResponse.from_orm(rec).dict(), 200)
    except Exception as e:
        db.session.rollback()
        return error_response(f'记录亲喂结束失败: {str(e)}')

@feeding_bp.route('/direct/<int:baby_id>', methods=['GET'])
@jwt_required()
def list_direct_breast(baby_id):
    try:
        current_user = get_current_user()
        if not current_user:
            return error_response('用户未登录', 401)

        from app.models.models import Baby
        baby = Baby.query.filter_by(id=baby_id, user_id=current_user.id).first()
        if not baby:
            return error_response('无权限访问该婴儿记录', 403)

        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        q = DirectBreastfeeding.query.filter_by(baby_id=baby_id).order_by(DirectBreastfeeding.start_time.desc())
        if start_date:
            from datetime import datetime as dt
            try:
                sd = dt.fromisoformat(start_date)
                q = q.filter(DirectBreastfeeding.start_time >= sd)
            except ValueError:
                return error_response('开始日期格式错误，应为 ISO 格式 (YYYY-MM-DDTHH:MM:SS)', 400)
        if end_date:
            from datetime import datetime as dt
            try:
                ed = dt.fromisoformat(end_date)
                q = q.filter(DirectBreastfeeding.start_time <= ed)
            except ValueError:
                return error_response('结束日期格式错误，应为 ISO 格式 (YYYY-MM-DDTHH:MM:SS)', 400)
        recs = q.all()
        data = [DirectBreastResponse.from_orm(r).dict() for r in recs]
        return success_response('获取亲喂记录成功', data, 200)
    except Exception as e:
        return error_response(f'获取亲喂记录失败: {str(e)}')

# ================== 新独立接口：瓶喂母乳 ==================
@feeding_bp.route('/breast-bottle', methods=['POST'])
@jwt_required()
def create_breast_bottle():
    try:
        current_user = get_current_user()
        if not current_user:
            return error_response('用户未登录', 401)

        data = BottleBreastCreate(**request.json)
        from app.models.models import Baby
        baby = Baby.query.filter_by(id=data.baby_id, user_id=current_user.id).first()
        if not baby:
            return error_response('无权限访问该婴儿记录', 403)

        inv = MilkInventory.query.filter_by(baby_id=data.baby_id).first()
        if not inv:
            inv = MilkInventory(baby_id=data.baby_id, remaining_ml=0)
            db.session.add(inv)
            db.session.flush()
        if (inv.remaining_ml or 0) < data.volume_ml:
            return error_response('剩余母乳量不足', 400)

        rec = BottleBreastFeeding(
            baby_id=data.baby_id,
            timestamp=data.timestamp or datetime.utcnow(),
            volume_ml=data.volume_ml,
            notes=data.notes,
        )
        db.session.add(rec)

        inv.remaining_ml = (inv.remaining_ml or 0) - data.volume_ml
        inv.updated_at = datetime.utcnow()

        db.session.commit()
        return success_response('瓶喂母乳记录成功', BottleBreastResponse.from_orm(rec).dict() | {'remaining_ml': inv.remaining_ml}, 201)
    except Exception as e:
        db.session.rollback()
        return error_response(f'记录瓶喂母乳失败: {str(e)}')

@feeding_bp.route('/breast-bottle/<int:baby_id>', methods=['GET'])
@jwt_required()
def list_breast_bottle(baby_id):
    try:
        current_user = get_current_user()
        if not current_user:
            return error_response('用户未登录', 401)
        from app.models.models import Baby
        baby = Baby.query.filter_by(id=baby_id, user_id=current_user.id).first()
        if not baby:
            return error_response('无权限访问该婴儿记录', 403)

        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        q = BottleBreastFeeding.query.filter_by(baby_id=baby_id).order_by(BottleBreastFeeding.timestamp.desc())
        if start_date:
            from datetime import datetime as dt
            try:
                sd = dt.fromisoformat(start_date)
                q = q.filter(BottleBreastFeeding.timestamp >= sd)
            except ValueError:
                return error_response('开始日期格式错误，应为 ISO 格式 (YYYY-MM-DDTHH:MM:SS)', 400)
        if end_date:
            from datetime import datetime as dt
            try:
                ed = dt.fromisoformat(end_date)
                q = q.filter(BottleBreastFeeding.timestamp <= ed)
            except ValueError:
                return error_response('结束日期格式错误，应为 ISO 格式 (YYYY-MM-DDTHH:MM:SS)', 400)
        recs = q.all()
        data = [BottleBreastResponse.from_orm(r).dict() for r in recs]
        return success_response('获取瓶喂母乳记录成功', data, 200)
    except Exception as e:
        return error_response(f'获取瓶喂母乳记录失败: {str(e)}')

# ================== 新独立接口：配方奶粉 ==================
@feeding_bp.route('/formula', methods=['POST'])
@jwt_required()
def create_formula():
    try:
        current_user = get_current_user()
        if not current_user:
            return error_response('用户未登录', 401)

        data = FormulaFeedingCreate(**request.json)
        from app.models.models import Baby
        baby = Baby.query.filter_by(id=data.baby_id, user_id=current_user.id).first()
        if not baby:
            return error_response('无权限访问该婴儿记录', 403)

        rec = FormulaFeeding(
            baby_id=data.baby_id,
            timestamp=data.timestamp or datetime.utcnow(),
            volume_ml=data.volume_ml,
            brand=data.brand,
            notes=data.notes,
        )
        db.session.add(rec)
        db.session.commit()
        return success_response('配方奶粉记录成功', FormulaFeedingResponse.from_orm(rec).dict(), 201)
    except Exception as e:
        db.session.rollback()
        return error_response(f'记录配方奶粉失败: {str(e)}')

@feeding_bp.route('/formula/<int:baby_id>', methods=['GET'])
@jwt_required()
def list_formula(baby_id):
    try:
        current_user = get_current_user()
        if not current_user:
            return error_response('用户未登录', 401)
        from app.models.models import Baby
        baby = Baby.query.filter_by(id=baby_id, user_id=current_user.id).first()
        if not baby:
            return error_response('无权限访问该婴儿记录', 403)

        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        q = FormulaFeeding.query.filter_by(baby_id=baby_id).order_by(FormulaFeeding.timestamp.desc())
        if start_date:
            from datetime import datetime as dt
            try:
                sd = dt.fromisoformat(start_date)
                q = q.filter(FormulaFeeding.timestamp >= sd)
            except ValueError:
                return error_response('开始日期格式错误，应为 ISO 格式 (YYYY-MM-DDTHH:MM:SS)', 400)
        if end_date:
            from datetime import datetime as dt
            try:
                ed = dt.fromisoformat(end_date)
                q = q.filter(FormulaFeeding.timestamp <= ed)
            except ValueError:
                return error_response('结束日期格式错误，应为 ISO 格式 (YYYY-MM-DDTHH:MM:SS)', 400)
        recs = q.all()
        data = [FormulaFeedingResponse.from_orm(r).dict() for r in recs]
        return success_response('获取配方奶粉记录成功', data, 200)
    except Exception as e:
        return error_response(f'获取配方奶粉记录失败: {str(e)}')

# ================== 兼容：旧接口保留但不推荐 ==================
# /feeding/ (POST) /feeding/bottle (POST) /feeding/breast/start /feeding/breast/<id>/end
# 建议逐步迁移至上方新接口。