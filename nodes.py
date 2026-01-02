"""
ComfyUI Gemini LiteLLM Nodes
Gemini 3 聊天和图片生成（通过 LiteLLM）

Architecture:
- Execution Nodes: LLMChatGenerate, LLMImageGenerate
- Config Nodes: LLMBaseConfig, ChatParams, GeminiImageParams
- Zero external dependencies (urllib only)

Author: ZUENS2020
Version: 3.0.0
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
                "image_1": ("IMAGE",),
                "image_2": ("IMAGE",),
                "image_3": ("IMAGE",),
                "image_4": ("IMAGE",),
                "image_5": ("IMAGE",),
            }
        }
    
    RETURN_TYPES = ("STRING",)
    FUNCTION = "run"
    CATEGORY = "Gemini-LiteLLM"

    def run(self, config, prompt, system="", image_1=None, image_2=None, image_3=None, image_4=None, image_5=None):
        api_base = config.get("api_base")
        api_key = config.get("api_key")
        model = config.get("model")
        temperature = config.get("temperature", 0.7)
        max_tokens = config.get("max_tokens", 2000)
        
        base = _normalize_url(api_base)
        if not base or not api_key or not model:
            _log("Chat error: missing base/key/model")
            return ("Error: Missing parameters",)
        
        # 收集多路图像输入
        image_inputs = [image_1, image_2, image_3, image_4, image_5]
        image_list = []
        for img in image_inputs:
            if img is None:
                continue
            if len(img.shape) == 3:
                image_list.append(img)
            else:
                # 若是批次，逐张展开加入列表
                for i in range(img.shape[0]):
                    image_list.append(img[i])
        
        msgs = []
        if system.strip():
            msgs.append({"role": "system", "content": system.strip()})
        
        # 构建用户消息（支持多模态）
        user_content = []
        if prompt.strip():
            user_content.append({"type": "text", "text": prompt})
        
        # 添加参考图像
        if image_list:
            for img_tensor in image_list:
                img_np = (img_tensor.cpu().numpy() * 255).astype(np.uint8)
                pil_img = Image.fromarray(img_np)
                buffered = BytesIO()
                pil_img.save(buffered, format="PNG")
                img_b64 = base64.b64encode(buffered.getvalue()).decode()
                user_content.append({
                    "type": "image_url",
                    "image_url": {"url": f"data:image/png;base64,{img_b64}"}
                })
        
        # 如果没有内容，使用默认提示
        if not user_content:
            user_content = "Hello"
        
        msgs.append({"role": "user", "content": user_content})
        
        try:
            payload = {
                "model": model,
                "messages": msgs,
                "temperature": temperature,
                "max_tokens": max_tokens
            }
            res = _request("POST", f"{base}/chat/completions", _headers(api_key), payload)
            txt = res.get("choices", [{}])[0].get("message", {}).get("content", "")
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
            "optional": {
                "image_1": ("IMAGE",),
                "image_2": ("IMAGE",),
                "image_3": ("IMAGE",),
                "image_4": ("IMAGE",),
                "image_5": ("IMAGE",),
                "additional_text": ("STRING", {"default": "", "multiline": True}),
            }
        }
    
    RETURN_TYPES = ("IMAGE",)
    FUNCTION = "run"
    CATEGORY = "Gemini-LiteLLM"

    def run(self, config, prompt, n, image_1=None, image_2=None, image_3=None, image_4=None, image_5=None, additional_text=""):
        api_base = config.get("api_base")
        api_key = config.get("api_key")
        model = config.get("model")
        use_gemini_image = config.get("use_gemini_image", False)
        temperature = config.get("temperature", 1.0)
        
        # Gemini 参数
        aspect_ratio = config.get("aspect_ratio")
        image_size = config.get("image_size")
        
        base = _normalize_url(api_base)
        if not base or not api_key or not model:
            _log("Image error: missing base/key/model")
            return (self._err(),)
        
        try:
            # 收集多路图像输入，合并为批次
            image_inputs = [image_1, image_2, image_3, image_4, image_5]
            image_list = []  # 允许不同尺寸，不再强制一致
            for img in image_inputs:
                if img is None:
                    continue
                if len(img.shape) == 3:
                    image_list.append(img)
                else:
                    # 若是批次，逐张展开加入列表
                    for i in range(img.shape[0]):
                        image_list.append(img[i])
            if use_gemini_image and aspect_ratio and image_size:
                # Gemini 图片生成 (使用 chat/completions 端点)
                # 构建多模态消息内容
                content = []
                
                # 添加主提示词
                if prompt.strip():
                    content.append({"type": "text", "text": prompt})
                
                # 添加图像（如果有，支持批量，尺寸可不同）
                if image_list:
                    for img_tensor in image_list:
                        img_np = (img_tensor.cpu().numpy() * 255).astype(np.uint8)
                        pil_img = Image.fromarray(img_np)
                        buffered = BytesIO()
                        pil_img.save(buffered, format="PNG")
                        img_b64 = base64.b64encode(buffered.getvalue()).decode()
                        content.append({
                            "type": "image_url",
                            "image_url": {"url": f"data:image/png;base64,{img_b64}"}
                        })
                
                # 添加额外文本（如果有）
                if additional_text.strip():
                    content.append({"type": "text", "text": additional_text})
                
                # 如果没有任何内容，使用默认提示
                if not content:
                    content = "Generate an image"
                
                payload = {
                    "model": model,
                    "messages": [{"role": "user", "content": content}],
                    "temperature": temperature,
                    "image_config": {
                        "image_size": image_size,
                        "aspect_ratio": aspect_ratio
                    }
                }
                
                res = _request("POST", f"{base}/chat/completions", _headers(api_key), payload, timeout=180)
                
                if "error" in res:
                    raise Exception(res.get("error", {}).get("message", "image generation failed"))
                if not res.get("choices"):
                    raise Exception(f"empty response: {res}")
                
                # 提取图片数据
                imgs = []
                message = res["choices"][0].get("message", {})
                images = message.get("images", [])
                
                # 检查是否返回了文本而不是图片
                if not images and message.get("content"):
                    _log(f"Image error: Gemini returned text instead of image. Content preview: {message['content'][:200]}...")
                    raise Exception("Gemini returned text response instead of image. Try using a simpler, more direct image description prompt.")
                
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
                    return (torch.stack(imgs),)
            else:
                raise Exception("Gemini image_config required. Please use Gemini Image config node.")
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
                "api_base": ("STRING", {"default": "https://your-litellm-server.com/v1"}),
                "api_key": ("STRING", {"default": ""}),
                "model": ("STRING", {"default": "gemini/gemini-3-pro-image-preview"}),
            }
        }
    
    RETURN_TYPES = ("LLM_BASE_CONFIG",)
    RETURN_NAMES = ("base_config",)
    FUNCTION = "run"
    CATEGORY = "Gemini-LiteLLM/Config"
    
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
    CATEGORY = "Gemini-LiteLLM/Config"
    
    def run(self, base_config, temperature, max_tokens):
        return ({
            **base_config,
            "temperature": temperature,
            "max_tokens": max_tokens,
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
                "temperature": ("FLOAT", {"default": 1.0, "min": 0, "max": 1, "step": 0.05}),
            }
        }
    
    RETURN_TYPES = ("LLM_IMAGE_CONFIG",)
    RETURN_NAMES = ("config",)
    FUNCTION = "run"
    CATEGORY = "Gemini-LiteLLM/Config"
    
    def run(self, base_config, aspect_ratio, image_size, temperature):
        return ({
            **base_config,
            "aspect_ratio": aspect_ratio,
            "image_size": image_size,
            "temperature": temperature,
            "use_gemini_image": True,  # 标记使用 Gemini 图片生成
        },)


NODE_CLASS_MAPPINGS = {
    # 执行节点
    "LLMChatGenerate": LLMChatGenerate,
    "LLMImageGenerate": LLMImageGenerate,
    
    # 配置节点
    "LLMBaseConfig": LLMBaseConfig,
    "ChatParams": ChatParams,
    "GeminiImageParams": GeminiImageParams,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    # 执行节点
    "LLMChatGenerate": "Chat",
    "LLMImageGenerate": "Image",
    
    # 配置节点
    "LLMBaseConfig": "Base Config",
    "ChatParams": "Chat Params",
    "GeminiImageParams": "Image Params",
}
