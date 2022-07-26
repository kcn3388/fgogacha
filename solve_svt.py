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


async def get_multi_svt(data):
    card_rule = re.compile("raw_str_list\s?=\s?\['(.*)'\]")
    pup_rule = re.compile("name_list\s?=\s?\['(.*)'\]")
    sub_list = re.search(pup_rule, data)[1]
    sub_list = sub_list.split("','")
    # 日替从者列表
    sub_list = list(filter(None, sub_list))
    svt_cft = re.search(card_rule, data)[1].split('\\n')[1:]

    indexs = [0]
    for i in range(len(svt_cft)):
        if svt_cft[i].endswith(",'type\tstar\tweight\tdisplay\tids"):
            indexs.append(i + 1)

    l_i = len(indexs)
    svt_data = []
    for k in range(l_i):
        if k + 1 == l_i:
            svt_data.append(svt_cft[indexs[k]:])
        else:
            svt_data.append(svt_cft[indexs[k]: indexs[k + 1]])

    combine_list = []
    for dailys in svt_data:
        index = svt_data.index(dailys)
        svt_all = []
        cft_all = []

        for each in dailys:
            if each.startswith("ce\t"):
                svt_all = dailys[:dailys.index(each)]
                cft_all = dailys[dailys.index(each):]
                break

        for i in svt_all:
            solved = i.split('\t')
            solved[1] = int(solved[1])
            solved[2] = float(solved[2])
            solved[3] = int(solved[3])
            solved[4] = solved[4].split(', ')
            svt_all[svt_all.index(i)] = solved

        for i in cft_all:
            bak = i
            if i.endswith("','type\tstar\tweight\tdisplay\tids"):
                i = i.split("','type\tstar\tweight\tdisplay\tids")[0]
            solved = i.split('\t')
            solved[1] = int(solved[1])
            solved[2] = float(solved[2])
            solved[3] = solved[3]
            cft = solved[4].split(', ')
            solved[4] = list(filter(None, cft))
            solved[4][-1] = solved[4][-1].replace("','", "")
            i = bak
            cft_all[cft_all.index(i)] = solved

        combine_list.append([sub_list[index], svt_all, cft_all])

    return combine_list
