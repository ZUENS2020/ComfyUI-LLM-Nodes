"""
ComfyUI LLM Nodes
支持 OpenAI 和 Gemini 的 LLM 集成插件
Version: 2.0.0
"""

from .nodes import NODE_CLASS_MAPPINGS, NODE_DISPLAY_NAME_MAPPINGS

__all__ = ['NODE_CLASS_MAPPINGS', 'NODE_DISPLAY_NAME_MAPPINGS']

print("\033[92m[ComfyUI-LLM-Nodes v2.0.0]\033[0m \033[93mLoaded successfully!\033[0m")
