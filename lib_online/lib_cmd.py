import re

from bs4 import BeautifulSoup

from .lib_online import *


async def lib_cmd_online(url, crt_file=False):
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


# noinspection PyUnresolvedReferences
async def lib_cmd(cmd_data, crt_file=False):
    url = "https://fgo.wiki/w/" + cmd_data["name_link"]
    print("查询纹章" + cmd_data["id"] + "……")
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
        cmd["error"] = [f"aiorequest error: {e}"]
        return cmd

    soup = BeautifulSoup(await response.content, 'html.parser')
    try:
        cmds = soup.find(class_="wikitable nomobile").find("tbody")
    except AttributeError:
        try:
            cmds = soup.find(class_="wikitable nomobile").find("tbody")
        except AttributeError:
            try:
                cmds = soup.find(class_="wikitable nomobile").find("tbody")
            except Exception as e:
                cmd["error"] = [f"first bs error: {e}"]
                return cmd

    s1 = []
    s2 = []
    info1 = cmds.find_all("th")
    info2 = cmds.find_all("td")
    for each in info1:
        arg = each.text.strip()
        if not arg == '' and not arg.startswith("No.") and not arg == "稀有度":
            s1.append(arg)
    for each in info2:
        arg = each.text.strip()
        if not arg == '' and not arg.startswith("卡面为"):
            s2.append(arg)

    s1[-1] = s1[-1].split("\n\n")
    if s2[-1].startswith("以下翻译内容由Mooncell用户贡献。"):
        s2[-1] = s2[-1].replace("以下翻译内容由Mooncell用户贡献。\n", "")
        s2[-1] = re.split(r"\n\n转载请保留网址 https://fgo.wiki/id/\d+\n", s2[-1])
    else:
        s2[-1] = s2[-1].split("\n\n\n")

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
                        "这部分内容目前尚无翻译。您可以勾选“日文”以查看原文，也可以编辑页面在“解说”中添加翻译。未经许可请勿添加其他来源的翻译。禁止添加机翻、塞翻等低质量翻译。\n", ""
                    )
            else:
                result[s1[index]] = s2[index].replace(
                    "这部分内容目前尚无翻译。您可以勾选“日文”以查看原文，也可以编辑页面在“解说”中添加翻译。未经许可请勿添加其他来源的翻译。禁止添加机翻、塞翻等低质量翻译。\n", ""
                )
    except IndexError:
        result["解说"] = ""
        result["日文解说"] = s2[-1][0].replace(
            "这部分内容目前尚无翻译。您可以勾选“日文”以查看原文，也可以编辑页面在“解说”中添加翻译。未经许可请勿添加其他来源的翻译。禁止添加机翻、塞翻等低质量翻译。\n", ""
        )
        pass

    cmd["detail"] = result

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
                if "error" in cmd:
                    cmd["error"].append(f"get card img error: {e}")
                else:
                    cmd["error"] = [f"get card img error: {e}"]
                pass

    cmd["cards_url"] = card_url

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
                if "error" in cmd:
                    cmd["error"].append(f"get star error: {e}")
                else:
                    cmd["error"] = [f"get star error: {e}"]
                pass

    cmd["rare"] = star + "星"

    return cmd
