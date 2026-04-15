from flask import request, jsonify
from flask_restx import Resource, fields
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from app import db
from app.models.user import User

class UserRegister(Resource):
    def post(self):
        """用户注册"""
        try:
            data = request.get_json()
            
            # 验证数据
            if not data or 'username' not in data or 'email' not in data or 'password' not in data:
                return jsonify({'error': 'Missing required fields'}), 400
            
            # 检查用户名是否已存在
            if User.query.filter_by(username=data['username']).first():
                return jsonify({'error': 'Username already exists'}), 400
            
            # 检查邮箱是否已存在
            if User.query.filter_by(email=data['email']).first():
                return jsonify({'error': 'Email already exists'}), 400
            
            # 创建新用户
            user = User(
                username=data['username'],
                email=data['email']
            )
            user.set_password(data['password'])
            
            db.session.add(user)
            db.session.commit()
            
            # 创建访问令牌
            access_token = create_access_token(identity=user.id)
            
            return jsonify({
                'access_token': access_token,
                'user': user.to_dict()
            }), 201
        except Exception as e:
            return jsonify({'error': str(e)}), 500

class UserLogin(Resource):
    def post(self):
        """用户登录"""
        try:
            data = request.get_json()
            
            # 验证数据
            if not data or 'email' not in data or 'password' not in data:
                return jsonify({'error': 'Missing required fields'}), 400
            
            # 查找用户
            user = User.query.filter_by(email=data['email']).first()
            
            # 验证用户和密码
            if not user or not user.check_password(data['password']):
                return jsonify({'error': 'Invalid email or password'}), 401
            
            # 创建访问令牌
            access_token = create_access_token(identity=user.id)
            
            return jsonify({
                'access_token': access_token,
                'user': user.to_dict()
            }), 200
        except Exception as e:
            return jsonify({'error': str(e)}), 500

class UserProfile(Resource):
    @jwt_required()
    def get(self):
        """获取用户信息"""
        try:
            user_id = get_jwt_identity()
            user = User.query.get(user_id)
            
            if not user:
                return jsonify({'error': 'User not found'}), 404
            
            return jsonify(user.to_dict()), 200
        except Exception as e:
            return jsonify({'error': str(e)}), 500
