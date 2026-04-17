# 说明

本仓库是我的个人博客，由 mkdocs 搭建，使用的主题是 mkdocs-material

## 本仓库的创建方式

通常博客都是由一堆 markdown 组成。但是我感觉学习笔记有各种各样的格式，除了 markdown，有时会直接用 word 或者 ppt 来写，有时看到好的内容会保存为照片、网页或者 pdf 等，甚至经常会有视频文件（尤其是一些系统性的课程）。

如果为了博客而强制写 markdown，我觉得受限太多，失去了意义。因此本仓库是由另一个文件夹转换而来，其中原始文件夹里面包含了各种各样的笔记，通过 python 脚本将其转换为 markdown 以此来在网页中显示。比如 pdf 文件，我会将其转为图片，然后将这些图片写入到 markdown 中，这样在网页上就能够将其显示出来了。

目前各个格式的文件转换还在开发中。我觉得肯定很多地方尚不完善，比如 word 我是用 docx2pdf 转为 pdf 后再转为图片，期间经常会报错。如果您有任何格式转换的方法和建议，烦请帮忙告知我一下，谢谢。

## 各种格式转换方式

| 格式     | 方式                                                                                                           |
| -------- | -------------------------------------------------------------------------------------------------------------- |
| markdown | 直接转换，会检查其中的引用链接，找到引用的文件（通常是图片），将其移动到资源仓库中，然后修改原始文件的链接内容 |
| ipynb    | 使用 jupyter nbconvert 进行转换                                                                                |
| pdf      | 使用 pdfium 转为图片，将图片合成到一个 markdown 中                                                             |
| word     | 使用 docx2pdf 转为 pdf，再转为图片，将图片合成到一个 markdown 中                                               |
| ppt      | 使用 pptx2pdf 转为 pdf，再转为图片，将图片合成到一个 markdown 中                                               |

## 主流程

`main.py` 使用流水线方式串联步骤：

| 步骤 | 脚本 | 作用 |
| --- | --- | --- |
| 01 | `repair_src_links.py` | 修复源目录链接，处理文件改名/路径变化导致的失效引用（基于文件 ID 查找）。 |
| 02 | `base_build.py` | 执行主转换流程，遍历源目录并生成目标文件，同时更新缓存以支持增量构建。 |
| 03 | `delete_unnecessary_files.py` | 清理生成目录中的多余文件（含失效转换结果与不再使用的资源）。 |
| 04 | `postprocess_dst_mds.py` | 后处理目标 Markdown 格式（列表、details、箭头等），提升 mkdocs 渲染效果。 |
| 05 | `repair_dst_links.py` | 修复目标 Markdown 中的引用链接，将资源链接对齐到目标目录。 |
| 06 | `compress_images.py` | 压缩图片资源（jpg / png 分别处理），减少体积且尽量避免改动链接后缀。 |
| 07 | `gen_archive.py` | 生成归档页面。 |
| 08 | `gen_navbar.py` | 生成侧边栏导航结构。 |
| 09 | `check_single_index.py` | 检查生成目录中“仅含 index.md”的目录，避免最终展示突兀。 |
| 10 | `write_asset_rawdir.py` | 在 asset 子目录写入 `rawdir.txt`，记录原始文件路径，便于追溯。 |
| 11 | `report_asset_sizes.py` | 统计 asset 目录大小。 |
| 12 | `delete_unnecessary_files.py` | 再次执行收尾清理。 |