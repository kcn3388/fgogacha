import re

from bs4 import BeautifulSoup
from typing import Tuple
from ..path_and_json import *


async def lib_cft_online(url, crt_file=False) -> Tuple[Union[Exception, str], int]:
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


async def lib_cft(cft_data, crt_file=False) -> Dict:
    url = "https://fgo.wiki/w/" + cft_data["name_link"]
    print("查询礼装" + cft_data["id"] + "……")
    cft = {
        "id": cft_data["id"],
        "name": cft_data["name"],
        "name_other": None,
        "name_link": cft_data["name_link"],
        "type": cft_data["type"]
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

    try:
        response = await aiorequests.get(url, timeout=20, verify=crt_file, headers=headers)
    except OSError:
        response = await aiorequests.get(url, timeout=20, verify=False, headers=headers)
    except Exception as e:
        cft["error"] = [f"aiorequest error: {e}"]
        return cft

    soup = BeautifulSoup(await response.content, 'html.parser')
    try:
        cfts = soup.find(class_="wikitable nomobile").find("tbody")
    except AttributeError:
        try:
            cfts = soup.find(class_="wikitable nomobile").find("tbody")
        except AttributeError:
            try:
                cfts = soup.find(class_="wikitable nomobile").find("tbody")
            except Exception as e:
                cft["error"] = [f"first bs error: {e}"]
                return cft

    s1 = []
    s2 = []
    info1 = cfts.find_all("th")
    info2 = cfts.find_all("td")
    for each in info1:
        arg = each.text.strip()
        if not arg == '' and not arg.startswith("No.") and not arg == "稀有度":
            s1.append(arg)
    for each in info2:
        arg = each.text.strip()
        if not arg == '' and not arg.startswith("卡面为"):
            s2.append(arg)

    s1[-1] = s1[-1].split("\n\n")  # noqa
    if s2[-1].startswith("以下翻译内容由Mooncell用户贡献。"):
        s2[-1] = s2[-1].replace("以下翻译内容由Mooncell用户贡献。", "")  # noqa
        s2[-1] = re.split(r"转载请保留网址 https://fgo.wiki/id/\d+\n\n\n", s2[-1])
    else:
        s2[-1] = s2[-1].split("\n\n\n")  # noqa

    if len(s1) < len(s2):
        t1 = s1.pop()
        t2 = s2.pop()
        skills = []
        ts2 = s2.copy()
        for i in range(len(ts2) - 1, 3, -1):
            skills.append(ts2[i])
            s2.pop()
        skills.reverse()
        s2.append(skills)
        s1.append(t1)
        s2.append(t2)

    result = {}
    try:
        for index in range(len(s1)):
            if isinstance(s1[index], list):
                for i in range(len(s1[index])):
                    if s1[index][i] == "日文":
                        s1[index][i] = "日文解说"
                    result[s1[index][i]] = s2[index][i].replace(
                        "这部分内容目前尚无翻译。您可以勾选“日文”以查看原文，也可以编辑页面在“解说”中添加翻译。未经许可请勿添加其他来源的翻译。禁止添加机翻、塞翻等低质量翻译。\n",
                        ""
                    )
            else:
                if isinstance(s2[index], list):
                    for ids2 in range(len(s2[index])):
                        s2[index][ids2] = s2[index][ids2].replace(
                            "这部分内容目前尚无翻译。您可以勾选“日文”以查看原文，也可以编辑页面在“解说”中添加翻译。未经许可请勿添加其他来源的翻译。禁止添加机翻、塞翻等低质量翻译。\n",
                            ""
                        )
                if isinstance(s2[index], str):
                    s2[index] = s2[index].replace(
                        "这部分内容目前尚无翻译。您可以勾选“日文”以查看原文，也可以编辑页面在“解说”中添加翻译。未经许可请勿添加其他来源的翻译。禁止添加机翻、塞翻等低质量翻译。\n",
                        ""
                    )
                result[s1[index]] = s2[index]
    except IndexError:
        result["解说"] = ""
        result["日文解说"] = s2[-1][0].replace(
            "这部分内容目前尚无翻译。您可以勾选“日文”以查看原文，也可以编辑页面在“解说”中添加翻译。未经许可请勿添加其他来源的翻译。禁止添加机翻、塞翻等低质量翻译。\n",
            ""
        )
        pass

    cft["detail"] = result

    card_url = ""
    rule_card = re.compile(r"卡面为游戏资源原始图片.+,(\s+)?/images/.+\.(png|jpg)")
    raw_html = await response.text
    try:
        card_url = re.search(rule_card, raw_html).group(0).split()[-1]
    except AttributeError:
        try:
            card_url = re.search(rule_card, raw_html).group(0).split()[-1]
        except AttributeError:
            try:
                card_url = re.search(rule_card, raw_html).group(0).split()[-1]
            except Exception as e:
                if "error" in cft:
                    cft["error"].append(f"get card img error: {e}")
                else:
                    cft["error"] = [f"get card img error: {e}"]
                pass

    cft["cards_url"] = card_url

    star = ""
    try:
        rule_star = re.compile(r"wgCategories.+星")
        star = re.search(rule_star, raw_html).group(0)
        star = star.split("\"")[-1].split("星")[0]
    except AttributeError:
        try:
            rule_star = re.compile(r"wgCategories.+星")
            star = re.search(rule_star, raw_html).group(0)
            star = star.split("\"")[-1].split("星")[0]
        except AttributeError:
            try:
                rule_star = re.compile(r"wgCategories.+星")
                star = re.search(rule_star, raw_html).group(0)
                star = star.split("\"")[-1].split("星")[0]
            except Exception as e:
                if "error" in cft:
                    cft["error"].append(f"get star error: {e}")
                else:
                    cft["error"] = [f"get star error: {e}"]
                pass

    cft["rare"] = star + "星"

    return cft
