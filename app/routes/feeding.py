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
from app.utils.helpers import get_current_user, success_response, error_response, parse_iso_datetime
from flask_jwt_extended import jwt_required
from datetime import datetime
from sqlalchemy import text

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

# NOTE: legacy `/api/feeding/bottle` endpoint has been removed. Use
# - POST /api/feeding/formula for formula feedings
# - POST /api/feeding/breast-bottle for bottle-fed breastmilk
# The old endpoint was removed to simplify API surface and avoid ambiguity.

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

        # 使用原子更新来避免并发竞态：先尝试 UPDATE，如果没有行被更新则插入新行
        table_name = MilkInventory.__table__.name
        now = datetime.utcnow()
        upd = db.session.execute(
            text(f"UPDATE {table_name} SET remaining_ml = remaining_ml + :v, updated_at = :now WHERE baby_id = :bid"),
            {"v": data.volume_ml, "now": now, "bid": data.baby_id}
        )
        if upd.rowcount == 0:
            # 没有现有条目，插入一条新记录
            inv = MilkInventory(baby_id=data.baby_id, remaining_ml=data.volume_ml, updated_at=now)
            db.session.add(inv)
            # 确保我们能返回剩余量
            db.session.flush()
            remaining = inv.remaining_ml
        else:
            # 查询最新值以返回
            inv = MilkInventory.query.filter_by(baby_id=data.baby_id).first()
            remaining = inv.remaining_ml

        db.session.commit()

        return success_response('吸奶记录成功，余量已更新', {
            'pump_id': pump.id,
            'baby_id': data.baby_id,
            'volume_ml': data.volume_ml,
            'remaining_ml': remaining
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
                start_datetime = parse_iso_datetime(start_date)
                query = query.filter(Feeding.start_time >= start_datetime)
            except ValueError:
                return error_response('开始日期格式错误，应为 ISO 格式 (YYYY-MM-DDTHH:MM:SS)', 400)

        if end_date:
            try:
                end_datetime = parse_iso_datetime(end_date)
                query = query.filter(Feeding.start_time <= end_datetime)
            except ValueError:
                return error_response('结束日期格式错误，应为 ISO 格式 (YYYY-MM-DDTHH:MM:SS)', 400)

        # 执行查询
        feedings = query.all()
        feedings_data = [FeedingResponse.from_orm(feeding) for feeding in feedings]

        return success_response('获取喂养记录成功', feedings_data, 200)

    except Exception as e:
        return error_response(f'获取喂养记录失败: {str(e)}')


@feeding_bp.route('/count', methods=['GET'])
@jwt_required()
def count_feedings():
    try:
        current_user = get_current_user()
        if not current_user:
            return error_response('用户未登录', 401)

        baby_id = request.args.get('baby_id')
        if not baby_id:
            # fallback to user's default baby if available
            if not current_user.default_baby_id:
                return error_response('缺少 baby_id 参数，且未设置默认婴儿', 400)
            baby_id = current_user.default_baby_id
        try:
            baby_id = int(baby_id)
        except ValueError:
            return error_response('baby_id 必须为整数', 400)

        from app.models.models import Baby
        baby = Baby.query.filter_by(id=baby_id, user_id=current_user.id).first()
        if not baby:
            return error_response('无权限访问该婴儿记录', 403)

        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        # 默认：今天 00:00 到现在
        if start_date:
            try:
                start_dt = parse_iso_datetime(start_date)
            except ValueError:
                return error_response('开始日期格式错误，应为 ISO 格式 (YYYY-MM-DDTHH:MM:SS)', 400)
        else:
            # default to local day's 00:00 converted to UTC so "today" matches user's local date when frontend
            # doesn't supply start_date. We compute local midnight then convert to UTC-aware naive datetime.
            local_now = datetime.now()
            local_midnight = local_now.replace(hour=0, minute=0, second=0, microsecond=0)
            # convert local midnight to UTC naive datetime for comparison with UTC stored DB timestamps
            start_dt = datetime.utcfromtimestamp(local_midnight.timestamp())

        if end_date:
            try:
                end_dt = parse_iso_datetime(end_date)
            except ValueError:
                return error_response('结束日期格式错误，应为 ISO 格式 (YYYY-MM-DDTHH:MM:SS)', 400)
        else:
            # use current UTC now as end
            end_dt = datetime.utcnow()

        # Count only direct breastfeeding as "亲喂次数" per product decision
        direct_count = DirectBreastfeeding.query.filter(
            DirectBreastfeeding.baby_id == baby_id,
            DirectBreastfeeding.start_time >= start_dt,
            DirectBreastfeeding.start_time <= end_dt
        ).count()

        total = direct_count

        return success_response('获取亲喂次数成功', {
            'total': total,
            'breakdown': {
                'direct': direct_count
            }
        }, 200)
    except Exception as e:
        return error_response(f'获取喂养次数失败: {str(e)}')

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
                start_datetime = parse_iso_datetime(start_date)
                query = query.filter(Feeding.start_time >= start_datetime)
            except ValueError:
                return error_response('开始日期格式错误，应为 ISO 格式 (YYYY-MM-DDTHH:MM:SS)', 400)

        if end_date:
            try:
                end_datetime = parse_iso_datetime(end_date)
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
            try:
                sd = parse_iso_datetime(start_date)
                q = q.filter(DirectBreastfeeding.start_time >= sd)
            except ValueError:
                return error_response('开始日期格式错误，应为 ISO 格式 (YYYY-MM-DDTHH:MM:SS)', 400)
        if end_date:
            try:
                ed = parse_iso_datetime(end_date)
                q = q.filter(DirectBreastfeeding.start_time <= ed)
            except ValueError:
                return error_response('结束日期格式错误，应为 ISO 格式 (YYYY-MM-DDTHH:MM:SS)', 400)
        recs = q.all()
        data = [DirectBreastResponse.from_orm(r).dict() for r in recs]
        return success_response('获取亲喂记录成功', data, 200)
    except Exception as e:
        return error_response(f'获取亲喂记录失败: {str(e)}')


@feeding_bp.route('/direct/active', methods=['GET'])
@jwt_required()
def get_active_direct():
    """Return the active direct breastfeeding record (end_time is NULL) for a baby, if any."""
    try:
        current_user = get_current_user()
        if not current_user:
            return error_response('用户未登录', 401)

        baby_id = request.args.get('baby_id')
        if not baby_id:
            if not current_user.default_baby_id:
                return error_response('缺少 baby_id 参数，且未设置默认婴儿', 400)
            baby_id = current_user.default_baby_id
        try:
            baby_id = int(baby_id)
        except ValueError:
            return error_response('baby_id 必须为整数', 400)

        from app.models.models import Baby
        baby = Baby.query.filter_by(id=baby_id, user_id=current_user.id).first()
        if not baby:
            return error_response('无权限访问该婴儿记录', 403)

        rec = DirectBreastfeeding.query.filter_by(baby_id=baby_id).filter(DirectBreastfeeding.end_time.is_(None)).order_by(DirectBreastfeeding.start_time.desc()).first()
        if not rec:
            return success_response('没有活动的亲喂记录', None, 200)

        return success_response('获取活动亲喂记录成功', DirectBreastResponse.from_orm(rec).dict(), 200)
    except Exception as e:
        return error_response(f'获取活动亲喂记录失败: {str(e)}')

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

        # 使用原子更新：仅在剩余量足够时扣减，避免竞态条件
        table_name = MilkInventory.__table__.name
        now = datetime.utcnow()
        upd = db.session.execute(
            text(f"UPDATE {table_name} SET remaining_ml = remaining_ml - :v, updated_at = :now WHERE baby_id = :bid AND (remaining_ml IS NOT NULL AND remaining_ml >= :v)"),
            {"v": data.volume_ml, "now": now, "bid": data.baby_id}
        )
        if upd.rowcount == 0:
            inv_check = MilkInventory.query.filter_by(baby_id=data.baby_id).first()
            if not inv_check or (inv_check.remaining_ml or 0) < data.volume_ml:
                return error_response('剩余母乳量不足', 400)

        rec = BottleBreastFeeding(
            baby_id=data.baby_id,
            timestamp=data.timestamp or datetime.utcnow(),
            volume_ml=data.volume_ml,
            notes=data.notes,
        )
        db.session.add(rec)

        # 查询并返回最新余量
        inv = MilkInventory.query.filter_by(baby_id=data.baby_id).first()
        remaining = inv.remaining_ml if inv else 0

        db.session.commit()
        return success_response('瓶喂母乳记录成功', BottleBreastResponse.from_orm(rec).dict() | {'remaining_ml': remaining}, 201)
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
            try:
                sd = parse_iso_datetime(start_date)
                q = q.filter(BottleBreastFeeding.timestamp >= sd)
            except ValueError:
                return error_response('开始日期格式错误，应为 ISO 格式 (YYYY-MM-DDTHH:MM:SS)', 400)
        if end_date:
            try:
                ed = parse_iso_datetime(end_date)
                q = q.filter(BottleBreastFeeding.timestamp <= ed)
            except ValueError:
                return error_response('结束日期格式错误，应为 ISO 格式 (YYYY-MM-DDTHH:MM:SS)', 400)
        recs = q.all()
        data = [BottleBreastResponse.from_orm(r).dict() for r in recs]
        return success_response('获取瓶喂母乳记录成功', data, 200)
    except Exception as e:
        return error_response(f'获取瓶喂母乳记录失败: {str(e)}')


@feeding_bp.route('/pumps/<int:baby_id>', methods=['GET'])
@jwt_required()
def list_pumps(baby_id):
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
        q = MilkPump.query.filter_by(baby_id=baby_id).order_by(MilkPump.start_time.desc())

        if start_date:
            try:
                sd = parse_iso_datetime(start_date)
                q = q.filter(MilkPump.start_time >= sd)
            except ValueError:
                return error_response('开始日期格式错误，应为 ISO 格式 (YYYY-MM-DDTHH:MM:SS)', 400)
        if end_date:
            try:
                ed = parse_iso_datetime(end_date)
                q = q.filter(MilkPump.start_time <= ed)
            except ValueError:
                return error_response('结束日期格式错误，应为 ISO 格式 (YYYY-MM-DDTHH:MM:SS)', 400)

        recs = q.all()
        # Simple serialization
        data = []
        for r in recs:
            data.append({
                'id': r.id,
                'start_time': r.start_time.isoformat() if r.start_time else None,
                'end_time': r.end_time.isoformat() if r.end_time else None,
                'volume_ml': r.volume_ml,
                'notes': r.notes,
                'created_at': r.created_at.isoformat() if r.created_at else None
            })

        return success_response('获取泵奶记录成功', data, 200)
    except Exception as e:
        return error_response(f'获取泵奶记录失败: {str(e)}')


@feeding_bp.route('/bottle-ml', methods=['GET'])
@jwt_required()
def bottle_ml_total():
    """返回在时间范围内（默认今天 00:00 到现在）婴儿的瓶喂总毫升数（包含瓶喂母乳与配方奶）"""
    try:
        current_user = get_current_user()
        if not current_user:
            return error_response('用户未登录', 401)

        baby_id = request.args.get('baby_id')
        if not baby_id:
            if not current_user.default_baby_id:
                return error_response('缺少 baby_id 参数，且未设置默认婴儿', 400)
            baby_id = current_user.default_baby_id
        try:
            baby_id = int(baby_id)
        except ValueError:
            return error_response('baby_id 必须为整数', 400)

        from app.models.models import Baby
        baby = Baby.query.filter_by(id=baby_id, user_id=current_user.id).first()
        if not baby:
            return error_response('无权限访问该婴儿记录', 403)

        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        # 默认：今天 00:00 到现在（本地日的 00:00 转为 UTC）
        if start_date:
            try:
                start_dt = parse_iso_datetime(start_date)
            except ValueError:
                return error_response('开始日期格式错误，应为 ISO 格式 (YYYY-MM-DDTHH:MM:SS)', 400)
        else:
            sd = datetime.now()
            sd = sd.replace(hour=0, minute=0, second=0, microsecond=0)
            start_dt = datetime.utcfromtimestamp(sd.timestamp())

        if end_date:
            try:
                end_dt = parse_iso_datetime(end_date)
            except ValueError:
                return error_response('结束日期格式错误，应为 ISO 格式 (YYYY-MM-DDTHH:MM:SS)', 400)
        else:
            end_dt = datetime.utcnow()

        # Sum bottle ml from BottleBreastFeeding and FormulaFeeding
        from sqlalchemy import func
        bottle_sum = BottleBreastFeeding.query.with_entities(func.coalesce(func.sum(BottleBreastFeeding.volume_ml), 0)).filter(
            BottleBreastFeeding.baby_id == baby_id,
            BottleBreastFeeding.timestamp >= start_dt,
            BottleBreastFeeding.timestamp <= end_dt
        ).scalar() or 0

        formula_sum = FormulaFeeding.query.with_entities(func.coalesce(func.sum(FormulaFeeding.volume_ml), 0)).filter(
            FormulaFeeding.baby_id == baby_id,
            FormulaFeeding.timestamp >= start_dt,
            FormulaFeeding.timestamp <= end_dt
        ).scalar() or 0

        total_ml = int(bottle_sum) + int(formula_sum)

        return success_response('获取瓶喂总毫升数成功', {'total_ml': total_ml}, 200)
    except Exception as e:
        return error_response(f'获取瓶喂总毫升数失败: {str(e)}')

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
            try:
                sd = parse_iso_datetime(start_date)
                q = q.filter(FormulaFeeding.timestamp >= sd)
            except ValueError:
                return error_response('开始日期格式错误，应为 ISO 格式 (YYYY-MM-DDTHH:MM:SS)', 400)
        if end_date:
            try:
                ed = parse_iso_datetime(end_date)
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