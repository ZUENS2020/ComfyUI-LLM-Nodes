"""
ComfyUI LLM Custom Nodes
支持聊天对话和图片生成（OpenAI / Gemini 兼容）

Architecture:
- Execution Nodes: LLMChatGenerate, LLMImageGenerate
- Config Nodes: LLMBaseConfig, ChatParams, OpenAIImageParams, GeminiImageParams
- Zero external dependencies (urllib only)

Author: ComfyUI Community
Version: 2.0.0
Date: 2026-01-02
"""

import json
import base64
import urllib.request
import urllib.error
import urllib.parse
import ssl
import re
from typing import Any
from io import BytesIO
import numpy as np
import torch
from PIL import Image


def _log(msg: str):
    print(f"[LLM-Custom] {msg}")


def _safe_key(key: str) -> str:
    """完全脱敏 API 密钥，不显示任何字符"""
    return "***" if key else "empty"


def _normalize_url(url: str) -> str:
    """标准化并验证 URL"""
    url = (url or "").strip().rstrip("/")
    if not url:
        return url
    
    # 验证 URL 格式
    try:
        parsed = urllib.parse.urlparse(url)
        if parsed.scheme not in ["https", "http"]:
            raise ValueError("URL 必须使用 http 或 https 协议")
        
        # 防止 SSRF 攻击 - 禁止内网地址
        hostname = parsed.hostname
        if hostname:
            hostname_lower = hostname.lower()
            # 禁止 localhost 和内网 IP
            if hostname_lower in ["localhost", "127.0.0.1", "0.0.0.0", "::1"]:
                raise ValueError("禁止访问本地地址")
            # 禁止内网 IP 段
            if hostname_lower.startswith(("10.", "172.16.", "172.17.", "172.18.", "172.19.", 
                                         "172.20.", "172.21.", "172.22.", "172.23.", "172.24.",
                                         "172.25.", "172.26.", "172.27.", "172.28.", "172.29.",
                                         "172.30.", "172.31.", "192.168.")):
                raise ValueError("禁止访问内网地址")
        
        return url
    except Exception as e:
        _log(f"URL 验证失败: {e}")
        raise ValueError(f"无效的 URL: {e}")


def _sanitize_input(text: str, max_length: int = 50000) -> str:
    """清理和验证用户输入"""
    if not text:
        return ""
    
    text = text.strip()
    
    # 限制长度防止资源耗尽
    if len(text) > max_length:
        _log(f"输入过长，截断到 {max_length} 字符")
        text = text[:max_length]
    
    return text


def _validate_config(config: dict) -> bool:
    """验证配置参数"""
    if not config:
        return False
    
    api_base = config.get("api_base", "")
    api_key = config.get("api_key", "")
    model = config.get("model", "")
    
    if not api_base or not api_key or not model:
        return False
    
    # 验证 API key 不为空且长度合理
    if len(api_key.strip()) < 10:
        _log("警告: API key 长度过短")
        return False
    
    return True


def _headers(key: str) -> dict:
    """生成请求头"""
    return {
        "Authorization": f"Bearer {(key or '').strip()}",
        "Content-Type": "application/json",
        "User-Agent": "ComfyUI"
    }


def _request(method: str, url: str, headers: dict, data: dict = None, timeout: int = 120) -> Any:
    """HTTP 请求 - 增强安全性"""
    # 限制 payload 大小（10MB）
    if data:
        body = json.dumps(data).encode()
        if len(body) > 10 * 1024 * 1024:
            raise Exception("请求数据过大（超过 10MB）")
    else:
        body = None
    
    req = urllib.request.Request(url, body, headers, method=method)
    
    # 创建 SSL 上下文，启用证书验证
    ssl_context = ssl.create_default_context()
    ssl_context.check_hostname = True
    ssl_context.verify_mode = ssl.CERT_REQUIRED
    
    try:
        with urllib.request.urlopen(req, timeout=timeout, context=ssl_context) as r:
            # 限制响应大小（50MB）
            content_length = r.getheader('Content-Length')
            if content_length and int(content_length) > 50 * 1024 * 1024:
                raise Exception("响应数据过大（超过 50MB）")
            
            response_data = r.read()
            if len(response_data) > 50 * 1024 * 1024:
                raise Exception("响应数据过大（超过 50MB）")
            
            return json.loads(response_data.decode())
    except urllib.error.HTTPError as e:
        # 不暴露详细错误信息
        error_msg = f"HTTP 错误 {e.code}"
        try:
            err_data = e.read().decode()
            # 解析错误但不完整暴露
            if len(err_data) < 500:
                error_msg = f"HTTP {e.code}: 请求失败"
        except:
            pass
        _log(f"HTTP 错误: {error_msg}")
        raise Exception(error_msg)
    except ssl.SSLError as e:
        _log(f"SSL 错误: {str(e)}")
        raise Exception("SSL 证书验证失败")
    except Exception as e:
        _log(f"请求异常: {str(e)}")
        raise Exception("请求失败")


