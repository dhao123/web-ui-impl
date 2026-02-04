# 震坤行AI 集成 - 快速参考指南

## ✅ 集成状态：完成

所有 8 个集成测试已通过 ✅

## 🚀 快速启动（3 步）

### 第一步：确认配置

你的 `.env` 文件已包含：
```
ZKH_ENDPOINT=https://ai-dev-gateway.zkh360.com/llm
ZKH_API_KEY=app-874b47968c73425dbeb1ef57
```

### 第二步：验证集成

```bash
python test_zkh_integration.py
```

预期输出：
```
总计: 8/8 个测试通过
🎉 所有测试通过！震坤行AI集成正常工作。
```

### 第三步：启动应用

**方式 A: Web UI（推荐新手）**
```bash
python webui.py
```
然后在浏览器打开 `http://127.0.0.1:7788`

**方式 B: 演示脚本**
```bash
python run_browser_task_with_zkh.py
```

**方式 C: Python 代码**
```python
from src.utils import llm_provider

llm = llm_provider.get_llm_model(
    provider="zkh",
    model_name="ep_20251217_i18v",
    api_key="your_key"
)
response = llm.invoke("你好")
print(response.content)
```

---

## 📋 可用的模型列表

| 模型ID | 名称 | 特点 |
|--------|------|------|
| `ep_20251217_i18v` | DeepSeek-V3 | 推荐使用，性能最佳 |
| `ep_20250908_1pgk` | DeepSeek-V3.1 | 升级版本 |
| `ep_20251217_hr5x` | DeepSeek-R1 | 推理模型，深度思考 |

---

## 🌐 Web UI 使用步骤

1. 启动 Web UI
   ```bash
   python webui.py
   ```

2. 打开浏览器访问 `http://127.0.0.1:7788`

3. 点击 **⚙️ Agent Settings** 标签

4. 配置如下：
   - **LLM Provider**: 选择 `震坤行AI`
   - **LLM Model Name**: 输入 `ep_20251217_i18v`（或其他模型ID）
   - **Temperature**: 设置为 `0.6`（可选）
   - **API Key**: `app-874b47968c73425dbeb1ef57`（已配置）

5. 点击 **🤖 Run Agent** 标签

6. 输入任务，例如：
   - "访问Google首页"
   - "搜索Python教程"
   - "打开GitHub"

7. 点击 **Run Agent** 按钮开始执行

---

## 🔧 核心集成文件

### 已修改的文件
| 文件 | 修改内容 |
|------|--------|
| `src/utils/config.py` | 添加 ZKH 提供商配置 |
| `src/utils/llm_provider.py` | 实现 ZKH LLM 工厂方法 |
| `.env` | 配置 API 密钥和端点 |
| `test_zkh_integration.py` | 使用正确的模型 ID |

### 新建的文件
| 文件 | 功能 |
|------|------|
| `src/utils/zkh_client.py` | ZKH API 客户端库 |
| `test_zkh_integration.py` | 集成测试（已更新） |
| `run_browser_task_with_zkh.py` | 演示脚本 |

---

## 📊 技术细节

### API 端点
```
https://ai-dev-gateway.zkh360.com/llm/v1/chat/completions
```

### 认证方式
```
Authorization: Bearer {API_KEY}
```

### 请求格式
标准的 OpenAI 兼容格式：
```json
{
  "model": "ep_20251217_i18v",
  "messages": [
    {"role": "user", "content": "你好"}
  ],
  "temperature": 0.6
}
```

### 响应格式
标准的 OpenAI chat.completion 格式：
```json
{
  "choices": [
    {
      "message": {
        "content": "你好！...",
        "role": "assistant"
      },
      "finish_reason": "stop"
    }
  ],
  "usage": {
    "prompt_tokens": 4,
    "completion_tokens": 15,
    "total_tokens": 19
  }
}
```

---

## ✨ 支持的功能

- ✅ 文本对话
- ✅ 流式输出
- ✅ 工具调用（Function Calling）
- ✅ 多模态输入（图像）
- ✅ 文档处理
- ✅ 向量化（Embeddings）
- ✅ 自定义参数（temperature, max_tokens 等）

---

## 🐛 常见问题

### Q: 如何更换模型？
A: 在 Web UI 的 Agent Settings 中，修改 "LLM Model Name" 字段，改为其他模型ID：
- `ep_20251217_i18v` (DeepSeek-V3)
- `ep_20250908_1pgk` (DeepSeek-V3.1)
- `ep_20251217_hr5x` (DeepSeek-R1)

### Q: 如何自定义系统提示词？
A: 在 Web UI 或 Python 代码中，添加 system 角色的消息：
```python
messages = [
    {"role": "system", "content": "你是一个编程助手"},
    {"role": "user", "content": "如何写Python？"}
]
```

### Q: 流式输出如何使用？
A: 使用 `chat_completions_stream` 方法：
```python
from src.utils.zkh_client import ZKHAPIClient

client = ZKHAPIClient(api_key="your_key")
for chunk in client.chat_completions_stream(
    model="ep_20251217_i18v",
    messages=[{"role": "user", "content": "你好"}]
):
    print(chunk, end="", flush=True)
```

### Q: 如何处理错误？
A: 所有 API 调用都已包含错误处理，会抛出异常或返回错误响应。查看日志获取详细信息：
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

---

## 📞 获取帮助

### 快速诊断
运行诊断脚本：
```bash
python test_zkh_integration.py
```

### 查看日志
```bash
export BROWSER_USE_LOGGING_LEVEL=debug
python webui.py
```

### 官方资源
- 震坤行文档: https://ai-dev.zkh360.com/docs
- API 参考: 参见 `ZKH_INTEGRATION_GUIDE.md`
- 集成指南: 参见 `ZKH_QUICKSTART.md`

---

## 🎯 关键配置

```env
# .env 文件中的关键配置
ZKH_API_KEY=app-874b47968c73425dbeb1ef57
ZKH_ENDPOINT=https://ai-dev-gateway.zkh360.com/llm
```

### 重要提示
- ⚠️ 不要将 API 密钥提交到版本控制系统
- ✅ 使用环境变量管理敏感信息
- ✅ 定期更新模型 ID 以使用最新模型

---

## 📈 下一步

1. ✅ 验证集成：`python test_zkh_integration.py`
2. ✅ 启动 Web UI：`python webui.py`
3. ✅ 尝试浏览器自动化任务
4. ✅ 集成到你的应用中
5. ✅ 实现自定义功能

---

**集成完成时间**: 2026-02-04  
**测试状态**: ✅ 8/8 通过  
**支持**: 文档和代码示例已完备
