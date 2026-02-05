#!/usr/bin/env python3
"""
测试ZKH LLM提供者的修复
验证ZKHChatOpenAI类能否正确调用API
"""

import os
import sys
import logging
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def test_zkh_api_connection():
    """测试ZKH API连接"""
    
    api_key = os.getenv("ZKH_API_KEY")
    if not api_key:
        logger.error("❌ ZKH_API_KEY 环境变量未设置！")
        return False
    
    logger.info("✅ ZKH_API_KEY 已设置")
    
    # 导入LLM提供者
    from src.utils import llm_provider
    
    try:
        logger.info("🔄 初始化ZKH LLM模型...")
        
        # 使用配置中的模型
        llm = llm_provider.get_llm_model(
            provider="zkh",
            model_name="ep_20251217_i18v",  # DeepSeek-V3
            temperature=0.6,
            api_key=api_key
        )
        
        logger.info(f"✅ LLM模型初始化成功: {type(llm).__name__}")
        logger.info(f"   模型类型: {type(llm)}")
        logger.info(f"   基础URL: {llm.model_config.get('base_url', 'N/A')}")
        
        # 测试简单的invoke
        logger.info("🔄 测试简单的文本调用...")
        from langchain_core.messages import HumanMessage, SystemMessage
        
        messages = [
            SystemMessage(content="你是一个有帮助的AI助手。"),
            HumanMessage(content="你好，请自我介绍一下。限制在50字以内。")
        ]
        
        response = llm.invoke(messages)
        logger.info(f"✅ API调用成功！")
        logger.info(f"   响应: {response.content[:100]}...")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ 测试失败: {e}", exc_info=True)
        return False

def test_zkh_client_directly():
    """直接测试ZKH客户端"""
    
    api_key = os.getenv("ZKH_API_KEY")
    if not api_key:
        logger.error("❌ ZKH_API_KEY 环境变量未设置！")
        return False
    
    try:
        from src.utils.zkh_client import ZKHAPIClient
        
        logger.info("🔄 初始化ZKH API客户端...")
        client = ZKHAPIClient(api_key=api_key)
        
        logger.info("✅ 客户端初始化成功")
        logger.info(f"   Base URL: {client.base_url}")
        
        # 测试模型列表
        logger.info("🔄 获取可用模型列表...")
        models = client.list_models()
        logger.info(f"✅ 获取模型列表成功")
        if 'data' in models:
            for model in models['data'][:3]:
                logger.info(f"   - {model.get('id', 'N/A')}: {model.get('name', 'N/A')}")
        
        # 测试聊天完成
        logger.info("🔄 测试聊天API调用...")
        response = client.chat_completions(
            model="ep_20251217_i18v",
            messages=[
                {"role": "system", "content": "你是一个有帮助的AI助手。"},
                {"role": "user", "content": "你好，请用5个字以内回复。"}
            ],
            temperature=0.6
        )
        
        logger.info(f"✅ 聊天API调用成功！")
        if 'choices' in response and len(response['choices']) > 0:
            content = response['choices'][0].get('message', {}).get('content', '')
            logger.info(f"   响应: {content[:100]}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ 直接客户端测试失败: {e}", exc_info=True)
        return False

if __name__ == "__main__":
    logger.info("=" * 60)
    logger.info("开始测试ZKH LLM修复")
    logger.info("=" * 60)
    
    # 首先测试直接客户端
    logger.info("\n[第1阶段] 测试ZKH API客户端")
    logger.info("-" * 60)
    client_ok = test_zkh_client_directly()
    
    # 然后测试LLM提供者
    logger.info("\n[第2阶段] 测试ZKHChatOpenAI提供者")
    logger.info("-" * 60)
    llm_ok = test_zkh_api_connection()
    
    # 总结
    logger.info("\n" + "=" * 60)
    if client_ok and llm_ok:
        logger.info("✅ 所有测试通过！ZKH LLM已正确配置")
        sys.exit(0)
    elif client_ok:
        logger.info("⚠️  客户端正常，但LLM提供者有问题")
        sys.exit(1)
    else:
        logger.info("❌ ZKH API连接失败，请检查API KEY和网络")
        sys.exit(1)
