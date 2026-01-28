"""
ComfyUI Gemini OpenRouter Nodes
Gemini 3 聊天和图片生成（通过 OpenRouter API）

Architecture:
- Execution Nodes: ORChatGenerate, ORImageGenerate
- Config Nodes: ORBaseConfig, ORChatParams, ORImageParams
- Zero external dependencies (urllib only)

Author: ZUENS2020
Version: 1.0.0
Date: 2026-01-28
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
import time


def _log(msg: str):
    """打印详细日志"""
    print(f"[OpenRouter] {msg}")

def _log_debug(msg: str):
    """打印调试日志"""
    print(f"[OpenRouter DEBUG] {msg}")

def _log_error(msg: str):
    """打印错误日志"""
    print(f"[OpenRouter ERROR] {msg}")

def _log_step(step: str, details: str = ""):
    """打印步骤日志"""
    if details:
        print(f"[OpenRouter STEP] {step}: {details}")
    else:
        print(f"[OpenRouter STEP] {step}")


def _safe_key(key: str) -> str:
    k = key or ""
    if len(k) <= 6:
        return "***"
    return f"{k[:3]}***{k[-3:]}"


def _normalize_url(url: str) -> str:
    """标准化 URL"""
    return (url or "").strip().rstrip("/")


def _headers(key: str, site_url: str = "", site_name: str = "") -> dict:
    """生成 OpenRouter 请求头"""
    headers = {
        "Authorization": f"Bearer {(key or '').strip()}",
        "Content-Type": "application/json",
        "HTTP-Referer": site_url,
        "X-Title": site_name,
        "User-Agent": "ComfyUI"
    }
    # 移除空值
    return {k: v for k, v in headers.items() if v}


def _request(method: str, url: str, headers: dict, data: dict = None, timeout: int = 120) -> Any:
    """HTTP 请求"""
    start_time = time.time()
    _log_debug(f"_request called: {method} {url}")
    _log_debug(f"Timeout: {timeout}s")

    body = json.dumps(data).encode() if data else None
    if body:
        _log_debug(f"Request body size: {len(body)} bytes")

    req = urllib.request.Request(url, body, headers, method=method)
    _log_debug("Request object created")

    try:
        _log_debug(f"Opening connection to {url}...")
        connection_start = time.time()

        with urllib.request.urlopen(req, timeout=timeout) as r:
            connection_time = time.time() - connection_start
            _log_debug(f"Connection established in {connection_time:.2f}s")
            _log_debug(f"Response received, status code: {r.status}")
            _log_debug(f"Response headers: {dict(r.headers)}")

            read_start = time.time()
            response_body = r.read()
            read_time = time.time() - read_start
            _log_debug(f"Response body size: {len(response_body)} bytes (read in {read_time:.2f}s)")

            _log_debug("Parsing JSON response...")
            parse_start = time.time()
            result = json.loads(response_body.decode())
            parse_time = time.time() - parse_start
            _log_debug(f"JSON parsed successfully in {parse_time:.2f}s")

            total_time = time.time() - start_time
            _log_debug(f"Total request time: {total_time:.2f}s")

            return result

    except urllib.error.HTTPError as e:
        _log_error(f"HTTP Error {e.code}")
        try:
            err_body = e.read().decode()
            _log_error(f"Error body: {err_body[:500]}")
        except:
            err_body = str(e.reason)
            _log_error(f"Error reason: {err_body}")
        raise Exception(f"HTTP {e.code}: {err_body}")

    except urllib.error.URLError as e:
        elapsed = time.time() - start_time
        _log_error(f"URL Error after {elapsed:.2f}s: {e.reason}")
        if isinstance(e.reason, TimeoutError):
            _log_error(f"Request timed out after {timeout}s")
        raise Exception(f"Connection failed: {e.reason}")

    except Exception as e:
        elapsed = time.time() - start_time
        _log_error(f"Request failed after {elapsed:.2f}s: {type(e).__name__}")
        _log_error(f"Error message: {str(e)}")
        raise Exception(str(e))


def _download(url: str) -> bytes:
    """下载二进制数据"""
    req = urllib.request.Request(url, headers={"User-Agent": "ComfyUI"})
    with urllib.request.urlopen(req, timeout=60) as r:
        return r.read()


# ============ 执行节点 ============

class ORChatGenerate:
    """OpenRouter 聊天生成节点"""

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "config": ("OR_CHAT_CONFIG",),
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
    CATEGORY = "Gemini-OpenRouter"

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
            user_content.append({"type": "text", "text": prompt.strip()})

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

        # 如果没有内容，使用默认提示词（保持为列表格式）
        if not user_content:
            user_content = [{"type": "text", "text": "Hello"}]

        msgs.append({"role": "user", "content": user_content})

        # 重试机制
        max_retries = 2
        for attempt in range(max_retries):
            try:
                payload = {
                    "model": model,
                    "messages": msgs,
                    "temperature": temperature,
                    "max_tokens": max_tokens
                }
                res = _request("POST", f"{base}/chat/completions",
                             _headers(api_key, config.get("site_url", ""), config.get("site_name", "")),
                             payload, timeout=120)
                txt = res.get("choices", [{}])[0].get("message", {}).get("content", "")
                if txt:
                    return (txt,)
                return ("No response from model",)
            except Exception as e:
                if attempt == max_retries - 1:
                    _log(f"Chat error (final): {e}")
                    raise Exception(f"Failed to get response after {max_retries} attempts: {e}")
                else:
                    _log(f"Chat retry {attempt + 1}/{max_retries} due to: {e}")


class ORImageGenerate:
    """OpenRouter 图片生成节点"""

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "config": ("OR_IMAGE_CONFIG",),
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
    CATEGORY = "Gemini-OpenRouter"

    def run(self, config, prompt, n, image_1=None, image_2=None, image_3=None, image_4=None, image_5=None, additional_text=""):
        _log_step("START", "ORImageGenerate.run() called")
        _log_debug(f"prompt: {prompt[:100]}...")
        _log_debug(f"n: {n}")

        api_base = config.get("api_base")
        api_key = config.get("api_key")
        model = config.get("model")
        temperature = config.get("temperature", 1.0)

        # Gemini 参数
        aspect_ratio = config.get("aspect_ratio")
        image_size = config.get("image_size")

        _log_debug(f"api_base: {api_base}")
        _log_debug(f"model: {model}")
        _log_debug(f"temperature: {temperature}")
        _log_debug(f"aspect_ratio: {aspect_ratio}")
        _log_debug(f"image_size: {image_size}")

        base = _normalize_url(api_base)
        if not base or not api_key or not model:
            _log_error("Image error: missing base/key/model")
            raise Exception("Missing API configuration")

        _log_step("Config check", "All required parameters present")

        # 重试机制
        max_retries = 2
        for attempt in range(max_retries):
            try:
                _log_step(f"Attempt {attempt + 1}/{max_retries}")

                # 收集多路图像输入
                image_inputs = [image_1, image_2, image_3, image_4, image_5]
                image_list = []
                for i, img in enumerate(image_inputs):
                    if img is None:
                        continue
                    _log_debug(f"Processing reference image {i+1}")
                    if len(img.shape) == 3:
                        image_list.append(img)
                        _log_debug(f"  Added as single image, shape: {img.shape}")
                    else:
                        # 若是批次，逐张展开加入列表
                        for j in range(img.shape[0]):
                            image_list.append(img[j])
                        _log_debug(f"  Expanded batch, added {img.shape[0]} images")

                _log_step("Reference images", f"Total: {len(image_list)}")

                # 构建多模态消息内容
                content = []
                if prompt.strip():
                    content.append({"type": "text", "text": prompt.strip()})
                    _log_debug(f"Added prompt text: {len(prompt.strip())} chars")

                if image_list:
                    _log_step("Encoding reference images", f"Count: {len(image_list)}")
                    for i, img_tensor in enumerate(image_list):
                        _log_debug(f"  Encoding image {i+1}/{len(image_list)}")
                        img_np = (img_tensor.cpu().numpy() * 255).astype(np.uint8)
                        pil_img = Image.fromarray(img_np)
                        buffered = BytesIO()
                        pil_img.save(buffered, format="PNG")
                        img_b64 = base64.b64encode(buffered.getvalue()).decode()
                        _log_debug(f"    Base64 size: {len(img_b64)} chars")
                        content.append({
                            "type": "image_url",
                            "image_url": {"url": f"data:image/png;base64,{img_b64}"}
                        })
                        _log_debug(f"    Image {i+1} encoded successfully")

                if additional_text.strip():
                    content.append({"type": "text", "text": additional_text.strip()})
                    _log_debug(f"Added additional text: {len(additional_text.strip())} chars")

                # 如果没有内容，使用默认提示词（保持为列表格式）
                if not content:
                    content = [{"type": "text", "text": "Generate a beautiful landscape"}]
                    _log_debug("Using default prompt")

                _log_step("Content built", f"Items: {len(content)}")

                # 构建基础 payload
                payload = {
                    "model": model,
                    "messages": [{"role": "user", "content": content}],
                    "temperature": temperature
                }

                # 添加 modalities 参数（用于图像生成）
                payload["modalities"] = ["image", "text"]
                _log_debug(f"modalities: {payload['modalities']}")

                # 添加 Gemini image_config
                if aspect_ratio:
                    payload["image_config"] = payload.get("image_config", {})
                    payload["image_config"]["aspect_ratio"] = aspect_ratio
                    _log_debug(f"aspect_ratio: {aspect_ratio}")

                if image_size:
                    payload["image_config"] = payload.get("image_config", {})
                    payload["image_config"]["image_size"] = image_size
                    _log_debug(f"image_size: {image_size}")

                _log_step("Sending request", f"URL: {base}/chat/completions")
                _log_debug(f"Payload size: {len(json.dumps(payload))} bytes")

                headers = _headers(api_key, config.get("site_url", ""), config.get("site_name", ""))
                _log_debug(f"Request headers: {list(headers.keys())}")

                # 根据图像尺寸调整超时时间
                # 1K: 3分钟, 2K: 5分钟, 4K: 10分钟
                if image_size == "4K":
                    timeout = 600  # 10分钟
                    _log_debug(f"Using extended timeout for 4K: {timeout}s")
                elif image_size == "2K":
                    timeout = 300  # 5分钟
                    _log_debug(f"Using extended timeout for 2K: {timeout}s")
                else:
                    timeout = 180  # 3分钟
                    _log_debug(f"Using standard timeout: {timeout}s")

                res = _request("POST", f"{base}/chat/completions", headers, payload, timeout=timeout)

                _log_step("Response received", f"Status: Success")

                if "error" in res:
                    err_msg = res.get("error", {}).get("message", "image generation failed")
                    _log_error(f"API returned error: {err_msg}")
                    raise Exception(err_msg)

                if not res.get("choices"):
                    _log_error(f"Empty response: {str(res)[:200]}")
                    raise Exception(f"empty response: {res}")

                _log_debug(f"Choices in response: {len(res.get('choices', []))}")

                imgs = []
                message = res["choices"][0].get("message", {})
                images = message.get("images", [])

                _log_step("Images in response", f"Count: {len(images)}")

                if not images and message.get("content"):
                    _log_error("Model returned text instead of image")
                    _log_debug(f"Text content: {message.get('content', '')[:200]}")
                    raise Exception("Model returned text instead of image. Use simpler image description.")

                _log_step("Processing images", f"Processing {len(images)} image(s)")

                for i, img_item in enumerate(images):
                    _log_debug(f"\nImage {i+1}:")
                    _log_debug(f"  Type: {type(img_item)}")

                    # OpenRouter 返回格式:
                    # 1. 字符串: "data:image/png;base64,..."
                    # 2. 对象: {"type": "image_url", "image_url": {"url": "data:image/png;base64,..."}}

                    if isinstance(img_item, str):
                        # 格式 1: 直接的 data URL 字符串
                        img_url = img_item
                        _log_debug(f"  Format: String (data URL)")
                    elif isinstance(img_item, dict):
                        # 格式 2: 对象格式
                        if "url" in img_item:
                            img_url = img_item["url"]
                            _log_debug(f"  Format: Dict with 'url' key")
                        elif "image_url" in img_item:
                            image_url_obj = img_item["image_url"]
                            if isinstance(image_url_obj, dict):
                                img_url = image_url_obj.get("url", "")
                                _log_debug(f"  Format: Dict with nested 'image_url.url'")
                            else:
                                img_url = image_url_obj
                                _log_debug(f"  Format: Dict with 'image_url' as string")
                        else:
                            img_url = ""
                            _log_debug(f"  Format: Unknown dict structure")
                            _log_debug(f"  Keys: {list(img_item.keys())}")
                    else:
                        _log_debug(f"  Format: Unsupported type")
                        continue

                    if img_url and img_url.startswith("data:image/"):
                        _log_debug(f"  URL prefix: {img_url[:60]}...")
                        b64_data = img_url.split(",", 1)[1] if "," in img_url else img_url
                        _log_debug(f"  Base64 length: {len(b64_data)} chars")

                        try:
                            data = base64.b64decode(b64_data)
                            _log_debug(f"  Decoded size: {len(data)} bytes")
                            _log_debug(f"  Decoded successfully")

                            pil = Image.open(BytesIO(data)).convert("RGB")
                            _log_debug(f"  PIL Image size: {pil.size}")

                            arr = np.array(pil).astype(np.float32) / 255.0
                            _log_debug(f"  Numpy array shape: {arr.shape}")
                            _log_debug(f"  Numpy array dtype: {arr.dtype}")
                            _log_debug(f"  Value range: [{arr.min():.3f}, {arr.max():.3f}]")

                            imgs.append(torch.from_numpy(arr))
                            _log_debug(f"  Converted to tensor successfully")

                        except Exception as e:
                            _log_error(f"Failed to decode image {i+1}: {e}")
                            raise
                    else:
                        _log_error(f"Invalid data URL format")
                        if not img_url:
                            _log_debug("Reason: Empty URL")
                        else:
                            _log_debug(f"Reason: {img_url[:100]}")

                if imgs:
                    result = torch.stack(imgs)
                    _log_step("Stacking images", f"Result shape: {result.shape}")

                    # 如果 n > 1，复制第一张图像
                    for _ in range(n - 1):
                        result = torch.cat([result, result[:1]], dim=0)
                    _log_step("Final result", f"Shape: {result.shape}, n={n}")

                    _log_step("SUCCESS", f"Generated {len(imgs)} image(s)")
                    return (result,)
                else:
                    _log_error("No images were processed successfully")
                    raise Exception("Failed to process any images")
            except Exception as e:
                if attempt == max_retries - 1:
                    _log_error(f"Image error (final): {e}")
                    raise Exception(f"Image generation failed after {max_retries} attempts: {e}")
                else:
                    _log(f"Retry {attempt + 1}/{max_retries} due to: {e}")
                    _log_debug(f"Error details: {str(e)[:200]}")


# ============ 配置节点 ============

class ORBaseConfig:
    """OpenRouter 基础配置"""

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "api_key": ("STRING", {"default": ""}),
                "model": ("STRING", {"default": "google/gemini-3-pro-image-preview"}),
            },
            "optional": {
                "api_base": ("STRING", {"default": "https://openrouter.ai/api/v1"}),
                "site_url": ("STRING", {"default": "", "multiline": False}),
                "site_name": ("STRING", {"default": "", "multiline": False}),
            }
        }

    RETURN_TYPES = ("OR_BASE_CONFIG",)
    RETURN_NAMES = ("base_config",)
    FUNCTION = "run"
    CATEGORY = "Gemini-OpenRouter/Config"

    def run(self, api_key, model, api_base="https://openrouter.ai/api/v1", site_url="", site_name=""):
        return ({
            "api_base": _normalize_url(api_base),
            "api_key": api_key,
            "model": model,
            "site_url": site_url,
            "site_name": site_name,
        },)


class ORChatParams:
    """OpenRouter 聊天参数配置"""

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "base_config": ("OR_BASE_CONFIG",),
                "temperature": ("FLOAT", {"default": 0.7, "min": 0, "max": 2, "step": 0.1}),
                "max_tokens": ("INT", {"default": 2000, "min": 1, "max": 128000}),
            }
        }

    RETURN_TYPES = ("OR_CHAT_CONFIG",)
    RETURN_NAMES = ("config",)
    FUNCTION = "run"
    CATEGORY = "Gemini-OpenRouter/Config"

    def run(self, base_config, temperature, max_tokens):
        return ({
            **base_config,
            "temperature": temperature,
            "max_tokens": max_tokens,
        },)


class ORImageParams:
    """OpenRouter 图片参数配置"""

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "base_config": ("OR_BASE_CONFIG",),
                "aspect_ratio": (["1:1", "16:9", "4:3", "9:16", "3:4", "2:3", "3:2", "4:5", "5:4", "21:9"], ),
                "image_size": (["1K", "2K", "4K"], ),
                "temperature": ("FLOAT", {"default": 1.0, "min": 0, "max": 1, "step": 0.05}),
            }
        }

    RETURN_TYPES = ("OR_IMAGE_CONFIG",)
    RETURN_NAMES = ("config",)
    FUNCTION = "run"
    CATEGORY = "Gemini-OpenRouter/Config"

    def run(self, base_config, aspect_ratio, image_size, temperature):
        return ({
            **base_config,
            "aspect_ratio": aspect_ratio,
            "image_size": image_size,
            "temperature": temperature,
        },)


NODE_CLASS_MAPPINGS = {
    # 执行节点
    "ORChatGenerate": ORChatGenerate,
    "ORImageGenerate": ORImageGenerate,

    # 配置节点
    "ORBaseConfig": ORBaseConfig,
    "ORChatParams": ORChatParams,
    "ORImageParams": ORImageParams,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    # 执行节点
    "ORChatGenerate": "Chat (OpenRouter)",
    "ORImageGenerate": "Image (OpenRouter)",

    # 配置节点
    "ORBaseConfig": "Base Config (OpenRouter)",
    "ORChatParams": "Chat Params (OpenRouter)",
    "ORImageParams": "Image Params (OpenRouter)",
}
