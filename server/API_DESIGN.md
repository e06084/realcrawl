# RealCrawl API 设计文档

## API 概览

RealCrawl 云端域名特征查询服务提供以下主要功能模块的API：

1. **特征库** - 公共域名特征查询、管理
2. **标注库** - 标注管理、分享、对比

## API端点设计

### 特征库 (/api/v1/domains)

#### GET /{domain}
查询域名特征

**参数**:
- `include_html`: boolean - 是否包含HTML内容

**响应**:
```json
{
    "domain": "example.com",
    "layout_ids": [
        {
            "layout_id": "example.com_01",
            "llm_prediction": {"1": "header", "2": "main"},
            "html_path": "s3://bucket/path/to/file.gz",
            "timestamp": 1640995200
        }
    ]
}
```

#### GET /{domain}/layouts/{layout_id}
查询特定布局

**参数**:
- `include_html`: boolean - 是否包含HTML内容

**响应**:
```json
{
    "layout_id": "example.com_01",
    "llm_prediction": {"1": "header", "2": "main"},
    "html_path": "s3://bucket/path/to/file.gz",
    "timestamp": 1640995200,
    "html_content": "<html>...</html>"
}
```

#### POST /{domain}
创建/更新域名特征

**请求体**:
```json
{
    "domain": "example.com",
    "layouts": [
        {
            "layout_id": "example.com_01",
            "llm_prediction": {"1": "header", "2": "main"},
            "html_content": "<html>...</html>",
            "timestamp": 1640995200
        }
    ]
}
```

**响应**:
```json
{
    "status": "success",
    "message": "Domain example.com saved successfully"
}
```

#### DELETE /{domain}
删除域名特征

**响应**:
```json
{
    "status": "success",
    "message": "Domain example.com deleted successfully"
}
```

---

### 标注库 (/api/v1/annotations)

#### GET /
获取标注列表

**参数**:
- `query`: string - 搜索关键词
- `domain`: string - 域名过滤
- `type`: string - 类型过滤 (manual/imported/generated)
- `status`: string - 状态过滤 (draft/completed/shared)
- `is_shared`: boolean - 是否已分享
- `page`: int - 页码
- `size`: int - 每页大小

**响应**:
```json
{
    "items": [
        {
            "id": 1,
            "domain": "example.com",
            "layout_id": "example.com_01",
            "type": "manual",
            "status": "completed",
            "is_shared": false,
            "created_at": "2024-01-01T00:00:00Z",
            "updated_at": "2024-01-01T12:00:00Z"
        },
        {
            "id": 2,
            "domain": "test.com",
            "layout_id": "test.com_01",
            "type": "imported",
            "status": "draft",
            "is_shared": true,
            "created_at": "2024-01-02T00:00:00Z",
            "updated_at": "2024-01-02T10:00:00Z"
        }
    ],
    "total": 150,
    "page": 1,
    "size": 20,
    "pages": 8
}
```

#### POST /
创建标注

**请求体**:
```json
{
    "domain": "example.com",
    "layout_id": "example.com_01",
    "html_content": "<html>...</html>",
    "annotations": {
        "elements": [
            {"id": "1", "type": "header", "xpath": "//header"},
            {"id": "2", "type": "main", "xpath": "//main"}
        ]
    },
    "type": "manual",
    "notes": "手动标注的示例页面"
}
```

**响应**:
```json
{
    "id": 1,
    "domain": "example.com",
    "layout_id": "example.com_01",
    "annotations": {
        "elements": [
            {"id": "1", "type": "header", "xpath": "//header"},
            {"id": "2", "type": "main", "xpath": "//main"}
        ]
    },
    "type": "manual",
    "status": "draft",
    "notes": "手动标注的示例页面",
    "is_shared": false,
    "created_at": "2024-01-01T00:00:00Z",
    "updated_at": "2024-01-01T00:00:00Z"
}
```

#### GET /{annotation_id}
获取标注详情

**响应**:
```json
{
    "id": 1,
    "domain": "example.com",
    "layout_id": "example.com_01",
    "html_content": "<html>...</html>",
    "annotations": {
        "elements": [
            {"id": "1", "type": "header", "xpath": "//header"},
            {"id": "2", "type": "main", "xpath": "//main"}
        ]
    },
    "type": "manual",
    "status": "completed",
    "notes": "手动标注的示例页面",
    "is_shared": false,
    "created_at": "2024-01-01T00:00:00Z",
    "updated_at": "2024-01-01T12:00:00Z"
}
```

#### PUT /{annotation_id}
更新标注

**请求体**:
```json
{
    "annotations": {
        "elements": [
            {"id": "1", "type": "header", "xpath": "//header"},
            {"id": "2", "type": "main", "xpath": "//main"},
            {"id": "3", "type": "footer", "xpath": "//footer"}
        ]
    },
    "status": "completed",
    "notes": "更新后的标注"
}
```

