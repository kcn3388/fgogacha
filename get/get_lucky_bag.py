import math
import random
import re
import time

from bs4 import BeautifulSoup
from datetime import datetime
from urllib.parse import quote

from .solve_svt import get_multi_svt
from ..path_and_json import *


async def get_all_lucky_bag(session: ClientSession) -> Union[Exception, dict]:
    lucky_bag = {
        "abstract": "",
        "cn": [],
        "jp": []
    }
    try:
        raw_bag_url = "https://fgo.wiki/w/福袋召唤"
        lucky_bag_url = "https://fgo.wiki/index.php?title=福袋召唤&action=edit"
        sv.logger.info(f"Downloading {lucky_bag_url} for lucky_bag.json")
        try:
            raw_html = (await get_content(raw_bag_url, session)).decode()
            raw_lucky = BeautifulSoup(
                await get_content(lucky_bag_url, session), 'html.parser'
            ).find("textarea").text.replace("<br />", "")
        except Exception as e:
            return e
    except Exception as e:
        sv_lucky.logger.error(f"{e}")
        return e
    lucky_bag["abstract"] = re.search(r"==概况==\n([\s\S]+?)\n\n==", raw_lucky).group(1).strip()
    lucky = re.search(
        r"==卡池信息==[\s\S]+", raw_lucky
    ).group(0).replace("==卡池信息==", "").replace("\n\n", "\n").strip()
    bags = re.findall(r"===(.+)===\n(\[\[文件[\s\S]+?)\n{{", lucky) if lucky else ""
    if not bags:
        return AttributeError("Empty Lucky")
    for each_bag in bags:
        info = each_bag[1].split("\n")
        bag: dict = {
            "name": each_bag[0],
            "title": re.search(r"link=(.+)]]", info[-1]).group(1),
            "href": f'/w/{re.search(r"link=(.+)]]", info[-1]).group(1)}',
            "img": "",
            "sim": "",
            "time_start": "",
            "time_end": "",
            "time_delta": ""
        }
        sim = f'/w/{re.search(r"link=(.+)]]", info[0]).group(1).replace(" ", "_")}' if len(info) > 1 else ""
        img_file = re.search(r"文件:(.+\.png)", info[-1]).group(1).replace(" ", "_")
        img = re.search(rf"https://media.fgo.wiki/./../{quote(img_file)}", raw_html).group(0).replace(quote(img_file), img_file)
        bag["img"] = img
        if "四周年" in bag["name"]:
            sim = sim.replace("2019", "2020").replace("(日服)", "")
        if "定命指定召唤" in bag["name"]:
            sim = ""
        bag["sim"] = sim
        try:
            new_href = bag['href'].replace("/w/", "")
            raw_time = BeautifulSoup(
                await get_content(f"https://fgo.wiki/index.php?title={new_href}&action=edit", session),
                'html.parser'
            ).find("textarea").text
            time_start = datetime.strptime(re.search(r"\|卡池开始时间jp=(.+)", raw_time).group(1), "%Y-%m-%d %H:%M")
            time_end = datetime.strptime(re.search(r"\|卡池结束时间jp=(.+)", raw_time).group(1), "%Y-%m-%d %H:%M")
            time_delta = time_end - time_start
            bag["time_start"] = time_start.strftime(
                f"%Y年%m月%d日({week_list[time_start.weekday()]}) %H:%M（JST）"
            )
            bag["time_end"] = time_end.strftime(
                f"%Y年%m月%d日({week_list[time_end.weekday()]}) %H:%M（JST）"
            )
            sec = time_delta.seconds
            bag["time_delta"] = f'{time_delta.days}天{int(sec / 3600)}小时{int((sec % 3600) / 60)}分钟（JST）'
        except Exception as e:
            sv_lucky.logger.error(f"{e}")
            pass

        detail_msg = await get_lucky_bag_detail(bag, session)
        if isinstance(detail_msg, list):
            bag["detail"] = detail_msg

        lucky_bag["jp"].append(bag)

    lucky_bag["cn"] = lucky_bag.get("jp")[:-3]
    return lucky_bag


