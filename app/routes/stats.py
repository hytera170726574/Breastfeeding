from flask import Blueprint, request, jsonify
from app import db
from app.models.models import Feeding, Diaper, Sleep
from app.schemas.schemas import StatsRequest
from app.utils.helpers import get_current_user, error_response
from flask_jwt_extended import jwt_required
from datetime import datetime, timedelta
from collections import defaultdict

stats_bp = Blueprint('stats_bp', __name__)

@stats_bp.route('/feeding/daily', methods=['POST'])
@jwt_required()
def get_daily_feeding_stats():
    """获取每日喂养量统计（用于柱状图）"""
    try:
        # 获取当前用户
        current_user = get_current_user()
        if not current_user:
            return error_response('用户未登录', 401)

        # 验证输入数据
        stats_request = StatsRequest(**request.json)

        # 验证婴儿权限
        from app.models.models import Baby
        baby = Baby.query.filter_by(id=stats_request.baby_id, user_id=current_user.id).first()
        if not baby:
            return error_response('无权限访问该婴儿记录', 403)

        # 查询指定时间范围内的喂养记录
        feedings = Feeding.query.filter(
            Feeding.baby_id == stats_request.baby_id,
            Feeding.start_time >= stats_request.start_date,
            Feeding.start_time <= stats_request.end_date
        ).all()

        # 按日期分组统计
        daily_stats = defaultdict(lambda: {
            'total_ml': 0,
            'breast_ml': 0,
            'bottle_ml': 0,
            'feedings_count': 0
        })

        for feeding in feedings:
            date_key = feeding.start_time.date().isoformat()
            daily_stats[date_key]['total_ml'] += feeding.total_ml
            daily_stats[date_key]['breast_ml'] += feeding.breast_ml
            daily_stats[date_key]['bottle_ml'] += feeding.bottle_ml
            daily_stats[date_key]['feedings_count'] += 1

        # 转换为图表数据格式
        dates = []
        total_ml_data = []
        breast_ml_data = []
        bottle_ml_data = []
        feedings_count_data = []

        # 按日期排序
        sorted_dates = sorted(daily_stats.keys())

        for date in sorted_dates:
            dates.append(date)
            total_ml_data.append(daily_stats[date]['total_ml'])
            breast_ml_data.append(daily_stats[date]['breast_ml'])
            bottle_ml_data.append(daily_stats[date]['bottle_ml'])
            feedings_count_data.append(daily_stats[date]['feedings_count'])

        chart_data = {
            'dates': dates,
            'series': [
                {
                    'name': '总喂养量(ml)',
                    'data': total_ml_data
                },
                {
                    'name': '母乳喂养量(ml)',
                    'data': breast_ml_data
                },
                {
                    'name': '奶粉喂养量(ml)',
                    'data': bottle_ml_data
                }
            ],
            'summary': {
                'total_feedings': sum(feedings_count_data),
                'total_ml': sum(total_ml_data),
                'average_daily_ml': round(sum(total_ml_data) / len(dates) if dates else 0, 2)
            }
        }

        return jsonify({
            'message': '获取每日喂养统计成功',
            'data': chart_data
        }), 200

    except Exception as e:
        return error_response(f'获取每日喂养统计失败: {str(e)}')

@stats_bp.route('/feeding/detail', methods=['POST'])
@jwt_required()
def get_feeding_detail_stats():
    """获取每次喂养详细记录（用于详细分析）"""
    try:
        # 获取当前用户
        current_user = get_current_user()
        if not current_user:
            return error_response('用户未登录', 401)

        # 验证输入数据
        stats_request = StatsRequest(**request.json)

        # 验证婴儿权限
        from app.models.models import Baby
        baby = Baby.query.filter_by(id=stats_request.baby_id, user_id=current_user.id).first()
        if not baby:
            return error_response('无权限访问该婴儿记录', 403)

        # 查询指定时间范围内的喂养记录
        feedings = Feeding.query.filter(
            Feeding.baby_id == stats_request.baby_id,
            Feeding.start_time >= stats_request.start_date,
            Feeding.start_time <= stats_request.end_date
        ).order_by(Feeding.start_time.desc()).all()

        # 转换为详细数据格式
        feeding_details = []
        for feeding in feedings:
            feeding_details.append({
                'id': feeding.id,
                'type': '母乳喂养' if feeding.feeding_type == 'breast' else '奶粉喂养',
                'start_time': feeding.start_time.isoformat() if feeding.start_time else None,
                'end_time': feeding.end_time.isoformat() if feeding.end_time else None,
                'duration_minutes': round(feeding.duration_minutes, 2) if feeding.duration_minutes else 0,
                'breast_ml': feeding.breast_ml,
                'bottle_ml': feeding.bottle_ml,
                'total_ml': feeding.total_ml
            })

        return jsonify({
            'message': '获取喂养详细记录成功',
            'data': feeding_details
        }), 200

    except Exception as e:
        return error_response(f'获取喂养详细记录失败: {str(e)}')

