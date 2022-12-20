import re
from typing import Tuple

from bs4 import BeautifulSoup

from ..path_and_json import *


async def lib_svt_online(url, crt_file=False) -> Tuple[Union[Exception, str], int]:
    try:
        response = await aiorequests.get(url, timeout=20, verify=crt_file, headers=headers)
    except OSError:
        response = await aiorequests.get(url, timeout=20, verify=False, headers=headers)
    except Exception as e:
        return e, -100
    soup = BeautifulSoup(await response.content, 'html.parser')
    is_get = soup.find(class_="SvtCardNameCN")
    if is_get:
        name = soup.find("title").text.split()[0]
        return name, 1
    else:
        return "在线也没找到", 0


async def lib_svt(svt_data, crt_file=False) -> Dict:
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

    await get_pickup(svt, url, crt_file)

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

    get_voice(svt, soup)

    return svt


def get_detail(svts, svt, svt_data):
    s1 = []
    s2 = []
    info1 = svts.find_all("th")
    info2 = svts.find_all("td")
    for each_info1 in info1:
        arg = each_info1.text.strip()
        if not arg == '' and not arg.startswith("卡面为游戏资源") and not arg == "指令卡":
            s1.append(arg)
    for each_info2 in info2:
        arg = each_info2.text.strip()
        if not arg == '':
            s2.append(arg)

    s1.pop()
    s1.pop(0)
    s1.pop(0)
    s2.pop()
    s2.pop(0)
    s2.pop(0)
    result = {}
    for each_stat in s1:
        if each_stat == "ATK" or each_stat == "职阶补正后" or each_stat == "HP" or each_stat == "能力":
            result[each_stat] = []
            continue
        if each_stat == "基础" or each_stat == "满级" or each_stat == "90级" \
                or each_stat == "100级" or each_stat == "120级":
            result["能力"].append(each_stat)
            continue
        else:
            result[each_stat] = each_stat

    counter = 0
    try:
        for each_data in result:
            if svt_data["id"] == "351":
                if each_data == "特性":
                    result[each_data] = ""
                    continue
            if each_data == "ATK" or each_data == "职阶补正后" or each_data == "HP":
                result[each_data] = s2[counter: counter + 5]
                counter += 5
            elif each_data == "能力":
                continue
            elif each_data.startswith("Hit信息"):
                result[each_data] = ""
                continue
            elif each_data == "NP获得率":
                result[each_data] = {
                    "Quick": s2[counter],
                    "Arts": s2[counter + 1],
                    "Buster": s2[counter + 2],
                    "Extra": s2[counter + 3],
                    "宝具": s2[counter + 4]
                }
                counter += 5
            else:
                result[each_data] = s2[counter]
                counter += 1
    except IndexError:
        print(svt_data["id"])
        pass

    svt["detail"] = result


