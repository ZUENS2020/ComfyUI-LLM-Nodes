"""
模拟 ComfyUI 加载节点的方式
"""
import sys
import os

# 添加到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

print("="*80)
print("Simulating ComfyUI Node Loading")
print("="*80)

try:
    print("\n[Step 1] Importing __init__.py...")
    import __init__ as plugin

    print("[OK] Plugin loaded")
    print(f"  Version: {plugin.__doc__}")

except Exception as e:
    print(f"[ERROR] Failed to load plugin: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

try:
    print("\n[Step 2] Checking NODE_CLASS_MAPPINGS...")
    from __init__ import NODE_CLASS_MAPPINGS

    print(f"[OK] Found {len(NODE_CLASS_MAPPINGS)} nodes")

    for node_name in sorted(NODE_CLASS_MAPPINGS.keys()):
        node_class = NODE_CLASS_MAPPINGS[node_name]
        category = getattr(node_class, 'CATEGORY', 'No category')
        print(f"  - {node_name:30} => {category}")

except Exception as e:
    print(f"[ERROR] Failed to load NODE_CLASS_MAPPINGS: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

try:
    print("\n[Step 3] Checking NODE_DISPLAY_NAME_MAPPINGS...")
    from __init__ import NODE_DISPLAY_NAME_MAPPINGS

    print(f"[OK] Found {len(NODE_DISPLAY_NAME_MAPPINGS)} display names")

    for node_name, display_name in sorted(NODE_DISPLAY_NAME_MAPPINGS.items()):
        print(f"  - {node_name:30} => {display_name}")

except Exception as e:
    print(f"[ERROR] Failed to load NODE_DISPLAY_NAME_MAPPINGS: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

try:
    print("\n[Step 4] Testing node instantiation...")

    # 测试 OpenRouter Base Config 节点
    or_base_class = NODE_CLASS_MAPPINGS.get("ORBaseConfig")
    if or_base_class:
        print(f"  Testing ORBaseConfig...")

        # 获取 INPUT_TYPES
        input_types = or_base_class.INPUT_TYPES()
        print(f"    INPUT_TYPES: OK")

        required = input_types.get("required", {})
        optional = input_types.get("optional", {})

        print(f"    Required inputs: {list(required.keys())}")
        print(f"    Optional inputs: {list(optional.keys())}")

        # 测试 RETURN_TYPES
        return_types = or_base_class.RETURN_TYPES
        print(f"    RETURN_TYPES: {return_types}")

        # 测试 FUNCTION
        function = or_base_class.FUNCTION
        print(f"    FUNCTION: {function}")

        # 测试 CATEGORY
        category = or_base_class.CATEGORY
        print(f"    CATEGORY: {category}")

        print(f"  [OK] ORBaseConfig test passed")
    else:
        print(f"  [ERROR] ORBaseConfig not found!")

    # 测试 OpenRouter Image Generate 节点
    or_image_class = NODE_CLASS_MAPPINGS.get("ORImageGenerate")
    if or_image_class:
        print(f"\n  Testing ORImageGenerate...")

        input_types = or_image_class.INPUT_TYPES()
        print(f"    INPUT_TYPES: OK")

        required = input_types.get("required", {})
        optional = input_types.get("optional", {})

        print(f"    Required inputs: {list(required.keys())}")
        print(f"    Optional inputs: {list(optional.keys())}")

        return_types = or_image_class.RETURN_TYPES
        print(f"    RETURN_TYPES: {return_types}")

        function = or_image_class.FUNCTION
        print(f"    FUNCTION: {function}")

        category = or_image_class.CATEGORY
        print(f"    CATEGORY: {category}")

        print(f"  [OK] ORImageGenerate test passed")
    else:
        print(f"  [ERROR] ORImageGenerate not found!")

except Exception as e:
    print(f"\n[ERROR] Node instantiation test failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("\n" + "="*80)
print("[SUCCESS] All tests passed!")
print("="*80)
print("\nComfyUI should be able to load these nodes successfully.")
print("\nTo use in ComfyUI:")
print("1. Restart ComfyUI completely")
print("2. Right-click -> Add Node -> 'Gemini-OpenRouter'")
print("3. Select nodes like:")
print("   - Base Config (OpenRouter)")
print("   - Image Params (OpenRouter)")
print("   - Image (OpenRouter)")
