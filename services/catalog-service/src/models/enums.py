# services/catalog-service/src/models/enums.py
from enum import Enum

class SyncStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    SYNCED = "synced"
    FAILED = "failed"

class AnalysisStatus(str, Enum):
    PENDING = "pending"
    REQUESTED = "requested"
    ANALYZED = "analyzed"
    FAILED = "failed"

class SyncOperationStatus(str, Enum):
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"

class SyncType(str, Enum):
    FULL = "full"
    INCREMENTAL = "incremental"