def get_nick_name(svt, soup):
    nick = soup.select("meta")
    nick_name = None
    for each_nick in nick:
        if each_nick.has_attr("name"):
            if each_nick.get("name") == "keywords":
                nick_name = each_nick.get("content")

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
        for each_img in all_img:
            text = each_img.group(0)
            text = text.split()
            rule = re.compile(r"/images/.+\.(jpg|png)")
            for each_text in text:
                if re.match(rule, each_text):
                    if each_text not in cards_url:
                        cards_url.append(each_text)
    except AttributeError:
        if svt["id"] in banned_id and not svt["id"] == "83":
            rule_card = re.compile(r"<th.+rowspan=\"22\".+,(\s+)?/images/.+\.(png|jpg)")
            try:
                card_url = re.search(rule_card, raw_html).group(0).split()[-1]
                cards_url.append(card_url)
            except AttributeError:
                try:
                    card_url = re.search(rule_card, raw_html).group(0).split()[-1]
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
                for each_img in all_img:
                    text = each_img.group(0)
                    img_url = re.search(r", /images/.+\.(jpg|png)", text).group(0).split()[-1]
                    if img_url not in cards_url:
                        cards_url.append(img_url)
            except AttributeError:
                try:
                    for each_img in all_img:
                        text = each_img.group(0)
                        img_url = re.search(r", /images/.+\.(jpg|png)", text).group(0).split()[-1]
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
                for each_img in all_img:
                    text = each_img.group(0)
                    text = text.split()
                    rule = re.compile(r"/images/.+\.(jpg|png)")
                    for each_text in text:
                        if re.match(rule, each_text):
                            if each_text not in cards_url:
                                cards_url.append(each_text)
            except AttributeError:
                try:
                    cards = re.compile(r"<div class=\"graphpicker-graph-\d\".+,(\s)?/images/.+\.(jpg|png)")
                    all_img = re.finditer(cards, raw_html)
                    for each_img in all_img:
                        text = each_img.group(0)
                        text = text.split()
                        rule = re.compile(r"/images/.+\.(jpg|png)")
                        for each_text in text:
                            if re.match(rule, each_text):
                                if each_text not in cards_url:
                                    cards_url.append(each_text)
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
            for each_name in names:
                if not each_name == "":
                    cards_name.append(each_name)
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
                svt_info = []
                if "error" in svt:
                    svt["error"].append(f"svt_info_main error: {e}")
                else:
                    svt["error"] = [f"svt_info_main error: {e}"]
                pass

    for each_info in svt_info:
        try:
            all_p = each_info.findAll("p")
            for data in all_p:
                if not data.text == "":
                    detail_info.append(data.text.strip())
        except AttributeError:
            try:
                all_p = each_info.findAll("p")
                for data in all_p:
                    if not data.text == "":
                        detail_info.append(data.text.strip())
            except AttributeError:
                try:
                    all_p = each_info.findAll("p")
                    for data in all_p:
                        if not data.text == "":
                            detail_info.append(data.text.strip())
                except Exception as e:
                    if "error" in svt:
                        svt["error"].append(f"svt_info error: {e}")
                    else:
                        svt["error"] = [f"svt_info error: {e}"]
                    pass

    svt_detail = {}
    try:
        if len(detail_info) > 6:
            for i in range(0, len(detail_info), 2):
                if i == 0:
                    svt_detail["角色详情"] = {
                        "资料": re.sub(r"\n\n+", "\n", detail_info[i]).replace(
                            "这部分内容目前尚无翻译。您可以切换为日文查看，也可以编辑页面添加翻译。请注意，取得许可前不要添加其他来源的翻译。也请不要添加机翻、塞翻等低质量翻译内容。",
                            ""
                        ),
                        "原文": re.sub(r"\n\n+", "\n", detail_info[i + 1]).replace(
                            "这部分内容目前尚无翻译。您可以切换为日文查看，也可以编辑页面添加翻译。请注意，取得许可前不要添加其他来源的翻译。也请不要添加机翻、塞翻等低质量翻译内容。",
                            ""
                        )
                    }
                else:
                    svt_detail["个人资料" + str(int(i / 2))] = {
                        "资料": re.sub(r"\n\n+", "\n", detail_info[i]).replace(
                            "这部分内容目前尚无翻译。您可以切换为日文查看，也可以编辑页面添加翻译。请注意，取得许可前不要添加其他来源的翻译。也请不要添加机翻、塞翻等低质量翻译内容。",
                            ""
                        ),
                        "原文": re.sub(r"\n\n+", "\n", detail_info[i + 1]).replace(
                            "这部分内容目前尚无翻译。您可以切换为日文查看，也可以编辑页面添加翻译。请注意，取得许可前不要添加其他来源的翻译。也请不要添加机翻、塞翻等低质量翻译内容。",
                            ""
                        )
                    }
        else:
            for i in range(len(detail_info)):
                if i == 0:
                    svt_detail["角色详情"] = {
                        "资料": "",
                        "原文": re.sub(r"\n\n+", "\n", detail_info[i]).replace(
                            "这部分内容目前尚无翻译。您可以切换为日文查看，也可以编辑页面添加翻译。请注意，取得许可前不要添加其他来源的翻译。也请不要添加机翻、塞翻等低质量翻译内容。",
                            ""
                        )
                    }
                else:
                    svt_detail["个人资料" + str(i)] = {
                        "资料": "",
                        "原文": re.sub(r"\n\n+", "\n", detail_info[i]).replace(
                            "这部分内容目前尚无翻译。您可以切换为日文查看，也可以编辑页面添加翻译。请注意，取得许可前不要添加其他来源的翻译。也请不要添加机翻、塞翻等低质量翻译内容。",
                            ""
                        )
                    }
    except IndexError as e:
        if "error" in svt:
            svt["error"].append(f"svt_detail error: {e}")
        else:
            svt["error"] = [f"svt_detail error: {e}"]

    svt["svt_detail"] = svt_detail


