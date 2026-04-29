"""
Skill 集成模块
预留外部工具调用能力（企业微信通知、第三方 API 调用等）
"""

async def send_wechat_notification(webhook_url: str, content: str) -> dict:
    """
    发送企业微信通知（占位实现）。

    参数:
        webhook_url: 企业微信机器人 Webhook 地址
        content: 通知文本内容

    返回:
        {"status": "success", "message": "通知已发送"}
    """
    return {
        "status": "success",
        "message": "企业微信通知功能将在后续迭代中实现",
        "note": "需配置 webhook_url 并实现 HTTP POST 调用",
    }


async def call_external_api(url: str, method: str = "GET", params: dict | None = None) -> dict:
    """
    调用外部 API（占位实现）。

    参数:
        url: API 地址
        method: HTTP 方法
        params: 请求参数

    返回:
        API 响应字典
    """
    return {
        "status": "success",
        "message": "外部 API 调用功能将在后续迭代中实现",
        "note": f"将 {method} {url} 参数: {params}",
    }


# 可用的 Skill 注册表
AVAILABLE_SKILLS = {
    "wechat_notification": {
        "name": "企业微信通知",
        "description": "向企业微信群发送通知消息",
        "function": send_wechat_notification,
    },
    "external_api": {
        "name": "外部 API 调用",
        "description": "调用第三方 HTTP API",
        "function": call_external_api,
    },
}


def get_available_skills() -> list[dict]:
    """获取所有可用 Skill 的列表"""
    return [
        {"id": skill_id, "name": info["name"], "description": info["description"]}
        for skill_id, info in AVAILABLE_SKILLS.items()
    ]
