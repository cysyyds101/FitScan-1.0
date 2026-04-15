import os
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

class Config:
    # 数据库配置
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URI', 'sqlite:///fitscan.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # JWT配置
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key')
    JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY', 'dev-jwt-secret-key')
    JWT_ACCESS_TOKEN_EXPIRES = int(os.getenv('JWT_ACCESS_TOKEN_EXPIRES', '3600'))
    
    # 应用配置
    DEBUG = os.getenv('DEBUG', 'True').lower() == 'true'
    PORT = int(os.getenv('PORT', '5000'))
    
    # 测量配置
    REFERENCE_OBJECTS = {
        "A4": {"width": 21.0, "height": 29.7},
        "ID_CARD": {"width": 8.56, "height": 5.398},
        "BANK_CARD": {"width": 8.56, "height": 5.398}
    }
    
    # 尺码表
    SIZE_RULES = {
        "S": {"height": (155, 170), "chest": (84, 92), "waist": (70, 78)},
        "M": {"height": (160, 175), "chest": (90, 98), "waist": (76, 84)},
        "L": {"height": (165, 180), "chest": (96, 104), "waist": (82, 90)},
        "XL": {"height": (170, 185), "chest": (102, 110), "waist": (88, 96)},
        "XXL": {"height": (175, 190), "chest": (108, 116), "waist": (94, 102)}
    }
