import os
import yaml 
import pickle
import settings
import json
import winshell
import utils
from pathlib import Path
from typing import Dict, Tuple

class ConfigParser:
    def __init__(self):
        self.config_dpath = config_dpath = Path(settings.config_dir)
        self.file_cache_dpath = config_dpath / 'file_info.bin'
        # self.new_generated_file_dpath = config_dpath / 'new_generated_filepath.bin'

        # 1. 加载 topdir.yml 文件 --> 读取哪些文件夹要处理
        topdir_info = yaml.load(open(config_dpath / 'topdir.yml', 'r', encoding='utf8'), Loader=yaml.FullLoader)
        self.topdir_dirs = topdir_info['dirs']

        self.file_cache: Dict[Path, Tuple[float, Path]] = dict() 
        ''' file_cache 的格式：<Key = 原始文件路径, Value = (原始文件修改时间, 转换后的文件路径)> '''

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

    def load_cache(self):
        self.new_file_cache = dict()
        if self.file_cache_dpath.exists():
            self.file_cache = pickle.load(open(self.file_cache_dpath, 'rb'))

    def update_cache(self, srcpath, dstpath, time):
        self.new_file_cache[srcpath] = (time, dstpath)

    def update_cache_byold(self, srcpath):
        self.new_file_cache[srcpath] = self.file_cache[srcpath]

    def save_cache(self):
        pickle.dump(self.new_file_cache, open(self.file_cache_dpath, 'wb'))
        self.file_cache = self.new_file_cache

        # # 存储新生成的文件
        # new_files = set()
        # for srcpth in self.new_file_cache:
        #     if srcpth not in self.file_cache:
        #         new_files.add(srcpth)
        # pickle.dump(new_files, open(self.new_generated_file_dpath, 'wb')) 

    def get_web_path(self, srcpath):
        return self.new_file_cache[srcpath][1]

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
        # 如果不在旧缓存中，需要更新
        if srcpath not in self.file_cache:
            return True

        old_mtime, old_dstpath = self.file_cache[srcpath]

        # 生成的文件是否一致
        if dstpath is not None and utils.abspath(old_dstpath) != utils.abspath(dstpath):
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
        if self.is_need_update(srcpath, dstpath):
            processor(srcpath, dstpath)
            self.update_cache(srcpath, dstpath, self.get_mtime(srcpath))
            return True
        else:
            self.update_cache_byold(srcpath)
            return False