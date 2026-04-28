import argparse
import ctypes
import json
import os
import sys
from datetime import datetime
from pathlib import Path
from ctypes import wintypes

import winshell
from win32com.client import Dispatch

import settings
import utils

# 不用追踪 ID 的目录
IGNORED_DIR_NAMES = {
    ".git",
    ".obsidian",
    "__pycache__",
}

# Windows 文件唯一标识（文件/目录）
kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
INVALID_HANDLE_VALUE = wintypes.HANDLE(-1).value

CREATEFILE = kernel32.CreateFileW
CREATEFILE.argtypes = [
    wintypes.LPCWSTR,
    wintypes.DWORD,
    wintypes.DWORD,
    wintypes.LPVOID,
    wintypes.DWORD,
    wintypes.DWORD,
    wintypes.HANDLE,
]
CREATEFILE.restype = wintypes.HANDLE


class BY_HANDLE_FILE_INFORMATION(ctypes.Structure):
    _fields_ = [
        ("dwFileAttributes", wintypes.DWORD),
        ("ftCreationTime", wintypes.FILETIME),
        ("ftLastAccessTime", wintypes.FILETIME),
        ("ftLastWriteTime", wintypes.FILETIME),
        ("dwVolumeSerialNumber", wintypes.DWORD),
        ("nFileSizeHigh", wintypes.DWORD),
        ("nFileSizeLow", wintypes.DWORD),
        ("nNumberOfLinks", wintypes.DWORD),
        ("nFileIndexHigh", wintypes.DWORD),
        ("nFileIndexLow", wintypes.DWORD),
    ]


GET_FILE_INFO = kernel32.GetFileInformationByHandle
GET_FILE_INFO.argtypes = [wintypes.HANDLE, ctypes.POINTER(BY_HANDLE_FILE_INFORMATION)]
GET_FILE_INFO.restype = wintypes.BOOL

FILE_READ_ATTRIBUTES = 0x0080
FILE_SHARE_READ = 0x00000001
FILE_SHARE_WRITE = 0x00000002
FILE_SHARE_DELETE = 0x00000004
OPEN_EXISTING = 3
FILE_ATTRIBUTE_NORMAL = 0x00000080
FILE_FLAG_BACKUP_SEMANTICS = 0x02000000

def abspath(p: str) -> str:
    return utils.abspath(os.path.abspath(p))


def get_file_unique_id(path: str):
    if not os.path.exists(path):
        return None

    path = os.path.abspath(path)
    flags = FILE_ATTRIBUTE_NORMAL
    if os.path.isdir(path):
        flags |= FILE_FLAG_BACKUP_SEMANTICS

    handle = CREATEFILE(
        path,
        FILE_READ_ATTRIBUTES,
        FILE_SHARE_READ | FILE_SHARE_WRITE | FILE_SHARE_DELETE,
        None,
        OPEN_EXISTING,
        flags,
        None,
    )
    if handle == INVALID_HANDLE_VALUE:
        return None

    info = BY_HANDLE_FILE_INFORMATION()
    success = GET_FILE_INFO(handle, ctypes.byref(info))
    kernel32.CloseHandle(handle)
    if not success:
        return None

    return (info.dwVolumeSerialNumber, info.nFileIndexHigh, info.nFileIndexLow)


def id_to_str(file_id) -> str | None:
    if not file_id:
        return None
    return f"{file_id[0]}:{file_id[1]}"


def list_all_paths(root: str):
    root = abspath(root)
    all_paths = []
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in IGNORED_DIR_NAMES]
        all_paths.append(abspath(dirpath))
        for d in dirnames:
            all_paths.append(abspath(os.path.join(dirpath, d)))
        for f in filenames:
            all_paths.append(abspath(os.path.join(dirpath, f)))
    return all_paths


def build_current_index(scan_roots: list[str]):
    path_to_id: dict[str, str] = {}
    id_to_path: dict[str, str] = {}

    for root in scan_roots:
        if not os.path.exists(root):
            continue
        for p in list_all_paths(root):
            fid = get_file_unique_id(p)
            fid_str = id_to_str(fid)
            if not fid_str:
                continue
            p = abspath(p)
            path_to_id[p] = fid_str
            id_to_path[fid_str] = p

    return path_to_id, id_to_path


def load_cache(cache_file: str):
    if not os.path.exists(cache_file):
        return {"version": 1, "paths": {}, "id_to_path": {}, "lnk_target_by_link_id": {}}
    with open(cache_file, "r", encoding="utf-8") as f:
        return json.load(f)


def save_cache(cache_file: str, cache_data: dict):
    os.makedirs(os.path.dirname(cache_file), exist_ok=True)
    with open(cache_file, "w", encoding="utf-8") as f:
        json.dump(cache_data, f, ensure_ascii=False, indent=2)


