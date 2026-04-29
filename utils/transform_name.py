
def remove_suffix(name):
    return name[:name.rfind('.')]


# 将文件名的中文和英文之间加一个空格点号除外
def beautify_name(name):
    if '#不上传' in name:
        name = name.replace('#不上传', '')

    # result = ''
    # prev_type = None
    # for ch in name:
    #     if ('\u4e00' <= ch <= '\u9fff'):
    #         now_type = 'CN'
    #     elif ch == ' ':
    #         now_type = 'Space'
    #     # elif ch == '_':
    #     #     # 如果是下划线就不用加空格，并且替换为空格
    #     #     now_type = None
    #     #     ch = ' '
    #     elif ch == '.' or ch == ':' or ch == '-':
    #         now_type = None
    #     elif ch == '\uff09' or ch == '\uff08' or ch == '\uff1a':
    #         # 如果是中文括号或者中文冒号，那就不要加空格
    #         now_type = None
    #     else:
    #         now_type = 'EN'

    #     if (prev_type == 'CN' and now_type == 'EN') or \
    #        (prev_type == 'EN' and now_type == 'CN'):
    #         result += ' '
    #     result += ch
    #     prev_type = now_type

    return name

if __name__ == '__main__':
    beautify_name('04.常见检测：文字（text 模块）.md')