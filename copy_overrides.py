"""将 overrides 中的静态资源和主题模板复制到站点目录。"""
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

    dst_overrides_dir = os.path.join(settings.dstdir, "overrides")
    os.makedirs(dst_overrides_dir, exist_ok=True)
    for name in os.listdir(overrides_dir):
        src_path = os.path.join(overrides_dir, name)
        if os.path.isfile(src_path):
            utils.copy(src_path, os.path.join(dst_overrides_dir, name))

    src_subdir = os.path.join(overrides_dir, "partials")
    if os.path.exists(src_subdir):
        dst_subdir = os.path.join(dst_overrides_dir, "partials")
        os.makedirs(dst_subdir, exist_ok=True)
        utils.copy(src_subdir, dst_subdir)


if __name__ == "__main__":
    main()