def _download(url: str) -> bytes:
    """下载二进制数据 - 增强安全性"""
    # 验证 URL
    if not url or not url.startswith(("https://", "http://", "data:")):
        raise ValueError("无效的下载 URL")
    
    # 如果是 data URL，直接解码
    if url.startswith("data:"):
        if "base64," in url:
            return base64.b64decode(url.split("base64,", 1)[1])
        raise ValueError("不支持的 data URL 格式")
    
    req = urllib.request.Request(url, headers={"User-Agent": "ComfyUI"})
    
    # 创建 SSL 上下文
    ssl_context = ssl.create_default_context()
    ssl_context.check_hostname = True
    ssl_context.verify_mode = ssl.CERT_REQUIRED
    
    with urllib.request.urlopen(req, timeout=60, context=ssl_context) as r:
        # 限制下载大小（100MB）
        content_length = r.getheader('Content-Length')
        if content_length and int(content_length) > 100 * 1024 * 1024:
            raise Exception("文件过大（超过 100MB）")
        
        data = r.read()
        if len(data) > 100 * 1024 * 1024:
            raise Exception("文件过大（超过 100MB）")
        
        return data


# ============ 执行节点 ============

class LLMChatGenerate:
    """聊天生成节点"""
    
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "config": ("LLM_CHAT_CONFIG",),
                "prompt": ("STRING", {"default": "Hello!", "multiline": True}),
            },
            "optional": {
                "system": ("STRING", {"default": "", "multiline": True}),
            }
        }
    
    RETURN_TYPES = ("STRING",)
    FUNCTION = "run"
    CATEGORY = "LLM"

    def run(self, config, prompt, system=""):
        # 验证配置
        if not _validate_config(config):
            _log("Chat 错误: 配置参数缺失或无效")
            return ("错误: 配置参数缺失或无效",)
        
        api_base = config.get("api_base")
        api_key = config.get("api_key")
        model = config.get("model")
        temperature = config.get("temperature", 0.7)
        max_tokens = config.get("max_tokens", 2000)
        
        # 验证并标准化 URL
        try:
            base = _normalize_url(api_base)
        except ValueError as e:
            _log(f"Chat 错误: URL 验证失败 - {e}")
            return (f"错误: URL 验证失败",)
        
        # 清理用户输入
        prompt = _sanitize_input(prompt, max_length=50000)
        system = _sanitize_input(system, max_length=10000)
        
        _log(f"Chat 开始 | model={model} | key={_safe_key(api_key)}")
        
        msgs = []
        if system:
            msgs.append({"role": "system", "content": system})
        msgs.append({"role": "user", "content": prompt})
        
        try:
            # 验证参数范围
            temperature = max(0.0, min(2.0, temperature))
            max_tokens = max(1, min(128000, max_tokens))
            
            payload = {
                "model": model,
                "messages": msgs,
                "temperature": temperature,
                "max_tokens": max_tokens
            }
            _log(f"Chat 请求 -> {base}/chat/completions")
            res = _request("POST", f"{base}/chat/completions", _headers(api_key), payload)
            txt = res.get("choices", [{}])[0].get("message", {}).get("content", "")
            _log(f"Chat 完成 | 输出长度={len(txt)}")
            return (txt or "无响应",)
        except Exception as e:
            _log(f"Chat 异常: {str(e)}")
            return (f"错误: 请求失败",)


