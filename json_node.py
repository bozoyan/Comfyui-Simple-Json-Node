import json
import re
import requests
from typing import Union
from urllib.parse import urlencode
import os
import urllib.request
import folder_paths
from nodes import LoadImage


class SimpleJSONParserNode:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "json_string": ("STRING", {"multiline": True}),
                "url": ("STRING", {"default": ""}),
                "query_string": ("STRING", {"default": "", "multiline": True}),
                "path": ("STRING", {"default": ""}),

            },
        }

    RETURN_TYPES = ("STRING", "INT","STRING")
    RETURN_NAMES = ("解析后数据", "数据大小","图片URL")
    FUNCTION = "parse_json"
    CATEGORY = "utils"

    def parse_json(self, json_string: str, path: str, url: str, query_string: str) -> tuple[str, int, str]:
        try:
            if url:
                # 处理查询字符串
                query_params = {}
                if query_string:
                    for line in query_string.split('\n'):
                        if '=' in line:
                            key, value = line.split('=', 1)
                            query_params[key.strip()] = value.strip()
                
                # 构建完整的 URL
                full_url = url
                if query_params:
                    full_url += '?' + urlencode(query_params)
                
                response = requests.get(full_url)
                response.raise_for_status()
                data = response.json()
            else:
                data = json.loads(json_string)

            if not path:
                array_size = len(data) if isinstance(data, list) else -1
                return json.dumps(data, indent=2), array_size, self.extract_image_url(data)
            
            keys = path.split('.')
            for key in keys:
                if key.isdigit():
                    data = data[int(key)]
                elif '[' in key and ']' in key:
                    list_key, index = key[:-1].split('[')
                    data = data[list_key][int(index)]
                else:
                    data = data[key]
            
            array_size = len(data) if isinstance(data, list) else -1
            
            if isinstance(data, (dict, list)):
                return json.dumps(data, indent=2), array_size, self.extract_image_url(data)
            else:
                return str(data), array_size, self.extract_image_url(data)
        except json.JSONDecodeError:
            raise ValueError("无效的 JSON 字符串")
        except requests.RequestException as e:
            raise ValueError(f"从 URL 获取 JSON 时出错: {str(e)}")
        except (KeyError, IndexError, TypeError):
            raise ValueError("无效的路径或未找到键")

    def extract_image_url(self, data):
        if isinstance(data, str) and (data.startswith('http') and any(ext in data.lower() for ext in ['.jpg', '.jpeg', '.png', '.gif'])):
            return data
        elif isinstance(data, dict):
            for value in data.values():
                url = self.extract_image_url(value)
                if url:
                    return url
        elif isinstance(data, list):
            for item in data:
                url = self.extract_image_url(item)
                if url:
                    return url
        return ""

    @classmethod
    def IS_CHANGED(cls, **kwargs):
        return float("NaN")

class DisplayImageFromURL:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "image_url": (
                    "STRING",
                    {
                        "multiline": True,  # True if you want the field to look like the one on the ClipTextEncode node
                        "default": "url or path",
                        "lazy": True,
                    },
                ),
            },
        }

    RETURN_TYPES = ("IMAGE", "MASK")
    FUNCTION = "display_image"
    CATEGORY = "utils"

    def display_image(self, image_url: str):
        if not image_url:
            raise ValueError("未提供图片 URL")
        
        image_url = image_url.strip()
        input_dir = folder_paths.get_input_directory()
        filename = os.path.basename(image_url)
        file_path = os.path.join(input_dir, filename)

        # Check if the file already exists
        if os.path.exists(file_path):
            print(f"File {filename} already exists, skipping download.")
        else:
            # Download the image
            urllib.request.urlretrieve(image_url, file_path)
            print(f"Image successfully downloaded and saved as {filename}.")
        return LoadImage().load_image(filename)


class DecodeChinese:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "encoded_string": ("STRING", {"multiline": True}),
            },
        }

    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("解码后的中文",)
    FUNCTION = "decode_chinese"
    CATEGORY = "utils"

    def decode_chinese(self, encoded_string: str) -> str:
        def decode_unicode(match):
            return chr(int(match.group(1), 16))

        # 使用正则表达式查找所有 Unicode 转义序列，包括连续的序列
        pattern = r'\\u([0-9a-fA-F]{4})'
        decoded_string = re.sub(pattern, decode_unicode, encoded_string)

        # 处理可能的 HTML 实体编码
        decoded_string = re.sub(r'&#x([0-9a-fA-F]+);', lambda m: chr(int(m.group(1), 16)), decoded_string)
        decoded_string = re.sub(r'&#(\d+);', lambda m: chr(int(m.group(1))), decoded_string)

        return decoded_string
