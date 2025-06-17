import gzip
import hashlib
from typing import Optional, BinaryIO
import boto3
from botocore.exceptions import ClientError
from ..core.config import settings

class MockS3:
    """模拟S3实例，用于开发环境"""
    def __init__(self):
        self._data = {}
    
    def put_object(self, Bucket, Key, Body, **kwargs):
        self._data[Key] = Body
        return True
    
    def get_object(self, Bucket, Key):
        if Key in self._data:
            # 创建一个模拟的response对象
            data = self._data[Key]
            class MockResponse:
                def read(self):
                    return data
            
            return {'Body': MockResponse()}
        else:
            from botocore.exceptions import ClientError
            raise ClientError({'Error': {'Code': 'NoSuchKey'}}, 'GetObject')
    
    def delete_object(self, Bucket, Key):
        self._data.pop(Key, None)
        return True

class S3Manager:
    def __init__(self):
        try:
            self._s3 = boto3.client(
                's3',
                region_name=settings.S3_REGION,
                aws_access_key_id=settings.S3_ACCESS_KEY,
                aws_secret_access_key=settings.S3_SECRET_KEY
            )
            self._bucket = settings.S3_BUCKET
            # 测试S3连接
            if settings.S3_ACCESS_KEY and settings.S3_SECRET_KEY:
                try:
                    self._s3.head_bucket(Bucket=self._bucket)
                    print("✅ S3连接成功")
                except:
                    print("⚠️  S3连接失败，使用模拟S3")
                    self._s3 = MockS3()
            else:
                print("🚧 未配置S3凭据，使用模拟S3")
                self._s3 = MockS3()
        except Exception as e:
            print(f"❌ S3初始化失败: {e}")
            print("🚧 使用模拟S3实例（仅用于开发）")
            self._s3 = MockS3()
            self._bucket = settings.S3_BUCKET

    def _get_html_path(self, domain: str, layout_id: str) -> str:
        """生成S3存储路径"""
        domain_hash = hashlib.md5(domain.encode()).hexdigest()
        layout_hash = hashlib.md5(layout_id.encode()).hexdigest()
        return f"html/{domain_hash[:2]}/{domain_hash[2:4]}/{domain_hash}/{layout_hash}.gz"

    async def save_html(self, domain: str, layout_id: str, html_content: str) -> str:
        """保存HTML内容到S3，返回S3路径"""
        try:
            # 压缩HTML内容
            compressed_content = gzip.compress(html_content.encode())
            
            # 生成S3路径
            s3_path = self._get_html_path(domain, layout_id)
            
            # 上传到S3
            self._s3.put_object(
                Bucket=self._bucket,
                Key=s3_path,
                Body=compressed_content,
                ContentType='application/gzip',
                ContentEncoding='gzip'
            )
            
            return s3_path
        except ClientError as e:
            raise Exception(f"Failed to save HTML to S3: {e}")

    async def get_html(self, s3_path: str) -> Optional[str]:
        """从S3获取HTML内容"""
        try:
            response = self._s3.get_object(
                Bucket=self._bucket,
                Key=s3_path
            )
            
            # 解压内容
            compressed_content = response['Body'].read()
            html_content = gzip.decompress(compressed_content).decode()
            
            return html_content
        except ClientError as e:
            if e.response['Error']['Code'] == 'NoSuchKey':
                return None
            raise Exception(f"Failed to get HTML from S3: {e}")

    async def delete_html(self, s3_path: str) -> bool:
        """从S3删除HTML内容"""
        try:
            self._s3.delete_object(
                Bucket=self._bucket,
                Key=s3_path
            )
            return True
        except ClientError as e:
            raise Exception(f"Failed to delete HTML from S3: {e}")

s3_manager = S3Manager() 