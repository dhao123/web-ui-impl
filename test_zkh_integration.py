#!/usr/bin/env python3
"""
震坤行AI集成测试脚本

用途：快速验证震坤行API集成是否正常工作
"""

import os
import sys
import asyncio
import json
import logging
from pathlib import Path

# 加载环境变量
try:
    from dotenv import load_dotenv
    env_path = Path(__file__).parent / '.env'
    load_dotenv(env_path)
except ImportError:
    pass

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent))

from src.utils.zkh_client import ZKHAPIClient, create_image_message_content
from src.utils import llm_provider


def test_api_key():
    """测试1: 验证API密钥"""
    print("\n" + "="*60)
    print("测试1: 验证API密钥")
    print("="*60)
    
    api_key = os.getenv("ZKH_API_KEY")
    if not api_key:
        print("❌ 失败: ZKH_API_KEY 环境变量未设置")
        print("   请执行: export ZKH_API_KEY='your_api_key_here'")
        return False
    
    print(f"✅ 成功: API密钥已设置 (长度: {len(api_key)} 字符)")
    return True


def test_client_initialization():
    """测试2: 初始化客户端"""
    print("\n" + "="*60)
    print("测试2: 初始化ZKH客户端")
    print("="*60)
    
    try:
        api_key = os.getenv("ZKH_API_KEY")
        base_url = os.getenv("ZKH_ENDPOINT", "https://ai-dev-gateway.zkh360.com/llm")
        client = ZKHAPIClient(api_key=api_key, base_url=base_url)
        print("✅ 成功: 客户端初始化完成")
        print(f"   端点: {base_url}")
        return client
    except Exception as e:
        print(f"❌ 失败: {e}")
        return None


def test_list_models(client):
    """测试3: 获取模型列表"""
    print("\n" + "="*60)
    print("测试3: 获取可用模型列表")
    print("="*60)
    
    try:
        models = client.list_models()
        if isinstance(models, dict) and 'data' in models:
            model_list = models['data']
        elif isinstance(models, list):
            model_list = models
        else:
            model_list = models
        
        print(f"✅ 成功: 获取到 {len(model_list)} 个模型")
        if len(model_list) > 0:
            print("\n前3个模型:")
            for i, model in enumerate(model_list[:3]):
                if isinstance(model, dict):
                    print(f"  {i+1}. ID: {model.get('id', '未知')}, "
                          f"名称: {model.get('name', '未知')}")
                else:
                    print(f"  {i+1}. {model}")
        return True
    except Exception as e:
        print(f"❌ 失败: {e}")
        logger.exception("获取模型列表错误")
        return False


def test_simple_chat(client):
    """测试4: 简单文本对话"""
    print("\n" + "="*60)
    print("测试4: 简单文本对话")
    print("="*60)
    
    try:
        model_id = os.getenv("ZKH_MODEL_ID", "ep_20251217_i18v")
        print(f"使用模型: {model_id}")
        
        response = client.chat_completions(
            model=model_id,
            messages=[
                {"role": "system", "content": "你是一个有帮助的AI助手。"},
                {"role": "user", "content": "请用一句话介绍自己"}
            ],
            temperature=0.6
        )
        
        content = response['choices'][0]['message']['content']
        print(f"✅ 成功: 获得回复")
        print(f"\n回复内容:\n{content}")
        return True
    except Exception as e:
        print(f"❌ 失败: {e}")
        logger.exception("对话请求错误")
        return False


def test_stream_chat(client):
    """测试5: 流式对话"""
    print("\n" + "="*60)
    print("测试5: 流式对话")
    print("="*60)
    
    try:
        model_id = os.getenv("ZKH_MODEL_ID", "ep_20251217_i18v")
        print(f"使用模型: {model_id}")
        print("\n流式回复: ", end="", flush=True)
        
        chunk_count = 0
        for chunk in client.chat_completions_stream(
            model=model_id,
            messages=[
                {"role": "user", "content": "请说一个有趣的冷笑话"}
            ]
        ):
            print(chunk, end="", flush=True)
            chunk_count += 1
        
        print(f"\n\n✅ 成功: 收到 {chunk_count} 个流式响应块")
        return True
    except Exception as e:
        print(f"❌ 失败: {e}")
        logger.exception("流式对话错误")
        return False


