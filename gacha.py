import random
import json
import os
import time

runtime_path = os.path.dirname(__file__)
banner_path = os.path.join(runtime_path, 'data/banner.json')
gacha_path = os.path.join(runtime_path, 'data/gacha.json')
banner_data_path = os.path.join(runtime_path, 'data/b_data.json')


async def gacha(gid):
    banners = json.load(open(banner_path, encoding="utf-8"))
    banner = {}
    exists = False
    for each in banners:
        if each["group"] == gid:
            banner = each
            exists = True

    if not exists:
        print("no banner")
        return 12

    gacha_data = json.load(open(gacha_path, encoding="utf-8"))
    data = {}
    for each in gacha_data:
        if each["p_id"] == banner["banner"]["id"]:
            data = each
            break
    if len(data) == 0:
        print("data error")
        return 13

    pool_data = {}
    for each in data["servants"]:
        each["weight"] /= 100
        each["weight"] = round(each["weight"], 3)
        d = {
            each["type"]: each["ids"],
            each["type"] + "_rate": each["weight"]
        }
        pool_data.update(d)

    for each in data["crafts"]:
        each["weight"] /= 100
        each["weight"] = round(each["weight"], 3)
        d = {
            each["type"]: each["ids"],
            each["type"] + "_rate": each["weight"]
        }
        pool_data.update(d)

    with open(banner_data_path, "w", encoding="utf-8") as f:
        f.write(json.dumps(pool_data, indent=2, ensure_ascii=False))

    result = await get_result(pool_data)
    return result


