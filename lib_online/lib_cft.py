import re
from typing import Tuple
from urllib.parse import quote, unquote
from bs4 import BeautifulSoup

from .lib_json import *


async def lib_cft_online(url: str, session: ClientSession) -> Tuple[Union[Exception, str], int]:
    try:
        soup = BeautifulSoup(await get_content(url, session), 'html.parser')
    except Exception as e:
        return e, -100

    try:
        is_get = soup.find(class_="wikitable nomobile").find_all("big")
    except AttributeError:
        is_get = False

    if is_get:
        name = soup.find("title").text.split()[0]
        return name, 1
    else:
        return "在线也没找到", 0


async def lib_cft(cft_data: dict) -> dict:
    # def lib_cft_debug(sid: int = 0) -> dict:
    #     with open(all_craft_path, 'r', encoding="utf-8") as f:
    #         crafts = json.load(f)
    #     if sid:
    #         cft_data = jsonpath(crafts, f"$..[?(@.id=='{sid}')]")[0]
    #     else:
    #         cft_data = jsonpath(crafts, "$..[?(@.id=='657')]")[0]
    sv_lib.logger.info("查询礼装" + cft_data["id"] + "……")
    cft = {
        "id": cft_data["id"],
        "name": cft_data["name"],
        "name_jp": cft_data["name"],
        "name_other": None,
        "name_link": cft_data["name_link"],
        "type": cft_data["type"],
        "error": []
    }

    if "local" in cft_data:
        cft["cft_icon"] = cft_data["local"]["cft_icon"]
        cft["skill_icon"] = cft_data["local"]["skill_icon"]
    else:
        cft["cft_icon"] = cft_data["cft_icon"]
        cft["skill_icon"] = cft_data["skill_icon"]

    if isinstance(cft_data["name_other"], list):
        cft["name_other"] = cft_data["name_other"]
    else:
        cft["name_other"] = cft_data["name_other"].split("&")

    if len(cft["name_other"]) == 1 and cft["name_other"][0] == "":
        cft["name_other"] = []

    local_data_path = os.path.join(mc_path, "cft", f'{cft_data["id"]}.txt')
    local_html_path = os.path.join(mc_path, "cft", f'{cft_data["id"]}.html')

    if os.path.exists(local_data_path):
        raw_data = open(local_data_path, "r", encoding="utf-8").read().replace("魔{{jin}}", "魔神(人)")
        raw_html = open(local_html_path, "r", encoding="utf-8").read()
    else:
        cft["error"].append(f"cft{cft['id']} init error: no local res")
        return cft

    painter = re.search(r"\|画师=(.+)", raw_data)
    cost = re.search(r"\|cost=(.+)", raw_data, re.I)
    name_jp = re.search(r"\|日文名称=(.+)", raw_data)
    hp = re.search(r"\|HP=(.+)", raw_data, re.I)
    atk = re.search(r"\|ATK=(.+)", raw_data, re.I)
    icon = re.search(r"\|图标=(.+)", raw_data)
    skills = re.search(r"\|持有技能=\n?([\s\S]+?)\n\|", raw_data)
    desc_cn = re.search(r"\|解说=\n?([\s\S]+?)\n\n?\n?\|", raw_data)
    desc_jp = re.search(r"\|日文解说=\n?([\s\S]+?)\n[|<]", raw_data)
    rare = re.search(r"\|稀有度=(.)", raw_data)
    raw_card_name = re.search(r"\|图片名=(.+)", raw_data)
    if not raw_card_name or cft["id"] == "657":
        raw_card_name = re.search(r"\|名称=(.+)", raw_data)

    cft["name_jp"] = name_jp.group(1) if name_jp else ""
    cft_detail = {
        "画师": painter.group(1) if painter else "",
        "Cost": cost.group(1) if cost else "",
        "初始/满级HP": hp.group(1) if hp else "",
        "初始/满级ATK": atk.group(1) if atk else "",
        "图标": icon.group(1) if icon else "",
        "持有技能": skills.group(1) if skills else "",
        "解说": desc_cn.group(1) if desc_cn else "",
        "日文解说": desc_jp.group(1) if desc_jp else ""
    }

    card_name = raw_card_name.group(1).strip().replace(" ", "_").replace("‎", "") if raw_card_name else ""
    raw_file = re.search(rf"(https://media.fgo.wiki/./../){quote(card_name)}.png", raw_html, re.I)
    if not raw_file:
        cft["error"].append("cards_url not found")
    cft["detail"] = cft_detail
    cft["rare"] = f"{rare.group(1)}星" if rare else "-"
    cft["cards_url"] = unquote(raw_file.group(0)) if raw_file else ""

    if not cft["error"]:
        cft.pop("error")
    return cft

# lib_cft_debug()
# errors = []
# for i in range(1950, 0, -1):
#     data = lib_cft_debug(i)
#     if "error" in data:
#         sv_lib.logger.error(f"更新礼装{i}出错：{data['error']}")
#         errors.append(i)
#
# print(errors)
