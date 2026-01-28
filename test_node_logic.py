"""
完全模拟 ORImageGenerate 节点的逻辑进行测试
"""
import json
import base64
import urllib.request
import urllib.error
from io import BytesIO
from typing import Any

# ========== 从 nodes_openrouter.py 复制的函数 ==========

def _log(msg: str):
    print(f"[OpenRouter] {msg}")


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


# ========== 模拟节点执行 ==========

def test_or_image_generate():
    """完全按照 ORImageGenerate 节点的逻辑"""

    print("="*80)
    print("Testing ORImageGenerate Node Logic")
    print("="*80)

    # 1. 模拟配置输入
    config = {
        "api_base": "https://openrouter.ai/api/v1",
        "api_key": "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",
        "model": "google/gemini-3-pro-image-preview",
        "site_url": "",
        "site_name": "",
        "aspect_ratio": "1:1",
        "image_size": "1K",
        "temperature": 1.0
    }

    prompt = "A simple red circle on white background"
    n = 1
    image_1 = None
    image_2 = None
    image_3 = None
    image_4 = None
    image_5 = None
    additional_text = ""

    print(f"\n[Config]")
    print(f"  api_base: {config['api_base']}")
    print(f"  api_key: {config['api_key'][:10]}***{config['api_key'][-4:]}")
    print(f"  model: {config['model']}")
    print(f"  aspect_ratio: {config['aspect_ratio']}")
    print(f"  image_size: {config['image_size']}")

    print(f"\n[Input]")
    print(f"  prompt: {prompt}")
    print(f"  n: {n}")

    # 2. 获取参数
    api_base = config.get("api_base")
    api_key = config.get("api_key")
    model = config.get("model")
    temperature = config.get("temperature", 1.0)

    # Gemini 参数
    aspect_ratio = config.get("aspect_ratio")
    image_size = config.get("image_size")

    base = _normalize_url(api_base)
    if not base or not api_key or not model:
        _log("Image error: missing base/key/model")
        raise Exception("Missing API configuration")

    print(f"\n[Step 1] Configuration check: OK")

    # 3. 重试机制
    max_retries = 2
    for attempt in range(max_retries):
        try:
            print(f"\n[Step 2] Attempt {attempt + 1}/{max_retries}")

            # 收集多路图像输入
            image_inputs = [image_1, image_2, image_3, image_4, image_5]
            image_list = []
            for img in image_inputs:
                if img is None:
                    continue
                # 这里跳过，因为我们是文本测试

            print(f"  Reference images: {len(image_list)}")

            # 构建多模态消息内容
            content = []
            if prompt.strip():
                content.append({"type": "text", "text": prompt.strip()})

            if image_list:
                # 这里跳过，因为没有参考图像
                pass

            if additional_text.strip():
                content.append({"type": "text", "text": additional_text.strip()})

            # 如果没有内容，使用默认提示词
            if not content:
                content = [{"type": "text", "text": "Generate a beautiful landscape"}]

            print(f"  Content items: {len(content)}")

            # 构建基础 payload
            payload = {
                "model": model,
                "messages": [{"role": "user", "content": content}],
                "temperature": temperature
            }

            # 添加 modalities 参数（用于图像生成）
            payload["modalities"] = ["image", "text"]

            print(f"  modalities: {payload['modalities']}")

            # 添加 Gemini image_config
            if aspect_ratio:
                payload["image_config"] = payload.get("image_config", {})
                payload["image_config"]["aspect_ratio"] = aspect_ratio
                print(f"  aspect_ratio: {aspect_ratio}")

            if image_size:
                payload["image_config"] = payload.get("image_config", {})
                payload["image_config"]["image_size"] = image_size
                print(f"  image_size: {image_size}")

            print(f"\n[Step 3] Sending request...")
            print(f"  URL: {base}/chat/completions")
            print(f"  Payload size: {len(json.dumps(payload))} bytes")

            headers = _headers(api_key, config.get("site_url", ""), config.get("site_name", ""))
            res = _request("POST", f"{base}/chat/completions", headers, payload, timeout=180)

            print(f"\n[Step 4] Response received")

            if "error" in res:
                raise Exception(res.get("error", {}).get("message", "image generation failed"))

            if not res.get("choices"):
                raise Exception(f"empty response: {res}")

            print(f"  Choices: {len(res.get('choices', []))}")

            imgs = []
            message = res["choices"][0].get("message", {})
            images = message.get("images", [])

            print(f"  Images in response: {len(images)}")

            if not images and message.get("content"):
                raise Exception("Model returned text instead of image. Use simpler image description.")

            print(f"\n[Step 5] Processing images...")

            for i, img_item in enumerate(images):
                print(f"\n  Image {i+1}:")
                print(f"    Type: {type(img_item)}")

                # OpenRouter 返回格式处理
                if isinstance(img_item, str):
                    # 格式 1: 直接的 data URL 字符串
                    img_url = img_item
                    print(f"    Format: String (data URL)")
                elif isinstance(img_item, dict):
                    # 格式 2: 对象格式
                    if "url" in img_item:
                        img_url = img_item["url"]
                        print(f"    Format: Dict with 'url' key")
                    elif "image_url" in img_item:
                        image_url_obj = img_item["image_url"]
                        if isinstance(image_url_obj, dict):
                            img_url = image_url_obj.get("url", "")
                            print(f"    Format: Dict with nested 'image_url.url'")
                        else:
                            img_url = image_url_obj
                            print(f"    Format: Dict with 'image_url' as string")
                    else:
                        img_url = ""
                        print(f"    Format: Unknown dict structure")
                        print(f"    Keys: {list(img_item.keys())}")
                else:
                    print(f"    Format: Unsupported type")
                    continue

                if img_url and img_url.startswith("data:image/"):
                    print(f"    URL prefix: {img_url[:50]}...")

                    b64_data = img_url.split(",", 1)[1] if "," in img_url else img_url
                    print(f"    Base64 length: {len(b64_data)}")

                    try:
                        data = base64.b64decode(b64_data)
                        print(f"    Decoded size: {len(data)} bytes")

                        # 保存测试文件
                        output_file = f"test_node_output_{i+1}.png"
                        with open(output_file, "wb") as f:
                            f.write(data)
                        print(f"    Saved to: {output_file}")

                        # 注意：这里不能导入 PIL 和 torch，因为是测试环境
                        # 在实际节点中会转换为 tensor
                        imgs.append({
                            "data": data,
                            "size": len(data)
                        })

                        print(f"    [OK] Successfully processed!")

                    except Exception as e:
                        print(f"    [ERROR] Failed to decode: {e}")
                        raise
                else:
                    print(f"    [ERROR] Invalid data URL format")
                    if not img_url:
                        print(f"    Reason: Empty URL")
                    else:
                        print(f"    Reason: {img_url[:50]}")

            if imgs:
                print(f"\n[Step 6] Result: {len(imgs)} image(s) processed")
                print(f"\n[SUCCESS] Test completed successfully!")
                return True
            else:
                print(f"\n[ERROR] No images were processed")
                return False

        except Exception as e:
            if attempt == max_retries - 1:
                _log(f"Image error (final): {e}")
                print(f"\n[FAILED] All {max_retries} attempts failed")
                print(f"Error: {e}")
                import traceback
                traceback.print_exc()
                return False
            else:
                _log(f"Image retry {attempt + 1}/{max_retries} due to: {e}")
                print(f"  Retrying...")

if __name__ == "__main__":
    import sys
    if sys.platform == "win32":
        import io
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

    success = test_or_image_generate()

    print("\n" + "="*80)
    if success:
        print("RESULT: SUCCESS")
    else:
        print("RESULT: FAILED")
    print("="*80)