def get_ultimate(svt, base):
    ul_soup = []
    open_info = []
    rule_multiple = re.compile(r"(灵基再临.+后|第.+阶段|初始|限定|助战|通常|第\d部|强化后|强化前|真名解放.+)")
    try:
        for each_base in base:
            if each_base.findParent(title=rule_multiple):
                try:
                    p_span_text = each_base.findParent(title=rule_multiple).findPrevious("span").text
                except AttributeError:
                    p_span_text = ""
                if "技能" not in p_span_text:
                    try:
                        if "技能" in each_base.findParent(title=rule_multiple).findPrevious("b").text:
                            continue
                    except AttributeError:
                        pass
                    open_time = each_base.findPrevious("p").text.strip().replace("开放时间", "\n开放时间")
                    if not each_base.findParent(title=rule_multiple):
                        if open_time not in open_info:
                            open_info.append(open_time)
                            ul_soup.append(each_base)
                    else:
                        open_request = each_base.findParent(title=rule_multiple)["title"].strip()
                        if open_request not in open_info:
                            open_info.append(f"{open_request}\n{open_time}".strip())
                            ul_soup.append(each_base)
    except IndexError:
        pass
    except Exception as e:
        if "error" in svt:
            svt["error"].append(f"get ultimate error: {e}")
        else:
            svt["error"] = [f"get ultimate error: {e}"]
        pass

    if not ul_soup:
        ul_soup.append(base[0])
        open_info.append("")

    ultimates = []
    for uls in ul_soup:
        u1 = []
        u2 = []
        ultimate1 = uls.find_all("th")
        ultimate2 = uls.find_all("td")
        for each_ulti1 in ultimate1:
            if each_ulti1.find("p"):
                for all_p in each_ulti1.findAll("p"):
                    arg = all_p.text.strip()
                    u1.append(arg)
            else:
                arg = each_ulti1.text.strip()
                u1.append(arg)

        for each_ulti2 in ultimate2:
            if each_ulti2.find("big"):
                arg = each_ulti2.find("big").text.strip()
                u2.append(arg)
                arg2 = each_ulti2.find(class_="npname-border").text.strip()
                u2.append(arg2)
            elif each_ulti2.find("small"):
                arg = each_ulti2.find("small").text.strip()
                u2.append(arg)
                arg2 = each_ulti2.text.strip().replace(arg, "")
                u2.append(arg2)
            else:
                arg = each_ulti2.text.strip()
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

    error_list = []
    for i in range(len(ul_soup)):
        try:
            color = ul_soup[i].find(class_="floatnone").find("img", alt=True)["alt"]
            ultimates[i]["卡色"] = color.split(".")[0]
        except AttributeError:
            error_list.append(i)
    for each_error in error_list:
        ultimates.pop(each_error)
        open_info.pop(each_error)

    for i in range(len(ultimates)):
        ultimates[i]["开放条件"] = open_info[i]

    svt["宝具信息"] = ultimates


