import re
from typing import Tuple
from urllib.parse import quote, unquote
from bs4 import BeautifulSoup

from .lib_json import *


async def lib_cmd_online(url: str, session: ClientSession) -> Tuple[Union[Exception, str], int]:
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


async def lib_cmd(cmd_data: dict) -> dict:
    # def lib_cmd_debug(sid: int = 0) -> dict:
    #     with open(all_command_path, 'r', encoding="utf-8") as f:
    #         commands = json.load(f)
    #     if sid:
    #         cmd_data = jsonpath(commands, f"$..[?(@.id=='{sid}')]")[0]
    #     else:
    #         cmd_data = jsonpath(commands, "$..[?(@.id=='74')]")[0]
    sv_lib.logger.info("查询纹章" + cmd_data["id"] + "……")
    cmd = {
        "id": cmd_data["id"],
        "name": cmd_data["name"],
        "name_jp": cmd_data["name"],
        "name_other": None,
        "name_link": cmd_data["name_link"],
        "type": cmd_data["type"],
        "error": []
    }

    if "local" in cmd_data:
        cmd["cmd_icon"] = cmd_data["local"]["cmd_icon"]
        cmd["skill_icon"] = cmd_data["local"]["skill_icon"]
    else:
        cmd["cmd_icon"] = cmd_data["cmd_icon"]
        cmd["skill_icon"] = cmd_data["skill_icon"]

    if isinstance(cmd_data["name_other"], list):
        cmd["name_other"] = cmd_data["name_other"]
    else:
        cmd["name_other"] = cmd_data["name_other"].split("&")

    if len(cmd["name_other"]) == 1 and cmd["name_other"][0] == "":
        cmd["name_other"] = []

    local_data_path = os.path.join(mc_path, "cmd", f'{cmd_data["id"]}.txt')
    local_html_path = os.path.join(mc_path, "cmd", f'{cmd_data["id"]}.html')

    if os.path.exists(local_data_path):
        raw_data = open(local_data_path, "r", encoding="utf-8").read().replace("魔{{jin}}", "魔神(人)")
        raw_html = open(local_html_path, "r", encoding="utf-8").read()
    else:
        cmd["error"].append(f"cmd{cmd['id']} init error: no local res")
        return cmd

    painter = re.search(r"\|画师=(.+)", raw_data)
    name_jp = re.search(r"\|日文名称=(.+)", raw_data)
    icon = re.search(r"\|图标=(.+)", raw_data)
    skills = re.search(r"\|持有技能=\n?([\s\S]+?)\n\|", raw_data)
    desc_cn = re.search(r"\|解说=\n?([\s\S]+?)\n\n?\n?\|", raw_data)
    desc_jp = re.search(r"\|日文解说=\n?([\s\S]+?)\n[|<]", raw_data)
    rare = re.search(r"\|稀有度=(.)", raw_data)
    raw_card_name = re.search(r"\|图片名=(.+)", raw_data)
    if not raw_card_name:
        raw_card_name = re.search(r"\|名称=(.+)", raw_data)

    cmd["name_jp"] = name_jp.group(1) if name_jp else ""
    cmd_detail = {
        "画师": painter.group(1) if painter else "",
        "图标": icon.group(1) if icon else "",
        "持有技能": skills.group(1) if skills else "",
        "解说": desc_cn.group(1) if desc_cn else "",
        "日文解说": desc_jp.group(1) if desc_jp else ""
    }

    card_name = raw_card_name.group(1).strip().replace(" ", "_") if raw_card_name else ""
    if cmd["id"] == "74":
        card_name = "魔神小姐"
    raw_file = re.search(rf"(https://media.fgo.wiki/./../){quote(card_name)}.png", raw_html, re.I)
    if not raw_file:
        cmd["error"].append("cards_url not found")
    cmd["detail"] = cmd_detail
    cmd["rare"] = f"{rare.group(1)}星" if rare else "-"
    cmd["cards_url"] = unquote(raw_file.group(0)) if raw_file else ""

    if not cmd["error"]:
        cmd.pop("error")
    return cmd

# lib_cmd_debug()
# errors = []
# for i in range(155, 0, -1):
#     data = lib_cmd_debug(i)
#     if "error" in data:
#         sv_lib.logger.error(f"更新纹章{i}出错：{data['error']}")
#         errors.append(i)
#
# print(errors)