@stats_bp.route('/diaper/daily', methods=['POST'])
@jwt_required()
def get_daily_diaper_stats():
    """获取每日大小便次数统计（用于柱状图）"""
    try:
        # 获取当前用户
        current_user = get_current_user()
        if not current_user:
            return error_response('用户未登录', 401)

        # 验证输入数据
        stats_request = StatsRequest(**request.json)

        # 验证婴儿权限
        from app.models.models import Baby
        baby = Baby.query.filter_by(id=stats_request.baby_id, user_id=current_user.id).first()
        if not baby:
            return error_response('无权限访问该婴儿记录', 403)

        # 查询指定时间范围内的大小便记录
        diapers = Diaper.query.filter(
            Diaper.baby_id == stats_request.baby_id,
            Diaper.timestamp >= stats_request.start_date,
            Diaper.timestamp <= stats_request.end_date
        ).all()

        # 按日期分组统计
        daily_stats = defaultdict(lambda: {
            'wet_count': 0,
            'dirty_count': 0,
            'total_count': 0
        })

        for diaper in diapers:
            date_key = diaper.timestamp.date().isoformat()
            daily_stats[date_key]['total_count'] += 1
            if diaper.diaper_type == 'wet':
                daily_stats[date_key]['wet_count'] += 1
            elif diaper.diaper_type == 'dirty':
                daily_stats[date_key]['dirty_count'] += 1

        # 转换为图表数据格式
        dates = []
        wet_data = []
        dirty_data = []
        total_data = []

        # 按日期排序
        sorted_dates = sorted(daily_stats.keys())

        for date in sorted_dates:
            dates.append(date)
            wet_data.append(daily_stats[date]['wet_count'])
            dirty_data.append(daily_stats[date]['dirty_count'])
            total_data.append(daily_stats[date]['total_count'])

        chart_data = {
            'dates': dates,
            'series': [
                {
                    'name': '小便次数',
                    'data': wet_data
                },
                {
                    'name': '大便次数',
                    'data': dirty_data
                },
                {
                    'name': '总计次数',
                    'data': total_data
                }
            ],
            'summary': {
                'total_wet': sum(wet_data),
                'total_dirty': sum(dirty_data),
                'total_diapers': sum(total_data),
                'average_daily': round(sum(total_data) / len(dates) if dates else 0, 2)
            }
        }

        return jsonify({
            'message': '获取每日大小便统计成功',
            'data': chart_data
        }), 200

    except Exception as e:
        return error_response(f'获取每日大小便统计失败: {str(e)}')

@stats_bp.route('/sleep/daily', methods=['POST'])
@jwt_required()
def get_daily_sleep_stats():
    """获取每日睡眠时间统计（用于柱状图）"""
    try:
        # 获取当前用户
        current_user = get_current_user()
        if not current_user:
            return error_response('用户未登录', 401)

        # 验证输入数据
        stats_request = StatsRequest(**request.json)

        # 验证婴儿权限
        from app.models.models import Baby
        baby = Baby.query.filter_by(id=stats_request.baby_id, user_id=current_user.id).first()
        if not baby:
            return error_response('无权限访问该婴儿记录', 403)

        # 查询指定时间范围内的睡眠记录
        sleeps = Sleep.query.filter(
            Sleep.baby_id == stats_request.baby_id,
            Sleep.start_time >= stats_request.start_date,
            Sleep.start_time <= stats_request.end_date
        ).all()

        # 按日期分组统计
        daily_stats = defaultdict(lambda: {
            'total_minutes': 0.0,
            'sleep_count': 0
        })

        for sleep in sleeps:
            if sleep.end_time:
                date_key = sleep.start_time.date().isoformat()
                daily_stats[date_key]['total_minutes'] += sleep.duration_minutes
                daily_stats[date_key]['sleep_count'] += 1

        # 转换为图表数据格式
        dates = []
        minutes_data = []
        count_data = []

        # 按日期排序
        sorted_dates = sorted(daily_stats.keys())

        for date in sorted_dates:
            dates.append(date)
            minutes_data.append(round(daily_stats[date]['total_minutes'], 2))
            count_data.append(daily_stats[date]['sleep_count'])

        chart_data = {
            'dates': dates,
            'series': [
                {
                    'name': '睡眠时间(分钟)',
                    'data': minutes_data
                },
                {
                    'name': '睡眠次数',
                    'data': count_data
                }
            ],
            'summary': {
                'total_minutes': round(sum(minutes_data), 2),
                'total_sleeps': sum(count_data),
                'average_daily_minutes': round(sum(minutes_data) / len(dates) if dates else 0, 2),
                'average_sleeps_per_day': round(sum(count_data) / len(dates) if dates else 0, 2)
            }
        }

        return jsonify({
            'message': '获取每日睡眠统计成功',
            'data': chart_data
        }), 200

    except Exception as e:
        return error_response(f'获取每日睡眠统计失败: {str(e)}')

