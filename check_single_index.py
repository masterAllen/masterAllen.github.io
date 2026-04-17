"""
检查生成目录下是否存在「仅含一个 index.md」的子目录。尽量不要有这种情况。
用法: python check_single_index.py [根目录，默认 settings.docsdir]
"""
import os
import sys

os.chdir(os.path.dirname(__file__))

import settings


def main() -> None:
    root = os.path.abspath(sys.argv[1]) if len(sys.argv) > 1 else settings.docsdir
    if not os.path.isdir(root):
        print(f"不是目录: {root}")
        sys.exit(1)

    hits: list[str] = []
    for dirpath, dirnames, filenames in os.walk(root):
        # 不深入隐藏目录（可选）
        dirnames[:] = [d for d in dirnames if not d.startswith(".")]

        names = os.listdir(dirpath)
        if len(names) != 1:
            continue
        only = names[0]
        if only.lower() == "index.md":
            hits.append(dirpath)

    print(f"扫描根目录: {root}")
    print(f"仅含 index.md 的目录数: {len(hits)}")
    for p in sorted(hits):
        print(p)


if __name__ == "__main__":
    main()
