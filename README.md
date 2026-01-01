# ComfyUI LLM Custom Nodes

ComfyUI 的 LLM 集成插件，支持聊天和图片生成功能。

## 功能特性

- ✅ 聊天对话（Chat Completions）
- ✅ 图片生成（Image Generation）
- ✅ 支持 OpenAI / LiteLLM 代理
- ✅ 支持 Gemini 3 图片生成（精确控制分辨率和宽高比）
- ✅ 零外部依赖（仅使用 Python 标准库 urllib）

## 节点列表

### 执行节点

| 节点名称 | 功能 | 输入 | 输出 |
|---------|------|------|------|
| Chat | 聊天对话 | config, prompt, system | text |
| Image | 图片生成 | config, prompt, n | image |

### 配置节点

| 节点名称 | 功能 | 说明 |
|---------|------|------|
| Base Config | 基础配置 | API地址、密钥、模型 |
| Chat Params | 聊天参数 | temperature、max_tokens |
| OpenAI Image | OpenAI图片参数 | size、quality |
| Gemini Image | Gemini图片参数 | aspect_ratio、image_size |

## 使用方法

### 1. 聊天对话

**工作流：**
```
Base Config → Chat Params → Chat
                             ↑
                           prompt
```

**配置示例：**
- api_base: `https://api.openai.com/v1`
- model: `gpt-3.5-turbo`
- temperature: `0.7`
- max_tokens: `2000`

### 2. OpenAI 图片生成

**工作流：**
```
Base Config → OpenAI Image → Image
                              ↑
                            prompt
```

**配置示例：**
- api_base: `https://api.openai.com/v1`
- model: `dall-e-3`
- size: `1024x1024`
- quality: `standard`

### 3. Gemini 图片生成（通过 LiteLLM）

**工作流：**
```
Base Config → Gemini Image → Image
                              ↑
                            prompt
```

**配置示例：**
- api_base: `https://your-litellm-server.com/v1`
- model: `gemini/gemini-3-pro-image-preview`
- aspect_ratio: `16:9`
- image_size: `2K`

## Gemini 图片生成详解

### 支持的分辨率

| image_size | 说明 | 像素数 |
|------------|------|--------|
| 1K | 低分辨率 | ~100万像素 |
| 2K | 中分辨率 | ~400万像素 |
| 4K | 高分辨率 | ~1600万像素 |

### 支持的宽高比

| aspect_ratio | 类型 | 说明 |
|--------------|------|------|
| 1:1 | 正方形 | 适合头像、图标 |
| 16:9 | 横向 | 适合壁纸、横幅 |
| 4:3 | 横向 | 适合传统显示器 |
| 9:16 | 竖向 | 适合手机屏幕 |
| 3:4 | 竖向 | 适合竖版海报 |

### 实际输出尺寸对照表

| image_size | aspect_ratio | 实际像素 |
|------------|--------------|----------|
| 1K | 1:1 | 1024 × 1024 |
| 2K | 1:1 | 2048 × 2048 |
| 4K | 1:1 | 4096 × 4096 |
| 2K | 16:9 | 2752 × 1536 |
| 2K | 4:3 | 2400 × 1792 |
| 2K | 9:16 | 1536 × 2752 |
| 2K | 3:4 | 1792 × 2400 |

### 技术细节

#### 为什么 Gemini 使用不同的 API 格式？

Gemini 图片生成通过 LiteLLM 时使用 Chat Completions 端点，这是因为：
1. Gemini 原生 API 设计为对话式接口
2. LiteLLM v1.80.7+ 支持通过 `image_config` 参数控制图片生成
3. 响应中图片数据以 `message.images` 形式返回

#### API 调用格式

**端点：** `/chat/completions`

**请求体：**
```json
{
  "model": "gemini/gemini-3-pro-image-preview",
  "messages": [{"role": "user", "content": "prompt"}],
  "image_config": {
    "image_size": "2K",
    "aspect_ratio": "16:9"
  }
}
```

**响应体：**
```json
{
  "choices": [{
    "message": {
      "images": [{
        "image_url": {
          "url": "data:image/jpeg;base64,..."
        }
      }]
    }
  }]
}
```

#### 测试验证

实测结果（LiteLLM v1.80.7+）：
- ✅ 1K + 1:1 → 1024×1024
- ✅ 2K + 16:9 → 2752×1536
- ✅ 2K + 9:16 → 1536×2752
- ✅ 4K + 1:1 → 4096×4096

