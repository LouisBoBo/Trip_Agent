#!/usr/bin/env python3
"""快速检查路由是否注册"""
from app import app

print("=" * 50)
print("检查已注册的路由:")
print("=" * 50)

speech_routes = []
for rule in app.url_map.iter_rules():
    if 'speech' in rule.rule:
        speech_routes.append(rule.rule)
        print(f"✓ {rule.rule} -> {rule.endpoint} (methods: {list(rule.methods)})")

if '/api/speech/recognize' in speech_routes:
    print("\n✓ 语音识别路由已正确注册！")
else:
    print("\n✗ 语音识别路由未找到！")
