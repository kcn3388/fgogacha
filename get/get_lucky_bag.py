import math
import random
import re
import time

from bs4 import BeautifulSoup

from .solve_svt import get_multi_svt
from ..path_and_json import *


async def get_all_lucky_bag(crt_file: Union[str, bool] = False) -> Union[Exception, dict]:
    lucky_bag = {
        "abstract": "",
        "cn": [],
        "jp": []
    }
    try:
        lucky_bag_url = "https://fgo.wiki/w/%E7%A6%8F%E8%A2%8B%E5%8F%AC%E5%94%A4"
        print(f"Downloading {lucky_bag_url} for lucky_bag.json")
        try:
            lucky_bag_page = await aiorequests.get(lucky_bag_url, timeout=20, verify=crt_file, headers=headers)
        except OSError:
            lucky_bag_page = await aiorequests.get(lucky_bag_url, timeout=20, verify=False, headers=headers)
        except Exception as e:
            return e
        soup = BeautifulSoup(await lucky_bag_page.content, 'html.parser')

        abstract = soup.find("span", id="概况").find_next("p").text.strip()
        lucky_bag["abstract"] = abstract

        bags: List[BeautifulSoup] = soup.find_all("span")
        for each_bag in bags:
            if each_bag.get("class") and "toc" not in each_bag.get("class")[0]:
                if "福袋" not in each_bag.text:
                    continue
                page_url = each_bag.find_next("a")
                sim_url = ""
                if "模拟器" in page_url.get("title"):
                    sim_url = page_url.get("href")
                    if "(%E6%97%A5%E6%9C%8D)" in sim_url:
                        sim_url = sim_url.replace("(%E6%97%A5%E6%9C%8D)", "")
                    page_url = page_url.find_next("a")

                pool_img = page_url.find_next("img")
                href = page_url.get("href")
                page = {
                    "name": each_bag.text,
                    "title": page_url.get("title"),
                    "href": href,
                    "img": pool_img.get("data-src"),
                    "sim": sim_url,
                    "time_start": "",
                    "time_end": "",
                    "time_delta": ""
                }

                time_soup = BeautifulSoup(await get_content(f"https://fgo.wiki{href}", crt_file), 'html.parser')
                try:
                    time_info = time_soup.find(text="日服卡池信息(使用日本标准时间)")
                    time_start = time_info.find_next("td")
                    time_end = time_start.find_next("td")
                    time_delta = time_end.find_next("td")
                    page["time_start"] = f'{time_start.string.strip()}（JST）'
                    page["time_end"] = f'{time_end.string.strip()}（JST）'
                    page["time_delta"] = f'{time_delta.string.strip()}（JST）'
                except AttributeError:
                    try:
                        time_info = time_soup.find(text="日服卡池信息")
                        time_start = time_info.find_next("td")
                        time_end = time_start.find_next("td")
                        time_delta = time_end.find_next("td")
                        page["time_start"] = f'{time_start.string.strip()}（JST）'
                        page["time_end"] = f'{time_end.string.strip()}（JST）'
                        page["time_delta"] = f'{time_delta.string.strip()}（JST）'
                    except Exception as e:
                        sv_lucky.logger.error(f"{e}")
                        pass

                detail_msg = await get_lucky_bag_detail(page, crt_file)
                if isinstance(detail_msg, list):
                    page["detail"] = detail_msg

                lucky_bag["jp"].append(page)

        lucky_bag["cn"] = lucky_bag.get("jp")[:-2]
        return lucky_bag

    except Exception as e:
        sv_lucky.logger.error(f"{e}")
        return e


async def get_lucky_bag_detail(bag: dict, crt_file: Union[str, bool] = False) -> Union[Exception, list, int]:
    bag_url = f"https://fgo.wiki{bag['sim']}"
    no_sim = False
    if not bag['sim']:
        bag_url = f"https://fgo.wiki{bag['href']}"
        no_sim = True

    try:
        bag_detail_page = await aiorequests.get(bag_url, timeout=20, verify=crt_file, headers=headers)
    except OSError:
        bag_detail_page = await aiorequests.get(bag_url, timeout=20, verify=False, headers=headers)
    except Exception as e:
        return e

    if not bag_detail_page.status_code == 200:
        return 1

    raw_html = await bag_detail_page.text

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


async def send_lucky_bag(select_lucky: Union[dict, list], crt_file: Union[str, bool] = False, is_next=False) -> list:
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
        image_bytes = await get_content(lucky_img, crt_file)
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
            image_bytes = await get_content(lucky_img, crt_file)
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
