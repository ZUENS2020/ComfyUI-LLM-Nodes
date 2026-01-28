"""
完整的 OpenRouter 图像生成工作流测试
"""
import json
import urllib.request
import base64
import sys
from io import BytesIO

if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

API_KEY = "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"
API_BASE = "https://openrouter.ai/api/v1"

def safe_key(key):
    if len(key) <= 10:
        return "***"
    return f"{key[:10]}***{key[-4:]}"

def headers(key):
    return {
        "Authorization": f"Bearer {key}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://comfyui-test",
        "X-Title": "ComfyUI Test"
    }

def test_image_extraction():
    """测试图像提取逻辑（与 nodes_openrouter.py 中的代码相同）"""
    print(f"Testing Image Extraction Logic")
    print(f"="*80)

    # 模拟 API 响应
    mock_response = {
        "choices": [{
            "message": {
                "content": "",
                "images": [
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=="
                        }
                    }
                ]
            }
        }]
    }

    message = mock_response["choices"][0]["message"]
    images = message.get("images", [])

    print(f"\nProcessing {len(images)} image(s)...")

    for i, img_item in enumerate(images):
        print(f"\nImage {i+1}:")
        print(f"  Type: {type(img_item)}")
        print(f"  Structure: {json.dumps(img_item, indent=4)[:200]}...")

        # 使用与 nodes_openrouter.py 相同的提取逻辑
        if isinstance(img_item, str):
            img_url = img_item
            print(f"  Format: String")
        elif isinstance(img_item, dict):
            if "url" in img_item:
                img_url = img_item["url"]
                print(f"  Format: Dict with 'url' key")
            elif "image_url" in img_item:
                image_url_obj = img_item["image_url"]
                if isinstance(image_url_obj, dict):
                    img_url = image_url_obj.get("url", "")
                    print(f"  Format: Dict with 'image_url.url' key")
                else:
                    img_url = image_url_obj
                    print(f"  Format: Dict with 'image_url' as string")
            else:
                img_url = ""
                print(f"  Format: Unknown dict structure")
        else:
            print(f"  Format: Unsupported type {type(img_item)}")
            continue

        print(f"  Extracted URL length: {len(img_url)}")

        if img_url and img_url.startswith("data:image/"):
            b64_data = img_url.split(",", 1)[1] if "," in img_url else img_url
            print(f"  Base64 data length: {len(b64_data)}")

            try:
                data = base64.b64decode(b64_data)
                print(f"  Decoded data length: {len(data)} bytes")
                print(f"  [OK] Successfully decoded image!")
            except Exception as e:
                print(f"  [ERROR] Failed to decode: {e}")
        else:
            print(f"  [ERROR] Invalid data URL")

def test_real_request():
    """测试真实的 API 请求"""
    print(f"\n{'='*80}")
    print(f"Testing Real API Request")
    print(f"="*80)

    payload = {
        "model": "google/gemini-3-pro-image-preview",
        "messages": [
            {
                "role": "user",
                "content": "A simple blue square on white background"
            }
        ],
        "modalities": ["text", "image"],
        "image_config": {
            "aspect_ratio": "1:1",
            "image_size": "1K"
        }
    }

    print(f"\nSending request to {API_BASE}/chat/completions")
    print(f"Model: {payload['model']}")

    try:
        body = json.dumps(payload).encode()
        req = urllib.request.Request(
            f"{API_BASE}/chat/completions",
            body,
            headers(API_KEY),
            method="POST"
        )

        with urllib.request.urlopen(req, timeout=180) as response:
            result = json.loads(response.read().decode())

            print(f"\n[OK] Request successful!")

            if "choices" in result and len(result["choices"]) > 0:
                message = result["choices"][0].get("message", {})
                images = message.get("images", [])

                print(f"\nImages in response: {len(images)}")

                if images:
                    print(f"\n[SUCCESS] Processing images...")
                    for i, img_item in enumerate(images):
                        print(f"\nImage {i+1}:")

                        # 使用与 nodes_openrouter.py 相同的提取逻辑
                        if isinstance(img_item, str):
                            img_url = img_item
                        elif isinstance(img_item, dict):
                            if "url" in img_item:
                                img_url = img_item["url"]
                            elif "image_url" in img_item:
                                image_url_obj = img_item["image_url"]
                                if isinstance(image_url_obj, dict):
                                    img_url = image_url_obj.get("url", "")
                                else:
                                    img_url = image_url_obj
                            else:
                                img_url = ""
                        else:
                            continue

                        if img_url and img_url.startswith("data:image/"):
                            b64_data = img_url.split(",", 1)[1] if "," in img_url else img_url

                            try:
                                data = base64.b64decode(b64_data)
                                print(f"  Decoded: {len(data)} bytes")
                                print(f"  [OK] Image {i+1} successfully processed!")

                                # 保存测试图像
                                output_path = f"test_image_{i+1}.png"
                                with open(output_path, "wb") as f:
                                    f.write(data)
                                print(f"  Saved to: {output_path}")

                            except Exception as e:
                                print(f"  [ERROR] Failed: {e}")
                else:
                    print(f"\n[ERROR] No images in response")
                    print(f"Message content: {message.get('content', '(empty)')[:200]}")
            else:
                print(f"\n[ERROR] No choices in response")

    except Exception as e:
        print(f"\n[ERROR] {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print(f"OpenRouter Image Generation - Full Test")
    print(f"API Key: {safe_key(API_KEY)}")
    print(f"="*80)

    # 测试 1: 图像提取逻辑
    test_image_extraction()

    # 测试 2: 真实 API 请求
    test_real_request()

    print(f"\n{'='*80}")
    print(f"Test completed!")
    print(f"="*80)
