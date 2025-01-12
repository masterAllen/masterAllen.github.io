def add_topinfo(fobj, comments=True, hide=[]):
    if not comments and len(hide) == 0:
        return

    fobj.writelines('---\n')
    if comments:
        fobj.writelines('comments: true\n')
    if len(hide) > 0:
        fobj.writelines('hide: true\n')
        for h in hide:
            fobj.writelines(f'  - {h}\n')
    fobj.writelines('---\n')
    fobj.flush()