import os
import io
import json
import requests
from typing import Dict, Any

# 获取智谱AI API Key
ZHIPU_API_KEY = os.getenv('ZHIPU_API_KEY', '')

def speech_to_text(audio_data: bytes, audio_format: str = "wav") -> Dict[str, Any]:
    """
    使用智谱AI进行语音识别
    
    参数:
        audio_data: 音频文件的二进制数据
        audio_format: 音频格式，支持 wav, mp3（智谱AI只支持这两种格式）
        
    返回:
        dict: 包含识别结果和错误信息
        {
            "success": bool,
            "text": str,  # 识别出的文字
            "error": str  # 错误信息（如果有）
        }
    """
    if not ZHIPU_API_KEY:
        return {
            "success": False,
            "text": "",
            "error": "智谱AI API Key未配置，请设置ZHIPU_API_KEY环境变量"
        }
    
    # 检查文件大小（≤ 25MB）
    max_size = 25 * 1024 * 1024  # 25MB
    if len(audio_data) > max_size:
        return {
            "success": False,
            "text": "",
            "error": f"音频文件过大 ({len(audio_data)} 字节 > {max_size} 字节)，智谱AI限制为25MB"
        }
    
    # 检查格式：智谱AI只支持 wav 和 mp3
    supported_formats = ['wav', 'mp3']
    audio_format_lower = audio_format.lower() if audio_format else 'wav'
    
    if audio_format_lower not in supported_formats:
        return {
            "success": False,
            "text": "",
            "error": f"音频格式 '{audio_format}' 不支持。智谱AI只支持 wav 和 mp3 格式，请将音频转换为支持的格式。"
        }
    
    try:
        # 智谱AI API地址 - 严格按照官方文档
        url = "https://open.bigmodel.cn/api/paas/v4/audio/transcriptions"
        
        # 设置正确的mime-type
        mime_type_map = {
            'wav': 'audio/wav',
            'mp3': 'audio/mpeg'
        }
        mime_type = mime_type_map.get(audio_format_lower, 'audio/wav')
        
        # 准备文件 - 使用BytesIO模拟文件对象
        filename = f"audio.{audio_format_lower}"
        
        # 重要：使用元组格式 (filename, file_obj, content_type, headers)
        files = {
            "file": (filename, io.BytesIO(audio_data), mime_type)
        }
        
        # 重要：尝试不同的参数组合
        # 根据智谱AI文档，transcriptions API通常只需要model参数
        payload = {
            "model": "glm-asr-2512",
            # 尝试去掉stream参数，或使用布尔值
            # "stream": False,  # 注释掉或使用False
            # 尝试添加language参数（如果有）
            # "language": "zh"  # 如果是中文语音
        }
        
        # 请求头 - 不要设置Content-Type，requests会自动设置multipart/form-data
        headers = {
            "Authorization": f"Bearer {ZHIPU_API_KEY}",
            # 不要手动设置Content-Type
        }
        
        print(f"[DEBUG] ========== 发送语音识别请求到智谱AI ==========")
        print(f"  URL: {url}")
        print(f"  文件大小: {len(audio_data)} 字节 ({len(audio_data) / 1024 / 1024:.2f} MB)")
        print(f"  音频格式: {audio_format_lower}")
        print(f"  文件名: {filename}")
        print(f"  MIME-Type: {mime_type}")
        print(f"  参数: {payload}")
        print(f"==================================================")
        
        # 方法1：使用files和data参数
        response = requests.post(
            url,
            files=files,
            data=payload,  # 使用data而不是json
            headers=headers,
            timeout=30
        )
        
        print(f"[DEBUG] API响应状态码: {response.status_code}")
        print(f"[DEBUG] API响应头: {dict(response.headers)}")
        
        # 检查HTTP状态码
        if response.status_code != 200:
            error_text = response.text
            print(f"\n[ERROR] ========== API返回错误详情 ==========")
            print(f"[ERROR] 状态码: {response.status_code}")
            print(f"[ERROR] 响应内容（原始）: {error_text}")
            print(f"[ERROR] 响应内容长度: {len(error_text)} 字符")
            
            # 尝试解析JSON错误信息
            try:
                error_json = response.json()
                print(f"[ERROR] 错误JSON: {json.dumps(error_json, indent=2, ensure_ascii=False)}")
                
                # 提取错误消息
                if isinstance(error_json, dict):
                    error_detail = error_json.get('error', error_json)
                    if isinstance(error_detail, dict):
                        error_msg = error_detail.get('message', error_detail.get('code', str(error_detail)))
                    else:
                        error_msg = str(error_detail)
                    if error_msg and error_msg != str(error_json):
                        error_text = error_msg
            except Exception as json_err:
                print(f"[ERROR] JSON解析失败: {json_err}")
            
            print(f"[ERROR] =======================================\n")
            
            return {
                "success": False,
                "text": "",
                "error": f"API错误 {response.status_code}: {error_text}"
            }
        
        # 解析JSON响应
        try:
            result = response.json()
            print(f"[DEBUG] API响应内容: {result}")
        except Exception as json_err:
            print(f"[ERROR] 解析响应JSON失败: {json_err}")
            return {
                "success": False,
                "text": "",
                "error": f"解析响应失败: {str(json_err)}"
            }
        
        # 提取识别文本
        # 根据智谱AI官方文档，响应格式通常为 {"text": "识别结果"}
        text = result.get('text', '')
        
        # 检查是否有其他可能的字段名
        if not text:
            possible_keys = ['transcription', 'result', 'content', 'data', 'output']
            for key in possible_keys:
                if key in result:
                    if isinstance(result[key], str):
                        text = result[key]
                    elif isinstance(result[key], dict) and 'text' in result[key]:
                        text = result[key]['text']
                    break
        
        if not text:
            # 如果没有找到文本，返回整个结果用于调试
            print(f"[WARNING] 未找到文本字段，完整响应: {result}")
            text = str(result)
        
        return {
            "success": True,
            "text": text.strip() if isinstance(text, str) else str(text),
            "error": ""
        }
        
    except requests.exceptions.HTTPError as http_err:
        # HTTP错误处理
        error_msg = f"HTTP错误: {str(http_err)}"
        if hasattr(http_err, 'response') and http_err.response is not None:
            error_msg = f"HTTP错误 {http_err.response.status_code}: {http_err.response.text[:200]}"
        print(f"[ERROR] {error_msg}")
        return {
            "success": False,
            "text": "",
            "error": error_msg
        }
    except requests.exceptions.RequestException as req_err:
        # 网络请求错误
        error_msg = f"网络请求失败: {str(req_err)}"
        print(f"[ERROR] {error_msg}")
        return {
            "success": False,
            "text": "",
            "error": error_msg
        }
    except Exception as e:
        # 其他错误
        error_msg = f"语音识别失败: {str(e)}"
        print(f"[ERROR] {error_msg}")
        import traceback
        traceback.print_exc()
        return {
            "success": False,
            "text": "",
            "error": error_msg
        }