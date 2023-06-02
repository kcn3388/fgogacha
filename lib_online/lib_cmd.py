import copy
import re
from typing import Tuple

from bs4 import BeautifulSoup

from .lib_json import *


async def lib_cmd_online(url: str, crt_file: str = False) -> Tuple[Union[Exception, str], int]:
    try:
        response = await aiorequests.get(url, timeout=20, verify=crt_file, headers=headers)
    except OSError:
        response = await aiorequests.get(url, timeout=20, verify=False, headers=headers)
    except Exception as e:
        return e, -100

    soup = BeautifulSoup(await response.content, 'html.parser')
    try:
        is_get = soup.find(class_="wikitable nomobile").find_all("big")
    except AttributeError:
        is_get = False

    if is_get:
        name = soup.find("title").text.split()[0]
        return name, 1
    else:
        return "在线也没找到", 0


async def lib_cmd(cmd_data: dict, crt_file: str = False) -> dict:
    url = "https://fgo.wiki/w/" + cmd_data["name_link"]
    sv_lib.logger.info("查询纹章" + cmd_data["id"] + "……")
    cmd = {
        "id": cmd_data["id"],
        "name": cmd_data["name"],
        "name_other": None,
        "name_link": cmd_data["name_link"],
        "type": cmd_data["type"]
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

    try:
        response = await aiorequests.get(url, timeout=20, verify=crt_file, headers=headers)
    except OSError:
        response = await aiorequests.get(url, timeout=20, verify=False, headers=headers)
    except Exception as e:
        cmd["error"] = [f"cmd{cmd['id']} aiorequest error: {e}"]
        return cmd

    raw_html = await response.text
    soup = BeautifulSoup(await response.content, 'html.parser')
    try:
        cmds = soup.find(class_="wikitable nodesktop").find("tbody")
    except Exception as e:
        cmd["error"] = [f"cmd{cmd['id']} first bs error: {e}"]
        return cmd

    info = [cmds.find("a", title="画师一览").text.strip() if cmds.find("a", title="画师一览") else ""]
    info_soup = cmds.find_all("div", class_="poem")
    for each_is in info_soup:
        next_p = each_is.find_next("p")
        if next_p:
            info.append(next_p.text.strip())
        else:
            info.append("")

    detail_counter = 0
    single_cmd_detail = copy.deepcopy(cmd_detail)
    for each_cd in single_cmd_detail:
        single_cmd_detail[each_cd] = info[detail_counter]
        detail_counter += 1

    cmd["detail"] = single_cmd_detail

    card_url = ""
    curl_soup = cmds.find_all("span")
    for each_cls in curl_soup:
        if each_cls.text.strip() == "卡面为游戏资源原始图片，未经任何处理。":
            curl_soup = each_cls
            break

    try:
        curl_soup = curl_soup.find_next("img").get("data-srcset")
        rule_card = re.compile(r"/images/.+?.\.(?:png|jpg)")
        card_set = re.findall(rule_card, curl_soup)
        card_url = card_set[-1]
    except Exception as e:
        if "error" in cmd:
            cmd["error"].append(f"cmd{cmd['id']} cmd{cmd['id']} get card img error: {e}")
        else:
            cmd["error"] = [f"cmd{cmd['id']} cmd{cmd['id']} get card img error: {e}"]
        pass

    cmd["cards_url"] = card_url

    star = ""
    try:
        rule_star = re.compile(r"wgCategories.+星")
        star = re.search(rule_star, raw_html).group(0)
        star = star.split("\"")[-1].split("星")[0]
    except Exception as e:
        if "error" in cmd:
            cmd["error"].append(f"cmd{cmd['id']} get star error: {e}")
        else:
            cmd["error"] = [f"cmd{cmd['id']} get star error: {e}"]
        pass

    cmd["rare"] = star + "星"

    return cmd
