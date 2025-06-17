# RealCrawl API 设计文档

## API 概览

RealCrawl 云端域名特征查询服务提供以下主要功能模块的API：

1. **认证模块** - 用户注册、登录、令牌管理
2. **用户管理** - 用户信息、统计数据
3. **API密钥管理** - 密钥创建、管理、使用统计
4. **特征库** - 公共域名特征查询、管理
5. **标注库** - 私有标注管理、分享、对比
6. **监控模块** - 系统监控、使用统计

## 认证机制

### 1. JWT令牌认证
- **用途**: Web控制台用户认证
- **Header**: `Authorization: Bearer <access_token>`
- **过期时间**: 30分钟（可刷新）

### 2. API密钥认证
- **用途**: 程序化API访问
- **Header**: `X-API-Key: rk_<key>`
- **格式**: `rk_` + 43位随机字符

## API端点设计

### 认证模块 (/api/v1/auth)

#### POST /register
用户注册

**请求体**:
```json
{
    "username": "john_doe",
    "email": "john@example.com", 
    "password": "SecurePass123"
}
```

**响应**:
```json
{
    "id": 1,
    "username": "john_doe",
    "email": "john@example.com",
    "role": "user",
    "is_active": true,
    "created_at": "2024-01-01T00:00:00Z"
}
```

#### POST /login
用户登录

**请求体**:
```json
{
    "username": "john_doe",  // 用户名或邮箱
    "password": "SecurePass123"
}
```

**响应**:
```json
{
    "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
    "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
    "token_type": "bearer",
    "expires_in": 1800
}
```

#### POST /refresh
刷新令牌

**Headers**: `Authorization: Bearer <refresh_token>`

#### POST /logout
用户登出

#### GET /me
获取当前用户信息

---

### 用户管理 (/api/v1/users)

#### GET /profile
获取用户详细信息

#### PUT /profile
更新用户信息

**请求体**:
```json
{
    "username": "new_username",
    "email": "newemail@example.com"
}
```

#### GET /stats
用户使用统计

**响应**:
```json
{
    "total_annotations": 150,
    "shared_annotations": 25,
    "api_calls": 1500,
    "last_activity": "2024-01-01T12:00:00Z"
}
```

---

### API密钥管理 (/api/v1/apikeys)

#### GET /
获取API密钥列表

**响应**:
```json
[
    {
        "id": 1,
        "name": "生产环境密钥",
        "permissions": ["read", "write"],
        "rate_limit": 1000,
        "is_active": true,
        "created_at": "2024-01-01T00:00:00Z",
        "last_used": "2024-01-01T12:00:00Z"
    }
]
```

#### POST /
创建API密钥

**请求体**:
```json
{
    "name": "新的API密钥",
    "permissions": ["read"],
    "rate_limit": 500,
    "expires_in_days": 90
}
```

**响应**:
```json
{
    "id": 2,
    "name": "新的API密钥",
    "api_key": "rk_abcdefghijklmnopqrstuvwxyz1234567890123",
    "permissions": ["read"],
    "rate_limit": 500,
    "expires_at": "2024-04-01T00:00:00Z"
}
```

#### PUT /{key_id}
更新API密钥

#### DELETE /{key_id}
删除API密钥

#### GET /{key_id}/stats
API密钥使用统计

**响应**:
```json
{
    "total_requests": 15000,
    "requests_today": 120,
    "requests_this_hour": 15,
    "last_request": "2024-01-01T12:30:00Z",
    "error_rate": 0.02
}
```

---

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

#### POST /{domain}
创建/更新域名特征 (管理员权限)

#### DELETE /{domain}
删除域名特征 (管理员权限)

---

### 标注库 (/api/v1/annotations)

#### GET /
获取我的标注列表

**参数**:
- `query`: string - 搜索关键词
- `domain`: string - 域名过滤
- `type`: string - 类型过滤 (manual/imported/generated)
- `status`: string - 状态过滤 (draft/completed/shared)
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

#### GET /{annotation_id}
获取标注详情

#### PUT /{annotation_id}
更新标注

#### DELETE /{annotation_id}
删除标注

#### POST /{annotation_id}/share
分享标注到公共库

**请求体**:
```json
{
    "notes": "分享给社区使用"
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

---

### 监控模块 (/api/v1/monitoring)

#### GET /stats
系统统计

**响应**:
```json
{
    "total_users": 1500,
    "active_users": 350,
    "total_domains": 50000,
    "total_annotations": 25000,
    "api_calls_today": 15000,
    "system_uptime": 864000
}
```

#### GET /api-usage
API使用情况

**参数**:
- `period`: string - 时间段 (hour/day/week/month)
- `start_date`: string - 开始日期
- `end_date`: string - 结束日期

#### GET /errors
错误统计

#### GET /performance
性能指标

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
                "field": "email",
                "message": "邮箱格式不正确"
            }
        ]
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

### JWT令牌
- 每用户每小时最多1000次请求
- 特殊端点（如登录）每IP每分钟最多5次

### API密钥
- 根据密钥配置的rate_limit限制
- 默认每小时1000次请求

## 版本控制

API采用URL版本控制：
- 当前版本：`/api/v1/`
- 向后兼容策略：保持至少2个主版本

## Webhook支持

计划支持的Webhook事件：
- 用户注册
- 标注分享
- 系统告警
- 限流触发 