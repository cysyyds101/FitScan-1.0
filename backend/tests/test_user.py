import pytest
from app import create_app, db
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

def test_user_register(client):
    """测试用户注册接口"""
    response = client.post('/api/user/register', json={
        'username': 'testuser',
        'email': 'test@example.com',
        'password': 'password'
    })
    assert response.status_code == 201
    data = response.json
    assert 'access_token' in data
    assert 'user' in data
    assert data['user']['username'] == 'testuser'
    assert data['user']['email'] == 'test@example.com'

def test_user_register_existing_username(client):
    """测试注册已存在的用户名"""
    # 先注册一个用户
    client.post('/api/user/register', json={
        'username': 'testuser',
        'email': 'test@example.com',
        'password': 'password'
    })
    
    # 再次注册相同的用户名
    response = client.post('/api/user/register', json={
        'username': 'testuser',
        'email': 'test2@example.com',
        'password': 'password'
    })
    assert response.status_code == 400
    data = response.json
    assert 'error' in data

def test_user_register_existing_email(client):
    """测试注册已存在的邮箱"""
    # 先注册一个用户
    client.post('/api/user/register', json={
        'username': 'testuser',
        'email': 'test@example.com',
        'password': 'password'
    })
    
    # 再次注册相同的邮箱
    response = client.post('/api/user/register', json={
        'username': 'testuser2',
        'email': 'test@example.com',
        'password': 'password'
    })
    assert response.status_code == 400
    data = response.json
    assert 'error' in data

def test_user_login(client):
    """测试用户登录接口"""
    # 先注册一个用户
    client.post('/api/user/register', json={
        'username': 'testuser',
        'email': 'test@example.com',
        'password': 'password'
    })
    
    # 登录
    response = client.post('/api/user/login', json={
        'email': 'test@example.com',
        'password': 'password'
    })
    assert response.status_code == 200
    data = response.json
    assert 'access_token' in data
    assert 'user' in data

def test_user_login_invalid_credentials(client):
    """测试登录无效凭证"""
    response = client.post('/api/user/login', json={
        'email': 'nonexistent@example.com',
        'password': 'password'
    })
    assert response.status_code == 401
    data = response.json
    assert 'error' in data

def test_user_profile(client):
    """测试获取用户信息接口"""
    # 先注册一个用户
    register_response = client.post('/api/user/register', json={
        'username': 'testuser',
        'email': 'test@example.com',
        'password': 'password'
    })
    token = register_response.json['access_token']
    
    # 获取用户信息
    response = client.get('/api/user/profile', headers={
        'Authorization': f'Bearer {token}'
    })
    assert response.status_code == 200
    data = response.json
    assert data['username'] == 'testuser'
    assert data['email'] == 'test@example.com'
