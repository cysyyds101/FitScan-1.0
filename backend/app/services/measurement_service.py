from app.utils.cache import CacheUtil

class MeasurementService:
    @staticmethod
    def calculate_size_recommendation(measurement_data):
        """根据测量数据推荐尺码"""
        height = measurement_data['height']
        chest = measurement_data['chest']
        waist = measurement_data['waist']
        
        # 宽松版尺码推荐
        loose_size = MeasurementService._get_size(height, chest, waist, loose=True)
        # 修身版尺码推荐
        slim_size = MeasurementService._get_size(height, chest, waist, loose=False)
        
        return {
            'loose': loose_size,
            'slim': slim_size
        }
    
    @staticmethod
    def _get_size(height, chest, waist, loose=True):
        """获取尺码"""
        size_rules = CacheUtil.get_size_rules()
        
        # 宽松版和修身版的调整因子
        adjustment_factor = 1.1 if loose else 0.95
        
        # 计算综合评分
        scores = {}
        for size, rules in size_rules.items():
            height_score = MeasurementService._calculate_score(height, rules['height'][0], rules['height'][1])
            chest_score = MeasurementService._calculate_score(chest * adjustment_factor, rules['chest'][0], rules['chest'][1])
            waist_score = MeasurementService._calculate_score(waist * adjustment_factor, rules['waist'][0], rules['waist'][1])
            scores[size] = (height_score + chest_score + waist_score) / 3
        
        # 选择评分最高的尺码
        best_size = max(scores, key=scores.get)
        return f"{best_size} ({'宽松版' if loose else '修身版'})"
    
    @staticmethod
    def _calculate_score(value, min_val, max_val):
        """计算评分"""
        if value >= min_val and value <= max_val:
            return 1.0
        elif value < min_val:
            return max(0, 1.0 - (min_val - value) / (min_val * 0.1))
        else:
            return max(0, 1.0 - (value - max_val) / (max_val * 0.1))
    
    @staticmethod
    def detect_reference(reference_type):
        """检测参照物"""
        reference_objects = CacheUtil.get_reference_objects()
        
        if reference_type in reference_objects:
            return {
                'detected': True,
                'referenceType': reference_type,
                'calibrationSuccess': True,
                'referenceInfo': reference_objects[reference_type]
            }
        else:
            # 默认使用A4纸
            return {
                'detected': True,
                'referenceType': 'A4',
                'calibrationSuccess': True,
                'referenceInfo': reference_objects['A4']
            }
