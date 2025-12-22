# srcdir = r'D:\Blog\test\srcdocs'
# dstdir = r'D:\Blog\test\web\docs'
# assetdir = r'D:\Blog\test\web\docs\asset'
# config_dir = r'D:\Blog\test\web\configs'

srcdir = r'D:\Blog\done'
# dstdir = r'D:\Blog\masterAllen.github.io'
dstdir = r'D:\BlogSite\masterAllen.github.io'

import os
docsdir = os.path.join(dstdir, 'docs')
assetdir = os.path.join(docsdir, 'asset')

# 配置文件使用当前脚本所在路径
config_dir = os.path.join('.', 'configs')
overrides_dir = os.path.join('.', 'overrides')

special_dirs = [
    '材料',
    'papers',
    'asset',
]

skip_types = {'web', 'base64', 'unknown'}

MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB