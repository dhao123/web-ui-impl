# 震坤行AI集成 - 执行清单

## 🚀 快速验证 (5分钟)

按照以下步骤快速验证集成是否正常工作：

### 步骤1: 配置API密钥

```bash
# 设置环境变量（选择一种方法）

# 方法A: 编辑.env文件
vi .env
# 添加以下行：
# ZKH_API_KEY=your_actual_api_key
# ZKH_MODEL_ID=your_actual_endpoint_id

# 方法B: 终端设置
export ZKH_API_KEY="your_actual_api_key"
export ZKH_MODEL_ID="ep-20250429102651-hd5dd"
```

### 步骤2: 运行测试脚本

```bash
python test_zkh_integration.py
```

**预期输出:**
```
✅ 通过: API密钥
✅ 通过: 客户端初始化
✅ 通过: 获取模型列表
✅ 通过: 简单文本对话
✅ 通过: 流式对话
✅ 通过: LLM提供商集成
✅ 通过: 工具调用
✅ 通过: 配置验证

总计: 8/8 个测试通过
```

### 步骤3: 启动Web UI

```bash
python webui.py --ip 127.0.0.1 --port 7788
```

### 步骤4: 在浏览器中测试

1. 打开 http://127.0.0.1:7788
2. 点击 **⚙️ Agent Settings** 标签
3. **LLM Provider**: 下拉选择 **"震坤行AI"**
4. **LLM Model Name**: 输入你的推理接入点ID
5. **Temperature**: 设置为 0.6
6. 点击 **🤖 Run Agent** 标签
7. 在Task框输入: "访问Google首页"
8. 点击 **Run Agent** 按钮

---

## ✅ 集成验证清单

### 核心功能验证

- [ ] **API密钥**
  - [ ] ZKH_API_KEY 已设置
  - [ ] API密钥格式正确 (sk_xxx)
  - [ ] 命令 `echo $ZKH_API_KEY` 有输出

- [ ] **模型配置**
  - [ ] 获取了有效的推理接入点ID
  - [ ] 推理接入点已启用/部署
  - [ ] 模型ID格式正确 (ep-xxx)

- [ ] **网络连接**
  - [ ] 可以ping ai-dev-gateway.zkh360.com
  - [ ] 防火墙未阻止HTTPS流量
  - [ ] 代理（如有）已配置

### 代码集成验证

- [ ] **配置文件**
  - [ ] src/utils/config.py 已修改
    - [ ] PROVIDER_DISPLAY_NAMES 中添加了 "zkh"
    - [ ] model_names 中添加了 "zkh" 模型列表
  
- [ ] **LLM提供商**
  - [ ] src/utils/llm_provider.py 已修改
    - [ ] get_llm_model() 中添加了 zkh provider 处理
    - [ ] 使用 ChatOpenAI 适配
  
- [ ] **环境配置**
  - [ ] .env 文件已更新
    - [ ] ZKH_API_KEY 已设置
    - [ ] ZKH_ENDPOINT 已配置（可选，有默认值）

- [ ] **新增文件**
  - [ ] src/utils/zkh_client.py 已创建
  - [ ] test_zkh_integration.py 已创建
  - [ ] run_browser_task_with_zkh.py 已创建

### 功能验证

- [ ] **基础对话**
  ```bash
  python -c "
  import os
  from src.utils.zkh_client import ZKHAPIClient
  client = ZKHAPIClient(api_key=os.getenv('ZKH_API_KEY'))
  response = client.chat_completions(
      model='ep-20250429102651-hd5dd',
      messages=[{'role': 'user', 'content': '你好'}]
  )
  print('✅ 对话成功')
  "
  ```

- [ ] **流式输出**
  ```bash
  python -c "
  import os
  from src.utils.zkh_client import ZKHAPIClient
  client = ZKHAPIClient(api_key=os.getenv('ZKH_API_KEY'))
  for chunk in client.chat_completions_stream(
      model='ep-20250429102651-hd5dd',
      messages=[{'role': 'user', 'content': '你好'}]
  ):
      print(chunk, end='', flush=True)
  "
  ```

- [ ] **LLM提供商集成**
  ```bash
  python -c "
  import os
  from src.utils import llm_provider
  llm = llm_provider.get_llm_model(
      provider='zkh',
      model_name='ep-20250429102651-hd5dd',
      api_key=os.getenv('ZKH_API_KEY')
  )
  print('✅ LLM集成成功')
  "
  ```

- [ ] **Web UI集成**
  - [ ] WebUI启动正常
  - [ ] Agent Settings 中可选择 "震坤行AI"
  - [ ] 模型ID可输入
  - [ ] Run Agent 可执行任务

