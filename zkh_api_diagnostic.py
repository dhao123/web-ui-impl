#!/usr/bin/env python3
"""
震坤行API诊断脚本
用于排查API连接和认证问题
"""

import os
import json
import requests
from dotenv import load_dotenv
from urllib.parse import urljoin

load_dotenv()

api_key = os.getenv('ZKH_API_KEY')
endpoint = os.getenv('ZKH_ENDPOINT', 'https://ai-dev-gateway.zkh360.com/llm')

print("=" * 70)
print("震坤行 API 诊断工具")
print("=" * 70)

print(f"\n配置信息:")
print(f"  API Key: {api_key[:20]}..." if api_key else "❌ 未设置")
print(f"  端点: {endpoint}")

if not api_key:
    print("\n❌ API密钥未设置，请先配置ZKH_API_KEY环境变量")
    exit(1)

# 测试各种可能的API格式
test_urls = [
    # 标准OpenAI格式
    f"{endpoint.rstrip('/')}/v1/models",
    # 不带/llm前缀
    "https://ai-dev-gateway.zkh360.com/v1/models",
    # 其他可能的格式
    f"{endpoint.rstrip('/')}/models",
    "https://ai-dev-gateway.zkh360.com/llm/models",
]

headers_variants = [
    # 标准Bearer token
    {
        'Authorization': f'Bearer {api_key}',
        'Content-Type': 'application/json'
    },
    # 可能的其他格式
    {
        'X-API-Key': api_key,
        'Content-Type': 'application/json'
    },
    # 可能需要特殊前缀
    {
        'Authorization': f'Bearer sk-{api_key}' if not api_key.startswith('sk-') else f'Bearer {api_key}',
        'Content-Type': 'application/json'
    },
]

print("\n" + "=" * 70)
print("测试1: 模型列表查询")
print("=" * 70)

for i, url in enumerate(test_urls, 1):
    print(f"\n测试 {i}: {url}")
    try:
        response = requests.get(
            url,
            headers=headers_variants[0],
            timeout=5
        )
        print(f"  状态码: {response.status_code}")
        
        if response.status_code == 200:
            try:
                resp_json = response.json()
                if 'code' in resp_json and resp_json['code'] == 500:
                    print(f"  ❌ 服务异常: {resp_json.get('message', 'Unknown')}")
                elif 'data' in resp_json or isinstance(resp_json.get('data'), list):
                    print(f"  ✅ 成功! 获取 {len(resp_json.get('data', []))} 个模型")
                else:
                    print(f"  响应: {str(resp_json)[:100]}...")
            except:
                print(f"  响应: {response.text[:100]}...")
        elif response.status_code == 404:
            print(f"  ❌ 404 Not Found - 端点不存在")
        elif response.status_code == 401:
            print(f"  ❌ 401 Unauthorized - API密钥问题")
        else:
            print(f"  响应: {response.text[:100]}...")
            
    except requests.exceptions.Timeout:
        print(f"  ❌ 超时 - 网络问题或服务不可用")
    except Exception as e:
        print(f"  ❌ 错误: {str(e)[:80]}")

# 测试对话接口
print("\n" + "=" * 70)
print("测试2: 对话接口")
print("=" * 70)

chat_url = f"{endpoint.rstrip('/')}/v1/chat/completions"
print(f"URL: {chat_url}")

payload = {
    "model": "ep-20250429102651-hd5dd",
    "messages": [
        {"role": "user", "content": "你好"}
    ],
    "temperature": 0.6
}

try:
    response = requests.post(
        chat_url,
        json=payload,
        headers=headers_variants[0],
        timeout=10
    )
    print(f"状态码: {response.status_code}")
    
    resp_json = response.json()
    if 'code' in resp_json:
        print(f"API Code: {resp_json.get('code')}")
        print(f"Message: {resp_json.get('message')}")
        print(f"Success: {resp_json.get('success')}")
    elif 'choices' in resp_json:
        print("✅ 成功! 获得响应")
        print(f"内容: {resp_json['choices'][0]['message']['content'][:100]}...")
    else:
        print(f"响应: {json.dumps(resp_json, indent=2, ensure_ascii=False)[:200]}...")
        
except Exception as e:
    print(f"❌ 错误: {e}")

# 诊断总结
print("\n" + "=" * 70)
print("诊断总结和建议")
print("=" * 70)

print("""
如果模型列表查询返回 404，可能的原因：

1. ⚠️ API端点格式错误
   - 当前使用: https://ai-dev-gateway.zkh360.com/llm/v1/models
   - 请确认震坤行文档中的正确端点格式

2. ⚠️ API密钥无效或过期
   - 当前密钥: app-874b47968c73425...
   - 请在AI开发平台重新生成API密钥

3. ⚠️ 推理接入点未激活
   - 当前模型ID: ep-20250429102651-hd5dd
   - 请在平台确认推理接入点已启用/部署

4. ⚠️ 认证方式不正确
   - 当前使用: Bearer token in Authorization header
   - 可能需要其他认证方式或请求头

建议操作:
1. 访问 https://ai-dev.zkh360.com 登录你的账户
2. 检查API密钥是否有效
3. 确认推理接入点ID正确且已激活
4. 查看平台API文档获取最新的端点信息
""")

print("\n如需更多帮助，请将上面的诊断信息提交给技术支持。")
