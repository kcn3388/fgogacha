import re

from bs4 import BeautifulSoup

from .lib_online import *
from ..path_and_json import banned_id


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

    raw_html = await response.text

    get_detail(svts, svt, svt_data)

    get_nick_name(svt, soup)

    get_card_url(svt, raw_html)

    get_fool(svt, soup)

    get_star(svt, raw_html)

    get_info(svt, soup)

    try:
        base = soup.findAll(class_="wikitable nomobile logo")
    except AttributeError:
        try:
            base = soup.findAll(class_="wikitable nomobile logo")
        except AttributeError:
            try:
                base = soup.findAll(class_="wikitable nomobile logo")
            except Exception as e:
                svt["error"] = [f"find power bs error: {e}"]
                return svt

    get_ultimate(svt, base)

    get_skills(svt, base, raw_html)

    return svt


# noinspection PyUnresolvedReferences
def get_detail(svts, svt, svt_data):
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
            elif each == "能力":
                continue
            elif each.startswith("Hit信息"):
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


def get_nick_name(svt, soup):
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


def get_card_url(svt, raw_html):
    cards_url = []
    try:
        cards = re.compile(r"<div class=\"graphpicker-graph-\d\".+,(\s)?/images/.+\.(jpg|png)")
        all_img = re.finditer(cards, raw_html)
        if svt["id"] in banned_id:
            raise AttributeError
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

    cards_name = []
    if svt["id"] not in banned_id:
        try:
            rule_names = re.compile(r"var\sarrayTitle\s=new\sArray\(.+\);")
            names = re.search(rule_names, raw_html).group(0)
            names = names.replace("var arrayTitle =new Array(", "").replace(");", "").replace("\"", "")
            names = names.split(",")
            for each in names:
                if not each == "":
                    cards_name.append(each)
        except AttributeError:
            pass

    svt["cards_url"] = {}
    if len(cards_name) == len(cards_url):
        for i in range(len(cards_url)):
            svt["cards_url"][cards_name[i]] = cards_url[i]
    else:
        for i in range(len(cards_url)):
            svt["cards_url"][f"卡面{i + 1}"] = cards_url[i]


def get_fool(svt, soup):
    rule_fool = re.compile(r"tl_svt_april_profile")
    fool = soup.find_all(class_=rule_fool)
    if len(fool) > 1:
        fools = {
            "资料": fool[0].text.strip(),
            "原文": fool[1].text.strip()
        }
    elif len(fool) == 1:
        fools = {
            "资料": "",
            "原文": fool[0].strip()
        }
    else:
        fools = {
            "资料": "",
            "原文": ""
        }

    svt["fool"] = fools


def get_star(svt, raw_html):
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


def get_info(svt, soup):
    detail_info = []
    rule_svt_info = re.compile(r"(角色详情|个人资料\d)")
    try:
        svt_info = soup.findAll(title=rule_svt_info)
    except AttributeError:
        try:
            svt_info = soup.findAll(title=rule_svt_info)
        except AttributeError:
            try:
                svt_info = soup.findAll(title=rule_svt_info)
            except Exception as e:
                svt["error"] = [f"svt_info error: {e}"]
                pass

    # noinspection PyUnboundLocalVariable
    for each in svt_info:
        try:
            all_p = each.findAll("p")
            for data in all_p:
                if not data.text == "":
                    detail_info.append(data.text.strip())
        except AttributeError:
            try:
                all_p = each.findAll("p")
                for data in all_p:
                    if not data.text == "":
                        detail_info.append(data.text.strip())
            except AttributeError:
                try:
                    all_p = each.findAll("p")
                    for data in all_p:
                        if not data.text == "":
                            detail_info.append(data.text.strip())
                except Exception as e:
                    svt["error"] = [f"svt_info error: {e}"]
                    pass

    svt_detail = {}
    if len(detail_info) > 6:
        for i in range(0, len(detail_info), 2):
            if i == 0:
                svt_detail["角色详情"] = {
                    "资料": re.sub(r"\n\n+", "\n", detail_info[i]),
                    "原文": re.sub(r"\n\n+", "\n", detail_info[i + 1])
                }
            else:
                svt_detail["个人资料" + str(int(i / 2))] = {
                    "资料": re.sub(r"\n\n+", "\n", detail_info[i]),
                    "原文": re.sub(r"\n\n+", "\n", detail_info[i + 1])
                }
    else:
        for i in range(len(detail_info)):
            if i == 0:
                svt_detail["角色详情"] = {
                    "资料": "",
                    "原文": re.sub(r"\n\n+", "\n", detail_info[i])
                }
            else:
                svt_detail["个人资料" + str(i)] = {
                    "资料": "",
                    "原文": re.sub(r"\n\n+", "\n", detail_info[i])
                }

    svt["svt_detail"] = svt_detail


