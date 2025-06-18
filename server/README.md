# RealCrawl 云端域名特征查询服务

## 项目概述

RealCrawl云端域名特征查询服务专注于核心的数据管理功能，提供：

1. **公共特征库**: 存储和查询海量域名布局特征数据（对应生产过程形成特征库）
2. **HTML标注工具**: 可视化HTML标注界面，支持重标注、检索功能  
3. **标注库**: 标注管理，支持：
   - 标注管理（增删改查）
   - 共享到公共库

## 技术架构

### 核心技术栈
- **Web框架**: FastAPI + React
- **特征库存储**: Redis Cluster (特征库缓存集群)
- **HTML存储**: S3/OSS (HTML内容存储)
- **标注数据**: PostgreSQL (私有标注数据)
- **数据压缩**: zlib压缩优化存储

### 服务架构

```
├── 前端应用层
│   ├── HTML标注工具 (React) - 重标注、我的、对比、检索
│   └── 管理控制台 (React) - 特征库查询管理
├── API服务层 (包含业务逻辑)
│   ├── 特征库API - 公共特征读写和管理逻辑
│   └── 标注库API - 标注管理和对比逻辑
└── 数据存储层
    ├── Redis Cluster (特征库缓存集群)
    ├── S3/OSS (HTML内容存储)
    └── PostgreSQL (标注数据)
```

## 功能模块

### 1. 公共特征库（生产过程形成特征库）
- **特征读取**: 高性能域名特征查询
- **特征写入**: 通过migrate.py脚本从CC/PJCC同步数据
- **数据压缩**: zlib压缩优化存储空间
- **Redis集群**: 支持海量数据分布式存储

### 2. HTML标注工具
- **重标注**: 在线可视化HTML标注界面
- **我的标注**: 个人标注数据管理（增删改查）
- **对比功能**: 与公共库特征智能对比
- **检索功能**: 快速搜索和过滤标注数据

### 3. 标注库管理
- **标注存储**: PostgreSQL存储标注数据
- **共享机制**: 将标注分享到公共特征库
- **对比分析**: 标注与公共库特征的相似度分析
- **版本管理**: 标注历史版本追踪

## 目录结构

### 整体架构分层

```
server/
├── app/                             # 应用后端核心代码
├── frontend/                        # 前端应用
├── docker/                          # 容器化配置
├── scripts/                         # 部署和维护脚本
├── requirements.txt                 # Python依赖
├── docker-compose.yml               # 容器编排配置
└── README.md                        # 项目文档
```

### app/ 应用核心 - 分层架构

```
app/
├── api/                             # API接口层 - HTTP请求处理和业务逻辑
│   ├── v1/                          #     API版本控制
│   │   ├── endpoints/               #     API端点和业务逻辑实现
│   │   │   ├── domain.py            #       特征库API (公共特征读写+业务逻辑)
│   │   │   └── annotations.py       #       标注库API (私有标注管理+业务逻辑)
│   │   └── router.py                #     API路由聚合
│   └── middleware/                  #     中间件层 (预留)
├── config/                          # 配置管理
│   └── settings.py                  #     应用配置 (环境变量/数据库/设置)
├── db/                              # 数据访问层 - 数据库连接和操作
│   ├── redis.py                     #     Redis集群管理 (特征库缓存)
│   ├── postgresql.py                #     PostgreSQL连接 (标注数据)
│   └── s3.py                        #     S3/OSS存储管理 (HTML文件)
├── models/                          # 数据模型层 - Pydantic模型定义
│   ├── domain.py                    #     域名特征模型 (layout/feature)
│   └── annotation.py                #     标注模型 (私有标注/分享)
├── utils/                           # 工具库 - 通用工具函数
│   ├── compression.py               #     压缩工具 (zlib压缩/解压)
│   ├── html_parser.py               #     HTML解析工具 (标注提取)
│   └── validators.py                #     验证工具 (数据校验)
└── main.py                          # 应用入口 - FastAPI应用启动
```

### frontend/ 前端应用

```
frontend/
```

### docker/ 容器化配置

```
docker/
├── Dockerfile                       # 应用容器构建文件
├── nginx.conf                       # Nginx反向代理配置
├── prometheus.yml                   # Prometheus监控配置
└── init-scripts/                    # 初始化脚本
    ├── init-db.sql                  #     PostgreSQL初始化
    └── init-redis.sh                #     Redis集群初始化
```

### scripts/ 数据迁移脚本

```
scripts/
└── migrate.py                       # 数据迁移脚本 (从CC/PJCC同步特征数据)
```

### 层级职责说明

| 层级 | 职责 | 依赖关系 |
|------|------|----------|
| **api/** | HTTP接口处理、业务逻辑、请求验证、响应格式化 | → db → models → utils |
| **db/** | 数据存储访问、连接管理、查询优化 | → config → utils |
| **models/** | 数据结构定义、验证规则、类型约束 | → config |
| **config/** | 配置管理、环境变量、数据库配置 | 无依赖 |
| **utils/** | 通用工具函数、算法实现、格式转换 | → config |

### 数据流向

```
HTTP请求 → api/ → db/ → 数据库
              ↓
           models/ (数据验证)
              ↓
           utils/ (工具处理)
              ↓
           config/ (配置读取)
```

这种分层架构确保了：
- **清晰的职责分离**：每层都有明确的功能边界
- **良好的可测试性**：每层可以独立测试
- **高度的可维护性**：修改某层不影响其他层
- **强大的可扩展性**：可以轻松添加新功能模块

## API设计

### 特征库API（公共特征读写）
- `GET /api/v1/domains/{domain}` - 查询域名特征
- `GET /api/v1/domains/{domain}/layouts/{layout_id}` - 查询特定布局
- `POST /api/v1/domains/{domain}` - 创建/更新域名特征
- `DELETE /api/v1/domains/{domain}` - 删除域名特征

### 标注库API（标注管理）
- `GET /api/v1/annotations` - 获取标注列表（检索功能）
- `POST /api/v1/annotations` - 创建标注（重标注功能）
- `GET /api/v1/annotations/{annotation_id}` - 获取标注详情
- `PUT /api/v1/annotations/{annotation_id}` - 更新标注
- `DELETE /api/v1/annotations/{annotation_id}` - 删除标注
- `POST /api/v1/annotations/{annotation_id}/share` - 分享到公共库
- `POST /api/v1/annotations/compare` - 与公共库对比功能

## 数据模型

### 域名特征模型（存储在Redis）
```python
class DomainFeature:
    domain: str                    # 域名
    layout_ids: List[LayoutInfo]   # 布局信息列表
    last_updated: datetime         # 最后更新时间
    
class LayoutInfo:
    layout_id: str                 # 布局ID
    llm_prediction: Dict           # LLM预测结果
    html_path: str                 # HTML文件在S3/OSS的路径
    timestamp: int                 # 时间戳
```

### 标注模型（存储在PostgreSQL）
```python
class Annotation:
    id: int                        # 标注ID
    domain: str                    # 域名
    url: str                       # 页面URL
    layout_id: str                 # 布局ID
    html_content: str              # HTML内容
    annotations: str               # 标注数据（字符串格式）
    is_shared: bool                # 是否已分享到公共库
    created_at: datetime           # 创建时间
    updated_at: datetime           # 更新时间
```



## 部署说明

### 开发环境
```bash
# 安装依赖
cd server
pip install -r requirements.txt

# 启动后端服务
uvicorn app.main:app --reload --port 8000

# 启动标注工具前端
cd frontend/annotation-tool
npm install && npm start

# 启动特征库控制台
cd frontend/feature-console
npm install && npm start
```

### 生产环境
```bash
# 使用Docker Compose一键部署
docker-compose up -d

# 包含组件：
# - Redis Cluster (特征库缓存集群)
# - PostgreSQL (标注数据存储)
# - MinIO/S3 (HTML内容存储)
# - FastAPI应用服务
# - React前端应用
```

## 数据存储设计

### Redis特征库存储
- **Key格式**: `domain:{domain_hash}`
- **存储内容**: 压缩的layouts JSON数据
- **压缩比**: 90%以上空间节省

### PostgreSQL标注存储
- **表结构**: annotations表存储标注数据
- **索引优化**: domain, created_at复合索引

### S3/OSS HTML存储  
- **路径格式**: `s3://bucket/{domain_hash_id}/{domain}/{layout_id}.html`，如`s3://bucket/1696/01-news.ru/01-news.ru_01.html`
- **压缩**: gzip压缩HTML内容
