import hashlib
import os

import settings


# filepth: 生成的文件路径；asset_type: 文件类型
# 返回：生成 asset 的绝对路径、相对 dir(filepth) 的路径
def asset_link(asset_src, asset_type, makedir=True):
    '''
    asset_link: 生成 asset 的绝对路径
    Args:
        asset_src: 原始路径，要求必须是文本文件。如 a.txt 包含 b.png，此时 asset_src 是 a.txt。
        asset_type: 文件类型，如 image, pdf, text, code, video, etc.
        makedir: 如果 asset 目录不存在，创建目录
    Returns:
        asset_absdir: 生成 asset 目录的绝对路径
    '''
    assert(not os.path.isdir(asset_src))

    asset_src_dir = abspath(os.path.dirname(asset_src))

    # 根据生成的文件，生成 MD5，作为文件夹名
    file_md5 = hashlib.md5(asset_src_dir.encode()).hexdigest()
    now_assetdir = abspath(os.path.join(settings.assetdir, asset_type, file_md5))

    if makedir:
        # print(f'创建 asset 目录: {now_assetdir}')
        os.makedirs(now_assetdir, exist_ok=True)

    return now_assetdir

def abspath(pth):
    result = os.path.abspath(pth)
    result = result[0].upper() + result[1:]
    return result

def relpath(pth1, pth2):
    # pth2 可能是 **尚未创建的目标文件路径**，此时 isfile 返回 False！
    if os.path.isfile(pth2) or (not os.path.exists(pth2) and os.path.splitext(pth2)[1] != ''):
        pth2 = os.path.dirname(pth2)
    result = os.path.relpath(pth1, pth2)
    result = result.replace('\\', '/')
    return result