## API 兼容性

### OpenAI 标准 API

| 项目 | 值 |
|------|-----|
| 端点 | `/images/generations` |
| 参数 | `prompt`, `size`, `quality`, `n` |
| 响应 | `data[].b64_json` 或 `data[].url` |

### Gemini（通过 LiteLLM）

| 项目 | 值 |
|------|-----|
| 端点 | `/chat/completions` |
| 参数 | `messages`, `image_config` |
| 响应 | `choices[].message.images[].image_url.url` |
| 要求 | LiteLLM v1.80.7+ |

## 常见问题

### Q: 为什么 Gemini 不使用 `/images/generations` 端点？

**A:** Gemini 图片生成通过 LiteLLM 时使用 `/chat/completions` 端点，这是 LiteLLM 对 Gemini 的标准实现方式。使用 `/images/generations` 会返回空数据。

### Q: 为什么参数是 `image_size` 而不是 `image_resolution`？

**A:** `image_size` 是 LiteLLM v1.80.7+ 的标准参数名称，与官方文档保持一致。旧版本可能使用 `imageResolution`，但新版本已废弃。

### Q: 支持哪些 LiteLLM 代理？

**A:** 任何支持 LiteLLM v1.80.7+ 的代理服务器，前提是代理正确转发 `image_config` 参数到 Gemini 后端。

### Q: OpenAI 和 Gemini 可以用同一个 Base Config 吗？

**A:** 不建议。虽然理论上可以，但它们使用不同的端点和参数格式：
- OpenAI: `/images/generations` + `prompt`/`size`
- Gemini: `/chat/completions` + `messages`/`image_config`

### Q: 为什么测试时返回 1408×768？

**A:** 如果使用错误的端点或参数格式，LiteLLM 会回退到默认尺寸。确保：
1. 使用 `/chat/completions` 端点
2. 传递 `image_config` 参数
3. LiteLLM 版本 ≥ 1.80.7

## 开发说明

### 依赖

- **必需：** Python 3.8+, ComfyUI, Pillow, NumPy, PyTorch
- **HTTP库：** 使用 Python 标准库 `urllib`（零外部依赖）

### 目录结构

```
ComfyUI-OpenAI-Custom/
├── __init__.py       # 插件入口
├── nodes.py          # 节点实现
└── README.md         # 本文档
```

### 代码架构

**执行节点：**
- `LLMChatGenerate` - 聊天对话执行
- `LLMImageGenerate` - 图片生成执行（支持 OpenAI 和 Gemini 两种格式）

**配置节点：**
- `LLMBaseConfig` - 基础配置（api_base, api_key, model）
- `ChatParams` - 聊天参数（base_config + temperature, max_tokens）
- `OpenAIImageParams` - OpenAI 图片参数（base_config + size, quality）
- `GeminiImageParams` - Gemini 图片参数（base_config + aspect_ratio, image_size）

**工具函数：**
- `_normalize_url()` - URL 标准化
- `_headers()` - 生成请求头
- `_request()` - 统一 HTTP 请求
- `_download()` - 下载二进制数据
- `_log()` - 日志输出
- `_safe_key()` - 密钥脱敏

## 更新日志

### v2.0.0 (2026-01-02)

- ✅ **重大更新：** 修复 Gemini 图片生成参数格式
- ✅ 使用 `/chat/completions` 端点代替 `/images/generations`
- ✅ 添加 `image_config` 参数支持
- ✅ 支持精确控制分辨率（1K/2K/4K）和宽高比（5种）
- ✅ 实测验证所有尺寸组合
- ✅ 删除无效的完整配置节点（Full Config）
- ✅ 简化节点命名（移除表情符号）
- ✅ 更新文档和使用说明

### v1.0.0

- 初始版本
- 支持基础聊天和图片生成

## 参考资料

- [LiteLLM Documentation](https://docs.litellm.ai/)
- [LiteLLM Issue #17075 - Gemini Image Config](https://github.com/BerriAI/litellm/issues/17075)
- [Gemini 3 API - Media Resolution](https://ai.google.dev/gemini-api/docs/gemini-3#media_resolution)
- [OpenAI Images API](https://platform.openai.com/docs/api-reference/images)

## License

MIT License