def get_skills(svt, base, raw_html):
    skill_soup = base[len(svt["宝具信息"]):]
    skill_list = []
    for i in range(len(skill_soup)):
        skill_list.append(
            (skill_soup[i], skill_soup[i].text.strip())
        )

    skills: dict = {}

    skill_flag = 0
    counter_skill = 1
    skills["职阶技能"] = []
    for each_skill_list in skill_list:
        skill_type = each_skill_list[0].findPrevious("span").text
        skill_icon = each_skill_list[0].find("img", alt=True)["data-srcset"].split(", ")[-1].split(" 2x")[0]
        if skill_type == "追加技能" or skill_flag == 2:
            skill_flag = 2
            skills[f"追加技能{counter_skill}"] = [each_skill_list[1], skill_icon, each_skill_list[0]]
            counter_skill += 1
        if skill_type == "职阶技能" or skill_flag == 1:
            skill_flag = 1
            skills["职阶技能"].append(each_skill_list[1])
        try:
            if skill_type == "持有技能" or skill_flag == 0:
                title = each_skill_list[0].findParent("div")["title"]
                if title == "强化后" or title == "强化后":
                    skills[f'{each_skill_list[0].findPrevious("b").text}({title})'] = [
                        each_skill_list[1], skill_icon, each_skill_list[0]
                    ]
                else:
                    skills[f'{each_skill_list[0].findPrevious("b").text}({title})'] = [
                        each_skill_list[1], skill_icon, each_skill_list[0]
                    ]
        except KeyError:
            if skill_type == "持有技能" or skill_flag == 0:
                skills[each_skill_list[0].findPrevious("b").text] = [each_skill_list[1], skill_icon, each_skill_list[0]]
        except AttributeError:
            title = each_skill_list[0].findParent("div")["title"]
            skills[f'特殊技能({title})'] = [each_skill_list[1], skill_icon, each_skill_list[0]]

    for each_skill in skills:
        if each_skill == "职阶技能":
            continue
        data = skills.get(each_skill)[0].strip()
        data = re.sub(r"\n+", "\n", data)
        rule_filter = re.compile(
            r"Ø|∅|\d+%\+\d+%\*\(.+\)|(\d+[.,])?\d+%(\*.+)?|\d\d+[^→]|\d+(\*.|次\n)"
        )
        data = re.sub(rule_filter, "", data).split("\n")
        trs = skills[each_skill][2].findAll("tr")
        for each_text in data[::-1]:
            if each_text.isdigit() or each_text == "":
                if not each_skill == "职阶技能":
                    data.remove(each_text)
        bak_data: list = data.copy()
        if not each_skill == "职阶技能":
            bak_data.append(skills[each_skill][1])
            tr_counter = 3
            for each_effect in data[3:]:
                value = []
                value_soup = trs[tr_counter].findAll("td")
                tr_counter += 2
                for each_value in value_soup:
                    value.append(each_value.text.strip())
                bak_data[data.index(each_effect)] = [each_effect, value]

        skills[each_skill] = bak_data

    if "职阶技能" in skills:
        bak_class_skill = skills["职阶技能"]
        counter = 1
        for each_bak_skill in bak_class_skill:
            ncs = each_bak_skill.strip()
            ncs = re.sub(r"\n+", "\n", ncs).split("\n")
            for index_ncs in range(0, len(ncs) - 1, 2):
                skills[f"职阶技能{counter}"] = [
                    ncs[index_ncs], ncs[index_ncs + 1]
                ]
                counter += 1
        skills.pop("职阶技能")

    rule_skill_icon = re.compile(r"职阶技能.+\.(png|jpg)")
    class_skill_icon = re.finditer(rule_skill_icon, raw_html)
    icons = []
    for each_skill_icon in class_skill_icon:
        tmp = each_skill_icon.group(0).split(", ")[1]
        icons.append(tmp)

    temp = skills.copy()
    counter_class_skill = 0
    for each_temp in temp:
        if each_temp.startswith("职阶技能"):
            tmp = temp[each_temp]
            skills[each_temp] = {
                "中文": tmp[0],
                "效果": tmp[1],
                "图标": icons[counter_class_skill]
            }
            counter_class_skill += 1
        elif each_temp.startswith("追加技能"):
            tmp = temp[each_temp]
            skills[each_temp] = {
                "中文": tmp[0],
                "原文": tmp[1],
                "效果": tmp[2],
                "图标": tmp[3]
            }
        else:
            tmp = temp[each_temp]
            skills[each_temp] = {
                "中文": tmp[0],
                "原文": tmp[2],
                "充能时间": tmp[1],
                "图标": tmp[-1]
            }
            if len(tmp) == 1:
                skills[each_temp]['效果'] = tmp[3]
            else:
                for i in range(3, len(tmp) - 1):
                    skills[each_temp][f'效果{i - 2}'] = tmp[i]

    svt["技能"] = skills


