import os
import yaml 
import settings
import json
from pathlib import Path

from .path_utils import abspath
from typing import Any, Dict, Tuple

class ConfigParser:
    def __init__(self):
        self.config_dpath = config_dpath = Path(settings.config_dir)
        self.file_cache_dpath = config_dpath / 'cache_file.json'
        self.pages_cache_dpath = config_dpath / 'pages_info.json'
        self.link_cache_dpath = config_dpath / 'cache_link.json'

        # 1. 加载 topdir.yml 文件 --> 读取哪些文件夹要处理
        topdir_info = yaml.load(open(config_dpath / 'topdir.yml', 'r', encoding='utf8'), Loader=yaml.FullLoader)
        self.topdir_dirs = topdir_info['dirs']

        self.file_cache: Dict[Path, Tuple[float, Path]] = dict() 
        ''' file_cache 的格式：<Key = 原始文件路径, Value = (原始文件修改时间, 转换后的文件路径)> '''

        self.pages_cache: Dict[Path, Path] = dict()
        ''' pages_cache 的格式：<Key = 原始 .pages 文件路径, Value = 转换后的 .pages 文件路径> '''

        self.link_cache: Dict[str, dict[str, Any]] = dict()
        ''' link_cache 的格式：<Key = 原始 link 文件路径, Value = 链接目标与派生产物信息> '''

        self.load_cache()

        # 4. 加载 Special 文件 --> 读取哪些文件不在 main 中处理，使用对应的文件进行处理
        special_file = config_dpath / 'special.yml'
        self.specials = dict() 
        if special_file.exists():
            loaded = yaml.load(open(special_file, 'r', encoding='utf8'), Loader=yaml.FullLoader)
            if loaded:  # 处理 YAML 文件为空或只有注释的情况
                self.specials = loaded

        # self.specials = {abspath(joinpath(srcdir, k)): [abspath(joinpath('.', v))] for k, v in specials.items()}
        # assert(all([os.path.exists(k) for k in specials.keys()]))
        # assert(all([os.path.exists(v[0]) for v in specials.values()]))

    def _load_json(self, path: Path, default):
        if not path.exists():
            return default
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)

    def _save_json(self, path: Path, data) -> None:
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def _serialize_file_cache(self, cache: Dict[str, Tuple[float, str]]) -> dict:
        result = {}
        for srcpath, (mtime, dstpath) in cache.items():
            result[abspath(srcpath)] = {
                'mtime': mtime,
                'dst': abspath(dstpath),
            }
        return result

    def _deserialize_file_cache(self, data: dict) -> Dict[str, Tuple[float, str]]:
        result = {}
        for srcpath, info in data.items():
            result[abspath(srcpath)] = (info['mtime'], abspath(info['dst']))
        return result

    def _serialize_pages_cache(self, cache: Dict[str, str]) -> dict:
        return {abspath(srcpath): abspath(dstpath) for srcpath, dstpath in cache.items()}

    def _deserialize_pages_cache(self, data: dict) -> Dict[str, str]:
        return {abspath(srcpath): abspath(dstpath) for srcpath, dstpath in data.items()}

    def load_cache(self):
        self.new_file_cache = dict()
        self.file_cache = dict()
        
        self.new_pages_cache = dict()
        self.pages_cache = dict()

        self.new_link_cache = dict()
        self.link_cache = dict()

        if self.file_cache_dpath.exists():
            self.file_cache = self._deserialize_file_cache(self._load_json(self.file_cache_dpath, {}))

        if self.pages_cache_dpath.exists():
            self.pages_cache = self._deserialize_pages_cache(self._load_json(self.pages_cache_dpath, {}))

        if self.link_cache_dpath.exists():
            self.link_cache = self._load_json(self.link_cache_dpath, {})

    def update_cache(self, srcpath, dstpath):
        srcpath = abspath(srcpath)
        dstpath = abspath(dstpath)
        self.new_file_cache[srcpath] = (self.get_mtime(srcpath), dstpath)

    def update_cache_byold(self, srcpath):
        srcpath = abspath(srcpath)
        self.new_file_cache[srcpath] = self.file_cache[srcpath]

    def save_main_cache(self):
        self._save_json(self.file_cache_dpath, self._serialize_file_cache(self.new_file_cache))
        self._save_json(self.pages_cache_dpath, self._serialize_pages_cache(self.new_pages_cache))

    def save_link_cache(self):
        with open(self.link_cache_dpath, 'w', encoding='utf-8') as f:
            json.dump(self.new_link_cache, f, ensure_ascii=False, indent=2)

    def save_cache(self):
        self.save_main_cache()
        self.save_link_cache()

    def get_web_path(self, srcpath):
        srcpath = abspath(srcpath)
        if srcpath in self.new_file_cache:
            return self.new_file_cache[srcpath][1]
        return self.file_cache[srcpath][1]

    def get_mtime(self, srcpath):
        """
        获取文件/目录的最新修改时间；目录返回的是文件夹中所有文件中的最新修改时间
        
        Args:
            srcpath: 源文件路径
        
        Returns:
            float: 最新修改时间
        """
        mtime = 0
        if os.path.isdir(srcpath):
            for root, dirs, files in os.walk(srcpath):
                for file in files:
                    file_path = os.path.join(root, file)
                    try:
                        mtime = max(mtime, os.stat(file_path).st_mtime)
                    except (OSError, FileNotFoundError):
                        continue
        else:
            mtime = os.stat(srcpath).st_mtime
        return mtime

    def is_need_update(self, srcpath, dstpath=None):
        """
        判断文件/目录是否需要更新（只读查询，不修改状态）
        
        Args:
            srcpath: 源文件路径
        
        Returns:
            bool: True 表示需要更新，False 表示不需要更新
        """
        srcpath = abspath(srcpath)
        if dstpath:
            dstpath = abspath(dstpath)

        # 如果不在旧缓存中，需要更新
        if srcpath not in self.file_cache:
            return True

        old_mtime, old_dstpath = self.file_cache[srcpath]

        # 生成的文件是否一致
        if dstpath is not None and abspath(old_dstpath) != abspath(dstpath):
            return True

        # 新文件不存在，需要更新
        if not os.path.exists(old_dstpath):
            return True

        new_mtime = self.get_mtime(srcpath)
        return old_mtime != new_mtime

    def get_outdated_files(self):
        for srcpth in self.file_cache:
            if srcpth not in self.new_file_cache:
                yield srcpth, self.file_cache[srcpth][1]
    
    def get_new_files(self):
        for srcpth in self.new_file_cache:
            if srcpth not in self.file_cache:
                yield srcpth, self.new_file_cache[srcpth][1]
    
    def process_if_needed(self, srcpath, dstpath, processor):
        """
        如果文件需要更新，则执行 processor 函数并更新缓存；否则直接使用旧缓存。
        
        Args:
            srcpath: 源文件路径
            dstpath: 目标文件路径
            processor: 处理函数，接受 (srcpath, dstpath) 作为参数
        
        Returns:
            bool: 是否需要更新（True=已更新，False=使用缓存）
        """
        srcpath = abspath(srcpath)
        dstpath = abspath(dstpath)
        if self.is_need_update(srcpath, dstpath):
            processor(srcpath, dstpath)
            self.update_cache(srcpath, dstpath)
            return True
        else:
            self.update_cache_byold(srcpath)
            return False
    
    def update_pages_cache(self, srcpath, dstpath):
        """
        更新 .pages 文件缓存
        
        Args:
            srcpath: 原始 .pages 文件路径
            dstpath: 目标 .pages 文件路径
        """
        srcpath = abspath(srcpath)
        dstpath = abspath(dstpath)
        self.new_pages_cache[srcpath] = dstpath

    def update_link_cache(self, link_srcpath, target_raw):
        link_srcpath = abspath(link_srcpath)
        target_raw = abspath(target_raw)
        self.new_link_cache[link_srcpath] = {
            'mtime': os.path.getmtime(link_srcpath) if os.path.exists(link_srcpath) else None,
            'target_raw': target_raw,
        }

    def get_link_output_file(self, link_srcpath, target_raw):
        link_srcpath = abspath(link_srcpath)
        target_raw = abspath(target_raw)

        try:
            source_web_path = abspath(self.get_web_path(target_raw))
        except KeyError:
            return None

        if os.path.isdir(source_web_path):
            return None

        rel_link_path = os.path.relpath(link_srcpath, settings.srcdir)
        link_dst_path = abspath(os.path.join(settings.docsdir, rel_link_path))
        return abspath(os.path.join(os.path.dirname(link_dst_path), os.path.basename(source_web_path)))

    def get_all_link_output_files(self):
        all_outputs = set()
        for cache in (self.link_cache, self.new_link_cache):
            for link_srcpath, info in cache.items():
                target_raw = info.get('target_raw')
                if not target_raw:
                    continue
                output_file = self.get_link_output_file(link_srcpath, target_raw)
                if output_file is not None:
                    all_outputs.add(output_file)
        return all_outputs
    
    def get_all_pages_files(self):
        """
        获取所有存储的 .pages 文件路径（目标路径）
        
        Returns:
            set: 所有 .pages 文件的目标路径集合
        """
        # 合并旧缓存和新缓存中的所有 .pages 文件
        all_pages = set()
        all_pages.update(self.pages_cache.values())
        all_pages.update(self.new_pages_cache.values())
        return all_pages