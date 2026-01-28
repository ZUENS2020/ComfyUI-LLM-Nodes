# OpenRouter 图像生成 API 使用指南

## 概述

在 OpenRouter 中使用 Google Gemini 模型（如 `google/gemini-3-pro-image-preview`）生成图像。

## 核心 API 使用

### 1. 基本请求格式

向 `https://openrouter.ai/api/v1/chat/completions` 发送 POST 请求：

```json
{
  "model": "google/gemini-3-pro-image-preview",
  "messages": [
    {
      "role": "user",
      "content": "一只可爱的橙色猫咪坐在窗台上"
    }
  ],
  "modalities": ["image", "text"]
}
```

**关键参数：**
- `modalities`: 必须设置为 `["image", "text"]` 以启用图像生成
- `model`: 使用支持图像生成的 Gemini 模型

### 2. 完整的 cURL 示例

```bash
curl https://openrouter.ai/api/v1/chat/completions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $OPENROUTER_API_KEY" \
  -H "HTTP-Referer: <YOUR_SITE_URL>" \
  -H "X-Title: <YOUR_SITE_NAME>" \
  -d '{
    "model": "google/gemini-3-pro-image-preview",
    "messages": [
      {
        "role": "user",
        "content": "Generate an image of a sunset over mountains"
      }
    ],
    "modalities": ["image", "text"]
  }'
```

### 3. Python 示例

```python
import requests
import json
import base64

response = requests.post(
    url="https://openrouter.ai/api/v1/chat/completions",
    headers={
        "Authorization": "Bearer YOUR_OPENROUTER_API_KEY",
        "HTTP-Referer": "YOUR_SITE_URL",
        "X-Title": "YOUR_SITE_NAME",
        "Content-Type": "application/json"
    },
    data=json.dumps({
        "model": "google/gemini-3-pro-image-preview",
        "messages": [
            {
                "role": "user",
                "content": "一只橘色的猫坐在花园里，阳光明媚"
            }
        ],
        "modalities": ["image", "text"]
    })
)

result = response.json()

# 提取生成的图像
if 'choices' in result and len(result['choices']) > 0:
    message = result['choices'][0]['message']

    # 检查是否有图像
    if 'images' in message:
        for i, image_data_url in enumerate(message['images']):
            # 数据格式: data:image/png;base64,<base64_string>
            # 提取 base64 部分
            base64_data = image_data_url.split(',')[1]

            # 解码并保存
            image_data = base64.b64decode(base64_data)
            with open(f'generated_image_{i}.png', 'wb') as f:
                f.write(image_data)
            print(f"图像已保存: generated_image_{i}.png")

    # 文本响应
    if 'content' in message:
        print("文本响应:", message['content'])
```

### 4. JavaScript/Node.js 示例

```javascript
import OpenAI from 'openai';

const openai = new OpenAI({
  baseURL: 'https://openrouter.ai/api/v1',
  apiKey: process.env.OPENROUTER_API_KEY,
  defaultHeaders: {
    'HTTP-Referer': 'YOUR_SITE_URL',
    'X-Title': 'YOUR_SITE_NAME'
  }
});

async function generateImage(prompt) {
  const completion = await openai.chat.completions.create({
    model: 'google/gemini-3-pro-image-preview',
    messages: [
      {
        role: 'user',
        content: prompt
      }
    ],
    modalities: ['image', 'text']
  });

  const message = completion.choices[0].message;

  // 提取图像
  if (message.images) {
    message.images.forEach((imageDataUrl, i) => {
      const base64Data = imageDataUrl.split(',')[1];
      const buffer = Buffer.from(base64Data, 'base64');
      require('fs').writeFileSync(`generated_image_${i}.png`, buffer);
      console.log(`图像已保存: generated_image_${i}.png`);
    });
  }

  // 文本响应
  if (message.content) {
    console.log('文本响应:', message.content);
  }

  return message;
}

// 使用
generateImage('一只可爱的小狗在草地上奔跑');
```

## 高级配置选项

### Gemini 图像配置参数

Gemini 图像生成模型支持额外的 `image_config` 参数：

#### 1. 宽高比 (aspect_ratio)

```json
{
  "model": "google/gemini-3-pro-image-preview",
  "messages": [
    {
      "role": "user",
      "content": "风景画"
    }
  ],
  "modalities": ["image", "text"],
  "image_config": {
    "aspect_ratio": "16:9"
  }
}
```

