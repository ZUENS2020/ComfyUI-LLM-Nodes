"""
测试 OpenRouter 图像生成 API
"""
import json
import urllib.request
import urllib.error
import base64
import sys

# 设置控制台输出为 UTF-8
if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

API_KEY = "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"
API_BASE = "https://openrouter.ai/api/v1"
MODEL = "google/gemini-2.0-flash-exp:free"

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

def test_image_gen():
    print(f"Testing OpenRouter - Checking Image Generation Models")
    print(f"API Key: {safe_key(API_KEY)}")
    print("-" * 80)

    # 检查模型列表
    print("\n[Checking available Gemini models...]")
    try:
        req = urllib.request.Request(
            f"{API_BASE}/models",
            headers={"Authorization": f"Bearer {API_KEY}"},
            method="GET"
        )

        with urllib.request.urlopen(req, timeout=30) as response:
            result = json.loads(response.read().decode())

            # 查找 Gemini 模型
            if "data" in result:
                gemini_models = [m for m in result["data"] if "gemini" in m.get("id", "").lower()]

                print(f"\nFound {len(gemini_models)} Gemini models")
                print("=" * 80)

                # 找出支持图像的模型
                image_models = []
                text_models = []

                for model in gemini_models:
                    model_id = model.get("id", "unknown")
                    arch = model.get("architecture", {})
                    modalities = arch.get("modalities", {})
                    output_modalities = modalities.get("output", [])

                    supports_image = "image" in output_modalities

                    if supports_image:
                        image_models.append(model_id)
                    else:
                        text_models.append(model_id)

                print(f"\n[IMAGE GENERATION MODELS] ({len(image_models)})")
                print("-" * 80)
                for model_id in sorted(image_models):
                    print(f"  {model_id}")

                print(f"\n[TEXT-ONLY MODELS] ({len(text_models)})")
                print("-" * 80)
                for model_id in sorted(text_models)[:20]:
                    print(f"  {model_id}")
                if len(text_models) > 20:
                    print(f"  ... and {len(text_models) - 20} more")

    except Exception as e:
        print(f"[ERROR] {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_image_gen()
