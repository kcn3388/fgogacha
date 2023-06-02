import random
import time
from typing import Tuple

from ..path_and_json import *


async def gacha(gid: int) -> Union[Tuple[int, int, int], Tuple[list, str, dict]]:
    banners = json.load(open(banner_path, encoding="utf-8"))
    banner = {}
    exists = False
    for each in banners:
        if each["group"] == gid:
            banner = each
            exists = True

    if not exists:
        print("no banner")
        return 12, 0, 0

    server: str = banner["banner"]["server"]

    gacha_data = json.load(open(gacha_path, encoding="utf-8"))
    data = {}
    for each in gacha_data:
        if each["p_id"] == banner["banner"]["id"]:
            if "s_id" in each:
                if each["s_id"] == banner["banner"]["s_id"]:
                    data = each
                    break
            else:
                data: dict = each
                break
    if len(data) == 0:
        print("data error")
        return 13, 0, 0

    pool_data = {
        "group": gid,
        "data": {}
    }
    for each in data["servants"]:
        each["weight"] /= 100
        each["weight"] = round(each["weight"], 3)
        d = {
            each["type"]: each["ids"],
            each["type"] + "_rate": each["weight"]
        }
        pool_data["data"].update(d)

    for each in data["crafts"]:
        each["weight"] /= 100
        each["weight"] = round(each["weight"], 3)
        d = {
            each["type"]: each["ids"],
            each["type"] + "_rate": each["weight"]
        }
        pool_data["data"].update(d)

    if not os.path.exists(banner_data_path):
        print("初始化数据json...")
        open(banner_data_path, 'w')
        pool_detail_data = []
    else:
        try:
            pool_detail_data = json.load(open(banner_data_path, encoding="utf-8"))
        except json.decoder.JSONDecodeError:
            pool_detail_data = []

    exists = False
    for i in range(len(pool_detail_data)):
        if pool_detail_data[i]["group"] == gid:
            pool_detail_data[i] = pool_data
            exists = True
    if not exists:
        pool_detail_data.append(pool_data)

    with open(banner_data_path, "w", encoding="utf-8") as f:
        f.write(json.dumps(pool_detail_data, indent=2, ensure_ascii=False))

    try:
        result = await get_gacha_result(pool_data["data"])
    except KeyError as e:
        sv.logger.error(f"{e}")
        return 13, 0, 0
    for each_result in result:
        card = int(random.choice(each_result[2]))
        each_result[2] = card
        if each_result[1] == "3 or 4 or 5" or each_result[1] == "4 or 5":
            for each_card in pool_data["data"]:
                if isinstance(pool_data["data"][each_card], list) and str(card) in pool_data["data"][each_card]:
                    if each_card == "svt_5":
                        each_result[1] = "5"
                    if each_card == "svt_4":
                        each_result[1] = "4"
                    if each_card == "svt_3":
                        each_result[1] = "3"
                    if each_card == "svt_pup_5":
                        each_result[1] = "up5"
                    if each_card == "svt_pup_4":
                        each_result[1] = "up4"
                    if each_card == "svt_pup_3":
                        each_result[1] = "up3"
    return result, server, data


