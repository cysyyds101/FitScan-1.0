import pytest
from app import create_app, db
from app.models.measurement import Measurement
from app.models.user import User

@pytest.fixture

def app():
    app = create_app()
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    
    with app.app_context():
        db.create_all()
        yield app
        db.drop_all()

@pytest.fixture

def client(app):
    return app.test_client()

@pytest.fixture

def token(client):
    # 创建测试用户
    user = User(username='testuser', email='test@example.com')
    user.set_password('password')
    db.session.add(user)
    db.session.commit()
    
    # 登录获取token
    response = client.post('/api/user/login', json={
        'email': 'test@example.com',
        'password': 'password'
    })
    return response.json['access_token']

def test_measurement_start(client):
    """测试开始测量接口"""
    response = client.post('/api/measurement/start')
    assert response.status_code == 200
    data = response.json
    assert 'shoulderWidth' in data
    assert 'armLength' in data
    assert 'legLength' in data
    assert 'height' in data
    assert 'chest' in data
    assert 'waist' in data
    assert 'hip' in data
    assert 'sizeRecommendation' in data
    assert 'slimSizeRecommendation' in data

def test_measurement_detect_reference(client):
    """测试检测参照物接口"""
    response = client.post('/api/measurement/detect-reference', json={
        'referenceType': 'A4'
    })
    assert response.status_code == 200
    data = response.json
    assert data['detected'] == True
    assert data['referenceType'] == 'A4'
    assert data['calibrationSuccess'] == True

def test_measurement_history(client, token):
    """测试获取历史记录接口"""
    # 未登录用户
    response = client.get('/api/measurement/history')
    assert response.status_code == 200
    data = response.json
    assert isinstance(data, list)
    
    # 登录用户
    response = client.get('/api/measurement/history', headers={
        'Authorization': f'Bearer {token}'
    })
    assert response.status_code == 200
    data = response.json
    assert isinstance(data, list)

def test_measurement_save(client, token):
    """测试保存测量结果接口"""
    # 测试数据
    measurement_data = {
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
    
    # 未登录用户
    response = client.post('/api/measurement/save', json=measurement_data)
    assert response.status_code == 200
    data = response.json
    assert data['success'] == True
    assert 'id' in data
    
    # 登录用户
    response = client.post('/api/measurement/save', json=measurement_data, headers={
        'Authorization': f'Bearer {token}'
    })
    assert response.status_code == 201
    data = response.json
    assert data['success'] == True
    assert 'id' in data
    
    # 验证数据是否保存
    with client.application.app_context():
        measurement = Measurement.query.get(data['id'])
        assert measurement is not None
        assert measurement.shoulder_width == 42.5
        assert measurement.arm_length == 68.3
