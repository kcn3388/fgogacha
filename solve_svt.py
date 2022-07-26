import re


async def get_svt(rule, data):
    svt_cft = re.search(rule, data)[1].split('\\n')[1:]  # .split('\\n')
    # split('\\n')[1]号位开始是五星，后面是四星，想想办法获取全部四星
    svt_all = []
    cft_all = []

    for each in svt_cft:
        if each.startswith("ce\t"):
            svt_all = svt_cft[:svt_cft.index(each)]
            cft_all = svt_cft[svt_cft.index(each):]
            break

    for i in svt_all:
        solved = i.split('\t')
        solved[1] = int(solved[1])
        solved[2] = float(solved[2])
        solved[3] = int(solved[3])
        solved[4] = solved[4].split(', ')
        svt_all[svt_all.index(i)] = solved

    for i in cft_all:
        solved = i.split('\t')
        solved[1] = int(solved[1])
        solved[2] = float(solved[2])
        solved[3] = solved[3]
        cft = solved[4].split(', ')
        solved[4] = list(filter(None, cft))
        solved[4][-1] = solved[4][-1].replace("','", "")
        cft_all[cft_all.index(i)] = solved

    return svt_all, cft_all
