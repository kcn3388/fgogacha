from hoshino import aiorequests, config
from bs4 import BeautifulSoup
import json
import os
import traceback
from .solve_svt import *

runtime_path = os.path.dirname(__file__)
pools_path = os.path.join(runtime_path, 'data/pools.json')
gacha_path = os.path.join(runtime_path, 'data/gacha.json')
icons_path = os.path.join(runtime_path, 'data/icons.json')


async def getgachapools():
    try:
        pool_url = "https://fgo.wiki/w/%E6%8A%BD%E5%8D%A1%E6%A8%A1%E6%8B%9F%E5%99%A8"
        print(f"Downloading {pool_url} for pools.json")
        pools_page = await aiorequests.get(pool_url, timeout=20, verify=config.RES_DIR + "ca-certificates.crt")
        pools = []
        gacha_data = []
        soup = BeautifulSoup(await pools_page.content, 'html.parser')
        all_a = soup.find_all("a", href=True, title=True)
        for each in all_a:
            title = each.get("title")
            href = each.get("href")
            if title.endswith("模拟器") and re.search("福袋", title) is None:
                title = title.replace("/卡池详情/模拟器", "")
                title = title.replace("/模拟器", "")
                title = title.replace("模拟器", "")
                t = {
                    "id": 0,
                    "title": title,
                    "href": 'https://fgo.wiki' + href,
                    "banner": "剧情卡池",
                    "type": "normal"
                }
                pools.append(t)
        pools = await drop_dup_pool(pools)

        print("Downloading pools for gacha.json and icons.json")
        icons = {
            "svtIcons": [],
            "cftIcons": [],
        }
        # counter = 0
        is_daily = False
        for i in pools:
            raw = await aiorequests.get(i["href"])
            data = await raw.text
            rule = re.compile("raw_str_list\s?=\s?\['(.*)'\]")
            # debug_path = os.path.join(runtime_path, f"data/html{counter}.txt")
            # counter += 1
            # with open(debug_path, "w", encoding="utf-8") as f:
            #     f.write(data)

            soup2 = BeautifulSoup(await raw.content, 'html.parser')
            s = soup2.find('a', class_='mw-selflink selflink')

            if s is not None:
                i["banner"] = s.string
            else:
                i["banner"] = i["title"]

            print(i["banner"])

            # 暂时屏蔽日替池，日替池不好算
            svt_counter = 0
            svt_cft = re.search(rule, data)[1].split('\\n')[1:]
            for each in svt_cft:
                if each.startswith("svt\t5"):
                    svt_counter += 1
            if svt_counter > 4:
                print("multi pickup, solve it alone")
                i["type"] = "daily pickup"
                is_daily = True

            if not is_daily:
                svt_all, cft_all = await get_svt(rule, data)
                g = {
                    "p_id": i["id"],
                    "banner": i["banner"],
                    "servants": [],
                    "crafts": []
                }
                for j in svt_all:
                    if j[3] == 1:
                        j[0] = "svt_pup"
                    j[0] = j[0] + "_" + str(j[1])
                    servants = {
                        "type": j[0],
                        "star": j[1],
                        "weight": j[2],
                        "display": j[3],
                        "ids": j[4]
                    }
                    g["servants"].append(servants)
                for j in cft_all:
                    if j[3] == "1":
                        j[0] = "ce_pup"
                    j[0] = j[0] + "_" + str(j[1])
                    crafts = {
                        "type": j[0],
                        "star": j[1],
                        "weight": j[2],
                        "display": j[3],
                        "ids": j[4]
                    }
                    g["crafts"].append(crafts)
                gacha_data.append(g)
                if len(icons["svtIcons"]) + len(icons["cftIcons"]) == 0:
                    svticonlist = re.search("svt_icons\s?=\s?(\[.*?\])", data)[1]
                    svticonlist = data_preprocessing(svticonlist)
                    svticonlist = svticonlist.split("\t")
                    for k in svticonlist:
                        icons["svtIcons"].append(k)
                    cfticonlist = re.search("cft_icons\s?=\s?(\[.*?\])", data)[1]
                    cfticonlist = data_preprocessing(cfticonlist)
                    cfticonlist = cfticonlist.split("\t")
                    for k in cfticonlist:
                        icons["cftIcons"].append(k)

            if is_daily:
                print("go to solve daily pickup")
                sublist = await get_multi_svt(data)
                daily = {
                    "id": i["id"],
                    "title": i["title"],
                    "href": i["href"],
                    "banner": i["banner"],
                    "type": i["type"],
                    "sub_pool": []
                }
                sub_p_counter = 0
                for each in sublist:
                    sub_title = each[0]
                    svt_all = each[1]
                    cft_all = each[2]
                    sub_p = {
                        "id": sub_p_counter,
                        "sub_title": sub_title
                    }
                    daily["sub_pool"].append(sub_p)

                    g = {
                        "p_id": i["id"],
                        "s_id": sub_p_counter,
                        "banner": i["banner"],
                        "sub_title": sub_title,
                        "servants": [],
                        "crafts": []
                    }
                    sub_p_counter += 1
                    for j in svt_all:
                        if j[3] == 1:
                            j[0] = "svt_pup"
                        j[0] = j[0] + "_" + str(j[1])
                        servants = {
                            "type": j[0],
                            "star": j[1],
                            "weight": j[2],
                            "display": j[3],
                            "ids": j[4]
                        }
                        g["servants"].append(servants)
                    for j in cft_all:
                        if j[3] == "1":
                            j[0] = "ce_pup"
                        j[0] = j[0] + "_" + str(j[1])
                        crafts = {
                            "type": j[0],
                            "star": j[1],
                            "weight": j[2],
                            "display": j[3],
                            "ids": j[4]
                        }
                        g["crafts"].append(crafts)
                    gacha_data.append(g)
                    if len(icons["svtIcons"]) + len(icons["cftIcons"]) == 0:
                        svticonlist = re.search("svt_icons\s?=\s?(\[.*?\])", data)[1]
                        svticonlist = data_preprocessing(svticonlist)
                        svticonlist = svticonlist.split("\t")
                        for k in svticonlist:
                            icons["svtIcons"].append(k)
                        cfticonlist = re.search("cft_icons\s?=\s?(\[.*?\])", data)[1]
                        cfticonlist = data_preprocessing(cfticonlist)
                        cfticonlist = cfticonlist.split("\t")
                        for k in cfticonlist:
                            icons["cftIcons"].append(k)

                is_daily = False
                pools[pools.index(i)] = daily

        with open(pools_path, "w", encoding="utf-8") as f:
            f.write(json.dumps(pools, indent=2, ensure_ascii=False))

        with open(gacha_path, "w", encoding="utf-8") as f:
            f.write(json.dumps(gacha_data, indent=2, ensure_ascii=False))

        with open(icons_path, "w", encoding="utf-8") as f:
            f.write(json.dumps(icons, indent=2, ensure_ascii=False))

        print("finish...")
        return 0

    except Exception as e:
        print(traceback.format_exc())
        return e


def data_preprocessing(string):
    s = string.replace("[", "")
    s = s.replace("]", "")
    s = s.replace("\",", "\t")
    s = s.replace("\"", "")
    return s


async def drop_dup_pool(pools):
    print("start drop duplicate pool")
    pools_out = [dict(t) for t in set([tuple(d.items()) for d in pools])]
    counter = 0
    for each in pools_out:
        each["id"] = counter
        counter += 1
    return pools_out
