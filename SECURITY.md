# 安全政策 (Security Policy)

## 支持的版本 (Supported Versions)

| 版本 (Version) | 支持状态 (Supported) |
| ------- | ------------------ |
| 2.0.x   | ✅ |
| < 2.0   | ❌ |

## 报告安全漏洞 (Reporting a Vulnerability)

如果您发现了安全漏洞，请**不要**在公开的 Issue 中报告。

### 报告方式 (How to Report)

1. **通过 GitHub Security Advisory**
   - 访问: https://github.com/ZUENS2020/ComfyUI-LLM-Nodes/security/advisories
   - 点击 "Report a vulnerability"
   - 填写详细信息

2. **通过邮件 (Via Email)**
   - 发送至仓库维护者的邮箱
   - 邮件主题: [SECURITY] 简要描述
   - 包含详细的漏洞信息和复现步骤

### 报告内容 (What to Include)

- 漏洞类型和严重程度
- 受影响的版本
- 复现步骤
- 潜在影响
- 建议的修复方案（如果有）

### 响应时间 (Response Time)

- **确认:** 48小时内确认收到报告
- **评估:** 7天内完成初步评估
- **修复:** 根据严重程度，30天内提供修复

---

## 安全最佳实践 (Security Best Practices)

### 对于用户 (For Users)

#### 1. API 密钥管理 (API Key Management)

**✅ 推荐做法 (Recommended):**
```yaml
# 使用环境变量
export OPENAI_API_KEY="sk-..."
export GEMINI_API_KEY="sk-..."
```

**❌ 避免做法 (Avoid):**
- 不要在工作流文件中硬编码 API 密钥
- 不要在截图中暴露完整的 API 密钥
- 不要将包含密钥的工作流文件提交到版本控制系统

#### 2. 网络安全 (Network Security)

- ✅ 始终使用 HTTPS 端点
- ✅ 验证 API 端点的合法性
- ❌ 不要使用不受信任的代理服务器

#### 3. 数据隐私 (Data Privacy)

- ✅ 了解您的数据会被发送到哪个 API 端点
- ✅ 不要在提示词中包含敏感个人信息
- ✅ 定期审查和清理工作流历史

### 对于开发者 (For Developers)

#### 1. Git 配置 (Git Configuration)

**保护您的邮箱地址:**
```bash
# 使用 GitHub 的 noreply 邮箱
git config user.email "your-username@users.noreply.github.com"

# 在 GitHub 设置中启用邮箱隐私保护
# Settings → Emails → "Keep my email addresses private"
```

#### 2. 代码审查 (Code Review)

在提交代码前检查：
- [ ] 没有硬编码的 API 密钥
- [ ] 没有个人信息
- [ ] 没有密码或令牌
- [ ] 敏感数据通过参数传递
- [ ] 日志输出已脱敏

**使用脱敏函数:**
```python
def _safe_key(key: str) -> str:
    """将 API 密钥脱敏用于日志输出"""
    k = key or ""
    if len(k) <= 6:
        return "***"
    return f"{k[:3]}***{k[-3:]}"
```

#### 3. 依赖管理 (Dependency Management)

- ✅ 定期更新依赖
- ✅ 审查新依赖的安全性
- ✅ 使用最小权限原则

#### 4. 测试环境 (Testing Environment)

**创建测试配置文件:**
```python
# test_config.py (不要提交到 Git!)
TEST_API_KEY = "sk-test-..."
TEST_API_BASE = "https://api.test.com/v1"
```

**添加到 .gitignore:**
```gitignore
# Test configurations
test_config.py
*_secret.py
*.secret.*
```

---

## 已知安全考虑事项 (Known Security Considerations)

### 1. API 密钥存储 (API Key Storage)

**问题:** API 密钥通过 ComfyUI 的节点输入框输入，可能存储在工作流文件中。

**风险:** 工作流文件可能被意外分享或提交到版本控制。

**缓解措施:**
- 用户应该意识到工作流文件可能包含敏感数据
- 建议使用环境变量管理 API 密钥
- 不要分享包含真实 API 密钥的工作流文件

### 2. 网络请求 (Network Requests)

**问题:** 插件使用 `urllib` 向用户指定的端点发送 HTTP 请求。

**风险:** 
- 恶意端点可能记录请求数据
- 中间人攻击（如果不使用 HTTPS）

**缓解措施:**
- 代码强制使用 HTTPS（建议）
- 用户应该只使用可信的 API 端点
- 实现证书验证

### 3. 数据隐私 (Data Privacy)

**问题:** 用户的提示词和生成的内容会发送到第三方 API。

**风险:** 敏感信息可能被 API 提供商记录。

**缓解措施:**
- 文档中明确说明数据流向
- 用户应该了解其使用的 API 提供商的隐私政策
- 避免在提示词中包含个人身份信息

---

## 安全更新 (Security Updates)

### 如何获取安全更新 (How to Get Security Updates)

1. **Watch this repository**
   - 点击仓库页面的 "Watch" 按钮
   - 选择 "Custom" → "Security alerts"

2. **检查 Release Notes**
   - 安全修复会在版本说明中标注 `[SECURITY]`

3. **订阅 GitHub Security Advisories**
   - 自动接收关键安全通知

### 更新流程 (Update Process)

```bash
# 1. 备份现有版本
cp -r ComfyUI-LLM-Nodes ComfyUI-LLM-Nodes.backup

# 2. 拉取最新版本
cd ComfyUI/custom_nodes/ComfyUI-LLM-Nodes
git pull origin main

# 3. 重启 ComfyUI
```

---

## 审计历史 (Audit History)

| 日期 (Date) | 审计类型 (Type) | 发现 (Findings) | 状态 (Status) |
|-------------|----------------|----------------|---------------|
| 2026-01-01  | 个人信息泄露检查 | Git 历史中的邮箱 | 已记录 (Documented) |

---

## 联系方式 (Contact)

- **安全问题:** 通过 GitHub Security Advisory
- **一般问题:** 通过 GitHub Issues
- **紧急情况:** 联系仓库维护者

---

## 致谢 (Acknowledgments)

感谢所有报告安全问题和帮助改进项目安全性的贡献者。

---

**最后更新:** 2026-01-01  
**版本:** 1.0
