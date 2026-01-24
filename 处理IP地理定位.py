'''
每一个目录生成一个对应的 md
'''
import os

MAX_DISPLAY_COUNT = 10

def list_files(folder, patterns=None, exclude_dirs=None, max_display_count=MAX_DISPLAY_COUNT):
    """
    生成传统的ASCII目录树格式（带横线竖线）
    - 使用 ├── 和 └── 表示层级结构
    - 按名称排序，目录在前，文件在后
    """
    if patterns is None:
        patterns = []
    if exclude_dirs is None:
        exclude_dirs = []

    def build_tree(abs_dir_path, prefix="", is_last=True):
        """
        递归构建目录树
        prefix: 当前行的前缀（包含竖线和缩进）
        is_last: 是否是父目录的最后一个子项
        """
        try:
            names = os.listdir(abs_dir_path)
        except Exception:
            names = []

        # 过滤排除的目录
        names = [n for n in names if n not in exclude_dirs]
        
        # 如果是顶层，排除 .upload 和 index.md
        if prefix == "":
            names = [n for n in names if n != '.upload' and n != 'index.md']

        # 目录在前，文件在后；均按不区分大小写排序
        dirs = [n for n in names if os.path.isdir(os.path.join(abs_dir_path, n))]
        files = [n for n in names if not os.path.isdir(os.path.join(abs_dir_path, n))]
        dirs.sort(key=lambda n: n.lower())
        files.sort(key=lambda n: n.lower())
        
        # 目录全部显示，文件如果超过限制则省略
        display_dirs = dirs  # 目录全部显示
        has_more_files = len(files) > max_display_count
        display_files = files[:max_display_count-1] if has_more_files else files
        
        # 合并显示列表：目录 + 文件
        display_names = display_dirs + display_files

        lines = []
        for i, name in enumerate(display_names):
            # 判断是否是最后一个显示的项（需要考虑是否有省略的文件）
            is_last_item = (i == len(display_names) - 1) and not has_more_files
            abs_path = os.path.join(abs_dir_path, name)
            
            # 确定当前行的连接符
            if is_last_item:
                connector = "└── "
                next_prefix = prefix + "    "
            else:
                connector = "├── "
                next_prefix = prefix + "│   "
            
            lines.append(prefix + connector + name)
            
            # 如果是目录，递归处理子目录
            if os.path.isdir(abs_path):
                child_lines = build_tree(abs_path, next_prefix, is_last_item)
                if child_lines:
                    lines.extend(child_lines)
        
        # 如果有更多文件，添加省略标记
        if has_more_files:
            # 省略标记使用最后一个连接符（因为它是显示的最后一个项）
            lines.append(prefix + "└── ...")

        return lines

    # 生成目录树
    tree_lines = [os.path.basename(folder)]
    tree_lines.extend(build_tree(folder))
    return "\n".join(tree_lines)
    
# record 整合 - 遍历record目录，合并文件内容
def merge_record_files(record_dir, output_file):
    """
    遍历record目录，将所有文件内容合并到一个文件中，保持分层结构
    """
    merged_content = []
    merged_content.append("# Record 文件内容整合\n\n")
    
    def process_directory(dir_path, relative_path="", depth=0):
        """递归处理目录"""
        try:
            items = os.listdir(dir_path)
        except Exception:
            return
        
        # 排序：目录在前，文件在后
        dirs = [d for d in items if os.path.isdir(os.path.join(dir_path, d))]
        files = [f for f in items if not os.path.isdir(os.path.join(dir_path, f))]
        dirs.sort(key=lambda n: n.lower())
        files.sort(key=lambda n: n.lower())
        
        # 如果有相对路径，添加目录标题（除了根目录）
        if relative_path and (dirs or files):
            heading_level = min(depth + 1, 6)  # 限制标题层级，最多到h6
            heading_prefix = "#" * heading_level
            merged_content.append(f"\n{heading_prefix} 📁 {relative_path}\n\n")
        
        # 处理文件
        for filename in files:
            if not filename.endswith('.md') and not filename.endswith('.txt'):
                continue

            file_path = os.path.join(dir_path, filename)
            
            # 添加文件标题（分层显示）
            heading_level = min(depth + 2, 6)  # 限制标题层级，最多到h6
            heading_prefix = "#" * heading_level
            merged_content.append(f"\n{heading_prefix} 📄 {filename}\n\n")
            
            # 读取文件内容
            try:
                # 尝试不同的编码
                encodings = ['utf-8', 'gbk', 'gb2312', 'latin-1']
                content = None
                for encoding in encodings:
                    try:
                        with open(file_path, 'r', encoding=encoding) as f:
                            content = f.read()
                        break
                    except UnicodeDecodeError:
                        continue
                    except Exception:
                        continue
                
                if content is not None:
                    merged_content.append('```\n')
                    merged_content.append(content)
                    merged_content.append("\n```\n")
                else:
                    merged_content.append(f"*[无法读取文件内容: {file_path}]*\n\n")
            except Exception as e:
                merged_content.append(f"*[读取文件出错: {file_path}, 错误: {str(e)}]*\n\n")
        
        # 递归处理子目录
        for dirname in dirs:
            subdir_path = os.path.join(dir_path, dirname)
            subdir_relative_path = os.path.join(relative_path, dirname) if relative_path else dirname
            process_directory(subdir_path, subdir_relative_path, depth + 1)
    
    # 开始处理
    process_directory(record_dir)
    
    # 写入合并后的内容
    with open(output_file, "w", encoding="utf-8") as f:
        f.write("".join(merged_content))
    
    print(f"Record 文件内容已合并到: {output_file}")
    

def run(srcdir, dstdir, configs):
    os.makedirs(dstdir, exist_ok=True)

    # 只显示这个文件夹里面的内容 - 生成目录树
    reading_folder = os.path.join(srcdir, '阅读论文及记录')
    if os.path.exists(reading_folder):
        # 生成整个目录树（排除record目录）
        tree_content = list_files(reading_folder, patterns=[], exclude_dirs=['record'], max_display_count=100)
        
        # 保存目录树到文件
        tree_output_file = os.path.join(dstdir, '阅读论文目录树.md')
        with open(tree_output_file, "w", encoding="utf-8") as f:
            f.write("# 阅读论文目录树\n\n")
            f.write('```markdown\n')
            f.write(tree_content)
            f.write('\n```\n')
        print(f"目录树已保存到: {tree_output_file}")
    configs.update_cache(reading_folder, tree_output_file)

    # 生成整体的目录树
    reading_folder = os.path.join(srcdir)
    if os.path.exists(reading_folder):
        # 生成整个目录树（排除record目录）
        tree_content = list_files(reading_folder, patterns=[], exclude_dirs=['record'])
        
        # 保存目录树到文件
        tree_output_file = os.path.join(dstdir, '整体目录树.md')
        with open(tree_output_file, "w", encoding="utf-8") as f:
            f.write("# 整体目录树\n\n")
            f.write('```')
            f.write(tree_content)
            f.write('\n```\n')
        print(f"目录树已保存到: {tree_output_file}")
    configs.update_cache(reading_folder, tree_output_file)

    record_folder = os.path.join(srcdir, '阅读论文及记录', 'record')
    if os.path.exists(record_folder):
        record_output_file = os.path.join(dstdir, '记录整合.md')
        configs.process_if_needed(record_folder, record_output_file, merge_record_files)

if __name__ == "__main__":
    pass