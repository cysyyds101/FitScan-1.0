from functools import lru_cache
from app.config import Config

class CacheUtil:
    @staticmethod
    @lru_cache(maxsize=100)
    def get_reference_objects():
        """缓存参照物信息"""
        return Config.REFERENCE_OBJECTS
    
    @staticmethod
    @lru_cache(maxsize=100)
    def get_size_rules():
        """缓存尺码规则"""
        return Config.SIZE_RULES
    
    @staticmethod
    def clear_cache():
        """清除缓存"""
        CacheUtil.get_reference_objects.cache_clear()
        CacheUtil.get_size_rules.cache_clear()
