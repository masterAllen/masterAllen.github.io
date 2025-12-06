import os
import re

def parse_rules(pth):
    def remove_number_prefix(s):
        return re.sub(r'^\d+\.\s*', '', s)

    navbar_rules = {'title': [], 'order': []}

    if not os.path.exists(pth):
        return navbar_rules

    with open(pth, 'r', encoding='utf8') as f:
        now_type = None
        for line in f:
            if 'filename' in line:
                now_type = 'title'
            elif 'order' in line:
                now_type = 'order'
            elif now_type is not None:
                re_str = remove_number_prefix(line).strip()
                navbar_rules[now_type].append(re_str)
    return navbar_rules