def resolve_moved_path(
    missing_abs: str,
    cache_data: dict,
    current_id_to_path: dict[str, str],
) -> str | None:
    # 仅通过“旧路径 -> 旧ID -> 新路径”恢复
    old_info = cache_data.get("paths", {}).get(missing_abs)
    if old_info:
        old_id = old_info.get("id")
        if old_id and old_id in current_id_to_path:
            return current_id_to_path[old_id]
    return None


def log_markdown_replacements(
    md_file: str,
    replacements: list[tuple[int, int, str, str, str, str]],
    dry_run: bool,
) -> None:
    """replacements: (start, end, new_rel, link_url, broken_abs, new_abs)"""
    if not replacements:
        return
    prefix = "[dry-run] " if dry_run else ""
    print(f"{prefix}Markdown: {md_file}（{len(replacements)} 处）")
    for start, _end, new_rel, link_url, broken_abs, new_abs in sorted(
        replacements, key=lambda x: x[0]
    ):
        print(f"  {link_url!r} -> {new_rel!r}")
        print(f"    原解析(失效): {broken_abs}")
        print(f"    替换为: {new_abs}")


def repair_markdown_links(
    md_roots: list[str],
    cache_data: dict,
    current_id_to_path: dict[str, str],
    dry_run: bool,
):
    total_files = 0
    total_replaced = 0
    unresolved: list[tuple[str, str]] = []

    for root in md_roots:
        if not os.path.exists(root):
            continue
        for dirpath, dirnames, filenames in os.walk(root):
            dirnames[:] = [d for d in dirnames if d not in IGNORED_DIR_NAMES]
            for fn in filenames:
                if not fn.lower().endswith(".md"):
                    continue

                md_file = abspath(os.path.join(dirpath, fn))
                total_files += 1
                with open(md_file, "r", encoding="utf-8") as f:
                    content = f.read()

                matches = utils.extract_links(content, exclude=settings.skip_types)
                to_replace = []
                for start, end, link_url, _ in matches:
                    parsed = link_url.strip()
                    if os.path.isabs(parsed):
                        continue
                    target_abs = abspath((Path(md_file).parent / parsed).resolve())
                    if os.path.exists(target_abs):
                        continue

                    new_abs = resolve_moved_path(
                        target_abs,
                        cache_data,
                        current_id_to_path,
                    )
                    if not new_abs:
                        unresolved.append((md_file, target_abs))
                        continue

                    rel = os.path.relpath(new_abs, os.path.dirname(md_file)).replace("\\", "/")
                    to_replace.append((start, end, rel, link_url, target_abs, new_abs))

                if not to_replace:
                    continue

                log_markdown_replacements(md_file, to_replace, dry_run)
                to_replace.sort(key=lambda x: x[0], reverse=True)
                for start, end, new_rel, _lu, _ba, _na in to_replace:
                    content = content[:start] + new_rel + content[end:]
                total_replaced += len(to_replace)
                if not dry_run:
                    with open(md_file, "w", encoding="utf-8") as f:
                        f.write(content)

    return total_files, total_replaced, unresolved


def update_shortcut_target(lnk_path: str, new_target: str):
    shell = Dispatch("WScript.Shell")
    shortcut = shell.CreateShortCut(lnk_path)
    shortcut.Targetpath = new_target
    shortcut.save()


def repair_shortcuts(
    link_roots: list[str],
    cache_data: dict,
    current_path_to_id: dict[str, str],
    current_id_to_path: dict[str, str],
    dry_run: bool,
):
    total_links = 0
    total_fixed = 0
    unresolved: list[tuple[str, str]] = []
    lnk_target_by_link_id = cache_data.get("lnk_target_by_link_id", {})

    for root in link_roots:
        if not os.path.exists(root):
            continue
        for dirpath, dirnames, filenames in os.walk(root):
            dirnames[:] = [d for d in dirnames if d not in IGNORED_DIR_NAMES]
            for fn in filenames:
                if not (fn.lower().endswith(".lnk") or fn.lower().endswith(".link")):
                    continue

                lnk_path = abspath(os.path.join(dirpath, fn))
                total_links += 1
                try:
                    target = winshell.shortcut(lnk_path).path
                except Exception:
                    continue
                if not target:
                    continue

                target_abs = abspath(target)
                link_id = current_path_to_id.get(lnk_path)

                if os.path.exists(target_abs):
                    target_id = current_path_to_id.get(target_abs) or id_to_str(get_file_unique_id(target_abs))
                    if link_id and target_id:
                        lnk_target_by_link_id[link_id] = target_id
                    continue

                new_target = None

                # 1) 从“link 的历史 target_id”恢复
                if link_id:
                    old_target_id = lnk_target_by_link_id.get(link_id)
                    if old_target_id and old_target_id in current_id_to_path:
                        new_target = current_id_to_path[old_target_id]

                # 2) 从“失效路径的历史 ID”恢复
                if not new_target:
                    new_target = resolve_moved_path(
                        target_abs, cache_data, current_id_to_path
                    )

                if not new_target:
                    unresolved.append((lnk_path, target_abs))
                    continue

                if dry_run:
                    print(f"[dry-run] 快捷方式: {lnk_path}")
                    print(f"  原指向(失效): {target_abs}")
                    print(f"  替换为: {new_target}")
                else:
                    update_shortcut_target(lnk_path, new_target)
                    print(f"快捷方式: {lnk_path}")
                    print(f"  原指向(失效): {target_abs}")
                    print(f"  替换为: {new_target}")

                total_fixed += 1

                if link_id:
                    target_id = current_path_to_id.get(new_target) or id_to_str(get_file_unique_id(new_target))
                    if target_id:
                        lnk_target_by_link_id[link_id] = target_id

    cache_data["lnk_target_by_link_id"] = lnk_target_by_link_id
    return total_links, total_fixed, unresolved


