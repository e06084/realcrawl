from datetime import datetime
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field
from enum import Enum


class AnnotationType(str, Enum):
    """标注类型枚举"""
    MANUAL = "manual"  # 手动标注
    IMPORTED = "imported"  # 导入标注
    GENERATED = "generated"  # 自动生成


class AnnotationStatus(str, Enum):
    """标注状态枚举"""
    DRAFT = "draft"  # 草稿
    COMPLETED = "completed"  # 完成
    SHARED = "shared"  # 已分享


class AnnotationCreate(BaseModel):
    """标注创建模型"""
    domain: str = Field(..., description="域名")
    layout_id: str = Field(..., description="布局ID")
    html_content: str = Field(..., description="HTML内容")
    annotations: Dict[str, Any] = Field(..., description="标注数据")
    type: AnnotationType = Field(default=AnnotationType.MANUAL, description="标注类型")
    notes: Optional[str] = Field(None, description="备注")


class AnnotationUpdate(BaseModel):
    """标注更新模型"""
    domain: Optional[str] = Field(None, description="域名")
    layout_id: Optional[str] = Field(None, description="布局ID")
    html_content: Optional[str] = Field(None, description="HTML内容")
    annotations: Optional[Dict[str, Any]] = Field(None, description="标注数据")
    notes: Optional[str] = Field(None, description="备注")
    status: Optional[AnnotationStatus] = Field(None, description="状态")


class AnnotationInDB(BaseModel):
    """数据库中的标注模型"""
    id: int
    domain: str
    layout_id: str
    html_content: str
    annotations: Dict[str, Any]
    type: AnnotationType
    status: AnnotationStatus
    notes: Optional[str] = None
    is_shared: bool
    shared_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime


class AnnotationResponse(BaseModel):
    """标注响应模型"""
    id: int
    domain: str
    layout_id: str
    annotations: Dict[str, Any]
    type: AnnotationType
    status: AnnotationStatus
    notes: Optional[str] = None
    is_shared: bool
    shared_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime


class AnnotationWithHTML(AnnotationResponse):
    """包含HTML内容的标注响应"""
    html_content: str


class AnnotationListItem(BaseModel):
    """标注列表项模型"""
    id: int
    domain: str
    layout_id: str
    type: AnnotationType
    status: AnnotationStatus
    is_shared: bool
    created_at: datetime
    updated_at: datetime


class AnnotationShareRequest(BaseModel):
    """标注分享请求模型"""
    notes: Optional[str] = Field(None, description="分享备注")


class AnnotationCompareRequest(BaseModel):
    """标注对比请求模型"""
    annotation_id: int = Field(..., description="要对比的标注ID")
    domain: str = Field(..., description="对比的域名")


class AnnotationCompareResult(BaseModel):
    """标注对比结果模型"""
    annotation_id: int
    domain: str
    similarity_score: float = Field(..., description="相似度分数(0-1)")
    differences: List[Dict[str, Any]] = Field(..., description="差异列表")
    matched_features: List[str] = Field(..., description="匹配的特征")


class AnnotationStats(BaseModel):
    """标注统计模型"""
    total: int = Field(default=0, description="总数")
    draft: int = Field(default=0, description="草稿数")
    completed: int = Field(default=0, description="完成数")
    shared: int = Field(default=0, description="已分享数")
    by_type: Dict[str, int] = Field(default_factory=dict, description="按类型统计")


class AnnotationSearchRequest(BaseModel):
    """标注搜索请求模型"""
    query: Optional[str] = Field(None, description="搜索关键词")
    domain: Optional[str] = Field(None, description="域名过滤")
    type: Optional[AnnotationType] = Field(None, description="类型过滤")
    status: Optional[AnnotationStatus] = Field(None, description="状态过滤")
    is_shared: Optional[bool] = Field(None, description="是否已分享")
    page: int = Field(default=1, ge=1, description="页码")
    size: int = Field(default=20, ge=1, le=100, description="每页大小")


class AnnotationSearchResponse(BaseModel):
    """标注搜索响应模型"""
    items: List[AnnotationListItem]
    total: int
    page: int
    size: int
    pages: int 