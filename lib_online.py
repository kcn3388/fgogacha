import re

from bs4 import BeautifulSoup

from hoshino import aiorequests
from .path_and_json import banned_id

headers = {
    "User-Agent": "Mozilla/5.0 (Windows; U; Windows NT 5.1; zh-CN; rv:1.9.1.6) ",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "zh-cn"
}


async def lib_svt_online(url, crt_file=False):
    try:
        response = await aiorequests.get(url, timeout=20, verify=crt_file, headers=headers)
    except OSError:
        response = await aiorequests.get(url, timeout=20, verify=False, headers=headers)
    except Exception as e:
        return e, -100
    soup = BeautifulSoup(await response.content, 'html.parser')
    is_get = soup.find(class_="SvtCardNameCN")
    if is_get:
        name = soup.find("title").text.split(" ")[0]
        return name, 1
    else:
        return "在线也没找到", 0


async def lib_cft_online(url, crt_file=False):
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
        name = soup.find("title").text.split(" ")[0]
        return name, 1
    else:
        return "在线也没找到", 0


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
        name = soup.find("title").text.split(" ")[0]
        return name, 1
    else:
        return "在线也没找到", 0


# noinspection PyUnresolvedReferences
async def lib_svt(svt_data, crt_file=False):
    url = "https://fgo.wiki/w/" + svt_data["name_link"]
    print("查询Servant" + svt_data["id"] + "……")
    svt = {
        "id": svt_data["id"],
        "name_cn": svt_data["name_cn"],
        "name_jp": svt_data["name_jp"],
        "name_en": svt_data["name_en"],
        "name_link": svt_data["name_link"],
        "name_other": None,
        "method": svt_data["method"]
    }

    if "local" in svt_data:
        svt["svt_icon"] = svt_data["local"]["svt_icon"]
        svt["class_icon"] = svt_data["local"]["class_icon"]
    else:
        svt["svt_icon"] = svt_data["svt_icon"]
        svt["class_icon"] = svt_data["class_icon"]

    if isinstance(svt_data["name_other"], list):
        svt["name_other"] = svt_data["name_other"]
    else:
        svt["name_other"] = svt_data["name_other"].split("&")

    if len(svt["name_other"]) == 1 and svt["name_other"][0] == "":
        svt["name_other"] = []

    try:
        response = await aiorequests.get(url, timeout=20, verify=crt_file, headers=headers)
    except OSError:
        response = await aiorequests.get(url, timeout=20, verify=False, headers=headers)
    except Exception as e:
        svt["error"] = [f"aiorequest error: {e}"]
        return svt

    soup = BeautifulSoup(await response.content, 'html.parser')
    try:
        svts = soup.find(class_="wikitable nomobile").find("tbody")
    except AttributeError:
        try:
            svts = soup.find(class_="wikitable nomobile").find("tbody")
        except AttributeError:
            try:
                svts = soup.find(class_="wikitable nomobile").find("tbody")
            except Exception as e:
                svt["error"] = [f"first bs error: {e}"]
                return svt

    s1 = []
    s2 = []
    info1 = svts.find_all("th")
    info2 = svts.find_all("td")
    for each in info1:
        arg = each.text.strip()
        if not arg == '' and not arg.startswith("卡面为游戏资源") and not arg == "指令卡":
            s1.append(arg)
    for each in info2:
        arg = each.text.strip()
        if not arg == '':
            s2.append(arg)

    s1.pop()
    s1.pop(0)
    s1.pop(0)
    s2.pop()
    s2.pop(0)
    s2.pop(0)
    result = {}
    for each in s1:
        if each == "ATK" or each == "职阶补正后" or each == "HP" or each == "能力":
            result[each] = []
            continue
        if each == "基础" or each == "满级" or each == "90级" \
                or each == "100级" or each == "120级":
            result["能力"].append(each)
            continue
        else:
            result[each] = each

    counter = 0
    try:
        for each in result:
            if svt_data["id"] == "351":
                if each == "特性":
                    result[each] = ""
                    continue
            if each == "ATK" or each == "职阶补正后" or each == "HP":
                result[each] = s2[counter: counter + 5]
                counter += 5
            elif each == "能力" or each.startswith("Hit信息"):
                result[each] = ""
                continue
            elif each == "NP获得率":
                result[each] = {
                    "Quick": s2[counter],
                    "Arts": s2[counter + 1],
                    "Buster": s2[counter + 2],
                    "Extra": s2[counter + 3],
                    "宝具": s2[counter + 4]
                }
                counter += 5
            else:
                result[each] = s2[counter]
                counter += 1
    except IndexError:
        print(svt_data["id"])
        pass

    svt["detail"] = result

    nick = soup.select("meta")
    nick_name = None
    for each in nick:
        if each.has_attr("name"):
            if each.attrs["name"] == "keywords":
                nick_name = each.attrs["content"]

    if nick_name is not None:
        if nick_name == "{{{昵称}}}":
            nick_name = ""
        svt["nick_name"] = nick_name.split(",")
    else:
        svt["nick_name"] = []

    cards_url = []
    raw_html = await response.text
    try:
        cards = re.compile(r"<div class=\"graphpicker-graph-\d\".+,(\s)?/images/.+\.(jpg|png)")
        all_img = re.finditer(cards, raw_html)
        for each in all_img:
            text = each.group(0)
            text = text.split(" ")
            rule = re.compile(r"/images/.+\.(jpg|png)")
            for each_img in text:
                if re.match(rule, each_img):
                    if each_img not in cards_url:
                        cards_url.append(each_img)
    except AttributeError:
        if svt["id"] in banned_id and not svt["id"] == "83":
            rule_card = re.compile(r"<th.+rowspan=\"22\".+,(\s+)?/images/.+\.(png|jpg)")
            try:
                card_url = re.search(rule_card, raw_html).group(0).split(" ")[-1]
                cards_url.append(card_url)
            except AttributeError:
                try:
                    card_url = re.search(rule_card, raw_html).group(0).split(" ")[-1]
                    cards_url.append(card_url)
                except Exception as e:
                    if "error" in svt:
                        svt["error"].append(f"get card img error: {e}")
                    else:
                        svt["error"] = [f"get card img error: {e}"]
                    pass
        elif svt["id"] == "83":
            rule = re.compile(r"<div\sclass=\"tabbertab\".+\n.+,(\s+)?/images/.+\.(png|jpg)")
            all_img = re.finditer(rule, raw_html)
            try:
                for each in all_img:
                    text = each.group(0)
                    img_url = re.search(r", /images/.+\.(jpg|png)", text).group(0).split(" ")[-1]
                    if img_url not in cards_url:
                        cards_url.append(img_url)
            except AttributeError:
                try:
                    for each in all_img:
                        text = each.group(0)
                        img_url = re.search(r", /images/.+\.(jpg|png)", text).group(0).split(" ")[-1]
                        if img_url not in cards_url:
                            cards_url.append(img_url)
                except Exception as e:
                    if "error" in svt:
                        svt["error"].append(f"get card img error: {e}")
                    else:
                        svt["error"] = [f"get card img error: {e}"]
                    pass
        else:
            try:
                cards = re.compile(r"<div class=\"graphpicker-graph-\d\".+,(\s)?/images/.+\.(jpg|png)")
                all_img = re.finditer(cards, raw_html)
                for each in all_img:
                    text = each.group(0)
                    text = text.split(" ")
                    rule = re.compile(r"/images/.+\.(jpg|png)")
                    for each_img in text:
                        if re.match(rule, each_img):
                            if each_img not in cards_url:
                                cards_url.append(each_img)
            except AttributeError:
                try:
                    cards = re.compile(r"<div class=\"graphpicker-graph-\d\".+,(\s)?/images/.+\.(jpg|png)")
                    all_img = re.finditer(cards, raw_html)
                    for each in all_img:
                        text = each.group(0)
                        text = text.split(" ")
                        rule = re.compile(r"/images/.+\.(jpg|png)")
                        for each_img in text:
                            if re.match(rule, each_img):
                                if each_img not in cards_url:
                                    cards_url.append(each_img)
                except Exception as e:
                    if "error" in svt:
                        svt["error"].append(f"get card img error: {e}")
                    else:
                        svt["error"] = [f"get card img error: {e}"]
                    pass

    svt["cards_url"] = cards_url

    rule_fool = re.compile(r"tl_svt_april_profile")
    fool = soup.find_all(class_=rule_fool)
    fools = []
    for each in fool:
        fools.append(each.text.strip())

    svt["fool"] = fools

    star = ""
    try:
        rule_star = re.compile(r"wgCategories.+星")
        star = re.search(rule_star, raw_html).group(0)
        star = star.split("\"")[-1].split("星")[0]
    except AttributeError:
        if svt["id"] in banned_id:
            try:
                rule_star = re.compile(r"<img\salt=\"\d星")
                star = re.search(rule_star, raw_html).group(0)
                star = star.split("\"")[-1].split("星")[0]
            except AttributeError:
                try:
                    rule_star = re.compile(r"<img\salt=\"\d星")
                    star = re.search(rule_star, raw_html).group(0)
                    star = star.split("\"")[-1].split("星")[0]
                except Exception as e:
                    if "error" in svt:
                        svt["error"].append(f"get star error: {e}")
                    else:
                        svt["error"] = [f"get star error: {e}"]
                    pass
        else:
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
                    if "error" in svt:
                        svt["error"].append(f"get star error: {e}")
                    else:
                        svt["error"] = [f"get star error: {e}"]
                    pass

    svt["rare"] = star + "星"

    return svt


