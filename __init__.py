from .json_node import SimpleJSONParserNode, DisplayImageFromURL,DecodeChinese

NODE_CLASS_MAPPINGS = {
    "SimpleJSONParserNode": SimpleJSONParserNode,
    "DisplayImageFromURL": DisplayImageFromURL,
    "DecodeChinese": DecodeChinese
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "SimpleJSONParserNode": "JSON解析器",
    "DisplayImageFromURL": "URL显示图片",
    "DecodeChinese": "Unicode解码中文"
}

__all__ = ["NODE_CLASS_MAPPINGS", "NODE_DISPLAY_NAME_MAPPINGS"]