async def get_lucky_bag_detail(bag: dict, session: ClientSession) -> Union[Exception, list, int]:
    bag_url = f"https://fgo.wiki{bag['sim']}"
    no_sim = False
    if not bag['sim']:
        bag_url = f"https://fgo.wiki{bag['href']}"
        no_sim = True

    try:
        raw_html = (await get_content(bag_url, session)).decode()
    except Exception as e:
        return e

    if no_sim:
        return 1

    else:
        data_list = await get_multi_svt(raw_html)
        sub_bag = []
        for each in data_list:
            sub_title = each[0]
            svt_all = each[1]
            cft_all = each[2]

            g = {
                "sub_title": sub_title,
                "servants": [],
                "crafts": []
            }
            for j in svt_all:
                j[0] = f"{j[0]}_{j[1]}"
                new_ids = [re.search(r"\d+", each_id).group(0) for each_id in j[4]]
                servants = {
                    "type": j[0],
                    "star": j[1],
                    "weight": j[2],
                    "display": j[3],
                    "ids": new_ids
                }
                g["servants"].append(servants)
            for j in cft_all:
                j[0] = f"{j[0]}_{j[1]}"
                new_ids = [re.search(r"\d+", each_id).group(0) for each_id in j[4]]
                crafts = {
                    "type": j[0],
                    "star": j[1],
                    "weight": j[2],
                    "display": j[3],
                    "ids": new_ids
                }
                g["crafts"].append(crafts)
            sub_bag.append(g)

        return sub_bag


async def get_lucky_bag_image(bag_pools: list) -> list:
    nodes = []
    counter = 1
    for each_pool in bag_pools:
        pool_title = each_pool["sub_title"]
        svt_s: list = each_pool["servants"][0]["ids"]
        img_path = [os.path.join(svt_path, f"Servant{str(svt).zfill(3)}.jpg") for svt in svt_s]

        cards = []
        for each in img_path:
            cards.append(Image.open(each).resize((66, 72)))

        rows = math.ceil(len(cards) / 4)
        cols = len(cards) if len(cards) < 4 else 4

        target = Image.open(frame_path).resize(((66 * cols) + 40, (72 * rows) + 40))
        r_counter = 0
        c_counter = 0
        for each in cards:
            target.paste(each, ((66 * c_counter) + 20, (72 * r_counter) + 20))
            c_counter += 1
            if c_counter >= cols:
                r_counter += 1
                if r_counter >= rows:
                    break
                else:
                    c_counter = 0

        card_msg = f'编号【{counter}】：' \
                   f'\n{pool_title}包含的五星从者：\n{gen_ms_img(target)}'
        nodes.append(gen_node(card_msg.strip()))
        counter += 1

    return nodes


async def send_lucky_bag(select_lucky: Union[dict, list], session: ClientSession, is_next=False) -> list:
    lucky_nodes = []
    if is_next:
        lucky_nodes.append(gen_node("国服千里眼卡池："))
    if isinstance(select_lucky, dict):
        lucky_msg = f"福袋名称：{select_lucky['name']}\n" \
                    f"关联卡池：{select_lucky['title']}\n" \
                    f"开放时间：{select_lucky['time_start']}\n" \
                    f"结束时间：{select_lucky['time_end']}\n" \
                    f"卡池时长：{select_lucky['time_delta']}\n"
        lucky_img = f"https://fgo.wiki{select_lucky['img']}"
        image_bytes = await get_content(lucky_img, session)
        if isinstance(image_bytes, Exception):
            return [gen_node("获取失败")]
        lucky_msg += gen_ms_img(image_bytes)
        lucky_nodes.append(gen_node(lucky_msg))

        if "detail" in select_lucky:
            bag_pools: list = select_lucky["detail"]
            card_msg = await get_lucky_bag_image(bag_pools)
            lucky_nodes.extend(card_msg)

    if isinstance(select_lucky, list):
        counter = 1
        for each_bag in select_lucky:
            sub_node: list = []
            lucky_msg = f"编号【{counter}】：\n" \
                        f"福袋名称：{each_bag['name']}\n" \
                        f"关联卡池：{each_bag['title']}\n" \
                        f"开放时间：{each_bag['time_start']}\n" \
                        f"结束时间：{each_bag['time_end']}\n" \
                        f"卡池时长：{each_bag['time_delta']}\n"
            lucky_img = f"https://fgo.wiki{each_bag['img']}"
            image_bytes = await get_content(lucky_img, session)
            if isinstance(image_bytes, Exception):
                continue
            counter += 1
            lucky_msg += gen_ms_img(image_bytes)
            sub_node.append(gen_node(lucky_msg))
            if "detail" in each_bag:
                bag_pools: list = each_bag["detail"]
                card_msg = await get_lucky_bag_image(bag_pools)
                sub_node.extend(card_msg)

            lucky_nodes.append(gen_node(sub_node))

    return lucky_nodes


