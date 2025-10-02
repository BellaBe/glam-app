from pydantic import BaseModel


class WebhookResponse(BaseModel):
    success: bool
    webhook_id: str
