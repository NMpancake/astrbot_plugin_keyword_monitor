from astrbot.api.event import filter, AstrMessageEvent
from astrbot.api.star import Context, Star, register
from astrbot.api import logger
from astrbot.api.message_components import Plain
import asyncio
import re
import json
import os

@register("keyword_monitor", "AstrBot Developer", "监控群聊关键词并支持命令管理", "1.0.0")
class KeywordMonitorPlugin(Star):
    def __init__(self, context: Context, config):
        super().__init__(context)
        self.config = config
        self.config_file = os.path.join(os.path.dirname(__file__), "config.json")
        
        # 加载配置
        self.load_config()
        logger.info("关键词监控插件已加载!")
    
    def load_config(self):
        """从配置文件加载配置"""
        try:
            # 如果配置文件存在，则加载
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    config_data = json.load(f)
                    self.keywords = config_data.get('keywords', ["重要", "紧急", "漏洞"])
                    self.white_list = config_data.get('white_list', ["987654321", "112233445"])
                    self.admin_qq = config_data.get('admin_qq', "123456789")
            else:
                # 否则使用默认配置
                self.keywords = ["重要", "紧急", "漏洞"]
                self.white_list = ["987654321", "112233445"]
                self.admin_qq = "123456789"
                self.save_config()
        except Exception as e:
            logger.error(f"加载配置文件失败: {str(e)}")
            # 加载失败时使用默认配置
            self.keywords = ["重要", "紧急", "漏洞"]
            self.white_list = ["987654321", "112233445"]
            self.admin_qq = "123456789"

    def save_config(self):
        """保存配置到文件"""
        try:
            config_data = {
                'keywords': self.keywords,
                'white_list': self.white_list,
                'admin_qq': self.admin_qq
            }
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(config_data, f, ensure_ascii=False, indent=2)
            logger.info("配置文件已保存")
        except Exception as e:
            logger.error(f"保存配置文件失败: {str(e)}")

    @filter.event_message_type(filter.EventMessageType.GROUP_MESSAGE)
    async def monitor_keywords(self, event: AstrMessageEvent):
        """监控群聊中的关键词"""
        try:
            # 检查是否在白名单群聊中
            group_id = event.get_group_id()
            if group_id not in self.white_list:
                return
            
            # 检查消息内容是否包含关键词
            message = event.message_str
            for keyword in self.keywords:
                if keyword in message:
                    # 获取发送者信息
                    sender_id = event.get_sender_id()
                    sender_name = event.get_sender_name()
                    
                    # 构建通知消息
                    alert_msg = (
                        f"⚠️ 检测到关键词警报 ⚠️\n"
                        f"关键词: {keyword}\n"
                        f"群号: {group_id}\n"
                        f"发送者: {sender_name}({sender_id})\n"
                        f"消息内容: {message[:50]}{'...' if len(message) > 50 else ''}"
                    )
                    
                    # 发送私聊通知给管理员
                    await self.send_private_alert(alert_msg)
                    logger.warning(f"检测到关键词: {keyword} 在群 {group_id} 由 {sender_id} 发送")
                    break
        except Exception as e:
            logger.error(f"监控插件出错: {str(e)}")

    @filter.command("km_admin", permission_type=filter.PermissionType.ADMIN)
    async def admin_commands(self, event: AstrMessageEvent, command: str = None):
        """管理员命令入口"""
        if not command:
            yield event.plain_result(
                "🔑 关键词监控管理命令 🔑\n"
                "----------------------\n"
                "1. 添加关键词: /km_admin add_key [关键词]\n"
                "2. 删除关键词: /km_admin del_key [关键词]\n"
                "3. 列出关键词: /km_admin list_keys\n"
                "4. 添加白名单群: /km_admin add_group [群号]\n"
                "5. 删除白名单群: /km_admin del_group [群号]\n"
                "6. 列出白名单: /km_admin list_groups\n"
                "7. 设置管理员QQ: /km_admin set_admin [QQ号]"
            )
            return
        
        command_parts = command.split(maxsplit=1)
        action = command_parts[0].lower()
        param = command_parts[1] if len(command_parts) > 1 else None
        
        # 根据命令类型直接处理逻辑
        if action == "add_key" and param:
            # 添加关键词
            if param in self.keywords:
                yield event.plain_result(f"❌ 关键词 '{param}' 已存在")
            else:
                self.keywords.append(param)
                self.save_config()
                yield event.plain_result(f"✅ 已添加关键词: {param}")
                logger.info(f"管理员添加关键词: {param}")
        
        elif action == "del_key" and param:
            # 删除关键词
            if param not in self.keywords:
                yield event.plain_result(f"❌ 关键词 '{param}' 不存在")
            else:
                self.keywords.remove(param)
                self.save_config()
                yield event.plain_result(f"✅ 已删除关键词: {param}")
                logger.info(f"管理员删除关键词: {param}")
        
        elif action == "list_keys":
            # 列出所有关键词
            if not self.keywords:
                yield event.plain_result("🔍 当前没有监控关键词")
            else:
                keywords_list = "\n".join([f"• {kw}" for kw in self.keywords])
                yield event.plain_result(f"📝 监控关键词列表:\n{keywords_list}")
        
        elif action == "add_group" and param:
            # 添加白名单群
            if not re.match(r"^\d+$", param):
                yield event.plain_result("❌ 群号必须是纯数字")
            elif param in self.white_list:
                yield event.plain_result(f"❌ 群 {param} 已在白名单中")
            else:
                self.white_list.append(param)
                self.save_config()
                yield event.plain_result(f"✅ 已添加白名单群: {param}")
                logger.info(f"管理员添加白名单群: {param}")
        
        elif action == "del_group" and param:
            # 删除白名单群
            if param not in self.white_list:
                yield event.plain_result(f"❌ 群 {param} 不在白名单中")
            else:
                self.white_list.remove(param)
                self.save_config()
                yield event.plain_result(f"✅ 已移除白名单群: {param}")
                logger.info(f"管理员移除白名单群: {param}")
        
        elif action == "list_groups":
            # 列出白名单群
            if not self.white_list:
                yield event.plain_result("🔍 当前没有白名单群")
            else:
                groups_list = "\n".join([f"• {group}" for group in self.white_list])
                yield event.plain_result(f"📝 白名单群列表:\n{groups_list}")
        
        elif action == "set_admin" and param:
            # 设置管理员QQ
            if not re.match(r"^\d{5,12}$", param):
                yield event.plain_result("❌ 无效的QQ号格式")
            else:
                self.admin_qq = param
                self.save_config()
                yield event.plain_result(f"✅ 管理员QQ已设置为: {param}")
                logger.info(f"管理员QQ更新为: {param}")
        
        else:
            yield event.plain_result("❌ 无效命令或参数，请使用 /km_admin 查看帮助")

    async def send_private_alert(self, message: str):
        """发送私聊通知给管理员"""
        try:
            # 构建私聊会话ID
            session_id = f"aiocqhttp:FRIEND_MESSAGE:{self.admin_qq}"
            
            # 创建消息链
            message_chain = [Plain(text=message)]
            
            # 发送消息
            await self.context.send_message(session_id, message_chain)
            logger.info(f"已向管理员 {self.admin_qq} 发送警报消息")
        except Exception as e:
            logger.error(f"发送私聊通知失败: {str(e)}")

    async def terminate(self):
        """插件卸载时执行"""
        logger.info("关键词监控插件已卸载")