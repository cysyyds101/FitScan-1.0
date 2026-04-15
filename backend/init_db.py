from app import create_app, db

app = create_app()

with app.app_context():
    # 创建数据库表
    db.create_all()
    print('Database initialized successfully!')
