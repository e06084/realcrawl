from fastapi import APIRouter
from .endpoints import domain, annotations

api_router = APIRouter()

# 注册domain相关路由
api_router.include_router(domain.router, prefix="/domains", tags=["domains"])

# 注册annotations相关路由
api_router.include_router(annotations.router, prefix="/annotations", tags=["annotations"]) 