def test_llm_provider_integration():
    """测试6: LLM提供商集成"""
    print("\n" + "="*60)
    print("测试6: LLM提供商集成")
    print("="*60)
    
    try:
        api_key = os.getenv("ZKH_API_KEY")
        model_id = os.getenv("ZKH_MODEL_ID", "ep_20251217_i18v")
        
        llm = llm_provider.get_llm_model(
            provider="zkh",
            model_name=model_id,
            temperature=0.6,
            api_key=api_key
        )
        
        print("✅ 成功: LLM实例创建成功")
        print(f"   类型: {type(llm).__name__}")
        # ChatOpenAI 使用 model_name 而不是 model
        if hasattr(llm, 'model_name'):
            print(f"   模型: {llm.model_name}")
        else:
            print(f"   模型: {model_id}")
        
        # 测试调用
        response = llm.invoke([
            {"type": "human", "content": "你是谁？"}
        ])
        
        print(f"\n✅ 成功: LLM调用成功")
        print(f"   回复: {response.content[:100]}...")
        return True
    except Exception as e:
        print(f"❌ 失败: {e}")
        logger.exception("LLM提供商集成错误")
        return False


def test_tool_calling(client):
    """测试7: 工具调用 (函数调用)"""
    print("\n" + "="*60)
    print("测试7: 工具调用 (Function Calling)")
    print("="*60)
    
    try:
        model_id = os.getenv("ZKH_MODEL_ID", "ep_20251217_i18v")
        
        tools = [
            {
                "type": "function",
                "function": {
                    "name": "get_current_weather",
                    "description": "获取指定城市的当前天气",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "location": {
                                "type": "string",
                                "description": "城市名称，例如：北京、上海、杭州"
                            },
                            "unit": {
                                "type": "string",
                                "enum": ["celsius", "fahrenheit"],
                                "description": "温度单位"
                            }
                        },
                        "required": ["location"]
                    }
                }
            }
        ]
        
        response = client.chat_completions(
            model=model_id,
            messages=[
                {"role": "user", "content": "杭州现在天气怎么样？"}
            ],
            tools=tools
        )
        
        print("✅ 成功: 工具调用请求完成")
        print("\nAPI响应:")
        
        # 检查是否包含工具调用
        message = response['choices'][0]['message']
        if 'tool_calls' in message:
            print(f"  检测到工具调用: {len(message['tool_calls'])} 个")
            for tool_call in message['tool_calls']:
                print(f"    - 工具: {tool_call['function']['name']}")
                print(f"      参数: {tool_call['function']['arguments']}")
        else:
            print(f"  直接回复: {message.get('content', '无内容')[:100]}...")
        
        return True
    except Exception as e:
        print(f"❌ 失败: {e}")
        logger.exception("工具调用错误")
        return False