@stats_bp.route('/sleep/detail', methods=['POST'])
@jwt_required()
def get_sleep_detail_stats():
    """获取每次睡眠详细记录（用于详细分析）"""
    try:
        # 获取当前用户
        current_user = get_current_user()
        if not current_user:
            return error_response('用户未登录', 401)

        # 验证输入数据
        stats_request = StatsRequest(**request.json)

        # 验证婴儿权限
        from app.models.models import Baby
        baby = Baby.query.filter_by(id=stats_request.baby_id, user_id=current_user.id).first()
        if not baby:
            return error_response('无权限访问该婴儿记录', 403)

        # 查询指定时间范围内的睡眠记录
        sleeps = Sleep.query.filter(
            Sleep.baby_id == stats_request.baby_id,
            Sleep.start_time >= stats_request.start_date,
            Sleep.start_time <= stats_request.end_date
        ).order_by(Sleep.start_time.desc()).all()

        # 转换为详细数据格式
        sleep_details = []
        for sleep in sleeps:
            if sleep.end_time:
                sleep_details.append({
                    'id': sleep.id,
                    'start_time': sleep.start_time.isoformat() if sleep.start_time else None,
                    'end_time': sleep.end_time.isoformat() if sleep.end_time else None,
                    'duration_minutes': round(sleep.duration_minutes, 2) if sleep.duration_minutes else 0
                })

        return jsonify({
            'message': '获取睡眠详细记录成功',
            'data': sleep_details
        }), 200

    except Exception as e:
        return error_response(f'获取睡眠详细记录失败: {str(e)}')

@stats_bp.route('/growth', methods=['POST'])
@jwt_required()
def get_growth_stats():
    """获取婴儿生长发育统计（体重/身长图表）"""
    try:
        # 获取当前用户
        current_user = get_current_user()
        if not current_user:
            return error_response('用户未登录', 401)

        # 验证输入数据
        stats_request = StatsRequest(**request.json)

        # 验证婴儿权限
        from app.models.models import Baby, Measurement
        baby = Baby.query.filter_by(id=stats_request.baby_id, user_id=current_user.id).first()
        if not baby:
            return error_response('无权限访问该婴儿记录', 403)

        # 查询指定时间范围内的测量记录
        measurements = Measurement.query.filter(
            Measurement.baby_id == stats_request.baby_id,
            Measurement.measurement_date >= stats_request.start_date.date(),
            Measurement.measurement_date <= stats_request.end_date.date()
        ).order_by(Measurement.measurement_date).all()

        # 转换为图表数据格式
        dates = []
        weight_data = []
        height_data = []

        for measurement in measurements:
            dates.append(measurement.measurement_date.isoformat())
            weight_data.append(measurement.weight_kg)
            height_data.append(measurement.height_cm)

        chart_data = {
            'dates': dates,
            'series': [
                {
                    'name': '体重(kg)',
                    'data': weight_data
                },
                {
                    'name': '身长(cm)',
                    'data': height_data
                }
            ],
            'summary': {
                'latest_weight': weight_data[-1] if weight_data else None,
                'latest_height': height_data[-1] if height_data else None,
                'weight_change': round(weight_data[-1] - weight_data[0], 2) if len(weight_data) > 1 else 0,
                'height_change': round(height_data[-1] - height_data[0], 2) if len(height_data) > 1 else 0
            }
        }

        return jsonify({
            'message': '获取生长发育统计成功',
            'data': chart_data
        }), 200

    except Exception as e:
        return error_response(f'获取生长发育统计失败: {str(e)}')