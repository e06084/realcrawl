from typing import List, Optional
from fastapi import APIRouter, HTTPException, Query
from ....models.domain import (
    DomainCreateRequest, 
    DomainFeatureResponse, 
    LayoutInfo, 
    LayoutInfoWithHtml
)
from ....db.redis import redis_manager
from ....db.s3 import s3_manager

router = APIRouter()

@router.get("/{domain}", response_model=DomainFeatureResponse)
async def get_domain_features(
    domain: str,
    include_html: bool = Query(False, description="是否包含HTML内容")
):
    """获取指定domain的特征信息"""
    try:
        # 获取domain信息
        domain_info = await redis_manager.get_domain_info(domain)
        if not domain_info:
            raise HTTPException(status_code=404, detail="Domain not found")

        layouts = []
        if 'layouts' in domain_info:
            for layout_id, layout_data in domain_info['layouts'].items():
                if include_html and layout_data.get('html_path'):
                    # 获取HTML内容
                    html_content = await s3_manager.get_html(layout_data['html_path'])
                    layout_with_html = LayoutInfoWithHtml(
                        layout_id=layout_data['layout_id'],
                        llm_prediction=layout_data['llm_prediction'],
                        timestamp=layout_data['timestamp'],
                        html_path=layout_data.get('html_path'),
                        html_content=html_content
                    )
                    layouts.append(layout_with_html)
                else:
                    layout_info = LayoutInfo(
                        layout_id=layout_data['layout_id'],
                        llm_prediction=layout_data['llm_prediction'],
                        timestamp=layout_data['timestamp'],
                        html_path=layout_data.get('html_path')
                    )
                    layouts.append(layout_info)

        return DomainFeatureResponse(
            domain=domain,
            layout_ids=layouts,
            total_layouts=len(layouts),
            last_updated=int(domain_info.get('last_updated', 0))
        )
    except Exception as e:
        import traceback
        print(f"Error in get_domain_features: {str(e)}")
        print(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/{domain}")
async def create_domain_features(domain: str, request: DomainCreateRequest):
    """创建或更新domain特征信息"""
    try:
        layouts_data = []
        
        # 处理每个layout的信息
        for layout in request.layouts:
            # 保存HTML到S3
            html_path = await s3_manager.save_html(
                domain,
                layout.layout_id,
                layout.html_content or ""
            )

            # 构建layout数据
            layout_data = {
                'layout_id': layout.layout_id,
                'llm_prediction': layout.llm_prediction,
                'html_path': html_path,
                'timestamp': layout.timestamp
            }
            layouts_data.append(layout_data)

        # 保存到Redis
        success = await redis_manager.save_domain_info(domain, layouts_data)
        
        if success:
            return {"status": "success", "message": f"Domain {domain} saved successfully"}
        else:
            raise HTTPException(status_code=500, detail="Failed to save domain")
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{domain}/layouts/{layout_id}", response_model=LayoutInfoWithHtml)
async def get_layout_info(
    domain: str,
    layout_id: str,
    include_html: bool = Query(True, description="是否包含HTML内容")
):
    """获取指定layout的详细信息"""
    try:
        layout_info = await redis_manager.get_layout_info(layout_id)
        if not layout_info:
            raise HTTPException(status_code=404, detail="Layout not found")

        # 构建返回数据
        result = LayoutInfoWithHtml(
            layout_id=layout_info['layout_id'],
            llm_prediction=layout_info['llm_prediction'],
            timestamp=layout_info['timestamp'],
            html_path=layout_info.get('html_path')
        )
        
        # 如果需要包含HTML内容
        if include_html and layout_info.get('html_path'):
            html_content = await s3_manager.get_html(layout_info['html_path'])
            result.html_content = html_content

        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/{domain}")
async def delete_domain_features(domain: str):
    """删除domain特征信息"""
    try:
        # 获取domain信息
        domain_info = await redis_manager.get_domain_info(domain)
        if not domain_info:
            raise HTTPException(status_code=404, detail="Domain not found")
        
        # 删除S3中的HTML文件
        if 'layouts' in domain_info:
            for layout_id, layout_data in domain_info['layouts'].items():
                if layout_data.get('html_path'):
                    await s3_manager.delete_html(layout_data['html_path'])

        # 删除Redis中的数据
        success = await redis_manager.delete_domain_info(domain)
        
        if success:
            return {"status": "success", "message": f"Domain {domain} deleted successfully"}
        else:
            raise HTTPException(status_code=500, detail="Failed to delete domain")
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/")
async def list_domains(
    limit: int = Query(100, ge=1, le=1000, description="返回结果数量限制"),
    offset: int = Query(0, ge=0, description="偏移量")
):
    """获取domain列表（示例接口，实际需要根据Redis实现）"""
    # 注意：由于Redis Cluster的限制，这个接口在生产环境中需要特殊实现
    # 可以考虑维护一个单独的domain列表或使用其他方式
    return {
        "message": "此接口需要根据具体需求实现",
        "suggestion": "建议使用具体的domain名称进行查询"
    } 