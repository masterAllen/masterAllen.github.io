# 站点构建流水线：按顺序执行各脚本
import os
import subprocess
import sys
import time

os.chdir(os.path.dirname(__file__))

# (步骤说明, 脚本文件名)
PIPELINE = [
    ("检查源目录链接（repair_src_links）", "repair_src_links.py"),
    ("基础构建（base_build）", "base_build.py"),
    ("生成目录 Markdown 格式处理（postprocess_dst_mds）", "postprocess_dst_mds.py"),
    ("生成目录链接修复（repair_dst_links）", "repair_dst_links.py"),
    ("生成链接副本（build_links）", "build_links.py"),
    ("删除多余生成文件（delete_unnecessary_files）", "delete_unnecessary_files.py"),
    ("压缩图片（compress_images）", "compress_images.py"),
    ("生成归档页（gen_archive）", "gen_archive.py"),
    ("生成导航（gen_navbar）", "gen_navbar.py"),
    ("检查单 index 目录（check_single_index）", "check_single_index.py"),
    ("写入 asset rawdir（write_asset_rawdir）", "write_asset_rawdir.py"),
    ("统计 asset 体积（report_asset_sizes）", "report_asset_sizes.py"),
    ("再次清理多余文件（delete_unnecessary_files）", "delete_unnecessary_files.py"),
]


def _print_banner() -> None:
    line = "=" * 64
    print(f"\n{line}")
    print("  Blog 构建流水线")
    print(line)


def _run_step(step_no: int, total: int, title: str, script: str) -> None:
    line = "-" * 64
    print(f"\n{line}")
    print(f"  [{step_no:02d}/{total:02d}] {title}")
    print(f"  命令: {sys.executable} {script}")
    print(line)
    t0 = time.perf_counter()
    subprocess.run([sys.executable, script], check=True)
    elapsed = time.perf_counter() - t0
    print(f"  状态: 完成  |  耗时: {elapsed:.2f}s")


def main() -> None:
    total = len(PIPELINE)
    t_all = time.perf_counter()
    _print_banner()

    for i, (title, script) in enumerate(PIPELINE, start=1):
        _run_step(i, total, title, script)

    print("\n" + "=" * 64)
    print(f"  全部完成  |  总耗时: {time.perf_counter() - t_all:.2f}s")
    print("=" * 64 + "\n")


if __name__ == "__main__":
    main()
