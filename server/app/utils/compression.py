"""
数据压缩工具模块
用于zlib压缩/解压功能
"""

import zlib
import json
from typing import Any, Union, Dict
from ..config.settings import settings


class CompressionError(Exception):
    """压缩相关异常"""
    pass


class CompressionUtils:
    """压缩工具类"""
    
    @staticmethod
    def compress_json(data: Dict[str, Any], level: int = None) -> str:
        """
        压缩JSON数据
        
        Args:
            data: 要压缩的字典数据
            level: 压缩级别(1-9)，默认使用配置值
            
        Returns:
            压缩后的十六进制字符串
            
        Raises:
            CompressionError: 压缩失败时抛出
        """
        try:
            if level is None:
                level = settings.COMPRESSION_LEVEL
                
            # 序列化为JSON字符串
            json_str = json.dumps(data, ensure_ascii=False, separators=(',', ':'))
            
            # 压缩数据
            compressed = zlib.compress(json_str.encode('utf-8'), level)
            
            # 转换为十六进制字符串
            return compressed.hex()
            
        except Exception as e:
            raise CompressionError(f"压缩数据失败: {str(e)}")
    
    @staticmethod
    def decompress_json(compressed_hex: Union[str, Dict]) -> Dict[str, Any]:
        """
        解压JSON数据
        
        Args:
            compressed_hex: 压缩的十六进制字符串或已解压的字典
            
        Returns:
            解压后的字典数据
            
        Raises:
            CompressionError: 解压失败时抛出
        """
        try:
            # 如果已经是字典，直接返回
            if isinstance(compressed_hex, dict):
                return compressed_hex
                
            # 如果是字符串但不是十六进制格式，尝试直接解析JSON
            if isinstance(compressed_hex, str):
                try:
                    # 尝试直接解析JSON（兼容未压缩的历史数据）
                    return json.loads(compressed_hex)
                except json.JSONDecodeError:
                    # 如果不是JSON，继续十六进制解压流程
                    pass
            
            # 从十六进制字符串转换为字节
            compressed = bytes.fromhex(compressed_hex)
            
            # 解压数据
            decompressed = zlib.decompress(compressed)
            
            # 解析JSON
            return json.loads(decompressed.decode('utf-8'))
            
        except Exception as e:
            raise CompressionError(f"解压数据失败: {str(e)}")
    
    @staticmethod
    def compress_text(text: str, level: int = None) -> str:
        """
        压缩文本数据
        
        Args:
            text: 要压缩的文本
            level: 压缩级别(1-9)，默认使用配置值
            
        Returns:
            压缩后的十六进制字符串
        """
        try:
            if level is None:
                level = settings.COMPRESSION_LEVEL
                
            compressed = zlib.compress(text.encode('utf-8'), level)
            return compressed.hex()
            
        except Exception as e:
            raise CompressionError(f"压缩文本失败: {str(e)}")
    
    @staticmethod
    def decompress_text(compressed_hex: str) -> str:
        """
        解压文本数据
        
        Args:
            compressed_hex: 压缩的十六进制字符串
            
        Returns:
            解压后的文本
        """
        try:
            compressed = bytes.fromhex(compressed_hex)
            decompressed = zlib.decompress(compressed)
            return decompressed.decode('utf-8')
            
        except Exception as e:
            raise CompressionError(f"解压文本失败: {str(e)}")
    
    @staticmethod
    def get_compression_ratio(original_data: str, compressed_hex: str) -> float:
        """
        计算压缩比
        
        Args:
            original_data: 原始数据
            compressed_hex: 压缩后的十六进制字符串
            
        Returns:
            压缩比（0-1之间，越小表示压缩效果越好）
        """
        try:
            original_size = len(original_data.encode('utf-8'))
            compressed_size = len(bytes.fromhex(compressed_hex))
            
            if original_size == 0:
                return 0.0
                
            return compressed_size / original_size
            
        except Exception:
            return 1.0  # 如果计算失败，返回1.0表示无压缩


# 全局压缩工具实例
compression_utils = CompressionUtils() 