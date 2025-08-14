# astrbot_plugin_keyword_monitor
这是一个插件用来提醒我群里出现了我所标记的关键词


## 如何使用？

🔑 关键词监控管理命令 🔑
----------------------
1. 添加关键词: /km add_key [关键词]
2. 删除关键词: /km del_key [关键词]
3. 列出关键词: /km list_keys
4. 添加白名单群: /km add_group [群号]
5. 删除白名单群: /km del_group [群号]
6. 列出白名单: /km list_groups
7. 设置管理员QQ: /km set_admin [QQ号]



- 发送 **/km** 给你的robot可以随时获得帮助😃😃😃

- 仅管理员QQ可使用以上命令，首次设置管理员QQ需要在

  ```  
  astrbot/data/plugins/astrbot_plugin_keyword_monitor/config.jison
  ```

  **config.jison**文件中手动配置 **admin_qq** （tips:配置完后记得回到AstrBot插件管理页面重载插件）

  

## 注意！！！

**不支持**通过AstrBot仪表盘中的“插件配置”功能进行配置！！！