**支持的宽高比：**
- `1:1` → 1024×1024 (默认)
- `2:3` → 832×1248
- `3:2` → 1248×832
- `3:4` → 864×1184
- `4:3` → 1184×864
- `4:5` → 896×1152
- `5:4` → 1152×896
- `9:16` → 768×1344
- `16:9` → 1344×768
- `21:9` → 1536×672

#### 2. 图像尺寸 (image_size)

```json
{
  "model": "google/gemini-3-pro-image-preview",
  "messages": [
    {
      "role": "user",
      "content": "高质量肖像"
    }
  ],
  "modalities": ["image", "text"],
  "image_config": {
    "aspect_ratio": "1:1",
    "image_size": "2K"
  }
}
```

**支持的尺寸：**
- `1K` → 标准分辨率 (默认)
- `2K` → 高分辨率
- `4K` → 最高分辨率

### 3. 组合配置示例

```python
data = {
    "model": "google/gemini-3-pro-image-preview",
    "messages": [
        {
            "role": "user",
            "content": "专业产品摄影，一个精致的咖啡杯放在木质桌上，温暖的光线"
        }
    ],
    "modalities": ["image", "text"],
    "image_config": {
        "aspect_ratio": "4:3",
        "image_size": "2K"
    }
}
```

## 响应格式

```json
{
  "id": "gen-xxx",
  "choices": [
    {
      "message": {
        "role": "assistant",
        "content": "图像已生成",
        "images": [
          "data:image/png;base64,iVBORw0KGgoAAAANSUhEUg..."
        ]
      }
    }
  ]
}
```

**图像格式说明：**
- 格式：base64 编码的 data URL
- 类型：通常是 PNG 格式 (`data:image/png;base64,`)
- 多图像：某些模型可以单次生成多张图像
- 尺寸：图像尺寸因模型而异

## 流式响应

图像生成也支持流式响应：

```python
from openai import OpenAI

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key="YOUR_OPENROUTER_API_KEY"
)

stream = client.chat.completions.create(
    model="google/gemini-3-pro-image-preview",
    messages=[{"role": "user", "content": "生成图像"}],
    modalities=["image", "text"],
    stream=True
)

for chunk in stream:
    if chunk.choices[0].delta.images:
        for image in chunk.choices[0].delta.images:
            print(f"收到图像块: {len(image)} 字节")
```

## 支持的图像生成模型

检查模型的 `output_modalities` 是否包含 "image"：

- `google/gemini-2.5-flash-image-preview`
- `google/gemini-3-pro-image-preview`
- `black-forest-labs/flux.2-pro`
- `black-forest-labs/flux.2-flex`
- `sourceful/riverflow-v2-standard-preview`
- 其他具有图像生成能力的模型

## 最佳实践

1. **清晰的提示词**：提供详细描述以获得更好的图像质量
2. **模型选择**：选择专为图像生成设计的模型
3. **错误处理**：处理响应前检查 `images` 字段
4. **速率限制**：图像生成可能有与文本生成不同的速率限制
5. **存储**：考虑如何处理和存储 base64 图像数据

## 故障排除

### 没有返回图像？

- ✅ 验证模型支持图像生成（`output_modalities` 包含 "image"）
- ✅ 确保请求中包含 `"modalities": ["image", "text"]`
- ✅ 检查提示词是否请求了图像生成

### 模型未找到？

- 在 [Models 页面](https://openrouter.ai/models) 查找可用的图像生成模型
- 按输出模态筛选以查看兼容模型

## 在 ComfyUI 中的集成

你的 ComfyUI-Gemini-LiteLLM 项目可以这样集成：

```python
# 在你的节点中调用 OpenRouter 图像生成
import requests
import base64

def generate_image_with_openrouter(api_key, prompt, aspect_ratio="1:1", image_size="1K"):
    response = requests.post(
        "https://openrouter.ai/api/v1/chat/completions",
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        },
        json={
            "model": "google/gemini-3-pro-image-preview",
            "messages": [{"role": "user", "content": prompt}],
            "modalities": ["image", "text"],
            "image_config": {
                "aspect_ratio": aspect_ratio,
                "image_size": image_size
            }
        }
    )

    result = response.json()

    if 'choices' in result and len(result['choices']) > 0:
        message = result['choices'][0]['message']
        if 'images' in message and len(message['images']) > 0:
            # 返回第一张图像的 base64 数据
            return message['images'][0].split(',')[1]

    return None
```

## 参考资料

- [OpenRouter 图像生成文档](https://openrouter.ai/docs/guides/overview/multimodal/image-generation)
- [Gemini 图像生成文档](https://ai.google.dev/gemini-api/docs/image-generation)
- [OpenRouter Models 页面](https://openrouter.ai/models)
