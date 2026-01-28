"""
ComfyUI Gemini LiteLLM + OpenRouter Nodes
支持通过 LiteLLM 和 OpenRouter 的 Gemini（聊天 + 图片，多模态）

GitHub: https://github.com/ZUENS2020/ComfyUI-Gemini-LiteLLM
Version: 4.0.0
"""

try:
    # 尝试相对导入（ComfyUI 正常加载时）
    from .nodes import NODE_CLASS_MAPPINGS as LLM_NODE_CLASS_MAPPINGS, NODE_DISPLAY_NAME_MAPPINGS as LLM_NODE_DISPLAY_NAME_MAPPINGS
    from .nodes_openrouter import NODE_CLASS_MAPPINGS as OR_NODE_CLASS_MAPPINGS, NODE_DISPLAY_NAME_MAPPINGS as OR_NODE_DISPLAY_NAME_MAPPINGS
except ImportError:
    # 回退到绝对导入（测试时）
    from nodes import NODE_CLASS_MAPPINGS as LLM_NODE_CLASS_MAPPINGS, NODE_DISPLAY_NAME_MAPPINGS as LLM_NODE_DISPLAY_NAME_MAPPINGS
    from nodes_openrouter import NODE_CLASS_MAPPINGS as OR_NODE_CLASS_MAPPINGS, NODE_DISPLAY_NAME_MAPPINGS as OR_NODE_DISPLAY_NAME_MAPPINGS

# 合并两组节点
NODE_CLASS_MAPPINGS = {
    **LLM_NODE_CLASS_MAPPINGS,
    **OR_NODE_CLASS_MAPPINGS,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    **LLM_NODE_DISPLAY_NAME_MAPPINGS,
    **OR_NODE_DISPLAY_NAME_MAPPINGS,
}

__all__ = ['NODE_CLASS_MAPPINGS', 'NODE_DISPLAY_NAME_MAPPINGS']

print("\033[92m[ComfyUI-Gemini v4.0.0]\033[0m \033[93mLoaded (LiteLLM + OpenRouter).\033[0m")
print("  - \033[96mLiteLLM nodes:\033[0m Category 'Gemini-LiteLLM'")
print("  - \033[96mOpenRouter nodes:\033[0m Category 'Gemini-OpenRouter'")