### 文档验证

- [ ] **集成指南**
  - [ ] 已读过 ZKH_INTEGRATION_GUIDE.md
  - [ ] 理解了API参数
  - [ ] 了解了高级功能

- [ ] **快速开始**
  - [ ] 已读过 ZKH_QUICKSTART.md
  - [ ] 知道如何配置
  - [ ] 知道常见问题解决方法

- [ ] **实现总结**
  - [ ] 已读过 ZKH_IMPLEMENTATION_SUMMARY.md
  - [ ] 理解了整体架构
  - [ ] 了解了技术细节

---

## 🔧 常见操作步骤

### 操作1: 配置API密钥

**场景**: 首次使用或需要更换密钥

```bash
# 方法1: 编辑.env文件（推荐）
echo "ZKH_API_KEY=your_key_here" >> .env
echo "ZKH_ENDPOINT=https://ai-dev-gateway.zkh360.com/llm" >> .env

# 方法2: 设置环境变量（临时）
export ZKH_API_KEY="your_key_here"

# 方法3: 验证配置
python -c "import os; print('API Key:', os.getenv('ZKH_API_KEY')[:10] + '...')"
```

### 操作2: 运行Web UI

```bash
# 基础启动
python webui.py

# 指定IP和端口
python webui.py --ip 0.0.0.0 --port 8080

# 选择主题
python webui.py --theme Ocean
```

### 操作3: 运行浏览器自动化任务

```bash
# 运行Demo脚本
python run_browser_task_with_zkh.py

# 或编写自己的脚本
python my_browser_task.py
```

### 操作4: 调试和日志

```bash
# 启用详细日志
export BROWSER_USE_LOGGING_LEVEL=debug
python webui.py

# 查看特定模块日志
python -c "
import logging
logging.basicConfig(level=logging.DEBUG)
from src.utils.zkh_client import ZKHAPIClient
# 你的代码...
"
```

### 操作5: 文件处理（文档上传）

```python
import os
from src.utils.zkh_client import ZKHAPIClient

client = ZKHAPIClient(api_key=os.getenv("ZKH_API_KEY"))

# 上传文件
result = client.upload_file("document.pdf")
file_id = result['id']

# 基于文件对话
response = client.chat_completions(
    model="ep-xxx",
    messages=[
        {"role": "system", "content": f"fileid://{file_id}"},
        {"role": "user", "content": "这是什么文档？"}
    ]
)

# 删除文件
client.delete_file(file_id)
```

---

## 🐛 故障排除指南

### 问题1: API密钥验证失败

```
错误: 💥 震坤行API Key未找到！🔑
```

**检查步骤:**

```bash
# 1. 检查环境变量是否设置
echo "API Key: $ZKH_API_KEY"

# 2. 检查.env文件
grep "ZKH_API_KEY" .env

# 3. 检查Python是否读取到
python -c "import os; print(os.getenv('ZKH_API_KEY'))"

# 4. 重启终端或重新加载环境
source ~/.bashrc
# 或
exec $SHELL
```

### 问题2: 连接超时

```
错误: Connection timeout to https://ai-dev-gateway.zkh360.com/llm
```

**检查步骤:**

```bash
# 1. 测试网络连接
ping ai-dev-gateway.zkh360.com

# 2. 检查HTTPS连接
curl -I https://ai-dev-gateway.zkh360.com/llm

# 3. 检查端点URL
echo $ZKH_ENDPOINT

# 4. 如使用代理
export HTTP_PROXY=http://proxy:8080
export HTTPS_PROXY=https://proxy:8080
python test_zkh_integration.py
```

### 问题3: 模型ID不存在

```
错误: Model not found: ep-xxx
```

**解决步骤:**

```bash
# 1. 获取可用模型列表
python -c "
import os
from src.utils.zkh_client import ZKHAPIClient
client = ZKHAPIClient(api_key=os.getenv('ZKH_API_KEY'))
models = client.list_models()
for m in models['data'][:5]:
    print(m['id'])
"

# 2. 更新.env中的模型ID
# ZKH_MODEL_ID=ep-correct-id

# 3. 验证推理接入点是否已启用
# 登录平台 → 推理接入点 → 检查状态
```

### 问题4: 流式输出中断

```
错误: 流式响应突然停止
```

**解决步骤:**