**响应**:
```json
{
    "id": 1,
    "domain": "example.com",
    "layout_id": "example.com_01",
    "annotations": {
        "elements": [
            {"id": "1", "type": "header", "xpath": "//header"},
            {"id": "2", "type": "main", "xpath": "//main"},
            {"id": "3", "type": "footer", "xpath": "//footer"}
        ]
    },
    "type": "manual",
    "status": "completed",
    "notes": "更新后的标注",
    "is_shared": false,
    "created_at": "2024-01-01T00:00:00Z",
    "updated_at": "2024-01-01T15:00:00Z"
}
```

#### DELETE /{annotation_id}
删除标注

**响应**:
```json
{
    "status": "success",
    "message": "标注删除成功"
}
```

#### POST /{annotation_id}/share
分享标注到公共库

**请求体**:
```json
{
    "notes": "分享给社区使用"
}
```

**响应**:
```json
{
    "status": "success",
    "message": "标注已成功分享到公共库"
}
```

#### POST /compare
与公共库对比

**请求体**:
```json
{
    "annotation_id": 1,
    "domain": "target-domain.com"
}
```

**响应**:
```json
{
    "annotation_id": 1,
    "domain": "target-domain.com",
    "similarity_score": 0.85,
    "differences": [
        {
            "type": "missing_element",
            "xpath": "//nav",
            "description": "目标域名缺少导航元素"
        }
    ],
    "matched_features": ["header", "main", "footer"]
}
```

#### GET /stats
获取标注统计

**响应**:
```json
{
    "total": 150,
    "draft": 25,
    "completed": 100,
    "shared": 25,
    "by_type": {
        "manual": 120,
        "imported": 20,
        "generated": 10
    }
}
```

---

## 错误响应格式

所有API错误响应遵循统一格式：

```json
{
    "error": {
        "code": "VALIDATION_ERROR",
        "message": "请求参数验证失败",
        "details": [
            {
                "field": "domain",
                "message": "域名格式不正确"
            }
        ]
    },
    "timestamp": "2024-01-01T12:00:00Z",
    "request_id": "req_1234567890"
}
```

### 常见错误示例

#### 资源不存在 (404)
```json
{
    "error": {
        "code": "NOT_FOUND",
        "message": "域名特征不存在"
    },
    "timestamp": "2024-01-01T12:00:00Z",
    "request_id": "req_1234567890"
}
```

#### 参数验证失败 (400)
```json
{
    "error": {
        "code": "VALIDATION_ERROR",
        "message": "标注数据验证失败",
        "details": [
            {
                "field": "annotations.elements",
                "message": "至少需要一个标注元素"
            }
        ]
    },
    "timestamp": "2024-01-01T12:00:00Z",
    "request_id": "req_1234567890"
}
```

#### 业务逻辑错误 (409)
```json
{
    "error": {
        "code": "CONFLICT",
        "message": "标注已经分享过，无法重复分享"
    },
    "timestamp": "2024-01-01T12:00:00Z",
    "request_id": "req_1234567890"
}
```

## 状态码说明

- **200**: 成功
- **201**: 创建成功
- **400**: 请求参数错误
- **401**: 未认证
- **403**: 权限不足
- **404**: 资源不存在
- **409**: 资源冲突
- **429**: 请求频率超限
- **500**: 服务器内部错误

## 限流规则

- 每IP每小时最多1000次请求
- 特殊端点（如创建、更新）每IP每分钟最多10次

## 版本控制

API采用URL版本控制：
- 当前版本：`/api/v1/`
- 向后兼容策略：保持至少2个主版本

## API使用示例

### 完整的标注工作流程

1. **创建标注**
```bash
curl -X POST "http://localhost:8000/api/v1/annotations" \
  -H "Content-Type: application/json" \
  -d '{
    "domain": "example.com",
    "layout_id": "example.com_01",
    "html_content": "<html><body><header>Header</header><main>Content</main></body></html>",
    "annotations": {
      "elements": [
        {"id": "1", "type": "header", "xpath": "//header"},
        {"id": "2", "type": "main", "xpath": "//main"}
      ]
    },
    "type": "manual",
    "notes": "示例标注"
  }'
```

2. **更新标注状态**
```bash
curl -X PUT "http://localhost:8000/api/v1/annotations/1" \
  -H "Content-Type: application/json" \
  -d '{
    "status": "completed"
  }'
```

3. **分享到公共库**
```bash
curl -X POST "http://localhost:8000/api/v1/annotations/1/share" \
  -H "Content-Type: application/json" \
  -d '{
    "notes": "分享给社区使用"
  }'
```

4. **查询公共特征**
```bash
curl "http://localhost:8000/api/v1/domains/example.com?include_html=true"
```

### 搜索和过滤

```bash
# 搜索包含"header"的标注
curl "http://localhost:8000/api/v1/annotations?query=header&page=1&size=10"

# 过滤特定域名的已完成标注
curl "http://localhost:8000/api/v1/annotations?domain=example.com&status=completed"

# 获取已分享的标注
curl "http://localhost:8000/api/v1/annotations?is_shared=true"
```

## 扩展功能

计划支持的功能：
- 标注导入/导出
- 批量操作API
- 数据统计分析
- WebSocket实时更新 