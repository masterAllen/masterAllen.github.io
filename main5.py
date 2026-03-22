"""
main5 - 压缩 asset 下的图片

1. 压缩前备份到 主目录/backup/（与备份文件相同时跳过写入，减少磁盘读写）
2. 仅处理 JPG、PNG；PNG 必须使用 pngquant（无则报错退出）
3. 后缀不变；JPG 有损；PNG 经 Pillow 缩放后由 pngquant 压缩
4. 缓存已压缩图片及参数，参数未变时跳过
"""
import os
import hashlib
import subprocess
import tempfile
from pathlib import Path
import shutil
import pickle

import utils
import settings
from PIL import Image

# 仅处理 JPG / PNG
IMAGE_EXTS = {'.jpg', '.jpeg', '.png'}
CONFIG_DIR = settings.config_dir
CACHE_PATH = os.path.join(CONFIG_DIR, 'image_compress_info.bin')

_script_dir = Path(settings.script_dir)


def _find_pngquant_exe():
    """与 test3 一致：同目录 pngquant 或上级目录 pngquant"""
    for base in (_script_dir, _script_dir.parent):
        exe = base / 'pngquant' / 'pngquant.exe'
        if exe.is_file():
            return exe
    return None


def _require_pngquant():
    exe = _find_pngquant_exe()
    if exe is None:
        raise FileNotFoundError(
            '未找到 pngquant.exe。请将 pngquant 放在 '
            f'{_script_dir / "pngquant"} 或 {_script_dir.parent / "pngquant"} 下。'
            'pngquant git repo: https://github.com/kornelski/pngquant'
        )
    return exe


def _load_cache():
    if os.path.exists(CACHE_PATH):
        with open(CACHE_PATH, 'rb') as f:
            return pickle.load(f)
    return {}


def _save_cache(cache):
    os.makedirs(CONFIG_DIR, exist_ok=True)
    with open(CACHE_PATH, 'wb') as f:
        pickle.dump(cache, f)


def _params_key(opts):
    pq = opts.get('png_quality', (65, 95))
    if isinstance(pq, (tuple, list)):
        pq_key = tuple(pq)
    else:
        pq_key = str(pq)
    return (opts.get('jpg_quality', 85), pq_key, opts.get('max_width', 1920))


def _pngquant_quality_arg(opts):
    """pngquant --quality=min-max 或单值"""
    pq = opts.get('png_quality', (65, 95))
    if isinstance(pq, (tuple, list)) and len(pq) == 2:
        qstr = f'{pq[0]}-{pq[1]}'
    else:
        qstr = str(pq).strip()
    return f'--quality={qstr}'


def _has_alpha(img):
    """判断图片是否有透明通道（且实际使用透明）"""
    if img.mode in ('RGBA', 'LA', 'P'):
        if img.mode == 'P':
            img = img.convert('RGBA')
        alpha = img.split()[-1]
        return alpha.getextrema()[0] < 255
    return False


def _resize_to_fit(img, opts):
    """仅按 max_width 等比缩小；宽度不超过限制则不缩放。"""
    w, h = img.size
    mw = opts.get('max_width', 1920)
    if w <= mw:
        return img
    ratio = mw / w
    nw, nh = int(w * ratio), int(h * ratio)
    return img.resize((nw, nh), Image.Resampling.LANCZOS)


def _compress_png_pngquant(img_path, opts, pngquant_exe: Path):
    """使用 pngquant 有损压缩 PNG，原地覆盖；--quality 使用 settings png_quality (min-max)"""
    quality_arg = _pngquant_quality_arg(opts)

    fd, tmp_path = tempfile.mkstemp(suffix='.png', dir=os.path.dirname(img_path))
    os.close(fd)
    try:
        r = subprocess.run(
            [
                str(pngquant_exe),
                quality_arg,
                str(Path(img_path).resolve()),
                '-o',
                tmp_path,
                '--force',
            ],
            capture_output=True,
            text=True,
        )
        if r.returncode != 0:
            err = (r.stderr or r.stdout or '').strip()
            raise RuntimeError(
                f'pngquant 失败 (code={r.returncode}): {err or "无输出"}'
            )
        shutil.move(tmp_path, img_path)
    except Exception:
        if os.path.exists(tmp_path):
            try:
                os.remove(tmp_path)
            except OSError:
                pass
        raise


