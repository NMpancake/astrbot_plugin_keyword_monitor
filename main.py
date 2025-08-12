from astrbot.api.event import filter, AstrMessageEvent, MessageEventResult
from astrbot.api.star import Context, Star, register
from astrbot.api import logger
#from astrbot.api import (
#    Star, register, Context, logger,
#    filter, AstrMessageEvent, MessageEventResult
#)
#from astrbot.api.platform import PlatformAdapterType
from astrbot.api.message_components import Plain
#from astrbot.api.star import PermissionType
from typing import Set

@register("keywordprompt", "NMpancake", "一个简单的 关键词监控 插件", "1.0.0")
class KeywordPrompt(Star):
    def __init__(self, context: Context):
        super().__init__(context)
        # init keyword group
        self.keywords: Set[str] = {"代课"}
        # get master QQ
        self.master_qq = self.context.congit.get("master_qq", "2461248172")

        # 初始化群白名单（存储群号）
        self.allowed_groups: Set[str] = set()

        # 从配置加载初始白名单
        if "allowed_groups" in self.context.config:
            self.allowed_groups = set(self.context.config["allowed_groups"].split(","))
            logger.info(f"已加载白名单群组: {self.allowed_groups}")

        logger.info(f"关键词监控插件已加载，主人QQ: {self.master_qq}")

    @filter.event_message_type(filter.EventMessageType.GROUP_MESSAGE)
    async def monitor_group_message(self, event: AstrMessageEvent):
        """监控群消息中的关键词"""
        group_id = event.get_group_id()

        # 检查群是否在白名单中
        if group_id not in self.allowed_groups:
            return  # 不在白名单中，忽略消息
        
        message_text = event.message_str
        sender_id = event.get_sender_id()

        # 检查消息是否包含关键词
        for keyword in self.keywords:
            if keyword in message_text:
                # init prompt message
                alert_msg = (
                    f"⚠️ 检测到关键词触发！\n"
                    f"▸ 关键词: {keyword}\n"
                    f"▸ 群号: {group_id}\n"
                    f"▸ 发送者: {sender_id}\n"
                    f"▸ 内容: {message_text[:50]}..."  # 截取前50字符
                )

                # 发送私聊通知给主人
                await self.context.send_message(
                    unified_msg_origin=f"private:{self.master_qq}",
                    chain=[Plain(text=alert_msg)]
                )
                logger.info(f"已向主人发送关键词警报: {keyword}")
                break # 发现一个关键词就停止检查

    # 群白名单管理命令
    @filter.permission_type(filter.PermissionType.ADMIN)
    @filter.command("添加监控群")
    @filter.event_message_type(filter.EventMessageType.PRIVATE_MESSAGE)
    async def add_group(self, event: AstrMessageEvent, group_id: str):
        """添加群到白名单"""
        if not group_id.isdigit():
            yield event.plain_result("⛔ 群号必须为数字")
            return
            
        if group_id in self.allowed_groups:
            yield event.plain_result(f"⛔ 群 {group_id} 已在白名单中")
        else:
            self.allowed_groups.add(group_id)
            self._save_config()  # 保存配置
            yield event.plain_result(f"✅ 已添加群 {group_id} 到白名单")
            logger.info(f"添加监控群: {group_id}")

    @filter.permission_type(filter.PermissionType.ADMIN)
    @filter.command("移除监控群")
    @filter.event_message_type(filter.EventMessageType.PRIVATE_MESSAGE)
    async def remove_group(self, event: AstrMessageEvent, group_id: str):
        """从白名单移除群"""
        if group_id in self.allowed_groups:
            self.allowed_groups.remove(group_id)
            self._save_config()  # 保存配置
            yield event.plain_result(f"✅ 已从白名单移除群 {group_id}")
            logger.info(f"移除监控群: {group_id}")
        else:
            yield event.plain_result(f"⛔ 群 {group_id} 不在白名单中")

    @filter.permission_type(filter.PermissionType.ADMIN)
    @filter.command("监控群列表")
    @filter.event_message_type(filter.EventMessageType.PRIVATE_MESSAGE)
    async def list_groups(self, event: AstrMessageEvent):
        """查看当前白名单群组"""
        if not self.allowed_groups:
            yield event.plain_result("当前没有监控群组")
            return
    
    @filter.permission_type(filter.PermissionType.ADMIN)
    @filter.command("开启所有群监控")
    @filter.event_message_type(filter.EventMessageType.PRIVATE_MESSAGE)
    async def enable_all_groups(self, event: AstrMessageEvent):
        """开启所有群监控（特殊值：all）"""
        self.allowed_groups = {"all"}
        self._save_config()
        yield event.plain_result("✅ 已开启所有群组监控")
        logger.info("开启所有群监控")
    
    @filter.permission_type(filter.PermissionType.ADMIN)
    @filter.command("关闭所有群监控")
    @filter.event_message_type(filter.EventMessageType.PRIVATE_MESSAGE)
    async def disable_all_groups(self, event: AstrMessageEvent):
        """关闭所有群监控"""
        self.allowed_groups = set()
        self._save_config()
        yield event.plain_result("✅ 已关闭所有群组监控")
        logger.info("关闭所有群监控")
    
    def _save_config(self):
        """保存配置到插件管理器"""
        # 将白名单转换为逗号分隔的字符串
        groups_str = ",".join(self.allowed_groups)
        
        # 更新配置
        self.context.config["allowed_groups"] = groups_str
        self.context.config.save_config()
        logger.info(f"已保存白名单配置: {groups_str}")

    # 关键词管理命令
    @filter.permission_type(filter.PermissionType.ADMIN)
    @filter.command("添加关键词")
    @filter.event_message_type(filter.EventMessageType.PRIVATE_MESSAGE)
    async def add_keyword(self, event: AstrMessageEvent, keyword: str):
        """添加新的监控关键词"""
        if not keyword:
            yield event.plain_result("请输入要添加的关键词")
            return
            
        if keyword in self.keywords:
            yield event.plain_result(f"⛔ 关键词已存在: {keyword}")
        else:
            self.keywords.add(keyword)
            yield event.plain_result(f"✅ 已添加关键词: {keyword}")
            logger.info(f"添加关键词: {keyword}")

    @filter.permission_type(filter.PermissionType.ADMIN)
    @filter.command("移除关键词")
    @filter.event_message_type(filter.EventMessageType.PRIVATE_MESSAGE)
    async def remove_keyword(self, event: AstrMessageEvent, keyword: str):
        """移除现有监控关键词"""
        if not keyword:
            yield event.plain_result("请输入要移除的关键词")
            return
        
        if keyword in self.keywords:
            self.keywords.remove(keyword)
            yield event.plain_result(f"✅ 已移除关键词: {keyword}")
            logger.info(f"移除关键词: {keyword}")
        else:
            yield event.plain_result(f"⛔ 关键词不存在: {keyword}")

    @filter.permission_type(filter.PermissionType.ADMIN)
    @filter.command("关键词列表")
    @filter.event_message_type(filter.EventMessageType.PRIVATE_MESSAGE)
    async def list_keywords(self, event: AstrMessageEvent):
        """查看当前所有监控关键词"""
        if not self.keywords:
            yield event.plain_result("当前没有监控关键词")
            return
            
        keyword_list = "\n".join(f"• {kw}" for kw in self.keywords)
        yield event.plain_result(f"📝 监控关键词列表:\n{keyword_list}")

    async def terminate(self):
        """插件卸载时的清理操作"""
        logger.info("关键词监控插件已卸载")