def get_voice(svt, soup):
    voices = soup.findAll(class_="wikitable mw-collapsible mw-collapsed nomobile")

    svt_voice = {}
    voice_type = ""
    for each_soup in voices:
        for each_type in each_soup.find("tbody").findAll("tr"):
            voice_title = each_type.find("th").text.strip()
            soup_voice = each_type.findAll("td")
            if not soup_voice:
                voice_type = voice_title
                svt_voice[voice_type] = {}
                continue
            voice_text = soup_voice[0].text.strip()
            try:
                voice_file = f'https:{soup_voice[1].findAll("a")[1]["href"]}'
            except IndexError:
                voice_file = ""
            svt_voice[voice_type][voice_title] = {
                "文本": voice_text,
                "文件": voice_file
            }

    for each_type in svt_voice:
        for each_voice in svt_voice[each_type]:
            text = svt_voice[each_type][each_voice]["文本"]
            # text = text.replace("。", "。\n").strip()
            # text = text.replace("(持有", "\n(持有")
            # text = text.replace("\n\n(持有", "\n(持有")
            # text = text.replace("(通关", "\n(通关")
            # text = text.replace("\n\n(通关", "\n(通关")
            # text = text.replace("(牵绊", "\n(牵绊")
            # text = text.replace("\n\n(牵绊", "\n(牵绊")
            # text = text.replace("(战斗", "\n(战斗")
            # text = text.replace("\n\n(战斗", "\n(战斗")
            svt_voice[each_type][each_voice]["文本"] = text

    svt["语音"] = svt_voice


async def get_pickup(svt, url, crt_file):
    new_url = f"{url}/未来Pick_Up情况"

    try:
        response = await aiorequests.get(new_url, timeout=20, verify=crt_file, headers=headers)
    except OSError:
        response = await aiorequests.get(new_url, timeout=20, verify=False, headers=headers)
    except Exception as e:
        if "error" in svt:
            svt["error"].append(f"get_pickup error: {e}")
        else:
            svt["error"] = [f"get_pickup error: {e}"]
        return

    soup = BeautifulSoup(await response.content, 'html.parser')

    try:
        pup = soup.find(class_="mw-parser-output")
    except Exception as e:
        if "error" in svt:
            svt["error"].append(f"get_pickup error: {e}")
        else:
            svt["error"] = [f"get_pickup error: {e}"]
        return

    if pup is None:
        return

    pup_status = []

    all_tds = pup.find_all("td")
    for each_td in all_tds:
        each_pool: BeautifulSoup = each_td.find("a")
        img_soup = each_pool.find("img")
        href = each_pool.get("href")
        try:
            img_urls = img_soup.get("srcset").split(",")[-1].strip()
        except AttributeError:
            img_urls = img_soup.get("data-srcset").split(",")[-1].strip()

        pup_future = {
            "title": each_pool.get("title"),
            "href": href,
            "img_url": img_urls,
            "time_start": "",
            "time_end": "",
            "time_delta": ""
        }
        time_soup = BeautifulSoup(await get_content(f"https://fgo.wiki{href}", crt_file), 'html.parser')
        try:
            time_info = time_soup.find(text="日服卡池信息")
            time_start = time_info.find_next("td")
            time_end = time_start.find_next("td")
            time_delta = time_end.find_next("td")
            pup_future["time_start"] = f'{time_start.string.strip()}（JST）'
            pup_future["time_end"] = f'{time_end.string.strip()}（JST）'
            pup_future["time_delta"] = f'{time_delta.string.strip()}（JST）'
        except Exception as e:
            logger.warning(f"{e}")
            try:
                time_info = time_soup.find(text="日服卡池信息(使用日本标准时间)")
                time_start = time_info.find_next("td")
                time_end = time_start.find_next("td")
                time_delta = time_end.find_next("td")
                pup_future["time_start"] = f'{time_start.string.strip()}（JST）'
                pup_future["time_end"] = f'{time_end.string.strip()}（JST）'
                pup_future["time_delta"] = f'{time_delta.string.strip()}（JST）'
            except Exception as e:
                if "error" in svt:
                    svt["error"].append(f"get_pickup error: {e}")
                else:
                    svt["error"] = [f"get_pickup error: {e}"]
                continue
        pup_status.append(pup_future)

    svt["pup"] = pup_status
