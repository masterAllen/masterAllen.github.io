
def remove_suffix(name):
    return name[:name.rfind('.')]


# 将文件名的中文和英文之间加一个空格
def beautify_name(name):
    result = ''
    prev_type = None
    for ch in name:
        if '\u4e00' <= ch <= '\u9fff':
            now_type = 'CN'
        elif ch == ' ':
            now_type = 'Space'
        elif ch == '_':
            # 如果是下划线就不用加空格，并且替换为空格
            now_type = None
            ch = ' '
        else:
            now_type = 'EN'

        if (prev_type == 'CN' and now_type == 'EN') or \
           (prev_type == 'EN' and now_type == 'CN'):
            result += ' '
        result += ch
        prev_type = now_type
    return result

if __name__ == '__main__':
    beautify_name('测试 test测试')