# srcdir = r'D:\Blog\test\srcdocs'
# dstdir = r'D:\Blog\test\web\docs'
# assetdir = r'D:\Blog\test\web\docs\asset'
# config_dir = r'D:\Blog\test\web\configs'

srcdir = r'D:\Blog\done'
# dstdir = r'D:\Blog\masterAllen.github.io'
dstdir = r'D:\BlogSite\masterAllen.github.io'

import os
from pathlib import Path

# 基于 settings.py 所在目录计算路径，不依赖 os.chdir
_script_dir = Path(__file__).resolve().parent
script_dir = str(_script_dir)
config_dir = str(_script_dir / 'configs')
overrides_dir = str(_script_dir / 'overrides')

docsdir = os.path.join(dstdir, 'docs')
assetdir = os.path.join(docsdir, 'asset')

special_dirs = [
    '材料',
    'papers',
    'asset',
    'code',
    'codes'
]

skip_types = {'web', 'base64', 'unknown'}

MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB

# 图片压缩参数（main5.py）
IMAGE_OPTIMIZATION = {
    'jpg_quality': 85,          # JPEG 质量 (1-100)
    # pngquant --quality=min-max；区间过窄易导致 exit 99（达不到最低质量）
    'png_quality': (65, 80),    # (min, max)，或字符串 '65-95'
    'max_width': 1920,          # 仅限制最大宽度，超过则等比缩小
}