import hashlib
import json
import zlib
import time
from typing import Optional, List, Dict, Any
import redis
from redis.cluster import RedisCluster
from redis.exceptions import RedisError
from ..core.config import settings

class MockRedis:
    """模拟Redis实例，用于开发环境"""
    def __init__(self):
        self._data = {}
    
    def hgetall(self, key):
        return self._data.get(key, {})
    
    def hset(self, key, mapping=None, **kwargs):
        if key not in self._data:
            self._data[key] = {}
        if mapping:
            self._data[key].update(mapping)
        if kwargs:
            self._data[key].update(kwargs)
        return True
    
    def hget(self, key, field):
        return self._data.get(key, {}).get(field)
    
    def hdel(self, key, *fields):
        if key in self._data:
            for field in fields:
                self._data[key].pop(field, None)
        return True
    
    def delete(self, key):
        self._data.pop(key, None)
        return True
    
    def ping(self):
        return True

class RedisManager:
    def __init__(self):
        self._cluster: Optional[RedisCluster] = None
        self._init_cluster()
    
    def _init_cluster(self):
        """初始化Redis集群连接"""
        try:
            # 解析Redis节点配置
            startup_nodes = []
            for node in settings.REDIS_CLUSTER_NODES:
                if "://" in node:
                    # 处理完整URL格式
                    parts = node.split("://")[1].split(":")
                    host = parts[0]
                    port = int(parts[1]) if len(parts) > 1 else 6379
                else:
                    # 处理host:port格式
                    parts = node.split(":")
                    host = parts[0]
                    port = int(parts[1]) if len(parts) > 1 else 6379
                
                startup_nodes.append({"host": host, "port": port})
            
            self._cluster = RedisCluster(
                startup_nodes=startup_nodes,
                password=settings.REDIS_PASSWORD,
                decode_responses=True,
                skip_full_coverage_check=True
            )
        except RedisError as e:
            raise Exception(f"Failed to connect to Redis cluster: {e}")
        except Exception as e:
            # 如果Redis集群连接失败，尝试连接单节点Redis（用于开发环境）
            print(f"⚠️  Redis集群连接失败: {e}")
            print("🔄 尝试连接单节点Redis...")
            try:
                import redis
                # 使用第一个节点作为单节点连接
                first_node = startup_nodes[0] if startup_nodes else {"host": "localhost", "port": 6379}
                self._cluster = redis.Redis(
                    host=first_node["host"], 
                    port=first_node["port"], 
                    password=settings.REDIS_PASSWORD,
                    decode_responses=True
                )
                # 测试连接
                self._cluster.ping()
                print("✅ 单节点Redis连接成功")
            except Exception as single_error:
                print(f"❌ 单节点Redis连接也失败: {single_error}")
                # 创建一个模拟的Redis实例用于开发
                self._cluster = MockRedis()
                print("🚧 使用模拟Redis实例（仅用于开发）")

    def _get_domain_hash(self, domain: str) -> str:
        """获取domain的哈希值，用于分片"""
        return hashlib.md5(domain.encode()).hexdigest()

    def _extract_domain_from_layout_id(self, layout_id: str) -> str:
        """从layout_id中提取domain"""
        # 假设layout_id格式为: {domain}_{suffix}
        # 例如: "01-news.ru_01" -> "01-news.ru"
        parts = layout_id.rsplit('_', 1)  # 从右边分割一次
        return parts[0] if len(parts) >= 2 else layout_id

    def _compress_layouts(self, layouts: Dict[str, Any]):
        """压缩layouts数据"""
        # 如果使用MockRedis，直接返回字典
        if isinstance(self._cluster, MockRedis):
            return layouts
        
        # 否则进行压缩
        json_str = json.dumps(layouts, ensure_ascii=False)
        compressed = zlib.compress(json_str.encode())
        return compressed.hex()

    def _decompress_layouts(self, compressed_data) -> Dict[str, Any]:
        """解压layouts数据"""
        if isinstance(compressed_data, dict):
            # 如果已经是字典格式（比如来自MockRedis），直接返回
            return compressed_data
        if isinstance(compressed_data, str):
            try:
                # 尝试解压缩
                compressed = bytes.fromhex(compressed_data)
                json_str = zlib.decompress(compressed).decode()
                return json.loads(json_str)
            except:
                # 如果解压缩失败，尝试直接解析JSON
                try:
                    return json.loads(compressed_data)
                except:
                    return {}
        return {}

    async def get_domain_info(self, domain: str) -> Optional[Dict[str, Any]]:
        """获取domain的完整信息"""
        try:
            domain_hash = self._get_domain_hash(domain)
            key = f"domain:{domain_hash}"
            data = self._cluster.hgetall(key)
            
            if not data:
                return None
            
            # 解压layouts数据
            if 'layouts' in data:
                data['layouts'] = self._decompress_layouts(data['layouts'])
            
            return data
        except RedisError as e:
            raise Exception(f"Failed to get domain info: {e}")

    async def get_layout_info(self, layout_id: str) -> Optional[Dict[str, Any]]:
        """通过layout_id获取layout信息"""
        try:
            # 1. 从layout_id中提取domain
            domain = self._extract_domain_from_layout_id(layout_id)
            
            # 2. 获取domain的完整信息
            domain_info = await self.get_domain_info(domain)
            if not domain_info or 'layouts' not in domain_info:
                return None
            
            # 3. 返回指定的layout信息
            layouts = domain_info['layouts']
            return layouts.get(layout_id)
        except RedisError as e:
            raise Exception(f"Failed to get layout info: {e}")

    async def get_domain_layouts(self, domain: str) -> List[Dict[str, Any]]:
        """获取domain下的所有layout信息"""
        try:
            domain_info = await self.get_domain_info(domain)
            if not domain_info or 'layouts' not in domain_info:
                return []
            
            return list(domain_info['layouts'].values())
        except RedisError as e:
            raise Exception(f"Failed to get domain layouts: {e}")

    async def save_domain_info(self, domain: str, layouts: List[Dict[str, Any]]) -> bool:
        """保存domain的完整信息"""
        try:
            domain_hash = self._get_domain_hash(domain)
            key = f"domain:{domain_hash}"
            
            # 构建layouts字典
            layouts_dict = {layout['layout_id']: layout for layout in layouts}
            
            # 保存domain信息
            domain_data = {
                'domain': domain,
                'last_updated': str(int(time.time())),
                'layout_count': str(len(layouts)),
                'layouts': self._compress_layouts(layouts_dict)
            }
            
            # 保存到Redis
            result = self._cluster.hset(key, mapping=domain_data)
            
            return bool(result)
        except RedisError as e:
            raise Exception(f"Failed to save domain info: {e}")

    async def delete_domain_info(self, domain: str) -> bool:
        """删除domain信息"""
        try:
            domain_hash = self._get_domain_hash(domain)
            key = f"domain:{domain_hash}"
            return bool(self._cluster.delete(key))
        except RedisError as e:
            raise Exception(f"Failed to delete domain info: {e}")

redis_manager = RedisManager() 