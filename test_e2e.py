"""
端到端测试：完整的 OpenRouter 图像生成工作流
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

print("="*80)
print("End-to-End Test: OpenRouter Image Generation")
print("="*80)

# 1. 加载节点
print("\n[1] Loading nodes...")
try:
    from nodes_openrouter import ORBaseConfig, ORImageParams, ORImageGenerate
    print("    [OK] Nodes loaded")
except Exception as e:
    print(f"    [ERROR] {e}")
    sys.exit(1)

# 2. 创建 Base Config
print("\n[2] Creating Base Config...")
try:
    base_config_node = ORBaseConfig()
    result = base_config_node.run(
        api_key="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",
        model="google/gemini-3-pro-image-preview",
        api_base="https://openrouter.ai/api/v1",
        site_url="",
        site_name=""
    )
    base_config = result[0]
    print(f"    [OK] Base config created")
    print(f"        api_base: {base_config['api_base']}")
    print(f"        model: {base_config['model']}")
except Exception as e:
    print(f"    [ERROR] {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# 3. 创建 Image Params
print("\n[3] Creating Image Params...")
try:
    image_params_node = ORImageParams()
    result = image_params_node.run(
        base_config=base_config,
        aspect_ratio="1:1",
        image_size="1K",
        temperature=1.0
    )
    config = result[0]
    print(f"    [OK] Image params created")
    print(f"        aspect_ratio: {config['aspect_ratio']}")
    print(f"        image_size: {config['image_size']}")
except Exception as e:
    print(f"    [ERROR] {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# 4. 执行图像生成
print("\n[4] Executing Image Generation...")
try:
    image_node = ORImageGenerate()
    result = image_node.run(
        config=config,
        prompt="A cute cat sitting on a windowsill",
        n=1,
        image_1=None,
        image_2=None,
        image_3=None,
        image_4=None,
        image_5=None,
        additional_text=""
    )

    # result 应该是一个包含 tensor 的元组
    import torch
    image_tensor = result[0]

    print(f"    [OK] Image generated!")
    print(f"        Shape: {image_tensor.shape}")
    print(f"        Dtype: {image_tensor.dtype}")
    print(f"        Min: {image_tensor.min().item():.3f}")
    print(f"        Max: {image_tensor.max().item():.3f}")

    # 保存图像
    from PIL import Image
    import numpy as np

    # 转换 tensor 到 PIL Image
    img_np = (image_tensor[0].cpu().numpy() * 255).astype(np.uint8)
    pil_img = Image.fromarray(img_np)

    output_path = "e2e_test_output.png"
    pil_img.save(output_path)
    print(f"        Saved to: {output_path}")

    print("\n" + "="*80)
    print("[SUCCESS] End-to-end test completed successfully!")
    print("="*80)
    print("\nThe nodes are working correctly in ComfyUI!")
    print("You can now use them in ComfyUI with the same workflow.")

except Exception as e:
    print(f"\n    [ERROR] {e}")
    import traceback
    traceback.print_exc()
    print("\n" + "="*80)
    print("[FAILED] End-to-end test failed")
    print("="*80)
    sys.exit(1)
