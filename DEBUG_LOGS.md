# 调试日志说明

## 📊 日志系统

现在 OpenRouter 节点会输出详细的调试日志，帮助你追踪整个图像生成过程。

## 🔍 日志类型

### 1. STEP 日志 - 主要步骤
```
[OpenRouter STEP] START: ORImageGenerate.run() called
[OpenRouter STEP] Config check: All required parameters present
[OpenRouter STEP] Attempt 1/2
[OpenRouter STEP] Sending request: URL: https://openrouter.ai/api/v1/chat/completions
[OpenRouter STEP] Response received: Status: Success
[OpenRouter STEP] Images in response: Count: 1
[OpenRouter STEP] SUCCESS: Generated 1 image(s)
```

### 2. DEBUG 日志 - 详细信息
```
[OpenRouter DEBUG] prompt: A cute cat...
[OpenRouter DEBUG] model: google/gemini-3-pro-image-preview
[OpenRouter DEBUG] aspect_ratio: 1:1
[OpenRouter DEBUG] image_size: 1K
[OpenRouter DEBUG] Payload size: 269 bytes
[OpenRouter DEBUG] Base64 length: 2416308 chars
[OpenRouter DEBUG] Decoded size: 1812230 bytes
[OpenRouter DEBUG] PIL Image size: (1024, 1024)
[OpenRouter DEBUG] Numpy array shape: (1024, 1024, 3)
[OpenRouter DEBUG] Value range: [0.000, 1.000]
```

### 3. ERROR 日志 - 错误信息
```
[OpenRouter ERROR] Image error: missing base/key/model
[OpenRouter ERROR] Model returned text instead of image
[OpenRouter ERROR] Failed to decode image: ...
```

## 📝 完整日志示例

### 成功的图像生成
```
[OpenRouter STEP] START: ORImageGenerate.run() called
[OpenRouter DEBUG] prompt: A red circle on white background
[OpenRouter DEBUG] n: 1
[OpenRouter DEBUG] api_base: https://openrouter.ai/api/v1
[OpenRouter DEBUG] model: google/gemini-3-pro-image-preview
[OpenRouter DEBUG] temperature: 1.0
[OpenRouter DEBUG] aspect_ratio: 1:1
[OpenRouter DEBUG] image_size: 1K
[OpenRouter STEP] Config check: All required parameters present
[OpenRouter STEP] Attempt 1/2
[OpenRouter STEP] Reference images: Total: 0
[OpenRouter DEBUG] Added prompt text: 34 chars
[OpenRouter STEP] Content built: Items: 1
[OpenRouter DEBUG] modalities: ['image', 'text']
[OpenRouter DEBUG] aspect_ratio: 1:1
[OpenRouter DEBUG] image_size: 1K
[OpenRouter STEP] Sending request: URL: https://openrouter.ai/api/v1/chat/completions
[OpenRouter DEBUG] Payload size: 269 bytes
[OpenRouter DEBUG] Request headers: ['Authorization', 'Content-Type', 'User-Agent']
[OpenRouter STEP] Response received: Status: Success
[OpenRouter DEBUG] Choices in response: 1
[OpenRouter STEP] Images in response: Count: 1
[OpenRouter STEP] Processing images: Processing 1 image(s)
[OpenRouter DEBUG]
Image 1:
[OpenRouter DEBUG]   Type: <class 'dict'>
[OpenRouter DEBUG]   Format: Dict with nested 'image_url.url'
[OpenRouter DEBUG]   URL prefix: data:image/png;base64,iVBORw0KGgo...
[OpenRouter DEBUG]   Base64 length: 2416308 chars
[OpenRouter DEBUG]   Decoded size: 1812230 bytes
[OpenRouter DEBUG]   Decoded successfully
[OpenRouter DEBUG]   PIL Image size: (1024, 1024)
[OpenRouter DEBUG]   Numpy array shape: (1024, 1024, 3)
[OpenRouter DEBUG]   Numpy array dtype: float32
[OpenRouter DEBUG]   Value range: [0.000, 1.000]
[OpenRouter DEBUG]   Converted to tensor successfully
[OpenRouter STEP] Stacking images: Result shape: torch.Size([1, 1024, 1024, 3])
[OpenRouter STEP] Final result: Shape: torch.Size([1, 1024, 1024, 3]), n=1
[OpenRouter STEP] SUCCESS: Generated 1 image(s)
```

## 🐛 常见问题的日志特征

### 问题 1: API 密钥错误
```
[OpenRouter ERROR] HTTP 401: Unauthorized
```
**解决**: 检查 API 密钥是否正确

### 问题 2: 模型不支持图像生成
```
[OpenRouter STEP] Images in response: Count: 0
[OpenRouter ERROR] Model returned text instead of image
[OpenRouter DEBUG] Text content: I can help you with...
```
**解决**: 使用 `google/gemini-3-pro-image-preview` 模型

### 问题 3: 提示词不当
```
[OpenRouter ERROR] Model returned text instead of image
[OpenRouter DEBUG] Text content: Sure, I'll describe...
```
**解决**: 使用简洁的描述性提示词

### 问题 4: 网络连接问题
```
[OpenRouter ERROR] HTTP Error 503: Service Unavailable
[OpenRouter ERROR] Image error (final): Connection timeout
```
**解决**: 检查网络连接，稍后重试

### 问题 5: 配置缺失
```
[OpenRouter ERROR] Image error: missing base/key/model
```
**解决**: 检查 Base Config 节点是否正确配置并连接

## 🔧 在 ComfyUI 中查看日志

### 方法 1: 控制台输出
1. 启动 ComfyUI 时会显示控制台窗口
2. 所有日志会直接输出到控制台
3. 运行工作流时实时查看日志

### 方法 2: 日志文件
ComfyUI 通常会将日志保存到文件中：
- Windows: `ComfyUI\comfyui.log`
- 查看最新日志

### 方法 3: 实时监控
在 Windows 上使用 PowerShell 监控日志：
```powershell
Get-Content ComfyUI\comfyui.log -Wait -Tail 50
```

## 📊 关键指标

从日志中你可以看到：

### 请求信息
- **Payload size**: 请求大小（字节）
- **URL**: API 端点
- **Headers**: 请求头

### 响应信息
- **Images in response**: 返回的图像数量
- **Base64 length**: Base64 编码的长度
- **Decoded size**: 解码后的字节数
- **PIL Image size**: 图像尺寸 (宽, 高)

### 处理信息
- **Numpy array shape**: 数组形状 (H, W, C)
- **Value range**: 像素值范围
- **Final result**: 最终输出的形状

## 🎯 调试建议

### 1. 确认节点加载
启动 ComfyUI 后查找：
```
[ComfyUI-Gemini v4.0.0] Loaded (LiteLLM + OpenRouter).
```

### 2. 确认配置正确
日志应该显示：
```
[OpenRouter STEP] Config check: All required parameters present
```

### 3. 确认请求发送
```
[OpenRouter STEP] Sending request: URL: https://openrouter.ai/api/v1/chat/completions
```

### 4. 确认响应接收
```
[OpenRouter STEP] Response received: Status: Success
```

### 5. 确认图像处理
```
[OpenRouter STEP] SUCCESS: Generated 1 image(s)
```

## 💡 提示

- 如果日志卡在某个步骤，检查网络连接
- 如果看到 ERROR 日志，根据错误信息解决问题
- 保存完整的日志以便排查问题
- 测试时使用简单的提示词

## 📞 需要帮助？

如果遇到问题：
1. 复制完整的日志输出
2. 查看 TROUBLESHOOTING.md
3. 在 GitHub 提交 Issue 时附上日志