def get_ultimate(svt, base):
    ul_soup = [base[0]]
    open_info = None
    open_info2 = None
    multiple = False
    rule_multiple = re.compile(r"(灵基再临.+后|第.+阶段|初始|限定|助战|通常)")
    # t2 = t1.findParent(title=rule_multiple).findPrevious("span").text
    try:
        if base[0].findPrevious(title="强化后") or base[1].findParent(title=rule_multiple):
            try:
                p_span_text = base[1].findParent(title=rule_multiple).findPrevious("span").text
            except AttributeError:
                p_span_text = ""
            if "技能" not in p_span_text:
                ul_soup.append(base[1])
                if not base[1].findParent(title=rule_multiple):
                    open_info = base[0].findPrevious("p").text.strip().replace("开放时间", "\n开放时间")
                if base[1].findParent(title=rule_multiple):
                    multiple = True
                    open_info = base[0].findParent(title=rule_multiple)["title"]
                    open_info2 = base[1].findParent(title=rule_multiple)["title"]
    except IndexError:
        pass
    except Exception as e:
        svt["error"] = [f"get ultimate error: {e}"]
        pass

    ultimates = []
    for uls in ul_soup:
        u1 = []
        u2 = []
        ultimate1 = uls.find_all("th")
        ultimate2 = uls.find_all("td")
        for each in ultimate1:
            if each.find("p"):
                for all_p in each.findAll("p"):
                    arg = all_p.text.strip()
                    u1.append(arg)
            else:
                arg = each.text.strip()
                u1.append(arg)

        for each in ultimate2:
            if each.find("big"):
                arg = each.find("big").text.strip()
                u2.append(arg)
                arg2 = each.find(class_="npname-border").text.strip()
                u2.append(arg2)
            elif each.find("small"):
                arg = each.find("small").text.strip()
                u2.append(arg)
                arg2 = each.text.strip().replace(arg, "")
                u2.append(arg2)
            else:
                arg = each.text.strip()
                u2.append(arg)

        u2 = u2[:4]
        ultimate = {}

        ultimate_names = ["中文", "英文", "假名", "日文"]
        for index in range(len(ultimate_names)):
            ultimate[ultimate_names[index]] = u2[index]

        for index in range(len(u1)):
            if index == 0 or index == 1:
                ultimate["类型"] = u1[1]
                ultimate["等级"] = u1[0]
            else:
                ultimate[f"效果{index - 1}"] = u1[index]

        ultimates.append(ultimate)

    for i in range(len(ul_soup)):
        color = ul_soup[i].find(class_="floatnone").find("img", alt=True)["alt"]
        ultimates[i]["卡色"] = color.split(".")[0]

    if open_info is not None and not multiple:
        ultimates[0]["开放条件"] = open_info

    if open_info is not None and open_info2 is not None and multiple:
        ultimates[0]["开放条件"] = open_info
        ultimates[1]["开放条件"] = open_info2

    svt["宝具信息"] = ultimates


# noinspection PyUnresolvedReferences
def get_skills(svt, base, raw_html):
    skill_soup = base[len(svt["宝具信息"]):]
    skill_list = []
    for i in range(len(skill_soup)):
        skill_list.append(
            (skill_soup[i], skill_soup[i].text.strip())
        )

    skills = {}

    skill_flag = 0
    counter_skill = 1
    for each in skill_list:
        skill_type = each[0].findPrevious("span").text
        skill_icon = each[0].find("img", alt=True)["data-srcset"].split(", ")[-1].split(" 2x")[0]
        if skill_type == "追加技能" or skill_flag == 2:
            skill_flag = 2
            skills[f"追加技能{counter_skill}"] = [each[1], skill_icon]
            counter_skill += 1
        if skill_type == "职阶技能" or skill_flag == 1:
            skill_flag = 1
            skills["职阶技能"] = [each[1]]
        try:
            if skill_type == "持有技能" or skill_flag == 0:
                title = each[0].findParent("div")["title"]
                if title == "强化后" or title == "强化后":
                    skills[f'{each[0].findPrevious("b").text}({title})'] = [each[1], skill_icon]
                else:
                    skills[f'{each[0].findPrevious("b").text}({title})'] = [each[1], skill_icon]
        except KeyError:
            if skill_type == "持有技能" or skill_flag == 0:
                skills[each[0].findPrevious("b").text] = [each[1], skill_icon]
        except AttributeError:
            title = each[0].findParent("div")["title"]
            skills[f'特殊技能({title})'] = [each[1], skill_icon]

    for each in skills:
        data = skills[each][0].strip()
        data = re.sub(r"\n+", "\n", data.strip())
        if each == "职阶技能":
            data = data.split("\n")
        else:
            data = re.sub(r"(∅|\d+%)", "", data.strip()).split("\n")
        for each_text in data[::-1]:
            if each_text.isdigit() or each_text == "":
                data.remove(each_text)
        if not each == "职阶技能":
            data.append(skills[each][1])
        skills[each] = data

    if "职阶技能" in skills:
        for i in range(0, len(skills["职阶技能"]) - 1, 2):
            skills[f"职阶技能{int(i / 2 + 1)}"] = [skills["职阶技能"][i], skills["职阶技能"][i + 1]]
        skills.pop("职阶技能")

    rule_skill_icon = re.compile(r"职阶技能.+\.(png|jpg)")
    class_skill_icon = re.finditer(rule_skill_icon, raw_html)
    icons = []
    for each in class_skill_icon:
        tmp = each.group(0).split(", ")[1]
        icons.append(tmp)

    temp = skills.copy()
    counter_class_skill = 0
    for each in temp:
        if each.startswith("职阶技能"):
            tmp = temp[each]
            skills[each] = {
                "中文": tmp[0],
                "效果": tmp[1],
                "图标": icons[counter_class_skill]
            }
            counter_class_skill += 1
        elif each.startswith("追加技能"):
            tmp = temp[each]
            skills[each] = {
                "中文": tmp[0],
                "原文": tmp[1],
                "效果": tmp[2],
                "图标": tmp[3]
            }
        else:
            tmp = temp[each]
            skills[each] = {
                "中文": tmp[0],
                "原文": tmp[2],
                "充能时间": tmp[1],
                "图标": tmp[-1]
            }
            for i in range(3, len(tmp) - 1):
                skills[each][f'效果{i - 2}'] = tmp[i]

    svt["技能"] = skills