class LLMImageGenerate:
    """图片生成节点"""
    
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "config": ("LLM_IMAGE_CONFIG",),
                "prompt": ("STRING", {"default": "A beautiful landscape", "multiline": True}),
                "n": ("INT", {"default": 1, "min": 1, "max": 4}),
            },
            "optional": {}
        }
    
    RETURN_TYPES = ("IMAGE",)
    FUNCTION = "run"
    CATEGORY = "LLM"

    def run(self, config, prompt, n):
        # 验证配置
        if not _validate_config(config):
            _log("Image 错误: 配置参数缺失或无效")
            return (self._err(),)
        
        api_base = config.get("api_base")
        api_key = config.get("api_key")
        model = config.get("model")
        use_gemini_image = config.get("use_gemini_image", False)
        
        # OpenAI 参数
        size = config.get("size", "1024x1024")
        quality = config.get("quality", "standard")
        
        # Gemini 参数
        aspect_ratio = config.get("aspect_ratio")
        image_size = config.get("image_size")
        
        # 验证并标准化 URL
        try:
            base = _normalize_url(api_base)
        except ValueError as e:
            _log(f"Image 错误: URL 验证失败 - {e}")
            return (self._err(),)
        
        # 清理用户输入
        prompt = _sanitize_input(prompt, max_length=10000)
        
        # 验证参数
        n = max(1, min(4, n))
        
        _log(f"Image 开始 | model={model} | key={_safe_key(api_key)}")
        
        try:
            if use_gemini_image and aspect_ratio and image_size:
                # Gemini 图片生成 (使用 chat/completions 端点)
                _log(f"Gemini image config: size={image_size} ratio={aspect_ratio}")
                
                payload = {
                    "model": model,
                    "messages": [{"role": "user", "content": prompt}],
                    "image_config": {
                        "image_size": image_size,
                        "aspect_ratio": aspect_ratio
                    }
                }
                
                _log(f"Image 请求 -> {base}/chat/completions | Gemini image_config")
                res = _request("POST", f"{base}/chat/completions", _headers(api_key), payload, timeout=180)
                
                if "error" in res:
                    raise Exception("图片生成失败")
                if not res.get("choices"):
                    raise Exception("空响应")
                
                # 提取图片数据
                imgs = []
                message = res["choices"][0].get("message", {})
                images = message.get("images", [])
                
                _log(f"Image 响应图片数量={len(images)}")
                
                for img_item in images:
                    img_url = img_item.get("image_url", {}).get("url", "")
                    if img_url.startswith("data:image/"):
                        # 解析 data URL: data:image/jpeg;base64,xxxxx
                        b64_data = img_url.split(",", 1)[1] if "," in img_url else img_url
                        data = base64.b64decode(b64_data)
                        pil = Image.open(BytesIO(data)).convert("RGB")
                        arr = np.array(pil).astype(np.float32) / 255.0
                        imgs.append(torch.from_numpy(arr))
                
                if imgs:
                    _log(f"Image 完成 | batch={len(imgs)}")
                    return (torch.stack(imgs),)
                    
            else:
                # OpenAI 标准图片生成
                payload = {
                    "model": model,
                    "prompt": prompt,
                    "n": n,
                    "size": size,
                    "quality": quality,
                    "response_format": "b64_json"
                }
                
                _log(f"Image 请求 -> {base}/images/generations | model={model} size={size} n={n}")
                
                res = _request("POST", f"{base}/images/generations", _headers(api_key), payload, timeout=180)
            if "error" in res:
                raise Exception("图片生成失败")
            if not res.get("data"):
                raise Exception("空响应")
            _log(f"Image 响应数据数量={len(res.get('data', []))}")
            
            imgs = []
            for item in res.get("data", []):
                data = None
                if "b64_json" in item:
                    data = base64.b64decode(item["b64_json"])
                elif "url" in item:
                    data = _download(item["url"])
                
                if data:
                    pil = Image.open(BytesIO(data)).convert("RGB")
                    arr = np.array(pil).astype(np.float32) / 255.0
                    imgs.append(torch.from_numpy(arr))
            
            if imgs:
                _log(f"Image 完成 | batch={len(imgs)}")
                return (torch.stack(imgs),)
            
            _log("Image 错误: 无法解码图片")
            return (self._err(),)
        except Exception as e:
            _log(f"Image 异常: {str(e)}")
            return (self._err(),)
    
    def _err(self):
        return torch.from_numpy(np.zeros((512, 512, 3), dtype=np.float32)).unsqueeze(0)


