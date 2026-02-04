# 震坤行AI大模型集成 - 完整使用指南

## 📋 目录

1. [快速开始](#快速开始)
2. [完整安装步骤](#完整安装步骤)
3. [配置方法](#配置方法)
4. [使用示例](#使用示例)
5. [测试验证](#测试验证)
6. [常见问题](#常见问题)

---

## 快速开始

### 前置条件

- Python 3.10 或更高版本
- 已申请震坤行API密钥
- 已创建推理接入点

### 5分钟快速配置

```bash
# 1. 配置环境变量
export ZKH_API_KEY="your_api_key_here"
export ZKH_MODEL_ID="ep-20250429102651-hd5dd"  # 替换为实际的推理接入点ID

# 2. 运行测试脚本验证集成
python test_zkh_integration.py

# 3. 启动Web UI
python webui.py --ip 127.0.0.1 --port 7788

# 4. 在浏览器中访问
# http://127.0.0.1:7788
```

在Web UI中：
- **Agent Settings** → LLM Provider 选择 "震坤行AI"
- **LLM Model Name** → 输入推理接入点ID
- **Run Agent** → 输入任务并执行

---

## 完整安装步骤

### 步骤1: 获取API密钥

1. 访问 [震坤行AI开发者平台](https://ai-dev.zkh360.com)
2. 注册并登录
3. 创建项目和API密钥
4. 创建推理接入点，记下其ID（格式如 `ep-xxx`）

### 步骤2: 配置环境

编辑项目根目录的 `.env` 文件：

```env
# 震坤行AI配置
ZKH_API_KEY=sk_xxx_your_api_key_here
ZKH_ENDPOINT=https://ai-dev-gateway.zkh360.com/llm
ZKH_MODEL_ID=ep-20250429102651-hd5dd

# 其他现有配置...
```

### 步骤3: 验证集成

```bash
# 方法1: 运行测试脚本
python test_zkh_integration.py

# 输出应该显示所有测试通过 ✅
```

### 步骤4: 启动应用

```bash
# 方法1: 运行Web UI
python webui.py --ip 127.0.0.1 --port 7788

# 方法2: 运行Demo脚本（浏览器自动化任务）
python run_browser_task_with_zkh.py
```

---

## 配置方法

### 方法1: .env 文件（推荐）

编辑 `.env` 文件添加：

```env
# 必需配置
ZKH_API_KEY=your_api_key_here

# 可选配置（有默认值）
ZKH_ENDPOINT=https://ai-dev-gateway.zkh360.com/llm
```

### 方法2: 环境变量

```bash
# Linux/macOS
export ZKH_API_KEY="your_api_key_here"
export ZKH_ENDPOINT="https://ai-dev-gateway.zkh360.com/llm"

# Windows (PowerShell)
$env:ZKH_API_KEY="your_api_key_here"
$env:ZKH_ENDPOINT="https://ai-dev-gateway.zkh360.com/llm"
```

### 方法3: Web UI 直接输入

在Web UI的 **Agent Settings** 中：
- 如果未设置环境变量，可在 **Base URL** 和 **API Key** 字段直接输入
- 应用会优先使用界面输入，其次使用环境变量

---

## 使用示例

### 示例1: Web UI（最简单）

1. 启动应用：`python webui.py`
2. 打开 http://127.0.0.1:7788
3. **Agent Settings** 标签页：
   - LLM Provider: 选择 "震坤行AI"
   - LLM Model Name: `ep-20250429102651-hd5dd` (换成你的ID)
   - Temperature: 0.6
4. **Browser Settings** 标签页：配置浏览器参数
5. **Run Agent** 标签页：
   - Task 输入框输入任务，如："搜索Python教程"
   - 点击 "Run Agent" 按钮执行

### 示例2: Python脚本（完全控制）

```python
import os
import asyncio
from src.utils import llm_provider
from src.browser.custom_browser import CustomBrowser
from src.controller.custom_controller import CustomController
from src.agent.browser_use.browser_use_agent import BrowserUseAgent
from browser_use.browser.browser import BrowserConfig
from browser_use.browser.context import BrowserContextConfig


async def main():
    # 初始化LLM
    llm = llm_provider.get_llm_model(
        provider="zkh",
        model_name="ep-20250429102651-hd5dd",  # 换成你的模型ID
        temperature=0.6,
        api_key=os.getenv("ZKH_API_KEY")
    )
    
    # 初始化浏览器
    browser = CustomBrowser(config=BrowserConfig(headless=False))
    browser_context = await browser.new_context()
    
    # 创建控制器
    controller = CustomController()
    
    # 创建Agent
    agent = BrowserUseAgent(
        task="搜索Python教程并打开第一个结果",
        llm=llm,
        browser=browser,
        browser_context=browser_context,
        controller=controller,
        use_vision=True
    )
    
    # 运行任务
    result = await agent.run(max_steps=50)
    
    # 清理
    await browser.close()


if __name__ == "__main__":
    asyncio.run(main())
```

### 示例3: 直接使用API客户端

```python
import os
from src.utils.zkh_client import ZKHAPIClient

# 初始化客户端
client = ZKHAPIClient(
    api_key=os.getenv("ZKH_API_KEY"),
    base_url="https://ai-dev-gateway.zkh360.com/llm"
)

# 简单对话
response = client.chat_completions(
    model="ep-20250429102651-hd5dd",
    messages=[
        {"role": "system", "content": "你是一个有帮助的AI助手"},
        {"role": "user", "content": "什么是Python？"}
    ],
    temperature=0.6
)

print(response['choices'][0]['message']['content'])
```

### 示例4: 流式对话

```python
from src.utils.zkh_client import ZKHAPIClient

client = ZKHAPIClient(api_key=os.getenv("ZKH_API_KEY"))

# 流式获取回复
for chunk in client.chat_completions_stream(
    model="ep-20250429102651-hd5dd",
    messages=[
        {"role": "user", "content": "写一个Python Hello World程序"}
    ]
):
    print(chunk, end="", flush=True)
```

### 示例5: 文件处理（Qwen-Long）

```python
from src.utils.zkh_client import ZKHAPIClient

client = ZKHAPIClient(api_key=os.getenv("ZKH_API_KEY"))

# 上传文件
result = client.upload_file("my_document.pdf")
file_id = result['id']
print(f"文件已上传，ID: {file_id}")

# 基于文件提问
response = client.chat_completions(
    model="ep-20250429102651-hd5dd",
    messages=[
        {"role": "system", "content": f"fileid://{file_id}"},
        {"role": "user", "content": "这份文档的主要内容是什么？"}
    ]
)

print(response['choices'][0]['message']['content'])

# 删除文件
client.delete_file(file_id)
```

---

## 测试验证

### 快速测试

```bash
# 运行集成测试套件
python test_zkh_integration.py
```

测试包括：
- ✅ API密钥验证
- ✅ 客户端初始化
- ✅ 模型列表获取
- ✅ 简单文本对话
- ✅ 流式对话
- ✅ LLM提供商集成
- ✅ 工具调用（Function Calling）
- ✅ 配置验证

### 逐步测试

```bash
# 测试1: 验证API连接
python -c "
import os
from src.utils.zkh_client import ZKHAPIClient
client = ZKHAPIClient(api_key=os.getenv('ZKH_API_KEY'))
models = client.list_models()
print(f'✅ 连接成功，获得 {len(models.get(\"data\", []))} 个模型')
"

# 测试2: 简单对话
python -c "
import os
from src.utils.zkh_client import ZKHAPIClient
client = ZKHAPIClient(api_key=os.getenv('ZKH_API_KEY'))
response = client.chat_completions(
    model='ep-20250429102651-hd5dd',
    messages=[{'role': 'user', 'content': '你好'}]
)
print(response['choices'][0]['message']['content'])
"
```

---

## 常见问题

### Q1: 如何获取推理接入点ID？

**A:** 在震坤行AI开发者平台：
1. 登录后进入"推理接入点"管理页面
2. 创建新的推理接入点
3. 选择模型版本
4. 部署后，复制生成的ID（格式：`ep-xxx`）

### Q2: API密钥验证失败

**A:** 检查以下项目：
```bash
# 验证环境变量是否设置
echo $ZKH_API_KEY

# 验证.env文件
cat .env | grep ZKH_API_KEY

# 重新设置并验证
export ZKH_API_KEY="your_actual_key"
python test_zkh_integration.py
```

### Q3: 连接超时

**A:** 
```bash
# 1. 检查网络
ping ai-dev-gateway.zkh360.com

# 2. 验证端点URL
echo $ZKH_ENDPOINT

# 3. 更改端口或检查防火墙
# 如果使用代理，配置环境变量：
export HTTP_PROXY=http://proxy:8080
export HTTPS_PROXY=https://proxy:8080
```

### Q4: 模型ID无效

**A:** 
```bash
# 获取可用模型列表
python -c "
import os
from src.utils.zkh_client import ZKHAPIClient
client = ZKHAPIClient(api_key=os.getenv('ZKH_API_KEY'))
models = client.list_models()
for model in models.get('data', [])[:5]:
    print(model.get('id'))
"

# 在.env中更新正确的ID
ZKH_MODEL_ID=ep-your-correct-id
```

### Q5: 如何在Deep Research Agent中使用震坤行？

**A:** 在Web UI中：
1. **Agent Settings** 标签页：
   - **LLM Provider**: 震坤行AI
   - **LLM Model Name**: 你的推理接入点ID
   
   - **Planner LLM Provider**: 震坤行AI (用于规划)
   - **Planner LLM Model Name**: 同一推理接入点ID

2. **Agent Marketplace** → **Deep Research** 标签页
3. 输入研究查询，点击运行

---

## 文件说明

### 新增/修改的文件

| 文件 | 说明 |
|------|------|
| `src/utils/zkh_client.py` | 震坤行API客户端（新增） |
| `src/utils/config.py` | 添加ZKH提供商配置（已修改） |
| `src/utils/llm_provider.py` | 添加ZKH LLM实现（已修改） |
| `.env` | 添加ZKH配置项（已修改） |
| `ZKH_INTEGRATION_GUIDE.md` | 详细集成指南（新增） |
| `test_zkh_integration.py` | 集成测试脚本（新增） |
| `run_browser_task_with_zkh.py` | Demo脚本（新增） |
| `ZKH_QUICKSTART.md` | 本文件（新增） |

### 关键类和函数

```
src/utils/zkh_client.py
├── ZKHAPIClient           # 主客户端类
│   ├── list_models()      # 获取模型列表
│   ├── chat_completions() # 对话API
│   ├── chat_completions_stream() # 流式对话
│   ├── upload_file()      # 文件上传
│   ├── list_files()       # 查询文件
│   ├── delete_file()      # 删除文件
│   └── embeddings()       # 获取向量
├── create_image_message_content() # 创建图像消息
└── create_file_message_content()  # 创建文件消息

src/utils/llm_provider.py
└── get_llm_model() # 添加了"zkh"提供商支持

src/utils/config.py
├── PROVIDER_DISPLAY_NAMES # 添加"zkh"显示名
└── model_names # 添加"zkh"模型列表
```

---

## 下一步

### 推荐行动

1. **验证安装**
   ```bash
   python test_zkh_integration.py
   ```

2. **启动Web UI**
   ```bash
   python webui.py
   ```

3. **运行Demo任务**
   ```bash
   python run_browser_task_with_zkh.py
   ```

4. **查看文档**
   - 详细指南: `ZKH_INTEGRATION_GUIDE.md`
   - 项目架构: `PROJECT_ARCHITECTURE.md`

5. **优化配置**
   - 根据任务调整 temperature 值
   - 根据需要启用 Vision 模式
   - 配置 max_steps 和 max_failures

---

## 支持和反馈

- **技术文档**: https://ai-dev.zkh360.com/docs
- **API问题**: support@zkh360.com
- **项目Issue**: 在GitHub上提交Issue

---

## 许可证

该集成遵循项目主许可证。

---

**最后更新**: 2025-02-04  
**版本**: 1.0
