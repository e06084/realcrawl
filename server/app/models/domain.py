from typing import Dict, List, Optional, Union
from pydantic import BaseModel, Field
from datetime import datetime

class LayoutPrediction(BaseModel):
    """Layout预测结果模型"""
    predictions: Dict[str, str] = Field(
        description="模型预测结果，key为item_id，value为预测类别"
    )

class LayoutInfo(BaseModel):
    """Layout信息模型"""
    layout_id: str = Field(..., description="Layout ID")
    llm_prediction: Dict[str, str] = Field(..., description="模型预测结果")
    html_path: Optional[str] = Field(None, description="HTML文件在S3中的路径")
    timestamp: int = Field(..., description="更新时间戳")

class LayoutInfoWithHtml(BaseModel):
    """包含HTML内容的Layout信息模型"""
    layout_id: str = Field(..., description="Layout ID")
    llm_prediction: Dict[str, str] = Field(..., description="模型预测结果")
    html_content: Optional[str] = Field(None, description="HTML内容")
    timestamp: int = Field(..., description="更新时间戳")
    html_path: Optional[str] = Field(None, description="HTML文件在S3中的路径")

class DomainCreateRequest(BaseModel):
    """创建Domain的请求模型"""
    domain: str = Field(..., description="域名")
    layouts: List[LayoutInfoWithHtml] = Field(..., description="Layout列表")

class DomainInfo(BaseModel):
    """Domain信息模型"""
    domain: str = Field(..., description="域名")
    layout_ids: List[LayoutInfo] = Field(default_factory=list, description="Layout列表")
    last_updated: int = Field(
        default_factory=lambda: int(datetime.now().timestamp()),
        description="最后更新时间戳"
    )

class DomainFeatureResponse(BaseModel):
    """Domain特征查询响应模型"""
    domain: str
    layout_ids: List[Union[LayoutInfo, LayoutInfoWithHtml]]
    total_layouts: int = Field(..., description="Layout总数")
    last_updated: int 