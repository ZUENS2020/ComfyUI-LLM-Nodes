"""
ComfyUI Gemini LiteLLM Nodes
仅支持通过 LiteLLM 的 Gemini（聊天 + 图片，多模态）

GitHub: https://github.com/ZUENS2020/ComfyUI-Gemini-LiteLLM
Version: 3.0.0
"""

from .nodes import NODE_CLASS_MAPPINGS, NODE_DISPLAY_NAME_MAPPINGS

__all__ = ['NODE_CLASS_MAPPINGS', 'NODE_DISPLAY_NAME_MAPPINGS']

print("\033[92m[ComfyUI-Gemini-LiteLLM v3.0.0]\033[0m \033[93mLoaded (Gemini only).\033[0m")
