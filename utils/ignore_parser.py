"""
.gitignore 文件解析器，实现类似 .gitignore 的功能
支持：
- 每行一个规则
- # 开头的注释行
- ! 开头的否定规则（不忽略）
- / 开头表示从当前目录根开始
- * 通配符
- ** 匹配任意层级目录
- 子文件夹的 .gitignore 文件优先于父文件夹的
"""
import os
import re
from pathlib import Path
from typing import List, Optional, Set


class IgnoreRule:
    """单个忽略规则"""
    def __init__(self, pattern: str, is_negation: bool = False):
        self.pattern = pattern.strip()
        self.is_negation = is_negation  # True 表示不忽略（! 开头）
        
        # 转换为正则表达式
        regex_pattern = self.pattern
        
        # 处理 ** 匹配任意层级（包括路径分隔符）
        regex_pattern = regex_pattern.replace('**', '__DOUBLE_STAR__')
        # 转义其他特殊字符
        regex_pattern = re.escape(regex_pattern)
        # 恢复 ** 为匹配任意字符（包括路径分隔符）
        regex_pattern = regex_pattern.replace('__DOUBLE_STAR__', '.*')
        # 将单个 * 转换为匹配任意字符（除了路径分隔符）
        regex_pattern = regex_pattern.replace(r'\*', '[^/\\\\]*')
        # 将 ? 转换为匹配单个字符（除了路径分隔符）
        regex_pattern = regex_pattern.replace(r'\?', '[^/\\\\]')
        
        # 如果以 / 开头，表示从当前目录根开始匹配
        if self.pattern.startswith('/'):
            regex_pattern = '^' + regex_pattern[1:]  # 去掉开头的 /
        else:
            # 否则可以匹配任意位置（文件名或路径中的任意部分）
            regex_pattern = '(^|/)' + regex_pattern
        
        # 如果以 / 结尾，表示匹配目录
        if self.pattern.endswith('/'):
            regex_pattern = regex_pattern[:-1] + r'($|[/\\])'
        else:
            regex_pattern = regex_pattern + '$'
        
        self.regex = re.compile(regex_pattern, re.IGNORECASE)
    
    def matches(self, path: str) -> bool:
        """
        检查路径是否匹配此规则
        path: 相对于 .gitignore 文件所在目录的相对路径
        """
        # 统一使用 / 作为路径分隔符进行匹配
        normalized_path = path.replace('\\', '/')
        return bool(self.regex.search(normalized_path))


class IgnoreParser:
    """解析和应用 .gitignore 文件"""
    
    def __init__(self, root_dir: str):
        """
        root_dir: 根目录路径
        """
        self.root_dir = os.path.abspath(root_dir)
        self._cache: dict = {}  # 缓存已解析的 .gitignore 文件
    
    def _load_ignore_file(self, dir_path: str) -> Optional[List[IgnoreRule]]:
        """
        加载指定目录下的 .gitignore 文件
        返回规则列表，如果文件不存在则返回 None
        """
        ignore_file = os.path.join(dir_path, '.gitignore')
        
        if not os.path.exists(ignore_file):
            return None
        
        # 检查缓存
        if ignore_file in self._cache:
            return self._cache[ignore_file]
        
        rules = []
        try:
            with open(ignore_file, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    # 跳过空行和注释
                    if not line or line.startswith('#'):
                        continue
                    
                    # 处理否定规则
                    is_negation = False
                    if line.startswith('!'):
                        is_negation = True
                        line = line[1:]
                    
                    if line:  # 确保去掉 ! 后还有内容
                        rules.append(IgnoreRule(line, is_negation))
        except Exception as e:
            print(f"警告: 读取 .gitignore 文件失败 {ignore_file}: {e}")
            return None
        
        # 缓存结果
        self._cache[ignore_file] = rules
        return rules
    
    def should_ignore(self, file_path: str) -> bool:
        """
        判断文件或目录是否应该被忽略
        file_path: 绝对路径
        返回 True 表示应该忽略，False 表示不忽略
        """
        file_path = os.path.abspath(file_path)
        
        # 确保路径在根目录下
        try:
            if os.path.commonpath([file_path, self.root_dir]) != self.root_dir:
                return False
        except ValueError:
            return False
        
        # 获取文件/目录所在目录
        if os.path.isfile(file_path):
            current_dir = os.path.dirname(file_path)
        else:
            current_dir = file_path
        
        # 从当前目录向上查找所有包含 .gitignore 的目录
        # 同时记录每个 .gitignore 文件对应的目录和规则
        dir_rules_pairs = []  # [(dir_path, rules), ...]
        temp_dir = current_dir
        
        while temp_dir and os.path.commonpath([temp_dir, self.root_dir]) == self.root_dir:
            rules = self._load_ignore_file(temp_dir)
            if rules:
                dir_rules_pairs.append((temp_dir, rules))
            parent = os.path.dirname(temp_dir)
            if parent == temp_dir:  # 到达根目录
                break
            temp_dir = parent
        
        # 如果没有找到任何 .gitignore 文件
        if not dir_rules_pairs:
            return False
        
        # 应用规则：从根目录到子目录的顺序，子目录的规则优先
        # 收集所有匹配的规则（按从根到子的顺序）
        matched_rules = []
        
        for base_dir, rules in dir_rules_pairs:
            # 计算相对于该 .gitignore 文件所在目录的相对路径
            try:
                rel_path = os.path.relpath(file_path, base_dir)
            except ValueError:
                rel_path = os.path.basename(file_path)
            
            # 也尝试匹配文件名（相对于文件所在目录）
            filename = os.path.basename(file_path)
            
            # 检查每个规则是否匹配
            for rule in rules:
                # 尝试匹配完整相对路径
                if rule.matches(rel_path):
                    matched_rules.append(rule)
                # 也尝试匹配文件名
                elif rule.matches(filename):
                    matched_rules.append(rule)
        
        if not matched_rules:
            return False
        
        # 最后一个匹配的规则决定结果（子目录的规则优先，因为子目录的规则在后面）
        last_rule = matched_rules[-1]
        return not last_rule.is_negation  # 如果是否定规则，返回 False（不忽略）
    
    def filter_paths(self, paths: List[str]) -> List[str]:
        """
        过滤路径列表，返回不被忽略的路径
        """
        return [path for path in paths if not self.should_ignore(path)]

