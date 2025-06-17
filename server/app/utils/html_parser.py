"""
HTML解析工具模块
用于解析HTML内容和提取标注信息
"""

import re
from typing import Dict, List, Any, Optional, Tuple
from bs4 import BeautifulSoup, Tag
import hashlib


class HTMLParseError(Exception):
    """HTML解析异常"""
    pass


class HTMLParser:
    """HTML解析工具类"""
    
    @staticmethod
    def parse_html(html_content: str) -> BeautifulSoup:
        """
        解析HTML内容
        
        Args:
            html_content: HTML内容字符串
            
        Returns:
            BeautifulSoup对象
            
        Raises:
            HTMLParseError: 解析失败时抛出
        """
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            return soup
        except Exception as e:
            raise HTMLParseError(f"HTML解析失败: {str(e)}")
    
    @staticmethod
    def extract_text_content(html_content: str) -> str:
        """
        提取HTML中的纯文本内容
        
        Args:
            html_content: HTML内容
            
        Returns:
            纯文本内容
        """
        try:
            soup = HTMLParser.parse_html(html_content)
            return soup.get_text(separator=' ', strip=True)
        except Exception:
            return ""
    
    @staticmethod
    def extract_elements_by_tag(html_content: str, tag_name: str) -> List[Dict[str, Any]]:
        """
        根据标签名提取元素
        
        Args:
            html_content: HTML内容
            tag_name: 标签名
            
        Returns:
            元素信息列表
        """
        try:
            soup = HTMLParser.parse_html(html_content)
            elements = []
            
            for i, element in enumerate(soup.find_all(tag_name)):
                element_info = {
                    'index': i,
                    'tag': tag_name,
                    'text': element.get_text(strip=True),
                    'attributes': dict(element.attrs),
                    'xpath': HTMLParser._generate_xpath(element)
                }
                elements.append(element_info)
                
            return elements
        except Exception as e:
            raise HTMLParseError(f"提取{tag_name}元素失败: {str(e)}")
    
    @staticmethod
    def extract_layout_features(html_content: str) -> Dict[str, Any]:
        """
        提取HTML布局特征
        
        Args:
            html_content: HTML内容
            
        Returns:
            布局特征字典
        """
        try:
            soup = HTMLParser.parse_html(html_content)
            
            features = {
                'page_info': {
                    'title': soup.title.string if soup.title else "",
                    'total_elements': len(soup.find_all()),
                    'text_length': len(HTMLParser.extract_text_content(html_content))
                },
                'structure': {
                    'header': HTMLParser._extract_semantic_elements(soup, ['header', 'h1', 'h2', 'h3']),
                    'navigation': HTMLParser._extract_semantic_elements(soup, ['nav', 'menu']),
                    'main': HTMLParser._extract_semantic_elements(soup, ['main', 'article', 'section']),
                    'sidebar': HTMLParser._extract_semantic_elements(soup, ['aside', 'sidebar']),
                    'footer': HTMLParser._extract_semantic_elements(soup, ['footer'])
                },
                'forms': HTMLParser._extract_forms(soup),
                'media': HTMLParser._extract_media(soup),
                'links': HTMLParser._extract_links(soup)
            }
            
            return features
        except Exception as e:
            raise HTMLParseError(f"提取布局特征失败: {str(e)}")
    
    @staticmethod
    def validate_annotations(html_content: str, annotations: Dict[str, Any]) -> Dict[str, Any]:
        """
        验证标注数据的有效性
        
        Args:
            html_content: HTML内容
            annotations: 标注数据
            
        Returns:
            验证结果
        """
        try:
            soup = HTMLParser.parse_html(html_content)
            result = {
                'valid': True,
                'errors': [],
                'warnings': []
            }
            
            # 验证标注元素是否存在
            elements = annotations.get('elements', [])
            for element in elements:
                xpath = element.get('xpath', '')
                if xpath:
                    # 简单的XPath验证（实际实现可能需要更复杂的XPath解析）
                    if not HTMLParser._validate_xpath(soup, xpath):
                        result['errors'].append(f"XPath无效: {xpath}")
                        result['valid'] = False
            
            return result
        except Exception as e:
            return {
                'valid': False,
                'errors': [f"验证失败: {str(e)}"],
                'warnings': []
            }
    
    @staticmethod
    def compare_html_similarity(html1: str, html2: str) -> float:
        """
        比较两个HTML的相似度
        
        Args:
            html1: 第一个HTML内容
            html2: 第二个HTML内容
            
        Returns:
            相似度分数 (0-1)
        """
        try:
            # 提取结构特征
            features1 = HTMLParser.extract_layout_features(html1)
            features2 = HTMLParser.extract_layout_features(html2)
            
            # 计算相似度（简化版本）
            similarities = []
            
            # 比较文本相似度
            text1 = features1['page_info']['text_length']
            text2 = features2['page_info']['text_length']
            if max(text1, text2) > 0:
                text_sim = min(text1, text2) / max(text1, text2)
                similarities.append(text_sim)
            
            # 比较结构相似度
            for section in ['header', 'navigation', 'main', 'sidebar', 'footer']:
                count1 = len(features1['structure'][section])
                count2 = len(features2['structure'][section])
                if max(count1, count2) > 0:
                    struct_sim = min(count1, count2) / max(count1, count2)
                    similarities.append(struct_sim)
            
            # 返回平均相似度
            return sum(similarities) / len(similarities) if similarities else 0.0
            
        except Exception:
            return 0.0
    
    @staticmethod
    def _extract_semantic_elements(soup: BeautifulSoup, tags: List[str]) -> List[Dict[str, Any]]:
        """提取语义化元素"""
        elements = []
        for tag in tags:
            for element in soup.find_all(tag):
                elements.append({
                    'tag': tag,
                    'text': element.get_text(strip=True)[:100],  # 限制文本长度
                    'attributes': dict(element.attrs),
                    'xpath': HTMLParser._generate_xpath(element)
                })
        return elements
    
    @staticmethod
    def _extract_forms(soup: BeautifulSoup) -> List[Dict[str, Any]]:
        """提取表单信息"""
        forms = []
        for form in soup.find_all('form'):
            form_info = {
                'action': form.get('action', ''),
                'method': form.get('method', 'get'),
                'inputs': []
            }
            
            for input_elem in form.find_all(['input', 'select', 'textarea']):
                form_info['inputs'].append({
                    'type': input_elem.get('type', 'text'),
                    'name': input_elem.get('name', ''),
                    'required': input_elem.has_attr('required')
                })
            
            forms.append(form_info)
        return forms
    
    @staticmethod
    def _extract_media(soup: BeautifulSoup) -> Dict[str, int]:
        """提取媒体元素统计"""
        return {
            'images': len(soup.find_all('img')),
            'videos': len(soup.find_all('video')),
            'audios': len(soup.find_all('audio'))
        }
    
    @staticmethod
    def _extract_links(soup: BeautifulSoup) -> Dict[str, Any]:
        """提取链接信息"""
        links = soup.find_all('a', href=True)
        return {
            'total': len(links),
            'external': len([link for link in links if link['href'].startswith(('http://', 'https://'))]),
            'internal': len([link for link in links if link['href'].startswith(('/', '#'))])
        }
    
    @staticmethod
    def _generate_xpath(element: Tag) -> str:
        """生成元素的XPath"""
        try:
            xpath_parts = []
            current = element
            
            while current and current.name:
                # 获取标签名
                tag_name = current.name
                
                # 计算在同级中的位置
                siblings = [s for s in current.parent.children if hasattr(s, 'name') and s.name == tag_name] if current.parent else [current]
                if len(siblings) > 1:
                    index = siblings.index(current) + 1
                    xpath_parts.append(f"{tag_name}[{index}]")
                else:
                    xpath_parts.append(tag_name)
                
                current = current.parent
                if not current or current.name == '[document]':
                    break
            
            xpath_parts.reverse()
            return "//" + "/".join(xpath_parts)
        except Exception:
            return ""
    
    @staticmethod
    def _validate_xpath(soup: BeautifulSoup, xpath: str) -> bool:
        """简单的XPath验证"""
        try:
            # 这里可以实现更复杂的XPath验证逻辑
            # 目前只做基本的格式检查
            return xpath.startswith('//') and len(xpath) > 2
        except Exception:
            return False


# 全局HTML解析器实例
html_parser = HTMLParser() 