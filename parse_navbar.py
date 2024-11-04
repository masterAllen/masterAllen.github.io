import os

def parse_rules(pth):
    # 检查文件夹里面有没有 .pages 文件，如果有则进行解析
    navbar_rules = []
    now_type = None
    with open(pth, 'r', encoding='utf8') as f:
        for line in f:
            if 'use_filename' in line:
                now_type = 'use_filename'
            else:
                # 1. xxxx
                re_str = line[line.find(' ')+1:]
                navbar_rules.append((now_type, re_str))
    return navbar_rules

            