```python
# 添加重试机制
import asyncio
from src.utils.zkh_client import ZKHAPIClient

client = ZKHAPIClient(api_key=os.getenv("ZKH_API_KEY"))

max_retries = 3
for attempt in range(max_retries):
    try:
        for chunk in client.chat_completions_stream(...):
            print(chunk, end="", flush=True)
        break  # 成功则退出
    except Exception as e:
        print(f"尝试 {attempt+1} 失败: {e}")
        if attempt < max_retries - 1:
            await asyncio.sleep(2 ** attempt)  # 指数退避
        else:
            raise
```

---

## 📊 性能优化建议

### 建议1: 调整Temperature参数

```python
# 精确任务（如数学计算）
temperature = 0.0  # 最确定性

# 一般任务（如对话）
temperature = 0.6  # 平衡

# 创意任务（如写作）
temperature = 0.9  # 最多样性
```

### 建议2: 使用流式API

```python
# ❌ 低效: 等待整个响应
response = client.chat_completions(...)
print(response['choices'][0]['message']['content'])

# ✅ 高效: 逐块处理
for chunk in client.chat_completions_stream(...):
    print(chunk, end="", flush=True)
```

### 建议3: 缓存结果

```python
import json
import hashlib

def cached_chat(messages, cache_file=".zkh_cache"):
    # 生成缓存键
    key = hashlib.md5(
        json.dumps(messages).encode()
    ).hexdigest()
    
    # 读取缓存
    try:
        with open(cache_file, 'r') as f:
            cache = json.load(f)
            if key in cache:
                return cache[key]
    except:
        pass
    
    # 调用API
    response = client.chat_completions(
        messages=messages
    )
    
    # 保存缓存
    try:
        with open(cache_file, 'r') as f:
            cache = json.load(f)
    except:
        cache = {}
    
    cache[key] = response
    with open(cache_file, 'w') as f:
        json.dump(cache, f)
    
    return response
```

---

## 📝 每日检查清单

每次使用前，建议运行以下检查：

```bash
#!/bin/bash

echo "=== 震坤行AI集成检查清单 ==="

# 1. 检查API密钥
if [ -z "$ZKH_API_KEY" ]; then
    echo "❌ ZKH_API_KEY 未设置"
    exit 1
else
    echo "✅ API密钥已设置"
fi

# 2. 检查网络连接
if ping -c 1 ai-dev-gateway.zkh360.com > /dev/null 2>&1; then
    echo "✅ 网络连接正常"
else
    echo "❌ 网络连接失败"
    exit 1
fi

# 3. 运行快速测试
python -c "
import os
from src.utils.zkh_client import ZKHAPIClient
try:
    client = ZKHAPIClient(api_key=os.getenv('ZKH_API_KEY'))
    client.list_models()
    print('✅ API连接正常')
except Exception as e:
    print(f'❌ API连接失败: {e}')
    exit(1)
"

echo ""
echo "✅ 所有检查通过，可以开始使用！"
```

---

## 🎓 学习资源

### 官方文档
- [震坤行AI文档](https://ai-dev.zkh360.com/docs)
- [OpenAI API参考](https://platform.openai.com/docs/api-reference)

### 项目文档
- [集成指南](./ZKH_INTEGRATION_GUIDE.md)
- [快速开始](./ZKH_QUICKSTART.md)
- [实现总结](./ZKH_IMPLEMENTATION_SUMMARY.md)
- [项目架构](./PROJECT_ARCHITECTURE.md)

### 代码示例
- [API客户端](./src/utils/zkh_client.py)
- [测试脚本](./test_zkh_integration.py)
- [Demo脚本](./run_browser_task_with_zkh.py)

---

## 📞 获取帮助

### 问题排查步骤

1. **查看错误日志**
   ```bash
   python -c "
   import logging
   logging.basicConfig(level=logging.DEBUG)
   # 运行你的代码
   "
   ```

2. **查看相关文档**
   - 错误消息中的关键字搜索文档
   - 查看 ZKH_QUICKSTART.md 的常见问题部分

3. **运行测试脚本**
   ```bash
   python test_zkh_integration.py
   ```

4. **联系技术支持**
   - 震坤行: support@zkh360.com
   - 项目: 在GitHub上提交Issue

---

## ✨ 最后的话

恭喜！你已经成功集成了震坤行AI大模型。现在你可以：

1. 🌐 使用Web UI与震坤行AI交互
2. 🤖 构建浏览器自动化任务
3. 📊 调用高级功能（文件处理、工具调用等）
4. 🔧 自定义和扩展功能

如有问题，请参考相关文档或联系技术支持。

**祝你使用愉快！** 🎉

---

**更新时间**: 2025-02-04  
**版本**: 1.0