def test_config():
    """测试8: 配置验证"""
    print("\n" + "="*60)
    print("测试8: 配置验证")
    print("="*60)
    
    api_key = os.getenv("ZKH_API_KEY", "")
    endpoint = os.getenv("ZKH_ENDPOINT", "")
    model_id = os.getenv("ZKH_MODEL_ID", "")
    
    # API Key 可以是 app- 或其他格式
    api_key_valid = bool(api_key and len(api_key) > 10)
    endpoint_valid = bool(endpoint and "ai-dev-gateway.zkh360.com" in endpoint)
    
    checks = {
        "ZKH_API_KEY": api_key_valid,
        "ZKH_ENDPOINT": endpoint_valid,
        "ZKH_MODEL_ID": bool(model_id),  # 可选，可以在运行时指定
    }
    
    all_passed = True
    for key, value in checks.items():
        actual_value = os.getenv(key, "未设置")
        if key == "ZKH_API_KEY" and actual_value != "未设置":
            actual_value = actual_value[:20] + "..."
        status = "✅" if value else "⚠️ "
        print(f"{status} {key}: {actual_value}")
        # 只有 ZKH_API_KEY 和 ZKH_ENDPOINT 是必需的
        if not value and key in ["ZKH_API_KEY", "ZKH_ENDPOINT"]:
            all_passed = False
    
    if all_passed:
        print("\n✅ 所有必需配置已就绪！")
        return True
    else:
        print("\n⚠️ 必要的配置未设置，请检查 ZKH_API_KEY 和 ZKH_ENDPOINT")
        return False


def main():
    """运行所有测试"""
    print("""
    ╔════════════════════════════════════════════════════════════╗
    ║                  震坤行AI集成测试脚本                        ║
    ║                                                            ║
    ║  用途: 验证震坤行大模型API集成是否正常工作                  ║
    ╚════════════════════════════════════════════════════════════╝
    """)
    
    results = []
    
    # 测试1: API密钥
    if not test_api_key():
        print("\n❌ 必要条件未满足，请先配置API密钥")
        print("\n设置方法:")
        print("1. 编辑 .env 文件，添加: ZKH_API_KEY=your_key_here")
        print("2. 或运行: export ZKH_API_KEY='your_key_here'")
        return
    results.append(("API密钥", True))
    
    # 测试2: 客户端初始化
    client = test_client_initialization()
    if client:
        results.append(("客户端初始化", True))
    else:
        results.append(("客户端初始化", False))
        return
    
    # 测试3: 获取模型列表
    if test_list_models(client):
        results.append(("获取模型列表", True))
    else:
        results.append(("获取模型列表", False))
    
    # 测试4: 简单对话
    if test_simple_chat(client):
        results.append(("简单文本对话", True))
    else:
        results.append(("简单文本对话", False))
    
    # 测试5: 流式对话
    if test_stream_chat(client):
        results.append(("流式对话", True))
    else:
        results.append(("流式对话", False))
    
    # 测试6: LLM提供商集成
    if test_llm_provider_integration():
        results.append(("LLM提供商集成", True))
    else:
        results.append(("LLM提供商集成", False))
    
    # 测试7: 工具调用
    if test_tool_calling(client):
        results.append(("工具调用", True))
    else:
        results.append(("工具调用", False))
    
    # 测试8: 配置验证
    if test_config():
        results.append(("配置验证", True))
    else:
        results.append(("配置验证", False))
    
    # 打印总结
    print("\n" + "="*60)
    print("测试总结")
    print("="*60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ 通过" if result else "❌ 失败"
        print(f"{status}: {test_name}")
    
    print("\n" + "-"*60)
    print(f"总计: {passed}/{total} 个测试通过")
    print("-"*60)
    
    if passed == total:
        print("\n🎉 所有测试通过！震坤行AI集成正常工作。")
        print("\n接下来的步骤:")
        print("1. 启动Web UI: python webui.py")
        print("2. 在浏览器中打开 http://127.0.0.1:7788")
        print("3. 在 'Agent Settings' 中选择 '震坤行AI' 提供商")
        print("4. 输入模型ID（推理接入点ID）")
        print("5. 开始使用！")
    else:
        print("\n⚠️ 部分测试未通过，请查看上面的错误信息")
        print("\n常见问题排查:")
        print("1. 检查API密钥是否正确")
        print("2. 检查网络连接")
        print("3. 检查模型ID是否有效")
        print("4. 查看详细日志: ZKH_INTEGRATION_GUIDE.md")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n用户中断测试")
        sys.exit(0)
    except Exception as e:
        print(f"\n\n❌ 未预期的错误: {e}")
        logger.exception("主程序错误")
        sys.exit(1)
