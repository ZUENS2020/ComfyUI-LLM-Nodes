"""
测试 OpenRouter 图像生成请求
"""
import json
import urllib.request
import urllib.error

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

def test_model(model_name, use_modalities=True):
    print(f"\n{'='*80}")
    print(f"Testing model: {model_name}")
    print(f"Use modalities: {use_modalities}")
    print('-'*80)

    payload = {
        "model": model_name,
        "messages": [
            {
                "role": "user",
                "content": "A red circle"
            }
        ],
    }

    # 添加 modalities 参数
    if use_modalities:
        payload["modalities"] = ["text", "image"]

    # 添加 image_config（如果模型支持）
    if "image" in model_name.lower():
        payload["image_config"] = {
            "aspect_ratio": "1:1",
            "image_size": "1K"
        }

    print(f"Payload:")
    print(json.dumps(payload, indent=2))

    try:
        body = json.dumps(payload).encode()
        req = urllib.request.Request(
            f"{API_BASE}/chat/completions",
            body,
            headers(API_KEY),
            method="POST"
        )

        with urllib.request.urlopen(req, timeout=120) as response:
            result = json.loads(response.read().decode())

            print(f"\n[OK] Request successful!")
            print(f"\nResponse summary:")

            if "choices" in result and len(result["choices"]) > 0:
                message = result["choices"][0].get("message", {})
                content = message.get("content", "")
                images = message.get("images", [])

                print(f"  Content: {content[:100] if content else '(empty)'}")
                print(f"  Images: {len(images)}")

                if images:
                    print(f"\n  [SUCCESS] Image data found!")
                    for i, img in enumerate(images):
                        if isinstance(img, str):
                            print(f"    Image {i+1}: {img[:100]}...")
                        else:
                            print(f"    Image {i+1}: {type(img)} - {str(img)[:100]}")
                else:
                    print(f"  [INFO] No images in response")
                    print(f"  Full message keys: {list(message.keys())}")
            else:
                print(f"  [ERROR] No choices in response")

    except urllib.error.HTTPError as e:
        print(f"\n[ERROR] HTTP {e.code}")
        try:
            err = e.read().decode()
            print(f"Error: {err[:500]}")
        except:
            print(f"Reason: {e.reason}")
    except Exception as e:
        print(f"\n[ERROR] {e}")
        import traceback
        traceback.print_exc()

# 测试不同的模型
print(f"OpenRouter Image Generation Test")
print(f"API Key: {safe_key(API_KEY)}")
print(f"="*80)

# 测试 1: gemini-3-pro-image-preview（有 modalities）
test_model("google/gemini-3-pro-image-preview", use_modalities=True)

# 测试 2: gemini-2.5-flash-image（有 modalities）
# test_model("google/gemini-2.5-flash-image", use_modalities=True)

# 测试 3: gemini-2.0-flash-exp:free（免费模型）
# test_model("google/gemini-2.0-flash-exp:free", use_modalities=True)