async def get_result(pool_data):
    # here is svt rate
    # if is pickup 5
    if "svt_pup_5" in pool_data:
        rate_pup_svt_5 = pool_data["svt_pup_5_rate"]
        rate_svt_5 = rate_pup_svt_5 + pool_data["svt_5_rate"]
        svt_pup_5 = pool_data["svt_pup_5"]
    else:
        rate_pup_svt_5 = 0
        rate_svt_5 = pool_data["svt_5_rate"]
        svt_pup_5 = []
    svt_5 = pool_data["svt_5"]

    # if is pickup 4
    if "svt_pup_4" in pool_data:
        rate_pup_svt_4 = rate_svt_5 + pool_data["svt_pup_4_rate"]
        rate_svt_4 = rate_pup_svt_4 + pool_data["svt_4_rate"]
        svt_pup_4 = pool_data["svt_pup_4"]
    else:
        rate_pup_svt_4 = 0
        rate_svt_4 = rate_svt_5 + pool_data["svt_4_rate"]
        svt_pup_4 = []
    svt_4 = pool_data["svt_4"]

    # if is pickup 3
    if "svt_pup_3" in pool_data:
        rate_pup_svt_3 = rate_svt_4 + pool_data["svt_pup_3_rate"]
        rate_svt_3 = rate_pup_svt_3 + pool_data["svt_3_rate"]
        svt_pup_3 = pool_data["svt_pup_3"]
    else:
        rate_pup_svt_3 = 0
        rate_svt_3 = rate_svt_4 + pool_data["svt_3_rate"]
        svt_pup_3 = []
    svt_3 = pool_data["svt_3"]

    # here is cft rate
    # if is pickup 5 ce
    if "ce_pup_5" in pool_data:
        rate_pup_ce_5 = rate_svt_3 + pool_data["ce_pup_5_rate"]
        rate_ce_5 = rate_pup_ce_5 + pool_data["ce_5_rate"]
        ce_pup_5 = pool_data["ce_pup_5"]
    else:
        rate_pup_ce_5 = 0
        rate_ce_5 = rate_svt_3 + pool_data["ce_5_rate"]
        ce_pup_5 = []
    ce_5 = pool_data["ce_5"]

    # if is pickup 4 ce
    if "ce_pup_4" in pool_data:
        rate_pup_ce_4 = rate_ce_5 + pool_data["ce_pup_4_rate"]
        rate_ce_4 = rate_pup_ce_4 + pool_data["ce_4_rate"]
        ce_pup_4 = pool_data["ce_pup_4"]
    else:
        rate_pup_ce_4 = 0
        rate_ce_4 = rate_ce_5 + pool_data["ce_4_rate"]
        ce_pup_4 = []
    ce_4 = pool_data["ce_4"]

    # if is pickup 3 ce
    if "ce_pup_3" in pool_data:
        rate_pup_ce_3 = rate_ce_4 + pool_data["ce_pup_3_rate"]
        rate_ce_3 = rate_pup_ce_3 + pool_data["ce_3_rate"]
        ce_pup_3 = pool_data["ce_pup_3"]
    else:
        rate_pup_ce_3 = 0
        rate_ce_3 = rate_ce_4 + pool_data["ce_3_rate"]
        ce_pup_3 = []
    ce_3 = pool_data["ce_3"]

    counter = 0
    svt_counter = 0
    gold_counter = 0
    result = []
    # 以下是根据时间戳生成随机种子以加强随机性，强烈建议不要放在循环内！除非你想体验千石一宝
    salt = 123383388
    salt += time.time()
    random.seed(salt)
    while counter < 12:
        counter += 1
        rate = random.uniform(0, 1)
        # here is svt gacha

        # if is not pickup 5
        if not rate_pup_svt_5 == 0 and not svt_pup_5 == []:
            if rate <= rate_pup_svt_5:
                result.append(["svt", "up5", svt_pup_5])
            if rate_pup_svt_5 < rate <= rate_svt_5:
                result.append(["svt", "5", svt_5])
            svt_counter += 1
            gold_counter += 1
        # if is not pickup 5
        if rate_pup_svt_5 == 0 or svt_pup_5 == []:
            if rate <= rate_svt_5:
                result.append(["svt", "5", svt_5])
            svt_counter += 1
            gold_counter += 1

        # if is not pickup 4
        if not rate_pup_svt_4 == 0 and not svt_pup_4 == []:
            if rate_svt_5 < rate <= rate_pup_svt_4:
                result.append(["svt", "up4", svt_pup_4])
            if rate_pup_svt_4 < rate <= rate_svt_4:
                result.append(["svt", "4", svt_4])
            svt_counter += 1
            gold_counter += 1
        # if is not pickup 4
        if rate_pup_svt_4 == 0 or svt_pup_4 == []:
            if rate_svt_5 < rate <= rate_svt_4:
                result.append(["svt", "4", svt_4])
            svt_counter += 1
            gold_counter += 1

        # if is pickup 3
        if not rate_pup_svt_3 == 0 and not svt_pup_3 == []:
            if rate_svt_4 < rate <= rate_pup_svt_3:
                result.append(["svt", "up3", svt_pup_3])
            if rate_pup_svt_3 < rate <= rate_svt_3:
                result.append(["svt", "3", svt_3])
            svt_counter += 1
        # if is not pickup 3
        if rate_pup_svt_3 == 0 or svt_pup_3 == []:
            if rate_svt_4 < rate <= rate_svt_3:
                result.append(["svt", "3", svt_3])
            svt_counter += 1

        # if no svt in previous 10 roll, and has gold in previous 10 roll
        if counter == 12 and svt_counter == 0 and rate > rate_svt_3 and not gold_counter == 0:
            servants = svt_5 + svt_4 + svt_3
            # if exists pickup 5
            if not svt_pup_5 == []:
                servants += svt_pup_5

            # if exists pickup 4
            if not svt_pup_4 == []:
                servants += svt_pup_4

            # if exists pickup 3
            if not svt_pup_3 == []:
                servants += svt_pup_3

            result.append(["svt", "3 or 4 or 5", servants])

        # if no svt in previous 10 roll, and no gold in previous 10 roll
        if counter == 12 and svt_counter == 0 and rate > rate_svt_3 and gold_counter == 0:
            servants = svt_5 + svt_4
            # if exists pickup 5
            if not svt_pup_5 == []:
                servants += svt_pup_5

            # if exists pickup 4
            if not svt_pup_4 == []:
                servants += svt_pup_4

            result.append(["svt", "4 or 5", servants])

        # now is cft gacha
        # if is pickup 5 ce
        if not rate_pup_ce_5 == 0 and not ce_pup_5 == []:
            if rate_svt_3 < rate <= rate_pup_ce_5:
                result.append(["cft", "up5", ce_pup_5])
            if rate_pup_ce_5 < rate <= rate_ce_5:
                result.append(["cft", "5", ce_5])
            gold_counter += 1
        # if is not pickup 5 ce
        if rate_pup_ce_5 == 0 or ce_pup_5 == []:
            if rate_svt_3 < rate <= rate_ce_5:
                result.append(["cft", "5", ce_5])
            gold_counter += 1

        # if is pickup 4 ce
        if not rate_pup_ce_4 == 0 and not ce_pup_4 == []:
            if rate_ce_5 < rate <= rate_pup_ce_4:
                result.append(["cft", "up4", ce_pup_4])
            if rate_pup_ce_4 < rate <= rate_ce_4:
                result.append(["cft", "4", ce_4])
            gold_counter += 1
        # if is not pickup 4 ce
        if rate_pup_ce_4 == 0 or ce_pup_4 == []:
            if rate_ce_5 < rate <= rate_ce_4:
                result.append(["cft", "4", ce_4])
            gold_counter += 1

        # if is pickup 3 ce
        if not rate_pup_ce_3 == 0 and not ce_pup_3 == []:
            if rate_ce_4 < rate <= rate_pup_ce_3:
                result.append(["cft", "up3", ce_pup_3])
            if rate_pup_ce_3 < rate <= rate_ce_3:
                result.append(["cft", "3", ce_3])
        # if is not pickup 3 ce
        if rate_pup_ce_3 == 0 or ce_pup_3 == []:
            if rate_ce_4 < rate <= rate_ce_3:
                result.append(["cft", "3", ce_3])

        # if no gold in previous 10 roll, and have svt in previous 10 roll
        if counter == 12 and gold_counter == 0 and not svt_counter == 0 and rate > rate_ce_4:
            crafts = ce_5 + ce_4
            # if exists pickup 5
            if not ce_pup_5 == []:
                crafts += ce_pup_5

            # if exists pickup 4
            if not ce_pup_4 == []:
                crafts += ce_pup_4

            result.append(["cft", "4 or 5", crafts])

    return result
