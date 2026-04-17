"""将 overrides 中的 javascripts、stylesheets、partials 复制到站点目录。"""
import os

os.chdir(os.path.dirname(__file__))

import utils
import settings


def main() -> None:
    overrides_dir = settings.overrides_dir
    for subdir in ["javascripts", "stylesheets"]:
        src_subdir = os.path.join(overrides_dir, subdir)
        dst_subdir = os.path.join(settings.docsdir, subdir)
        os.makedirs(dst_subdir, exist_ok=True)
        utils.copy(src_subdir, dst_subdir)

    src_subdir = os.path.join(overrides_dir, "partials")
    if os.path.exists(src_subdir):
        dst_subdir = os.path.join(settings.dstdir, "overrides", "partials")
        os.makedirs(dst_subdir, exist_ok=True)
        utils.copy(src_subdir, dst_subdir)


if __name__ == "__main__":
    main()
