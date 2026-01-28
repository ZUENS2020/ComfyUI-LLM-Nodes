# ComfyUI-Gemini-LiteLLM v4.0.0 更新说明

## 🎉 新功能：OpenRouter 支持

本次更新添加了对 OpenRouter API 的完整支持，现在插件同时支持 LiteLLM 和 OpenRouter 两种 API 接入方式。

## 📁 新增文件

### `nodes_openrouter.py`
新增的 OpenRouter 节点文件，包含：
- **ORChatGenerate**: OpenRouter 聊天生成节点
- **ORImageGenerate**: OpenRouter 图片生成节点
- **ORBaseConfig**: OpenRouter 基础配置
- **ORChatParams**: OpenRouter 聊天参数
- **ORImageParams**: OpenRouter 图片参数

## 🔄 修改文件

### `__init__.py`
- 更新版本号：v3.0.0 → v4.0.0
- 导入两组节点映射（LiteLLM 和 OpenRouter）
- 合并两组节点到统一的导出字典
- 更新启动日志信息

### `README.md`
- 更新标题：添加 "LiteLLM + OpenRouter" 说明
- 新增两个版本的节点分类说明
- 添加 OpenRouter 快速开始指南
- 更新模型名称示例
- 更新版本号至 v4.0.0

### `docs/openrouter-image-generation-guide.md`
新增的 OpenRouter 图像生成 API 完整使用指南，包含：
- API 调用格式
- Python/JavaScript/cURL 代码示例
- Gemini 专属配置参数（宽高比、分辨率）
- 响应格式说明
- ComfyUI 集成示例

## 📂 节点分类结构

在 ComfyUI 中，节点现在分为两个独立的文件夹：

### LiteLLM 节点（原有）
**分类**: `Gemini-LiteLLM`

**执行节点**:
- `Chat` - 多模态聊天
- `Image` - 图片生成

**配置节点**:
- `Base Config` - 基础配置
- `Chat Params` - 聊天参数
- `Image Params` - 图片参数

### OpenRouter 节点（新增）
**分类**: `Gemini-OpenRouter`

**执行节点**:
- `Chat (OpenRouter)` - 多模态聊天
- `Image (OpenRouter)` - 图片生成

**配置节点**:
- `Base Config (OpenRouter)` - 基础配置（含可选的站点 URL 和名称）
- `Chat Params (OpenRouter)` - 聊天参数
- `Image Params (OpenRouter)` - 图片参数

## 🔑 主要差异

### LiteLLM 版本
- 使用自建的 LiteLLM 服务器
- 需要配置 `api_base`（服务器地址）
- 配置类型：`LLM_BASE_CONFIG`, `LLM_CHAT_CONFIG`, `LLM_IMAGE_CONFIG`

### OpenRouter 版本
- 直接使用 OpenRouter API（默认：https://openrouter.ai/api/v1）
- 需要配置 `api_key`（从 OpenRouter 获取）
- 支持可选的 `site_url` 和 `site_name`（用于排名统计）
- 自动添加 OpenRouter 特定的请求头（HTTP-Referer, X-Title）
- 配置类型：`OR_BASE_CONFIG`, `OR_CHAT_CONFIG`, `OR_IMAGE_CONFIG`

## 🚀 使用方法

### OpenRouter 快速开始

1. 访问 https://openrouter.ai/keys 获取 API 密钥
2. 在 ComfyUI 右键菜单 → `Gemini-OpenRouter` → `Base Config (OpenRouter)`
3. 填写配置：
   - `api_key`: 你的 OpenRouter API 密钥
   - `model`: 如 `google/gemini-3-pro-image-preview`
   - `api_base`: 默认 `https://openrouter.ai/api/v1`（可选）
   - `site_url`: 你的网站 URL（可选）
   - `site_name`: 你的网站名称（可选）
4. 连接到 `Chat Params (OpenRouter)` 或 `Image Params (OpenRouter)`
5. 连接到对应的执行节点

### LiteLLM 使用方法

保持不变，与 v3.0.0 版本相同。

## 📝 API 兼容性

### OpenRouter 图像生成
OpenRouter 使用 `modalities` 参数来请求图像生成：

