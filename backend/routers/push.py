"""小居数据监控台 - 推送接口"""
import httpx
import json
from pydantic import BaseModel
from typing import Optional
from fastapi import APIRouter
import config
from services.logger import logger

router = APIRouter()

_FEISHU_APP_ID = "cli_a94d32b716b8dccd"
_FEISHU_APP_SECRET = "sVbxWF7MNCepX2UMonmxidIIPYdJ4LMR"
_FEISHU_USER_OPEN_ID = "ou_a5779a94565733ace8dadf91a09287d1"
_FEISHU_API_BASE = "https://open.feishu.cn/open-apis"


class PushRequest(BaseModel):
    platform: str = "feishu"
    content: str = ""
    webhook: Optional[str] = None

class PushReportRequest(BaseModel):
    platform: str = "feishu"
    report_type: str = "morning"


async def _get_feishu_token() -> str | None:
    """获取飞书tenant_access_token"""
    async with httpx.AsyncClient(timeout=10.0) as client:
        resp = await client.post(
            f"{_FEISHU_API_BASE}/auth/v3/tenant_access_token/internal",
            json={"app_id": _FEISHU_APP_ID, "app_secret": _FEISHU_APP_SECRET}
        )
        data = resp.json()
        if data.get("code") == 0:
            return data["tenant_access_token"]
        logger.error(f"获取飞书token失败: {data}")
        return None


async def push_to_feishu(message: str, webhook: str = None) -> dict:
    """推送消息到飞书（应用身份API）"""
    token = await _get_feishu_token()
    if not token:
        return {"success": False, "error": "获取飞书access_token失败"}

    async with httpx.AsyncClient(timeout=15.0) as client:
        resp = await client.post(
            f"{_FEISHU_API_BASE}/im/v1/messages?receive_id_type=open_id",
            headers={
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json"
            },
            json={
                "receive_id": _FEISHU_USER_OPEN_ID,
                "msg_type": "text",
                "content": json.dumps({"text": message})
            }
        )
        result = resp.json()
        if result.get("code") == 0:
            logger.info("飞书推送成功")
            return {"success": True}
        else:
            logger.error(f"飞书推送失败: {result}")
            return {"success": False, "error": str(result)}


async def push_to_wecom(message: str, webhook: str = None) -> dict:
    """推送消息到企业微信"""
    webhook_url = webhook or getattr(config, 'WECOM_WEBHOOK', None)
    if not webhook_url:
        return {"success": False, "error": "未配置企业微信Webhook"}

    async with httpx.AsyncClient(timeout=10.0) as client:
        resp = await client.post(
            webhook_url,
            json={
                "msgtype": "text",
                "text": {"content": message}
            }
        )
        result = resp.json()
        if result.get("errcode") == 0:
            logger.info("企业微信推送成功")
            return {"success": True}
        else:
            logger.error(f"企业微信推送失败: {result.get('errmsg')}")
            return {"success": False, "error": result.get("errmsg")}


async def push_report(report_type: str = "morning", platform: str = "feishu") -> dict:
    """推送日报"""
    from routers import report

    if report_type == "morning":
        rep = await report.generate_morning_report()
    else:
        rep = await report.generate_evening_report()

    # 优先用content字段（完整格式化内容），没有则用sections
    content = rep.get("content", "")
    if not content and rep.get("sections"):
        content = f"📰 {rep['title']} - {rep['date']}\n\n"
        for section in rep.get("sections", []):
            content += f"{section['title']}\n{section['content']}\n\n"

    if platform == "feishu":
        return await push_to_feishu(content)
    elif platform == "wecom":
        return await push_to_wecom(content)
    else:
        return {"success": False, "error": f"不支持的平台: {platform}"}


# ========== API 端点 ==========

@router.post("/")
async def api_push_message(req: PushRequest):
    """API: 推送消息"""
    if not req.content:
        return {"success": False, "error": "消息内容不能为空"}

    if req.platform == "feishu":
        return await push_to_feishu(req.content, req.webhook)
    elif req.platform == "wecom":
        return await push_to_wecom(req.content, req.webhook)
    else:
        return {"success": False, "error": f"不支持的平台: {req.platform}"}


@router.post("/report")
async def api_push_report(req: PushReportRequest):
    """API: 推送日报"""
    return await push_report(req.report_type, req.platform)


@router.get("/platforms")
async def api_get_platforms():
    """API: 获取支持的推送平台"""
    return {
        "platforms": [
            {"id": "feishu", "name": "飞书", "configured": True},
            {"id": "wecom", "name": "企业微信", "configured": bool(getattr(config, 'WECOM_WEBHOOK', None))},
        ]
    }
