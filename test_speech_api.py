"""
测试智谱AI语音识别API
用于诊断400错误
"""
import io
import requests
import os
from graph.env_utils import ZHIPU_API_KEY

# 测试参数
url = "https://open.bigmodel.cn/api/paas/v4/audio/transcriptions"

# 创建一个测试音频数据（假设是空数据或无效数据）
test_audio = b"test audio data"

print("=" * 60)
print("测试智谱AI语音识别API")
print("=" * 60)
print(f"API Key: {ZHIPU_API_KEY[:10]}..." if ZHIPU_API_KEY else "API Key: 未设置")
print(f"URL: {url}")
print()

# 测试1: 使用BytesIO
print("测试1: 使用BytesIO发送文件")
files = {"file": ("test-audio.webm", io.BytesIO(test_audio))}
payload = {"model": "glm-asr-2512", "stream": "false"}
headers = {"Authorization": f"Bearer {ZHIPU_API_KEY}"}

try:
    response = requests.post(url, data=payload, files=files, headers=headers, timeout=30)
    print(f"状态码: {response.status_code}")
    print(f"响应内容: {response.text}")
    print(f"响应头: {dict(response.headers)}")
    if response.status_code != 200:
        try:
            error_json = response.json()
            print(f"错误JSON: {error_json}")
        except:
            pass
except Exception as e:
    print(f"请求异常: {e}")

print()
print("=" * 60)
print("请查看上面的错误信息，这可以帮助诊断400错误的原因")
print("=" * 60)