def refresh_cache(cache_data: dict, current_path_to_id: dict[str, str], current_id_to_path: dict[str, str]):
    cache_data["version"] = 1
    cache_data["updated_at"] = datetime.now().isoformat(timespec="seconds")
    cache_data["paths"] = {p: {"id": fid} for p, fid in current_path_to_id.items()}
    cache_data["id_to_path"] = dict(current_id_to_path)


def main():
    parser = argparse.ArgumentParser(description="一键修复 src 中失效链接")
    parser.add_argument("--dry-run", action="store_true", help="只显示修复计划，不写回文件")
    parser.add_argument("--src-root", default=settings.srcdir, help="原始资料根目录，默认 settings.srcdir")
    parser.add_argument(
        "--cache-file",
        default=os.path.join(settings.config_dir, "link_identity_cache.json"),
        help="缓存文件路径",
    )
    args = parser.parse_args()

    src_root = abspath(args.src_root)
    cache_file = abspath(args.cache_file)

    cache_data = load_cache(cache_file)

    roots = [src_root] if os.path.exists(src_root) else []

    if not roots:
        print("没有可扫描目录，请检查 --src-root")
        return

    total_indexed = 0
    total_md_files = 0
    total_md_replaced = 0
    total_lnk_files = 0
    total_lnk_fixed = 0
    merged_path_to_id: dict[str, str] = {}
    merged_id_to_path: dict[str, str] = {}

    # 仅 src_root：索引、Markdown 修复、快捷方式修复都在 src 内进行
    current_path_to_id, current_id_to_path = build_current_index([src_root])

    total_indexed += len(current_path_to_id)
    merged_path_to_id.update(current_path_to_id)
    merged_id_to_path.update(current_id_to_path)

    print(f"扫描目录: {src_root}，索引对象数: {len(current_path_to_id)}")
    md_files, md_replaced, md_unresolved = repair_markdown_links(
        [src_root],
        cache_data,
        current_id_to_path,
        args.dry_run,
    )
    lnk_files, lnk_fixed, lnk_unresolved = repair_shortcuts(
        [src_root],
        cache_data,
        current_path_to_id,
        current_id_to_path,
        args.dry_run,
    )

    total_md_files += md_files
    total_md_replaced += md_replaced
    total_lnk_files += lnk_files
    total_lnk_fixed += lnk_fixed

    refresh_cache(cache_data, merged_path_to_id, merged_id_to_path)
    if not args.dry_run:
        save_cache(cache_file, cache_data)
        print(f"缓存已更新: {cache_file}")
    else:
        print(f"[dry-run] 未写缓存: {cache_file}")

    print("----")
    print(f"索引对象总数: {total_indexed}")
    print(f"Markdown 扫描文件数: {total_md_files}, 修复链接数: {total_md_replaced}")
    print(f"快捷方式扫描数: {total_lnk_files}, 修复数: {total_lnk_fixed}")
    print(f"可替代总数: {total_md_replaced + total_lnk_fixed}")
    print(f"找不到总数: {len(md_unresolved) + len(lnk_unresolved)}")

    if md_unresolved:
        print("---- 未找到（Markdown）----")
        for md_file, broken_abs in md_unresolved:
            print(f"{md_file} -> {broken_abs}")

    if lnk_unresolved:
        print("---- 未找到（快捷方式）----")
        for lnk_file, broken_abs in lnk_unresolved:
            print(f"{lnk_file} -> {broken_abs}")

    if md_unresolved or lnk_unresolved:
        print("================================================")
        print("修复失败，请检查修复结果")
        print("================================================")
        print()
        print()
        sys.exit(1)


if __name__ == "__main__":
    main()

