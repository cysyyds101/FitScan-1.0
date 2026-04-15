import pytest
from app.services.measurement_service import MeasurementService


def test_calculate_size_recommendation():
    """测试尺码推荐功能"""
    # 测试数据
    measurement_data = {
        'height': 175.0,
        'chest': 92.0,
        'waist': 76.0
    }
    
    # 计算尺码推荐
    result = MeasurementService.calculate_size_recommendation(measurement_data)
    
    # 验证结果
    assert 'loose' in result
    assert 'slim' in result
    assert isinstance(result['loose'], str)
    assert isinstance(result['slim'], str)


def test_detect_reference():
    """测试参照物检测功能"""
    # 测试A4纸
    result = MeasurementService.detect_reference('A4')
    assert result['detected'] == True
    assert result['referenceType'] == 'A4'
    assert result['calibrationSuccess'] == True
    assert 'referenceInfo' in result
    
    # 测试身份证
    result = MeasurementService.detect_reference('ID_CARD')
    assert result['detected'] == True
    assert result['referenceType'] == 'ID_CARD'
    assert result['calibrationSuccess'] == True
    
    # 测试银行卡
    result = MeasurementService.detect_reference('BANK_CARD')
    assert result['detected'] == True
    assert result['referenceType'] == 'BANK_CARD'
    assert result['calibrationSuccess'] == True
    
    # 测试未知参照物
    result = MeasurementService.detect_reference('UNKNOWN')
    assert result['detected'] == True
    assert result['referenceType'] == 'A4'  # 默认使用A4
    assert result['calibrationSuccess'] == True
