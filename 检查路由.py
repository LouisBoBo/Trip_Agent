#!/usr/bin/env python3
"""检查Flask应用中的路由注册情况"""
import sys
import os

# 确保在项目目录中
os.chdir(os.path.dirname(os.path.abspath(__file__)))

try:
    from app import app
    
    print("=" * 60)
    print("Flask应用路由检查")
    print("=" * 60)
    
    all_rules = list(app.url_map.iter_rules())
    
    # 查找语音识别路由
    speech_rules = [r for r in all_rules if 'speech' in r.rule]
    api_rules = [r for r in all_rules if r.rule.startswith('/api')]
    
    print(f"\n总路由数: {len(all_rules)}")
    print(f"API路由数: {len(api_rules)}")
    print(f"语音识别路由数: {len(speech_rules)}")
    
    print("\n" + "-" * 60)
    print("所有API路由:")
    print("-" * 60)
    for rule in sorted(api_rules, key=lambda x: x.rule):
        print(f"  {rule.rule:30s} -> {rule.endpoint:20s} (methods: {sorted(list(rule.methods))})")
    
    if speech_rules:
        print("\n" + "-" * 60)
        print("语音识别路由详情:")
        print("-" * 60)
        for rule in speech_rules:
            print(f"  路由: {rule.rule}")
            print(f"  端点: {rule.endpoint}")
            print(f"  方法: {sorted(list(rule.methods))}")
            print(f"  规则: {rule}")
    else:
        print("\n⚠ 警告: 未找到语音识别路由！")
    
    print("\n" + "=" * 60)
    
except Exception as e:
    print(f"错误: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