async def get_gacha_result(pool_data: dict) -> list:
    # here is svt rate
    # if is pickup 5
    if "svt_pup_5" in pool_data:
        rate_pup_svt_5 = pool_data["svt_pup_5_rate"]
        if "svt_5_rate" in pool_data:
            rate_svt_5 = rate_pup_svt_5 + pool_data["svt_5_rate"]
        else:
            rate_svt_5 = rate_pup_svt_5
        svt_pup_5 = pool_data["svt_pup_5"]
    else:
        rate_pup_svt_5 = 0
        rate_svt_5 = pool_data["svt_5_rate"]
        svt_pup_5 = []
    if "svt_5" in pool_data:
        svt_5 = pool_data["svt_5"]
    else:
        svt_5 = None

    # if is pickup 4
    if "svt_pup_4" in pool_data:
        rate_pup_svt_4 = rate_svt_5 + pool_data["svt_pup_4_rate"]
        if "svt_4_rate" in pool_data:
            rate_svt_4 = rate_pup_svt_4 + pool_data["svt_4_rate"]
        else:
            rate_svt_4 = rate_pup_svt_4
        svt_pup_4 = pool_data["svt_pup_4"]
    else:
        rate_pup_svt_4 = 0
        rate_svt_4 = rate_svt_5 + pool_data["svt_4_rate"]
        svt_pup_4 = []
    if "svt_4" in pool_data:
        svt_4 = pool_data["svt_4"]
    else:
        svt_4 = None

    # if is pickup 3
    if "svt_pup_3" in pool_data:
        rate_pup_svt_3 = rate_svt_4 + pool_data["svt_pup_3_rate"]
        if "svt_3_rate" in pool_data:
            rate_svt_3 = rate_pup_svt_3 + pool_data["svt_3_rate"]
        else:
            rate_svt_3 = rate_pup_svt_3
        svt_pup_3 = pool_data["svt_pup_3"]
    else:
        rate_pup_svt_3 = 0
        rate_svt_3 = rate_svt_4 + pool_data["svt_3_rate"]
        svt_pup_3 = []
    if "svt_3" in pool_data:
        svt_3 = pool_data["svt_3"]
    else:
        svt_3 = None

    # here is cft rate
    # if is pickup 5 ce
    if "ce_pup_5" in pool_data:
        rate_pup_ce_5 = rate_svt_3 + pool_data["ce_pup_5_rate"]
        if "ce_5_rate" in pool_data:
            rate_ce_5 = rate_pup_ce_5 + pool_data["ce_5_rate"]
        else:
            rate_ce_5 = rate_pup_ce_5
        ce_pup_5 = pool_data["ce_pup_5"]
    else:
        rate_pup_ce_5 = 0
        rate_ce_5 = rate_svt_3 + pool_data["ce_5_rate"]
        ce_pup_5 = []
    if "ce_5" in pool_data:
        ce_5 = pool_data["ce_5"]
    else:
        ce_5 = None

    # if is pickup 4 ce
    if "ce_pup_4" in pool_data:
        rate_pup_ce_4 = rate_ce_5 + pool_data["ce_pup_4_rate"]
        if "ce_4_rate" in pool_data:
            rate_ce_4 = rate_pup_ce_4 + pool_data["ce_4_rate"]
        else:
            rate_ce_4 = rate_pup_ce_4
        ce_pup_4 = pool_data["ce_pup_4"]
    else:
        rate_pup_ce_4 = 0
        rate_ce_4 = rate_ce_5 + pool_data["ce_4_rate"]
        ce_pup_4 = []
    if "ce_4" in pool_data:
        ce_4 = pool_data["ce_4"]
    else:
        ce_4 = None

    # if is pickup 3 ce
    if "ce_pup_3" in pool_data:
        rate_pup_ce_3 = rate_ce_4 + pool_data["ce_pup_3_rate"]
        if "ce_3_rate" in pool_data:
            rate_ce_3 = rate_pup_ce_3 + pool_data["ce_3_rate"]
        else:
            rate_ce_3 = rate_pup_ce_3
        ce_pup_3 = pool_data["ce_pup_3"]
    else:
        rate_pup_ce_3 = 0
        rate_ce_3 = rate_ce_4 + pool_data["ce_3_rate"]
        ce_pup_3 = []
    if "ce_3" in pool_data:
        ce_3 = pool_data["ce_3"]
    else:
        ce_3 = None

    counter = 0
    svt_counter = 0
    gold_counter = 0
    result = []
    # 以下是根据时间戳生成随机种子以加强随机性，强烈建议不要放在循环内！除非你想体验千石一宝
    salt = 123383388
    salt += time.time()
    random.seed(salt)
    while counter < 11:
        # 以下是根据时间戳生成随机种子以加强随机性，强烈建议不要放在循环内！除非你想体验千石一宝
        # salt = 123383388
        # salt += time.time()
        # random.seed(salt)
        counter += 1
        rate = random.uniform(0, 1)

        # if counter == 1:
        #     rate = rate_ce_5
        # else:
        #     rate = rate_ce_3

        # here is svt gacha

        # if is pickup 5
        if not rate_pup_svt_5 == 0 and not svt_pup_5 == []:
            if rate <= rate_pup_svt_5:
                result.append(["svt", "up5", svt_pup_5])
                svt_counter += 1
                gold_counter += 1
            if rate_pup_svt_5 < rate <= rate_svt_5:
                if svt_5 is None:
                    result.append(["svt", "5", svt_pup_5])
                else:
                    result.append(["svt", "5", svt_5])
                svt_counter += 1
                gold_counter += 1

        # if is not pickup 5
        if rate_pup_svt_5 == 0 or svt_pup_5 == []:
            if rate <= rate_svt_5:
                result.append(["svt", "5", svt_5])
                svt_counter += 1
                gold_counter += 1

        # if is pickup 4
        if not rate_pup_svt_4 == 0 and not svt_pup_4 == []:
            if rate_svt_5 < rate <= rate_pup_svt_4:
                result.append(["svt", "up4", svt_pup_4])
                svt_counter += 1
                gold_counter += 1
            if rate_pup_svt_4 < rate <= rate_svt_4:
                if svt_4 is None:
                    result.append(["svt", "4", svt_pup_4])
                else:
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
                svt_counter += 1
            if rate_pup_svt_3 < rate <= rate_svt_3:
                if svt_3 is None:
                    result.append(["svt", "3", svt_pup_3])
                else:
                    result.append(["svt", "3", svt_3])
                svt_counter += 1

        # if is not pickup 3
        if rate_pup_svt_3 == 0 or svt_pup_3 == []:
            if rate_svt_4 < rate <= rate_svt_3:
                result.append(["svt", "3", svt_3])
                svt_counter += 1

        # if no svt in previous 10 roll, and has gold in previous 10 roll
        if counter == 11 and svt_counter == 0 and rate > rate_svt_3 and not gold_counter == 0:
            servants = []
            if svt_5 is not None:
                servants += svt_5

            if svt_4 is not None:
                servants += svt_4

            if svt_3 is not None:
                servants += svt_3

            # if exists pickup 5
            if not svt_pup_5 == []:
                servants += svt_pup_5

            # if exists pickup 4
            if not svt_pup_4 == []:
                servants += svt_pup_4

            # if exists pickup 3
            if not svt_pup_3 == []:
                servants += svt_pup_3

            if len(result) < 11:
                result.append(["svt", "3 or 4 or 5", servants])
            else:
                result[-1] = ["svt", "3 or 4 or 5", servants]
            break

        # if no svt in previous 10 roll or last roll is svt 3, and no gold in previous 10 roll
        if counter == 11 and gold_counter == 0:
            if svt_counter == 0 or (result[-1][0] == "svt" and result[-1][1] == "3"):
                servants = []
                if svt_5 is not None:
                    servants += svt_5

                if svt_4 is not None:
                    servants += svt_4

                # if exists pickup 5
                if not svt_pup_5 == []:
                    servants += svt_pup_5

                # if exists pickup 4
                if not svt_pup_4 == []:
                    servants += svt_pup_4

                if len(result) < 11:
                    result.append(["svt", "4 or 5", servants])
                else:
                    result[-1] = ["svt", "3 or 4 or 5", servants]
                break

        # now is cft gacha
        # if is pickup 5 ce
        if not rate_pup_ce_5 == 0 and not ce_pup_5 == []:
            if rate_svt_3 < rate <= rate_pup_ce_5:
                result.append(["cft", "up5", ce_pup_5])
                gold_counter += 1
            if rate_pup_ce_5 < rate <= rate_ce_5:
                if ce_5 is None:
                    result.append(["cft", "5", ce_pup_5])
                else:
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
                gold_counter += 1
            if rate_pup_ce_4 < rate <= rate_ce_4:
                if ce_4 is None:
                    result.append(["cft", "4", ce_pup_4])
                else:
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
                if ce_3 is None:
                    result.append(["cft", "3", ce_pup_3])
                else:
                    result.append(["cft", "3", ce_3])

        # if is not pickup 3 ce
        if rate_pup_ce_3 == 0 or ce_pup_3 == []:
            if rate_ce_4 < rate <= rate_ce_3:
                result.append(["cft", "3", ce_3])

        # if no gold in previous 10 roll, and have svt in previous 10 roll
        if counter == 11 and gold_counter == 0 and not svt_counter == 0 and rate > rate_ce_4:
            crafts = []
            if ce_5 is not None:
                crafts += ce_5

            if ce_4 is not None:
                crafts += ce_4

            # if exists pickup 5
            if not ce_pup_5 == []:
                crafts += ce_pup_5

            # if exists pickup 4
            if not ce_pup_4 == []:
                crafts += ce_pup_4

            if len(result) < 11:
                result.append(["cft", "4 or 5", crafts])
            else:
                result[-1] = ["cft", "4 or 5", crafts]
            break

    return result
