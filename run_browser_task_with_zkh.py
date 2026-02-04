#!/usr/bin/env python3
"""
快速启动脚本 - 使用震坤行AI的Browser Agent

这个脚本演示如何直接使用震坤行大模型来驱动浏览器自动化任务
"""

import os
import sys
import asyncio
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

from src.utils import llm_provider
from src.browser.custom_browser import CustomBrowser
from src.browser.custom_context import CustomBrowserContext
from src.controller.custom_controller import CustomController
from src.agent.browser_use.browser_use_agent import BrowserUseAgent
from browser_use.browser.browser import BrowserConfig
from browser_use.browser.context import BrowserContextConfig


async def run_browser_task_with_zkh(
    task: str,
    api_key: str,
    model_id: str = "ep-20250429102651-hd5dd",
    headless: bool = False,
    max_steps: int = 100,
):
    """
    使用震坤行AI运行浏览器自动化任务
    
    Args:
        task: 浏览器任务描述（中文）
        api_key: 震坤行API密钥
        model_id: 推理接入点ID
        headless: 是否使用无头浏览器
        max_steps: 最大执行步数
    """
    
    print(f"""
    ╔══════════════════════════════════════════════════════════╗
    ║                    Browser Agent Demo                     ║
    ║                    使用震坤行AI大模型                     ║
    ╚══════════════════════════════════════════════════════════╝
    
    任务: {task}
    模型: 震坤行 ({model_id})
    最大步数: {max_steps}
    """)
    
    # 1. 初始化LLM
    print("📌 步骤1: 初始化AI模型...")
    try:
        llm = llm_provider.get_llm_model(
            provider="zkh",
            model_name=model_id,
            temperature=0.6,
            api_key=api_key
        )
        print("   ✅ AI模型初始化成功")
    except Exception as e:
        print(f"   ❌ AI模型初始化失败: {e}")
        return
    
    # 2. 初始化浏览器
    print("\n📌 步骤2: 初始化浏览器...")
    try:
        browser = CustomBrowser(
            config=BrowserConfig(
                headless=headless,
                new_context_config=BrowserContextConfig(
                    window_width=1280,
                    window_height=1100,
                )
            )
        )
        print("   ✅ 浏览器初始化成功")
    except Exception as e:
        print(f"   ❌ 浏览器初始化失败: {e}")
        return
    
    # 3. 创建浏览器上下文
    print("\n📌 步骤3: 创建浏览器上下文...")
    try:
        browser_context = await browser.new_context(
            config=BrowserContextConfig(
                save_downloads_path="./tmp/downloads",
                window_height=1100,
                window_width=1280,
                force_new_context=True,
            )
        )
        print("   ✅ 浏览器上下文创建成功")
    except Exception as e:
        print(f"   ❌ 浏览器上下文创建失败: {e}")
        return
    
    # 4. 初始化控制器
    print("\n📌 步骤4: 初始化浏览器控制器...")
    try:
        controller = CustomController()
        print("   ✅ 浏览器控制器初始化成功")
    except Exception as e:
        print(f"   ❌ 浏览器控制器初始化失败: {e}")
        return
    
    # 5. 创建Agent
    print("\n📌 步骤5: 创建Browser Agent...")
    try:
        agent = BrowserUseAgent(
            task=task,
            llm=llm,
            browser=browser,
            browser_context=browser_context,
            controller=controller,
            use_vision=True,
            source="demo"
        )
        print("   ✅ Browser Agent创建成功")
    except Exception as e:
        print(f"   ❌ Browser Agent创建失败: {e}")
        return
    
    # 6. 运行Agent
    print(f"\n📌 步骤6: 运行任务（最多{max_steps}步）...")
    print("-" * 60)
    
    try:
        history = await agent.run(max_steps=max_steps)
        
        print("-" * 60)
        print(f"\n✅ 任务执行完成！")
        print(f"\n执行统计:")
        print(f"  - 总步数: {len(history.history)}")
        
        # 显示执行过程摘要
        if len(history.history) > 0:
            print(f"\n执行过程摘要:")
            for i, step in enumerate(history.history[:5], 1):  # 显示前5步
                print(f"\n  步骤{i}:")
                if step.state:
                    print(f"    URL: {step.state.url}")
                if step.model_output:
                    print(f"    AI决策: {len(step.model_output.action)} 个动作")
                if step.result:
                    print(f"    结果: {len(step.result)} 个反馈")
        
        # 保存历史记录
        output_file = "browser_agent_history.json"
        try:
            import json
            history_dict = {
                "task": task,
                "steps": len(history.history),
                "success": history.is_done(),
                "timestamp": str(Path(__file__).stat().st_mtime)
            }
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(history_dict, f, ensure_ascii=False, indent=2)
            print(f"\n📁 执行历史已保存到: {output_file}")
        except Exception as e:
            logger.warning(f"保存历史文件失败: {e}")
        
    except Exception as e:
        print(f"\n❌ 任务执行失败: {e}")
        logger.exception("Agent执行错误")
    finally:
        # 清理资源
        print("\n📌 清理资源...")
        try:
            await browser.close()
            print("   ✅ 浏览器已关闭")
        except Exception as e:
            logger.warning(f"关闭浏览器时出错: {e}")


async def main():
    """主函数"""
    
    # 读取配置
    api_key = os.getenv("ZKH_API_KEY")
    model_id = os.getenv("ZKH_MODEL_ID", "ep-20250429102651-hd5dd")
    
    if not api_key:
        print("""
        ❌ 错误: 未设置ZKH_API_KEY环境变量
        
        请先配置环境变量:
        
        方法1 (编辑.env文件):
            ZKH_API_KEY=your_api_key_here
            ZKH_MODEL_ID=ep-20250429102651-hd5dd
        
        方法2 (命令行):
            export ZKH_API_KEY="your_api_key_here"
            export ZKH_MODEL_ID="ep-20250429102651-hd5dd"
        
        然后重新运行此脚本。
        """)
        sys.exit(1)
    
    # 任务示例
    task = """
    请帮我完成以下任务:
    1. 打开Google搜索页面
    2. 搜索 "Python 教程"
    3. 点击第一个搜索结果
    4. 等待页面加载完成
    5. 提取页面的标题和URL
    
    完成后使用 done() 动作结束任务。
    """
    
    # 运行任务
    await run_browser_task_with_zkh(
        task=task.strip(),
        api_key=api_key,
        model_id=model_id,
        headless=False,  # 改为True可使用无头模式
        max_steps=50
    )


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n⚠️ 任务被用户中断")
        sys.exit(0)
    except Exception as e:
        print(f"\n\n❌ 发生错误: {e}")
        logger.exception("主程序错误")
        sys.exit(1)
