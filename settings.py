# srcdir = r'D:\Blog\test\srcdocs'
# dstdir = r'D:\Blog\test\web\docs'
# assetdir = r'D:\Blog\test\web\docs\asset'
# config_dir = r'D:\Blog\test\web\configs'

srcdir = r'D:\Blog\done'
dstdir = r'D:\Blog\masterAllen.github.io'

import os
docsdir = os.path.join(dstdir, 'docs')
assetdir = os.path.join(docsdir, 'asset')
config_dir = os.path.join(dstdir, 'configs')

special_dirs = [
    '材料',
    'reference',
    'papers',
    'src',
    'code',
    'asset',
]