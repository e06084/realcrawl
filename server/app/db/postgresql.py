"""
PostgreSQL数据库访问层
管理标注数据的CRUD操作
"""

import asyncpg
import json
from typing import Optional, List, Dict, Any
from datetime import datetime
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '../../../'))
from config.settings import settings
from ..models.annotation import (
    AnnotationCreate,
    AnnotationUpdate,
    AnnotationInDB,
    AnnotationSearchRequest,
    AnnotationSearchResponse,
    AnnotationListItem,
    AnnotationStats,
    AnnotationType,
    AnnotationStatus
)


class PostgreSQLManager:
    """PostgreSQL数据库管理器"""
    
    def __init__(self):
        self._pool: Optional[asyncpg.Pool] = None
    
    async def init_pool(self):
        """初始化连接池"""
        if not self._pool:
            self._pool = await asyncpg.create_pool(
                settings.async_database_url,
                min_size=1,
                max_size=settings.POSTGRES_POOL_SIZE,
                command_timeout=60
            )
    
    async def close_pool(self):
        """关闭连接池"""
        if self._pool:
            await self._pool.close()
            self._pool = None
    
    async def create_tables(self):
        """创建数据库表"""
        create_sql = """
        -- 创建枚举类型
        DO $$ BEGIN
            CREATE TYPE annotation_type_enum AS ENUM ('manual', 'imported', 'generated');
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
        
        DO $$ BEGIN
            CREATE TYPE annotation_status_enum AS ENUM ('draft', 'completed', 'shared');
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
        
        -- 创建标注表
        CREATE TABLE IF NOT EXISTS annotations (
            id SERIAL PRIMARY KEY,
            domain VARCHAR(255) NOT NULL,
            layout_id VARCHAR(255) NOT NULL,
            html_content TEXT NOT NULL,
            annotations JSONB NOT NULL,
            type annotation_type_enum NOT NULL DEFAULT 'manual',
            status annotation_status_enum NOT NULL DEFAULT 'draft',
            notes TEXT,
            is_shared BOOLEAN NOT NULL DEFAULT FALSE,
            shared_at TIMESTAMP WITH TIME ZONE,
            created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
            updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
        );
        
        -- 创建索引
        CREATE INDEX IF NOT EXISTS idx_annotations_domain ON annotations(domain);
        CREATE INDEX IF NOT EXISTS idx_annotations_layout_id ON annotations(layout_id);
        CREATE INDEX IF NOT EXISTS idx_annotations_type ON annotations(type);
        CREATE INDEX IF NOT EXISTS idx_annotations_status ON annotations(status);
        CREATE INDEX IF NOT EXISTS idx_annotations_is_shared ON annotations(is_shared);
        CREATE INDEX IF NOT EXISTS idx_annotations_created_at ON annotations(created_at);
        CREATE INDEX IF NOT EXISTS idx_annotations_data ON annotations USING GIN (annotations);
        
        -- 创建全文搜索索引
        CREATE INDEX IF NOT EXISTS idx_annotations_search ON annotations 
        USING GIN (to_tsvector('english', domain || ' ' || layout_id || ' ' || COALESCE(notes, '')));
        
        -- 创建更新时间触发器函数
        CREATE OR REPLACE FUNCTION update_updated_at_column()
        RETURNS TRIGGER AS $$
        BEGIN
            NEW.updated_at = NOW();
            RETURN NEW;
        END;
        $$ language 'plpgsql';
        
        -- 创建触发器
        DROP TRIGGER IF EXISTS update_annotations_updated_at ON annotations;
        CREATE TRIGGER update_annotations_updated_at
            BEFORE UPDATE ON annotations
            FOR EACH ROW
            EXECUTE FUNCTION update_updated_at_column();
        """
        
        await self.init_pool()
        async with self._pool.acquire() as conn:
            await conn.execute(create_sql)
    
    async def create_annotation(self, annotation_data: AnnotationCreate) -> AnnotationInDB:
        """创建新标注"""
        await self.init_pool()
        
        insert_sql = """
        INSERT INTO annotations (domain, layout_id, html_content, annotations, type, notes)
        VALUES ($1, $2, $3, $4, $5, $6)
        RETURNING id, domain, layout_id, html_content, annotations, type, status, 
                  notes, is_shared, shared_at, created_at, updated_at
        """
        
        async with self._pool.acquire() as conn:
            row = await conn.fetchrow(
                insert_sql,
                annotation_data.domain,
                annotation_data.layout_id,
                annotation_data.html_content,
                json.dumps(annotation_data.annotations),
                annotation_data.type.value,
                annotation_data.notes
            )
            
            return AnnotationInDB(
                id=row['id'],
                domain=row['domain'],
                layout_id=row['layout_id'],
                html_content=row['html_content'],
                annotations=row['annotations'],
                type=AnnotationType(row['type']),
                status=AnnotationStatus(row['status']),
                notes=row['notes'],
                is_shared=row['is_shared'],
                shared_at=row['shared_at'],
                created_at=row['created_at'],
                updated_at=row['updated_at']
            )
    
    async def get_annotation(self, annotation_id: int) -> Optional[AnnotationInDB]:
        """根据ID获取标注"""
        await self.init_pool()
        
        select_sql = """
        SELECT id, domain, layout_id, html_content, annotations, type, status,
               notes, is_shared, shared_at, created_at, updated_at
        FROM annotations
        WHERE id = $1
        """
        
        async with self._pool.acquire() as conn:
            row = await conn.fetchrow(select_sql, annotation_id)
            
            if not row:
                return None
            
            return AnnotationInDB(
                id=row['id'],
                domain=row['domain'],
                layout_id=row['layout_id'],
                html_content=row['html_content'],
                annotations=row['annotations'],
                type=AnnotationType(row['type']),
                status=AnnotationStatus(row['status']),
                notes=row['notes'],
                is_shared=row['is_shared'],
                shared_at=row['shared_at'],
                created_at=row['created_at'],
                updated_at=row['updated_at']
            )
    
    async def update_annotation(self, annotation_id: int, update_data: AnnotationUpdate) -> Optional[AnnotationInDB]:
        """更新标注"""
        await self.init_pool()
        
        # 构建动态更新SQL
        update_fields = []
        values = []
        param_count = 1
        
        if update_data.domain is not None:
            update_fields.append(f"domain = ${param_count}")
            values.append(update_data.domain)
            param_count += 1
        
        if update_data.layout_id is not None:
            update_fields.append(f"layout_id = ${param_count}")
            values.append(update_data.layout_id)
            param_count += 1
        
        if update_data.html_content is not None:
            update_fields.append(f"html_content = ${param_count}")
            values.append(update_data.html_content)
            param_count += 1
        
        if update_data.annotations is not None:
            update_fields.append(f"annotations = ${param_count}")
            values.append(json.dumps(update_data.annotations))
            param_count += 1
        
        if update_data.notes is not None:
            update_fields.append(f"notes = ${param_count}")
            values.append(update_data.notes)
            param_count += 1
        
        if update_data.status is not None:
            update_fields.append(f"status = ${param_count}")
            values.append(update_data.status.value)
            param_count += 1
        
        if not update_fields:
            # 没有字段需要更新，返回原数据
            return await self.get_annotation(annotation_id)
        
        values.append(annotation_id)
        
        update_sql = f"""
        UPDATE annotations 
        SET {', '.join(update_fields)}
        WHERE id = ${param_count}
        RETURNING id, domain, layout_id, html_content, annotations, type, status,
                  notes, is_shared, shared_at, created_at, updated_at
        """
        
        async with self._pool.acquire() as conn:
            row = await conn.fetchrow(update_sql, *values)
            
            if not row:
                return None
            
            return AnnotationInDB(
                id=row['id'],
                domain=row['domain'],
                layout_id=row['layout_id'],
                html_content=row['html_content'],
                annotations=row['annotations'],
                type=AnnotationType(row['type']),
                status=AnnotationStatus(row['status']),
                notes=row['notes'],
                is_shared=row['is_shared'],
                shared_at=row['shared_at'],
                created_at=row['created_at'],
                updated_at=row['updated_at']
            )
    
    async def delete_annotation(self, annotation_id: int) -> bool:
        """删除标注"""
        await self.init_pool()
        
        delete_sql = "DELETE FROM annotations WHERE id = $1"
        
        async with self._pool.acquire() as conn:
            result = await conn.execute(delete_sql, annotation_id)
            return result == "DELETE 1"
    
    async def search_annotations(self, search_request: AnnotationSearchRequest) -> AnnotationSearchResponse:
        """搜索标注"""
        await self.init_pool()
        
        # 构建WHERE条件
        where_conditions = []
        values = []
        param_count = 1
        
        if search_request.query:
            where_conditions.append(f"""
                to_tsvector('english', domain || ' ' || layout_id || ' ' || COALESCE(notes, '')) 
                @@ plainto_tsquery('english', ${param_count})
            """)
            values.append(search_request.query)
            param_count += 1
        
        if search_request.domain:
            where_conditions.append(f"domain = ${param_count}")
            values.append(search_request.domain)
            param_count += 1
        
        if search_request.type:
            where_conditions.append(f"type = ${param_count}")
            values.append(search_request.type.value)
            param_count += 1
        
        if search_request.status:
            where_conditions.append(f"status = ${param_count}")
            values.append(search_request.status.value)
            param_count += 1
        
        if search_request.is_shared is not None:
            where_conditions.append(f"is_shared = ${param_count}")
            values.append(search_request.is_shared)
            param_count += 1
        
        where_clause = "WHERE " + " AND ".join(where_conditions) if where_conditions else ""
        
        # 计算总数
        count_sql = f"SELECT COUNT(*) FROM annotations {where_clause}"
        
        # 查询数据
        offset = (search_request.page - 1) * search_request.size
        select_sql = f"""
        SELECT id, domain, layout_id, type, status, is_shared, created_at, updated_at
        FROM annotations 
        {where_clause}
        ORDER BY created_at DESC
        LIMIT ${param_count} OFFSET ${param_count + 1}
        """
        values.extend([search_request.size, offset])
        
        async with self._pool.acquire() as conn:
            # 获取总数
            total = await conn.fetchval(count_sql, *values[:-2])
            
            # 获取数据
            rows = await conn.fetch(select_sql, *values)
            
            items = [
                AnnotationListItem(
                    id=row['id'],
                    domain=row['domain'],
                    layout_id=row['layout_id'],
                    type=AnnotationType(row['type']),
                    status=AnnotationStatus(row['status']),
                    is_shared=row['is_shared'],
                    created_at=row['created_at'],
                    updated_at=row['updated_at']
                )
                for row in rows
            ]
            
            pages = (total + search_request.size - 1) // search_request.size
            
            return AnnotationSearchResponse(
                items=items,
                total=total,
                page=search_request.page,
                size=search_request.size,
                pages=pages
            )
    
    async def mark_as_shared(self, annotation_id: int, notes: Optional[str] = None) -> bool:
        """标记为已分享"""
        await self.init_pool()
        
        update_sql = """
        UPDATE annotations 
        SET is_shared = TRUE, shared_at = NOW(), status = 'shared'
        WHERE id = $1 AND is_shared = FALSE
        """
        
        async with self._pool.acquire() as conn:
            result = await conn.execute(update_sql, annotation_id)
            return result == "UPDATE 1"
    
    async def get_stats(self) -> AnnotationStats:
        """获取标注统计"""
        await self.init_pool()
        
        stats_sql = """
        SELECT 
            COUNT(*) as total,
            COUNT(CASE WHEN status = 'draft' THEN 1 END) as draft,
            COUNT(CASE WHEN status = 'completed' THEN 1 END) as completed,
            COUNT(CASE WHEN is_shared = TRUE THEN 1 END) as shared,
            COUNT(CASE WHEN type = 'manual' THEN 1 END) as manual,
            COUNT(CASE WHEN type = 'imported' THEN 1 END) as imported,
            COUNT(CASE WHEN type = 'generated' THEN 1 END) as generated
        FROM annotations
        """
        
        async with self._pool.acquire() as conn:
            row = await conn.fetchrow(stats_sql)
            
            return AnnotationStats(
                total=row['total'],
                draft=row['draft'],
                completed=row['completed'],
                shared=row['shared'],
                by_type={
                    "manual": row['manual'],
                    "imported": row['imported'],
                    "generated": row['generated']
                }
            )


# 全局数据库管理器实例
annotation_db = PostgreSQLManager() 