def _compress_image(img_path, opts, pngquant_exe: Path):
    """压缩单张图片，返回 (新路径, 原大小, 新大小)。后缀保持不变。"""
    img_path = utils.abspath(img_path)
    orig_size = os.path.getsize(img_path)
    ext = Path(img_path).suffix.lower()

    if ext in {'.jpg', '.jpeg'}:
        img = Image.open(img_path)
        img = _resize_to_fit(img, opts)
        img = img.convert('RGB')
        img.save(img_path, 'JPEG', quality=opts.get('jpg_quality', 85), optimize=True)
    elif ext == '.png':
        img = Image.open(img_path)
        img = _resize_to_fit(img, opts)
        if img.mode not in ('RGBA', 'LA', 'P') or not _has_alpha(img):
            img = img.convert('RGB')
        else:
            img = img.convert('RGBA')
        img.save(img_path, 'PNG')
        _compress_png_pngquant(img_path, opts, pngquant_exe)
    else:
        # 其他格式不处理
        pass

    new_size = os.path.getsize(img_path)
    return img_path, orig_size, new_size


def _file_hash(path, chunk_size=65536):
    """计算文件 MD5，用于快速比较"""
    h = hashlib.md5()
    with open(path, 'rb') as f:
        while chunk := f.read(chunk_size):
            h.update(chunk)
    return h.hexdigest()


def _ensure_backup(img_path, backup_path):
    """
    压缩前备份：若备份已存在且与待压缩文件内容相同，则跳过写入。
    返回是否执行了复制。
    """
    if not os.path.exists(img_path):
        return False
    if os.path.exists(backup_path):
        try:
            if _file_hash(img_path) == _file_hash(backup_path):
                return False  # 相同，无需复制
        except OSError:
            pass
    os.makedirs(os.path.dirname(backup_path), exist_ok=True)
    shutil.copy2(img_path, backup_path)
    return True


def run():
    asset_image_dir = os.path.join(settings.assetdir, 'image')
    dstdir = utils.abspath(settings.dstdir)
    backup_root = os.path.join(dstdir, 'backup')

    if not os.path.isdir(asset_image_dir):
        print(f'asset/image 目录不存在: {asset_image_dir}')
        return

    pngquant_exe = _require_pngquant()
    print(f'PNG 使用 pngquant: {pngquant_exe}')

    opts = settings.IMAGE_OPTIMIZATION
    params_key = _params_key(opts)
    cache = _load_cache()

    images = []
    for root, _, files in os.walk(asset_image_dir):
        for f in files:
            if Path(f).suffix.lower() in IMAGE_EXTS:
                images.append(os.path.join(root, f))

    print(f'找到 {len(images)} 张图片（仅 jpg/jpeg/png）')
    compressed, skipped, errors = 0, 0, 0

    for img_path in images:
        img_path = utils.abspath(img_path)
        if not os.path.exists(img_path):
            continue
        cached = cache.get(img_path)
        mtime = os.path.getmtime(img_path)

        if cached and cached.get('params') == params_key and cached.get('mtime') == mtime:
            skipped += 1
            continue

        try:
            # 压缩前备份
            rel_from_dstdir = os.path.relpath(img_path, settings.assetdir)
            backup_path = os.path.join(backup_root, rel_from_dstdir)
            if _ensure_backup(img_path, backup_path):
                print(f'备份: {img_path}')

            new_path, orig_size, new_size = _compress_image(img_path, opts, pngquant_exe)
            pct = (1 - new_size / orig_size) * 100 if orig_size > 0 else 0
            # print(f'压缩: {img_path}')
            print(f'  {orig_size/1024:.1f} KB -> {new_size/1024:.1f} KB (减少 {pct:.1f}%)')

            cache[new_path] = {'params': params_key, 'mtime': os.path.getmtime(new_path)}
            compressed += 1
        except Exception as e:
            print(f'错误: {img_path} - {e}')
            errors += 1

    _save_cache(cache)
    print(f'\n压缩完成: {compressed} 张, 跳过 {skipped} 张, 错误 {errors} 张')


if __name__ == '__main__':
    run()