async def get_lucky_gacha(select_lucky_pool: dict) -> list:
    pool_data = {}
    for each in select_lucky_pool["servants"]:
        each["weight"] /= 100
        each["weight"] = round(each["weight"], 3)
        d = {
            each["type"]: each["ids"],
            each["type"] + "_rate": each["weight"]
        }
        pool_data.update(d)

    for each in select_lucky_pool["crafts"]:
        each["weight"] /= 100
        each["weight"] = round(each["weight"], 3)
        d = {
            each["type"]: each["ids"],
            each["type"] + "_rate": each["weight"]
        }
        pool_data.update(d)

    result = await get_lucky_result(pool_data)

    for each_result in result:
        card = int(random.choice(each_result[2]))
        each_result[2] = card

    return result


async def get_lucky_result(pool_data: dict) -> list:
    # here is svt rate
    rate_svt_5 = pool_data["svt_5_rate"]
    svt_5 = pool_data["svt_5"]

    rate_svt_4 = rate_svt_5 + pool_data["svt_4_rate"]
    svt_4 = pool_data["svt_4"]

    rate_svt_3 = rate_svt_4 + pool_data["svt_3_rate"]
    svt_3 = pool_data["svt_3"]

    # here is cft rate
    rate_ce_5 = rate_svt_3 + pool_data["ce_5_rate"]
    ce_5 = pool_data["ce_5"]

    rate_ce_4 = rate_ce_5 + pool_data["ce_4_rate"]
    ce_4 = pool_data["ce_4"]

    rate_ce_3 = rate_ce_4 + pool_data["ce_3_rate"]
    ce_3 = pool_data["ce_3"]

    counter = 0
    svt_counter = 0
    svt_5_counter = 0
    svt_4_counter = 0
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

        # here is svt gacha
        # if is not pickup 5
        if rate <= rate_svt_5:
            result.append(["svt", "5", svt_5])
            svt_counter += 1
            svt_5_counter += 1

        if rate_svt_5 < rate <= rate_svt_4:
            result.append(["svt", "4", svt_4])
            svt_counter += 1
            svt_4_counter += 1

        if rate_svt_4 < rate <= rate_svt_3:
            result.append(["svt", "3", svt_3])

        # if no gold svt in previous 9 roll:
        if counter == 9 and svt_counter == 0:
            result.append(["svt", "5", svt_5])
            result.append(["svt", "4", svt_4])
            break

        # if no svt_5 in previous 10 roll:
        if counter == 10 and svt_5_counter == 0:
            result.append(["svt", "5", svt_5])
            break

        # if no svt_4 in previous 10 roll:
        if counter == 10 and svt_4_counter == 0:
            result.append(["svt", "4", svt_4])
            break

        # now is cft gacha
        if rate_svt_3 < rate <= rate_ce_5:
            result.append(["cft", "5", ce_5])

        if rate_ce_5 < rate <= rate_ce_4:
            result.append(["cft", "4", ce_4])

        if rate_ce_4 < rate <= rate_ce_3:
            result.append(["cft", "3", ce_3])

    return result