# noinspection PyUnresolvedReferences
async def lib_cft(cft_data, crt_file=False):
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

    s1[-1] = s1[-1].split("\n\n")
    if s2[-1].startswith("以下翻译内容由Mooncell用户贡献。"):
        s2[-1] = s2[-1].replace("以下翻译内容由Mooncell用户贡献。", "")
        s2[-1] = re.split(r"转载请保留网址 https://fgo.wiki/id/\d+\n\n\n", s2[-1])
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
                if isinstance(s2[index], list):
                    for ids2 in range(len(s2[index])):
                        s2[index][ids2] = s2[index][ids2].replace(
                            "这部分内容目前尚无翻译。您可以勾选“日文”以查看原文，也可以编辑页面在“解说”中添加翻译。未经许可请勿添加其他来源的翻译。禁止添加机翻、塞翻等低质量翻译。\n", ""
                        )
                if isinstance(s2[index], str):
                    s2[index] = s2[index].replace(
                        "这部分内容目前尚无翻译。您可以勾选“日文”以查看原文，也可以编辑页面在“解说”中添加翻译。未经许可请勿添加其他来源的翻译。禁止添加机翻、塞翻等低质量翻译。\n", ""
                    )
                result[s1[index]] = s2[index]
    except IndexError:
        result["解说"] = ""
        result["日文解说"] = s2[-1][0].replace(
            "这部分内容目前尚无翻译。您可以勾选“日文”以查看原文，也可以编辑页面在“解说”中添加翻译。未经许可请勿添加其他来源的翻译。禁止添加机翻、塞翻等低质量翻译。\n", ""
        )
        pass

    cft["detail"] = result

    card_url = ""
    rule_card = re.compile(r"卡面为游戏资源原始图片.+,(\s+)?/images/.+\.(png|jpg)")
    raw_html = await response.text
    try:
        card_url = re.search(rule_card, raw_html).group(0).split(" ")[-1]
    except AttributeError:
        try:
            card_url = re.search(rule_card, raw_html).group(0).split(" ")[-1]
        except AttributeError:
            try:
                card_url = re.search(rule_card, raw_html).group(0).split(" ")[-1]
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
        card_url = re.search(rule_card, raw_html).group(0).split(" ")[-1]
    except AttributeError:
        try:
            card_url = re.search(rule_card, raw_html).group(0).split(" ")[-1]
        except AttributeError:
            try:
                card_url = re.search(rule_card, raw_html).group(0).split(" ")[-1]
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


async def get_card(url, crt_file=False):
    url = "https://fgo.wiki" + url
    try:
        response = await aiorequests.get(url, timeout=20, verify=crt_file, headers=headers)
    except OSError:
        response = await aiorequests.get(url, timeout=20, verify=False, headers=headers)
    except Exception as e:
        print(f"aiorequest error: {e}")
        return 100

    image = await response.content
    return image
