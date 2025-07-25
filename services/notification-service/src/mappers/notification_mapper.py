# services/notification-service/src/mappers/notification_mapper.py
"""Mapper for notification schemas and models."""

from ..models import Notification
from ..schemas import (
    NotificationCreate,
    NotificationUpdate,
    NotificationResponse
)
from shared.mappers.crud_mapper import CRUDMapper


class NotificationMapper(
    CRUDMapper[
        Notification, NotificationCreate, NotificationUpdate, NotificationResponse
    ]
):
    """Maps between notification schemas and models."""

    model_cls = Notification
    out_schema = NotificationResponse