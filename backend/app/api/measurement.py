from flask import request, jsonify
from flask_restx import Resource, fields
from flask_jwt_extended import jwt_required, get_jwt_identity
from app import db
from app.models.measurement import Measurement
from app.services.measurement_service import MeasurementService
from app.utils.logger import get_logger
import random

# 创建日志记录器
logger = get_logger(__name__)

class MeasurementStart(Resource):
    @jwt_required(optional=True)
    def post(self):
        """开始测量"""
        try:
            user_id = get_jwt_identity()
            logger.info(f'Starting measurement for user {user_id}')
            
            # 模拟测量数据（实际应用中应该从前端接收真实数据）
            measurement_data = {
                'shoulder_width': round(random.uniform(38, 50), 1),
                'arm_length': round(random.uniform(60, 75), 1),
                'leg_length': round(random.uniform(85, 105), 1),
                'height': round(random.uniform(160, 190), 1),
                'chest': round(random.uniform(80, 110), 1),
                'waist': round(random.uniform(65, 95), 1),
                'hip': round(random.uniform(85, 115), 1)
            }
            
            logger.info(f'Measurement data: {measurement_data}')
            
            # 计算尺码推荐
            size_recommendation = MeasurementService.calculate_size_recommendation(measurement_data)
            logger.info(f'Size recommendation: {size_recommendation}')
            
            # 构建响应数据
            response_data = {
                'shoulderWidth': measurement_data['shoulder_width'],
                'armLength': measurement_data['arm_length'],
                'legLength': measurement_data['leg_length'],
                'height': measurement_data['height'],
                'chest': measurement_data['chest'],
                'waist': measurement_data['waist'],
                'hip': measurement_data['hip'],
                'sizeRecommendation': size_recommendation['loose'],
                'slimSizeRecommendation': size_recommendation['slim']
            }
            
            logger.info(f'Measurement completed successfully for user {user_id}')
            return jsonify(response_data), 200
        except Exception as e:
            logger.error(f'Error starting measurement: {str(e)}')
            return jsonify({'error': str(e)}), 500

class MeasurementDetectReference(Resource):
    def post(self):
        """检测参照物"""
        try:
            data = request.get_json()
            reference_type = data.get('referenceType', 'A4')
            logger.info(f'Detecting reference: {reference_type}')
            
            # 检测参照物
            result = MeasurementService.detect_reference(reference_type)
            logger.info(f'Reference detection result: {result}')
            
            return jsonify(result), 200
        except Exception as e:
            logger.error(f'Error detecting reference: {str(e)}')
            return jsonify({'error': str(e)}), 500

class MeasurementHistory(Resource):
    @jwt_required(optional=True)
    def get(self):
        """获取历史记录"""
        try:
            user_id = get_jwt_identity()
            logger.info(f'Getting measurement history for user {user_id}')
            
            if user_id:
                # 获取当前用户的测量记录
                measurements = Measurement.query.filter_by(user_id=user_id).order_by(Measurement.created_at.desc()).all()
                logger.info(f'Found {len(measurements)} measurements for user {user_id}')
            else:
                # 未登录用户返回示例数据
                # 实际应用中应该返回空列表或要求登录
                measurements = []
                logger.info('User not logged in, returning sample data')
            
            # 转换为前端需要的格式
            history_data = []
            for measurement in measurements:
                history_data.append({
                    'id': measurement.id,
                    'date': measurement.created_at.strftime('%Y-%m-%d'),
                    'time': measurement.created_at.strftime('%H:%M'),
                    'data': measurement.to_dict()
                })
            
            # 如果没有数据，返回示例数据
            if not history_data:
                # 生成示例数据
                sample_data = [
                    {
                        'id': 1,
                        'date': '2026-04-12',
                        'time': '14:30',
                        'data': {
                            'shoulderWidth': 42.5,
                            'armLength': 68.3,
                            'legLength': 95.7,
                            'height': 175.2,
                            'chest': 92.1,
                            'waist': 76.5,
                            'hip': 94.3,
                            'sizeRecommendation': 'M (宽松版)',
                            'slimSizeRecommendation': 'M (修身版)'
                        }
                    },
                    {
                        'id': 2,
                        'date': '2026-04-10',
                        'time': '10:15',
                        'data': {
                            'shoulderWidth': 43.0,
                            'armLength': 68.3,
                            'legLength': 95.7,
                            'height': 175.2,
                            'chest': 93.5,
                            'waist': 76.5,
                            'hip': 94.3,
                            'sizeRecommendation': 'L (宽松版)',
                            'slimSizeRecommendation': 'M (修身版)'
                        }
                    },
                    {
                        'id': 3,
                        'date': '2026-04-05',
                        'time': '16:45',
                        'data': {
                            'shoulderWidth': 42.5,
                            'armLength': 68.3,
                            'legLength': 96.5,
                            'height': 176.0,
                            'chest': 92.1,
                            'waist': 76.5,
                            'hip': 94.3,
                            'sizeRecommendation': 'M (宽松版)',
                            'slimSizeRecommendation': 'M (修身版)'
                        }
                    }
                ]
                logger.info('Returning sample measurement data')
                return jsonify(sample_data), 200
            
            logger.info(f'Returning {len(history_data)} measurement records')
            return jsonify(history_data), 200
        except Exception as e:
            logger.error(f'Error getting measurement history: {str(e)}')
            return jsonify({'error': str(e)}), 500

class MeasurementSave(Resource):
    @jwt_required(optional=True)
    def post(self):
        """保存测量结果"""
        try:
            user_id = get_jwt_identity()
            data = request.get_json()
            logger.info(f'Saving measurement for user {user_id}')
            
            # 验证数据
            required_fields = ['shoulderWidth', 'armLength', 'legLength', 'height', 'chest', 'waist', 'hip', 'sizeRecommendation', 'slimSizeRecommendation']
            for field in required_fields:
                if field not in data:
                    logger.error(f'Missing required field: {field}')
                    return jsonify({'error': f'Missing required field: {field}'}), 400
            
            # 如果用户已登录，保存到数据库
            if user_id:
                measurement = Measurement(
                    user_id=user_id,
                    shoulder_width=data['shoulderWidth'],
                    arm_length=data['armLength'],
                    leg_length=data['legLength'],
                    height=data['height'],
                    chest=data['chest'],
                    waist=data['waist'],
                    hip=data['hip'],
                    size_recommendation=data['sizeRecommendation'],
                    slim_size_recommendation=data['slimSizeRecommendation']
                )
                db.session.add(measurement)
                db.session.commit()
                logger.info(f'Measurement saved successfully with id {measurement.id} for user {user_id}')
                return jsonify({'success': True, 'id': measurement.id}), 201
            else:
                # 未登录用户返回成功但不保存
                mock_id = int(random.random() * 1000000)
                logger.info(f'User not logged in, returning mock id {mock_id}')
                return jsonify({'success': True, 'id': mock_id}), 200
        except Exception as e:
            logger.error(f'Error saving measurement: {str(e)}')
            return jsonify({'error': str(e)}), 500
