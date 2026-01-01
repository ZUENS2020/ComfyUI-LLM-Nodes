"""
ComfyUI OpenAI Custom Node
支持自定义 API Base 和 Key 的 OpenAI 兼容节点
Version: 2.0 - Fixed Config
"""

from .nodes import NODE_CLASS_MAPPINGS, NODE_DISPLAY_NAME_MAPPINGS

__all__ = ['NODE_CLASS_MAPPINGS', 'NODE_DISPLAY_NAME_MAPPINGS']

print("\033[92m[ComfyUI-OpenAI-Custom v2.0]\033[0m \033[93mLoaded successfully! Fixed config support.\033[0m")