# ============ 配置节点 ============

class LLMBaseConfig:
    """基础配置（只含 api_base/key/model）"""
    
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "api_base": ("STRING", {"default": "https://api.openai.com/v1"}),
                "api_key": ("STRING", {"default": ""}),
                "model": ("STRING", {"default": "gpt-3.5-turbo"}),
            }
        }
    
    RETURN_TYPES = ("LLM_BASE_CONFIG",)
    RETURN_NAMES = ("base_config",)
    FUNCTION = "run"
    CATEGORY = "LLM/Config"
    
    def run(self, api_base, api_key, model):
        # 验证并标准化 URL
        try:
            normalized_base = _normalize_url(api_base)
        except ValueError as e:
            _log(f"配置错误: {e}")
            raise ValueError(f"无效的 API base URL: {e}")
        
        # 验证 API key
        if not api_key or len(api_key.strip()) < 10:
            _log("配置错误: API key 无效")
            raise ValueError("API key 必须至少 10 个字符")
        
        # 验证 model
        model = model.strip()
        if not model or len(model) > 200:
            _log("配置错误: model 名称无效")
            raise ValueError("model 名称无效")
        
        return ({
            "api_base": normalized_base,
            "api_key": api_key.strip(),
            "model": model,
        },)


class ChatParams:
    """聊天参数配置"""
    
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "base_config": ("LLM_BASE_CONFIG",),
                "temperature": ("FLOAT", {"default": 0.7, "min": 0, "max": 2, "step": 0.1}),
                "max_tokens": ("INT", {"default": 2000, "min": 1, "max": 128000}),
            }
        }
    
    RETURN_TYPES = ("LLM_CHAT_CONFIG",)
    RETURN_NAMES = ("config",)
    FUNCTION = "run"
    CATEGORY = "LLM/Config"
    
    def run(self, base_config, temperature, max_tokens):
        return ({
            **base_config,
            "temperature": temperature,
            "max_tokens": max_tokens,
        },)


class OpenAIImageParams:
    """OpenAI 图片参数配置"""
    
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "base_config": ("LLM_BASE_CONFIG",),
                "size": (["256x256", "512x512", "1024x1024", "1024x1792", "1792x1024"], {"default": "1024x1024"}),
                "quality": (["standard", "hd"], {"default": "standard"}),
            }
        }
    
    RETURN_TYPES = ("LLM_IMAGE_CONFIG",)
    RETURN_NAMES = ("config",)
    FUNCTION = "run"
    CATEGORY = "LLM/Config"
    
    def run(self, base_config, size, quality):
        return ({
            **base_config,
            "size": size,
            "quality": quality,
        },)


class GeminiImageParams:
    """Gemini 图片参数配置（LiteLLM v1.80.7+）
    使用 image_config 参数控制分辨率和宽高比
    """
    
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "base_config": ("LLM_BASE_CONFIG",),
                "aspect_ratio": (["1:1", "16:9", "4:3", "9:16", "3:4"], ),
                "image_size": (["1K", "2K", "4K"], ),
            }
        }
    
    RETURN_TYPES = ("LLM_IMAGE_CONFIG",)
    RETURN_NAMES = ("config",)
    FUNCTION = "run"
    CATEGORY = "LLM/Config"
    
    def run(self, base_config, aspect_ratio, image_size):
        return ({
            **base_config,
            "aspect_ratio": aspect_ratio,
            "image_size": image_size,
            "use_gemini_image": True,  # 标记使用 Gemini 图片生成
        },)


NODE_CLASS_MAPPINGS = {
    # 执行节点
    "LLMChatGenerate": LLMChatGenerate,
    "LLMImageGenerate": LLMImageGenerate,
    
    # 配置节点
    "LLMBaseConfig": LLMBaseConfig,
    "ChatParams": ChatParams,
    "OpenAIImageParams": OpenAIImageParams,
    "GeminiImageParams": GeminiImageParams,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    # 执行节点
    "LLMChatGenerate": "Chat",
    "LLMImageGenerate": "Image",
    
    # 配置节点
    "LLMBaseConfig": "Base Config",
    "ChatParams": "Chat Params",
    "OpenAIImageParams": "OpenAI Image",
    "GeminiImageParams": "Gemini Image",
}
