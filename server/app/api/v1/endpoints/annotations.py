"""
标注库API端点
提供标注管理、分享功能
"""

from typing import List, Optional
from fastapi import APIRouter, HTTPException, Query, Header, Depends
from ....models.annotation import (
    AnnotationCreate,
    AnnotationUpdate,
    AnnotationResponse,
    AnnotationWithHTML,
    AnnotationListItem,
    AnnotationShareRequest,
    AnnotationSearchRequest,
    AnnotationSearchResponse,
    AnnotationStats,
    AnnotationType,
    AnnotationStatus
)
from ....db.postgresql import annotation_db

router = APIRouter()


async def get_current_user_id(x_user_id: str = Header(..., description="用户ID，由middleware提供")):
    """
    获取当前用户ID
    这个函数从HTTP Header中获取用户ID，实际部署时会由middleware设置
    """
    if not x_user_id:
        raise HTTPException(status_code=401, detail="用户ID未提供")
    return x_user_id


@router.get("/", response_model=AnnotationSearchResponse, summary="获取标注列表")
async def get_annotations(
    user_id: str = Depends(get_current_user_id),
    query: Optional[str] = Query(None, description="搜索关键词"),
    domain: Optional[str] = Query(None, description="域名过滤"),
    url: Optional[str] = Query(None, description="URL过滤"),
    type: Optional[AnnotationType] = Query(None, description="类型过滤"),
    status: Optional[AnnotationStatus] = Query(None, description="状态过滤"),
    is_shared: Optional[bool] = Query(None, description="是否已分享"),
    page: int = Query(1, ge=1, description="页码"),
    size: int = Query(20, ge=1, le=100, description="每页大小")
):
    """
    获取标注列表（支持检索功能）
    
    - **query**: 在域名、URL、布局ID、备注中搜索关键词
    - **domain**: 按域名精确过滤
    - **url**: 按URL精确过滤
    - **type**: 按标注类型过滤
    - **status**: 按状态过滤
    - **is_shared**: 按是否分享过滤
    - **page**: 页码，从1开始
    - **size**: 每页大小，最大100
    
    注意：只返回当前用户的标注
    """
    try:
        search_request = AnnotationSearchRequest(
            query=query,
            domain=domain,
            url=url,
            type=type,
            status=status,
            is_shared=is_shared,
            page=page,
            size=size
        )
        result = await annotation_db.search_annotations(search_request, user_id)
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/", response_model=AnnotationResponse, summary="创建标注")
async def create_annotation(
    annotation_data: AnnotationCreate,
    user_id: str = Depends(get_current_user_id)
):
    """
    创建新的标注（重标注功能）
    
    - **domain**: 域名
    - **url**: 页面URL
    - **layout_id**: 布局ID  
    - **html_content**: HTML内容
    - **annotations**: 标注数据（元素标注信息）
    - **type**: 标注类型（manual/imported/generated）
    - **notes**: 备注信息
    
    注意：标注会自动关联到当前用户
    """
    try:
        # TODO: 验证HTML内容和标注数据
        # validation_result = html_parser.validate_annotations(
        #     annotation_data.html_content,
        #     annotation_data.annotations
        # )
        # if not validation_result['valid']:
        #     raise HTTPException(
        #         status_code=400,
        #         detail=f"标注数据验证失败: {validation_result['errors']}"
        #     )
        
        # 保存到数据库
        annotation = await annotation_db.create_annotation(annotation_data, user_id)
        
        # 转换为响应模型
        return AnnotationResponse(
            id=annotation.id,
            user_id=annotation.user_id,
            domain=annotation.domain,
            url=annotation.url,
            layout_id=annotation.layout_id,
            annotations=annotation.annotations,
            type=annotation.type,
            status=annotation.status,
            notes=annotation.notes,
            is_shared=annotation.is_shared,
            shared_at=annotation.shared_at,
            created_at=annotation.created_at,
            updated_at=annotation.updated_at
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{annotation_id}", response_model=AnnotationWithHTML, summary="获取标注详情")
async def get_annotation(
    annotation_id: int,
    user_id: str = Depends(get_current_user_id)
):
    """
    获取标注的详细信息（包含HTML内容）
    
    - **annotation_id**: 标注ID
    
    注意：只能获取当前用户的标注
    """
    try:
        # 从数据库获取标注
        annotation = await annotation_db.get_annotation(annotation_id)
        if not annotation:
            raise HTTPException(status_code=404, detail="标注不存在")
        
        # 检查用户权限
        if annotation.user_id != user_id:
            raise HTTPException(status_code=403, detail="无权限访问此标注")
        
        # 转换为响应模型
        return AnnotationWithHTML(
            id=annotation.id,
            user_id=annotation.user_id,
            domain=annotation.domain,
            url=annotation.url,
            layout_id=annotation.layout_id,
            annotations=annotation.annotations,
            type=annotation.type,
            status=annotation.status,
            notes=annotation.notes,
            is_shared=annotation.is_shared,
            shared_at=annotation.shared_at,
            created_at=annotation.created_at,
            updated_at=annotation.updated_at,
            html_content=annotation.html_content
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/{annotation_id}", response_model=AnnotationResponse, summary="更新标注")
async def update_annotation(
    annotation_id: int,
    annotation_update: AnnotationUpdate,
    user_id: str = Depends(get_current_user_id)
):
    """
    更新标注信息
    
    - **annotation_id**: 标注ID
    - 只更新提供的字段，其他字段保持不变
    
    注意：只能更新当前用户的标注
    """
    try:
        # 验证和更新数据
        updated_annotation = await annotation_db.update_annotation(
            annotation_id, 
            annotation_update,
            user_id
        )
        
        if not updated_annotation:
            raise HTTPException(status_code=404, detail="标注不存在或无权限修改")
        
        # 转换为响应模型
        return AnnotationResponse(
            id=updated_annotation.id,
            user_id=updated_annotation.user_id,
            domain=updated_annotation.domain,
            url=updated_annotation.url,
            layout_id=updated_annotation.layout_id,
            annotations=updated_annotation.annotations,
            type=updated_annotation.type,
            status=updated_annotation.status,
            notes=updated_annotation.notes,
            is_shared=updated_annotation.is_shared,
            shared_at=updated_annotation.shared_at,
            created_at=updated_annotation.created_at,
            updated_at=updated_annotation.updated_at
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{annotation_id}", summary="删除标注")
async def delete_annotation(
    annotation_id: int,
    user_id: str = Depends(get_current_user_id)
):
    """
    删除标注
    
    - **annotation_id**: 标注ID
    
    注意：只能删除当前用户的标注
    """
    try:
        # 验证和删除数据
        success = await annotation_db.delete_annotation(annotation_id, user_id)
        
        if not success:
            raise HTTPException(status_code=404, detail="标注不存在或无权限删除")
        
        return {"message": "标注删除成功"}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{annotation_id}/share", summary="分享标注到公共库")
async def share_annotation(
    annotation_id: int,
    share_request: AnnotationShareRequest,
    user_id: str = Depends(get_current_user_id)
):
    """
    将标注分享到公共特征库
    
    - **annotation_id**: 标注ID
    - **notes**: 分享备注
    
    注意：只能分享当前用户的标注
    """
    try:
        # 获取标注
        annotation = await annotation_db.get_annotation(annotation_id)
        if not annotation:
            raise HTTPException(status_code=404, detail="标注不存在")
        
        # 检查用户权限
        if annotation.user_id != user_id:
            raise HTTPException(status_code=403, detail="无权限分享此标注")
        
        if annotation.is_shared:
            raise HTTPException(status_code=400, detail="标注已经分享过")
        
        # 标记为已分享
        success = await annotation_db.mark_as_shared(annotation_id, user_id, share_request.notes)
        
        if not success:
            raise HTTPException(status_code=500, detail="分享失败")
        
        return {"message": "标注分享成功"}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stats", response_model=AnnotationStats, summary="获取标注统计")
async def get_annotation_stats(user_id: str = Depends(get_current_user_id)):
    """
    获取当前用户的标注统计信息
    
    - 总数、各状态数量、各类型数量
    """
    try:
        stats = await annotation_db.get_stats(user_id)
        return stats
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) 