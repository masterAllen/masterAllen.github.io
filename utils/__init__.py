"""
兼容原根目录 `utils` 单模块：从 file_utils / path_utils 聚合导出。
"""
from .file_utils import (
    check_url_type,
    copy,
    extract_links,
    get_filelink,
    get_md_title,
    get_topinfo,
    make_filetree,
)
from .path_utils import abspath, asset_link, relpath

__all__ = [
    "abspath",
    "asset_link",
    "check_url_type",
    "copy",
    "extract_links",
    "get_filelink",
    "get_md_title",
    "get_topinfo",
    "make_filetree",
    "relpath",
]
