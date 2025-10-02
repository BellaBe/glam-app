# services/selfie-ai-analyzer/src/dependencies.py
from typing import Annotated
from fastapi import Depends, Request
from .lifecycle import ServiceLifecycle
from .services.analysis_service import AnalysisService

def get_lifecycle(request: Request) -> ServiceLifecycle:
    return request.app.state.lifecycle

def get_config(request: Request):
    return request.app.state.config

def get_analysis_service(lifecycle: Annotated[ServiceLifecycle, Depends(get_lifecycle)]) -> AnalysisService:
    return lifecycle.analysis_service

# Type aliases
LifecycleDep = Annotated[ServiceLifecycle, Depends(get_lifecycle)]
ConfigDep = Annotated[object, Depends(get_config)]
AnalysisServiceDep = Annotated[AnalysisService, Depends(get_analysis_service)]