```python
payload = {
    "model": "google/gemini-3-pro-image-preview",
    "messages": [{"role": "user", "content": "..."}],
    "modalities": ["image", "text"],  # 关键参数
    "image_config": {
        "aspect_ratio": "16:9",
        "image_size": "2K"
    }
}
```

### LiteLLM 图像生成
LiteLLM 仅使用 `image_config` 参数：

```python
payload = {
    "model": "gemini/gemini-3-pro-image-preview",
    "messages": [{"role": "user", "content": "..."}],
    "image_config": {
        "aspect_ratio": "16:9",
        "image_size": "2K"
    }
}
```

## 🎯 推荐模型

### OpenRouter 模型名称
- `google/gemini-3-pro-image-preview` - Gemini 3 Pro（推荐）
- `google/gemini-2.5-flash-image-preview` - 更快的版本
- `google/gemini-2.0-flash-exp:free` - 免费体验版
- 更多模型见：https://openrouter.ai/models

### LiteLLM 模型名称
- `gemini/gemini-3-pro-image-preview`
- `gemini/gemini-2.5-flash-image-preview`
- 取决于你的 LiteLLM 配置

## ⚙️ 技术细节

### 请求头差异

**OpenRouter**:
```python
{
    "Authorization": "Bearer <api_key>",
    "Content-Type": "application/json",
    "HTTP-Referer": "<site_url>",  # OpenRouter 特有
    "X-Title": "<site_name>",      # OpenRouter 特有
    "User-Agent": "ComfyUI"
}
```

**LiteLLM**:
```python
{
    "Authorization": "Bearer <api_key>",
    "Content-Type": "application/json",
    "User-Agent": "ComfyUI"
}
```

### 响应格式
两个版本的响应格式基本一致，都返回标准的 OpenAI 兼容格式：
```json
{
  "choices": [{
    "message": {
      "content": "...",
      "images": ["data:image/png;base64,..."]
    }
  }]
}
```

## 🐛 故障排除

### OpenRouter 常见问题

1. **认证失败**
   - 检查 API 密钥是否正确
   - 确认密钥有足够的额度

2. **模型未找到**
   - 检查模型名称格式（应包含 `provider/` 前缀，如 `google/`）
   - 访问 https://openrouter.ai/models 确认模型可用性

3. **返回文本而非图像**
   - 使用简洁的图像描述性提示词
   - 避免使用问句或过于复杂的描述
   - 检查 `modalities` 参数是否包含 `"image"`

### LiteLLM 常见问题

与之前版本相同，无变化。

## 📊 版本对比

| 特性 | v3.0.0 (LiteLLM) | v4.0.0 (LiteLLM + OpenRouter) |
|------|------------------|--------------------------------|
| LiteLLM 支持 | ✅ | ✅ |
| OpenRouter 支持 | ❌ | ✅ |
| 节点分类 | 1 个文件夹 | 2 个独立文件夹 |
| 模型格式 | LiteLLM 格式 | OpenAI 兼容格式 |
| API 密钥 | LiteLLM 密钥 | OpenRouter 密钥 |
| 站点统计 | 不支持 | 支持（HTTP-Referer） |

## 🔄 升级指南

### 从 v3.0.0 升级到 v4.0.0

1. **完全兼容**：所有原有的 LiteLLM 节点和工作流完全兼容
2. **新增功能**：可以开始使用 OpenRouter 节点
3. **零学习成本**：两组节点的使用方式完全一致
4. **独立使用**：可以选择只使用 LiteLLM 或只使用 OpenRouter，或同时使用两者

### 推荐工作流

**新用户**：
- 如果没有自建服务器，推荐使用 OpenRouter 版本
- 获取 API 密钥更简单，无需服务器配置

**现有用户**：
- 继续使用 LiteLLM 版本，无需任何改动
- 可以尝试 OpenRouter 版本进行对比测试

**高级用户**：
- 同时使用两个版本，根据不同场景选择：
  - LiteLLM：本地/私有部署
  - OpenRouter：云服务/更多模型选择

## 📄 许可证

MIT License - 与之前版本相同

## 🙏 致谢

感谢 OpenRouter 提供的 API 服务！
