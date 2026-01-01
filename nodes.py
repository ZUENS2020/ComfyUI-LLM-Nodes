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
from typing import Any
from io import BytesIO
import numpy as np
import torch
from PIL import Image


def _log(msg: str):
    print(f"[LLM-Custom] {msg}")


def _safe_key(key: str) -> str:
    k = key or ""
    if len(k) <= 6:
        return "***"
    return f"{k[:3]}***{k[-3:]}"


def _normalize_url(url: str) -> str:
    """标准化 URL"""
    return (url or "").strip().rstrip("/")


def _headers(key: str) -> dict:
    """生成请求头"""
    return {
        "Authorization": f"Bearer {(key or '').strip()}",
        "Content-Type": "application/json",
        "User-Agent": "ComfyUI"
    }


def _request(method: str, url: str, headers: dict, data: dict = None, timeout: int = 120) -> Any:
    """HTTP 请求"""
    body = json.dumps(data).encode() if data else None
    req = urllib.request.Request(url, body, headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return json.loads(r.read().decode())
    except urllib.error.HTTPError as e:
        try:
            err = e.read().decode()
        except:
            err = str(e.reason)
        raise Exception(f"HTTP {e.code}: {err}")
    except Exception as e:
        raise Exception(str(e))


def _download(url: str) -> bytes:
    """下载二进制数据"""
    req = urllib.request.Request(url, headers={"User-Agent": "ComfyUI"})
    with urllib.request.urlopen(req, timeout=60) as r:
        return r.read()


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
        api_base = config.get("api_base")
        api_key = config.get("api_key")
        model = config.get("model")
        temperature = config.get("temperature", 0.7)
        max_tokens = config.get("max_tokens", 2000)
        
        base = _normalize_url(api_base)
        _log(f"Chat start | base={base} | model={model} | key={_safe_key(api_key)}")
        if not base or not api_key or not model:
            _log("Chat error: missing base/key/model")
            return ("Error: Missing parameters",)
        
        msgs = []
        if system.strip():
            msgs.append({"role": "system", "content": system.strip()})
        msgs.append({"role": "user", "content": prompt})
        
        try:
            payload = {
                "model": model,
                "messages": msgs,
                "temperature": temperature,
                "max_tokens": max_tokens
            }
            _log(f"Chat request -> {base}/chat/completions | temp={temperature} max_tokens={max_tokens}")
            res = _request("POST", f"{base}/chat/completions", _headers(api_key), payload)
            txt = res.get("choices", [{}])[0].get("message", {}).get("content", "")
            _log(f"Chat done | output_len={len(txt)}")
            return (txt or "No response",)
        except Exception as e:
            _log(f"Chat exception: {e}")
            return (f"Error: {e}",)


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
        
        base = _normalize_url(api_base)
        _log(f"Image start | base={base} | model={model} | key={_safe_key(api_key)}")
        if not base or not api_key or not model:
            _log("Image error: missing base/key/model")
            return (self._err(),)
        
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
                
                _log(f"Image request -> {base}/chat/completions | Gemini image_config")
                res = _request("POST", f"{base}/chat/completions", _headers(api_key), payload, timeout=180)
                
                if "error" in res:
                    raise Exception(res.get("error", {}).get("message", "image generation failed"))
                if not res.get("choices"):
                    raise Exception(f"empty response: {res}")
                
                # 提取图片数据
                imgs = []
                message = res["choices"][0].get("message", {})
                images = message.get("images", [])
                
                _log(f"Image response images_count={len(images)}")
                
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
                    _log(f"Image done | batch={len(imgs)} | shape={list(imgs[0].shape) if imgs else 'n/a'}")
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
                
                _log(f"Image request -> {base}/images/generations | model={model} size={size} n={n}")
                
                res = _request("POST", f"{base}/images/generations", _headers(api_key), payload, timeout=180)
            if "error" in res:
                raise Exception(res.get("error", {}).get("message", "image generation failed"))
            if not res.get("data"):
                raise Exception(f"empty response: {res}")
            _log(f"Image response data_count={len(res.get('data', []))}")
            
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
                _log(f"Image done | batch={len(imgs)} | shape={list(imgs[0].shape) if imgs else 'n/a'}")
                return (torch.stack(imgs),)
            
            _log("Image error: no decoded images")
            return (self._err(),)
        except Exception as e:
            _log(f"Image exception: {e}")
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
        return ({
            "api_base": _normalize_url(api_base),
            "api_key": api_key,
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
