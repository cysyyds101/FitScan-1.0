from flask import Blueprint
from flask_restx import Api, Namespace
from app.api.measurement import MeasurementStart, MeasurementDetectReference, MeasurementHistory, MeasurementSave
from app.api.user import UserRegister, UserLogin, UserProfile

# 创建蓝图
bp = Blueprint('api', __name__)

# 创建API实例
api = Api(
    bp,
    title='FitScan API',
    description='智能人体尺寸估算系统API',
    version='1.0',
    doc='/docs'
)

# 创建命名空间
measurement_ns = Namespace('measurement', description='测量相关接口')
user_ns = Namespace('user', description='用户相关接口')

# 注册命名空间
api.add_namespace(measurement_ns)
api.add_namespace(user_ns)

# 注册测量相关的API资源
measurement_ns.add_resource(MeasurementStart, '/start')
measurement_ns.add_resource(MeasurementDetectReference, '/detect-reference')
measurement_ns.add_resource(MeasurementHistory, '/history')
measurement_ns.add_resource(MeasurementSave, '/save')

# 注册用户相关的API资源
user_ns.add_resource(UserRegister, '/register')
user_ns.add_resource(UserLogin, '/login')
user_ns.add_resource(UserProfile, '/profile')
