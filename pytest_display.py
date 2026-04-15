#!/usr/bin/env python3
"""
FitScan 工程自动化测试脚本
基于 pytest 框架，用于测试工程的关键功能点
"""

import pytest
import sys
import os

# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.abspath('.'))

# 测试配置
TEST_CONFIG = {
    'test_dirs': ['main/tests'],
    'test_patterns': ['test_*.py'],
    'verbose': True
}

def run_tests():
    """运行测试用例"""
    print("=== FitScan 工程测试开始 ===")
    print(f"测试目录: {TEST_CONFIG['test_dirs']}")
    print(f"测试文件模式: {TEST_CONFIG['test_patterns']}")
    print("=" * 50)
    
    # 构建 pytest 命令参数
    args = []
    for test_dir in TEST_CONFIG['test_dirs']:
        args.append(test_dir)
    
    if TEST_CONFIG['verbose']:
        args.extend(['-v'])
    
    # 运行测试
    try:
        result = pytest.main(args)
        print("=" * 50)
        if result == 0:
            print("✅ 所有测试用例通过！")
        else:
            print("❌ 部分测试用例失败，请查看详细输出。")
        return result
    except Exception as e:
        print(f"❌ 测试执行失败: {str(e)}")
        return 1

def display_test_summary():
    """显示测试摘要"""
    print("\n=== 测试摘要 ===")
    print("测试覆盖范围:")
    print("1. 环境测试 - 验证系统环境配置")
    print("2. 参照物检测 - 验证参照物识别功能")
    print("3. 几何计算 - 验证尺寸计算算法")
    print("4. 姿态估计 - 验证人体关键点提取")
    print("5. 尺码推荐 - 验证尺码推荐算法")
    print("\n测试执行说明:")
    print("- 运行此脚本将自动执行所有测试用例")
    print("- 测试结果将显示在控制台中")
    print("- 详细测试报告将保存在测试输出目录中")

if __name__ == '__main__':
    display_test_summary()
    print("\n开始执行测试...\n")
    exit_code = run_tests()
    sys.exit(exit_code)
