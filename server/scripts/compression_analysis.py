import json
import zlib
import time
from typing import Dict, Any

def create_sample_layouts_data(num_layouts: int = 50, max_item_id: int = 100) -> Dict[str, Any]:
    """创建模拟的layouts数据"""
    layouts = {}
    
    for i in range(num_layouts):
        layout_id = f"example.com_{i:02d}"
        
        # 创建llm_prediction数据（模拟真实场景）
        llm_prediction = {}
        for item_id in range(1, max_item_id + 1):
            llm_prediction[str(item_id)] = "main" if item_id % 3 == 0 else "other"
        
        layouts[layout_id] = {
            "layout_id": layout_id,
            "llm_prediction": llm_prediction,
            "html_path": f"s3://bucket/path/to/{layout_id}.gz",
            "timestamp": 1674767988 + i
        }
    
    return layouts

def compress_data(data: Dict[str, Any]) -> str:
    """压缩数据"""
    json_str = json.dumps(data, ensure_ascii=False)
    compressed = zlib.compress(json_str.encode())
    return compressed.hex()

def decompress_data(compressed_hex: str) -> Dict[str, Any]:
    """解压数据"""
    compressed = bytes.fromhex(compressed_hex)
    json_str = zlib.decompress(compressed).decode()
    return json.loads(json_str)

def analyze_compression():
    """分析压缩效果和性能"""
    print("=== Redis Layouts压缩分析 ===\n")
    
    # 测试不同数据量
    test_cases = [
        (10, 50),   # 10个layouts，每个50个predictions
        (50, 100),  # 50个layouts，每个100个predictions
        (100, 200), # 100个layouts，每个200个predictions
    ]
    
    for num_layouts, max_item_id in test_cases:
        print(f"测试场景: {num_layouts}个layouts，每个{max_item_id}个predictions")
        
        # 1. 创建测试数据
        layouts_data = create_sample_layouts_data(num_layouts, max_item_id)
        
        # 2. 原始数据大小
        json_str = json.dumps(layouts_data, ensure_ascii=False)
        original_size = len(json_str.encode())
        
        # 3. 压缩性能测试
        start_time = time.time()
        compressed_hex = compress_data(layouts_data)
        compress_time = time.time() - start_time
        
        compressed_size = len(compressed_hex.encode())
        
        # 4. 解压性能测试
        start_time = time.time()
        decompressed_data = decompress_data(compressed_hex)
        decompress_time = time.time() - start_time
        
        # 5. 计算压缩比
        compression_ratio = compressed_size / original_size
        space_saved = (1 - compression_ratio) * 100
        
        print(f"  原始大小:     {original_size:,} 字节 ({original_size/1024:.1f} KB)")
        print(f"  压缩后大小:   {compressed_size:,} 字节 ({compressed_size/1024:.1f} KB)")
        print(f"  压缩比:       {compression_ratio:.3f}")
        print(f"  节省空间:     {space_saved:.1f}%")
        print(f"  压缩耗时:     {compress_time*1000:.2f} ms")
        print(f"  解压耗时:     {decompress_time*1000:.2f} ms")
        print(f"  数据一致性:   {'✓' if layouts_data == decompressed_data else '✗'}")
        print("-" * 50)

def memory_impact_analysis():
    """内存影响分析"""
    print("\n=== 内存影响分析 ===\n")
    
    # 假设参数
    total_domains = 100_000_000  # 1亿个domain
    avg_layouts_per_domain = 50  # 每个domain平均50个layout
    avg_predictions_per_layout = 100  # 每个layout平均100个prediction
    
    # 创建单个domain的数据样本
    sample_data = create_sample_layouts_data(avg_layouts_per_domain, avg_predictions_per_layout)
    
    # 计算单个domain的存储大小
    json_str = json.dumps(sample_data, ensure_ascii=False)
    original_size_per_domain = len(json_str.encode())
    
    compressed_hex = compress_data(sample_data)
    compressed_size_per_domain = len(compressed_hex.encode())
    
    # 计算总内存需求
    total_original_memory = total_domains * original_size_per_domain / (1024**3)  # GB
    total_compressed_memory = total_domains * compressed_size_per_domain / (1024**3)  # GB
    
    memory_saved = total_original_memory - total_compressed_memory
    
    print(f"总domain数量:        {total_domains:,}")
    print(f"每domain平均layouts: {avg_layouts_per_domain}")
    print(f"每layout平均predictions: {avg_predictions_per_layout}")
    print(f"")
    print(f"单domain原始大小:    {original_size_per_domain:,} 字节 ({original_size_per_domain/1024:.1f} KB)")
    print(f"单domain压缩大小:    {compressed_size_per_domain:,} 字节 ({compressed_size_per_domain/1024:.1f} KB)")
    print(f"")
    print(f"总内存需求(原始):    {total_original_memory:.1f} GB")
    print(f"总内存需求(压缩):    {total_compressed_memory:.1f} GB")
    print(f"节省内存:           {memory_saved:.1f} GB")
    print(f"节省比例:           {(memory_saved/total_original_memory)*100:.1f}%")

if __name__ == "__main__":
    analyze_compression()
    memory_impact_analysis() 