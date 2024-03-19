import datetime
import re
from datetime import datetime
from typing import Tuple
from urllib.parse import quote, unquote

from bs4 import BeautifulSoup

from .lib_json import *


async def lib_svt_online(url: str, session: ClientSession) -> Tuple[Union[Exception, str], int]:
    try:
        soup = BeautifulSoup(await get_content(url, session), 'html.parser')
    except Exception as e:
        return e, -100

    is_get = soup.find(class_="SvtCardNameCN")
    if is_get:
        name = soup.find("title").text.split()[0]
        return name, 1
    else:
        return "在线也没找到", 0


async def lib_svt(svt_data: dict, session: ClientSession) -> dict:
    # def lib_svt_debug(sid: int = 0) -> dict:
    #     with open(all_servant_path, 'r', encoding="utf-8") as f:
    #         servants = json.load(f)
    #     if sid:
    #         svt_data = jsonpath(servants, f"$..[?(@.id=='{sid}')]")[0]
    #     else:
    #         svt_data = jsonpath(servants, "$..[?(@.id=='312')]")[0]
    sv_lib.logger.info("查询Servant" + svt_data["id"] + "……")
    svt: dict = {
        "id": svt_data["id"],
        "name_cn": svt_data["name_cn"],
        "name_jp": svt_data["name_jp"],
        "name_en": svt_data["name_en"],
        "name_link": svt_data["name_link"],
        "name_other": None,
        "method": svt_data["method"],
        "error": []
    }

    if "local" in svt_data:
        svt["svt_icon"] = svt_data["local"]["svt_icon"] if "local" in svt_data else svt_data["svt_icon"]
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

    local_data_path = os.path.join(mc_path, "svt", f'{svt_data["id"]}.txt')
    local_html_path = os.path.join(mc_path, "svt", f'{svt_data["id"]}.html')

    if os.path.exists(local_data_path) and os.path.exists(local_html_path):
        raw_data = open(local_data_path, "r", encoding="utf-8").read().replace("魔{{jin}}", "魔神(人)")
        raw_html = open(local_html_path, "r", encoding="utf-8").read()
    else:
        svt["error"].append(f"svt{svt['id']} init error: no local res")
        return svt

    get_base(svt, raw_html, raw_data)

    get_card_url(svt, raw_html, raw_data)

    get_fool(svt, raw_data)

    get_info(svt, raw_data)

    await get_pickup(
        svt, BeautifulSoup(raw_html, 'html.parser'), f'https://fgo.wiki/w/{svt_data["name_link"]}', session
    )

    get_ultimate(svt, raw_data)

    get_skills(svt, raw_data)

    get_voice(svt, BeautifulSoup(raw_html, 'html.parser'))

    if not svt["error"]:
        svt.pop("error")
    return svt


def get_base(svt: dict, raw_html: str, raw_data: str):
    single_svt_detail: dict = {}
    # here is painter info
    painter = re.search(r"\|画师=(.+)", raw_data).group(1)
    extra_painters = re.findall(r"\|画师(\d+)=(.+)", raw_data)
    paints = re.findall(r"\|立绘\d+=(.+)", raw_data)
    painter_dict = {}
    if extra_painters:
        first_extra_id = int(extra_painters[0][0]) - 1
        for paint_index in range(first_extra_id):
            painter_dict[paints[paint_index]] = painter
        for paint_index in range(len(extra_painters)):
            painter_dict[paints[paint_index + first_extra_id]] = extra_painters[paint_index][1]
    else:
        for paint_index in range(len(paints)):
            painter_dict[paints[paint_index]] = painter
    single_svt_detail["画师"] = painter_dict

    select_attr = base_svt_detail if svt["id"] not in banned_id else sp_svt_detail
    # now go to attribute
    for each_attr in select_attr:
        if each_attr == "属性" or each_attr == "特性":
            attr = re.findall(rf"\|{each_attr}\d+=(.+)", raw_data)
        elif each_attr == "ATK" or each_attr == "HP":
            raw_num = re.findall(rf"\|.+{each_attr}=(.+)", raw_data)
            if len(raw_num) < 5:
                lv120_data = re.search(rf'"lv":120.+?{each_attr}":(\d+)', raw_html)
                raw_num.append(lv120_data.group(1)) if lv120_data else ""
            attr = [int(num) for num in raw_num if num.isdigit()]
            attr.extend([num for num in raw_num if not num.isdigit()])
        elif each_attr == "职阶补正后":
            attr = [
                round(num * atk_coefficient(single_svt_detail["职阶"]))
                if isinstance(num, str) and num.isdigit() else num for num in single_svt_detail["ATK"]
            ]
        elif each_attr == "Hit信息（括号内为每hit伤害百分比）":
            attr = {}
            cards = ["Q卡", "A卡", "B卡", "EX卡", "宝具卡"]
            for each_card in cards:
                hit = re.search(rf"\|{each_card}hit数=(\d+)", raw_data)
                hit = hit.group(1) if hit else ""
                damage_percentage = re.search(rf"\|{each_card}伤害分布=(.+)", raw_data)
                damage_percentage = damage_percentage.group(1) if damage_percentage else ""
                attr[each_card] = f"{hit} Hits ({damage_percentage})"
        elif each_attr == "NP获得率":
            attr = {}
            cards = ["Q卡", "A卡", "B卡", "EX卡", "宝具", "受击"]
            for each_card in cards:
                np_percentage = re.search(rf"\|{each_card}np率=(.+)", raw_data)
                attr[each_card] = np_percentage.group(1) if np_percentage else ""
        elif each_attr == "能力":
            attr = base_svt_detail[each_attr]
        else:
            attr = re.search(rf"\|{each_attr}=(.+)", raw_data)
            attr = attr.group(1) if attr else ""
        single_svt_detail[each_attr] = attr

    nick_names = re.search(r"\|昵称=(.+)", raw_data)
    nick_names = nick_names.group(1).split(",") if nick_names else []
    rare = re.search(r"\|稀有度=(\d)", raw_data)

    svt["detail"] = single_svt_detail
    svt["昵称"] = nick_names
    svt["rare"] = f"{rare.group(1)}星" if rare else "-"


def get_card_url(svt: dict, raw_html: str, raw_data: str):
    cards_url = []
    cards = {}
    paints = re.findall(r"\|立绘\d+=(.+)", raw_data)
    all_files = re.findall(r"\|文件\d+=(.+)", raw_data)
    if svt["id"] == "81":
        all_files.pop()
    for each_file in all_files:
        # 使用[^.]+代替.+?以避免出现非贪婪失效
        # raw_file = re.search(rf"(https://media.fgo.wiki/./[^.]+){quote(each_file)}.png", raw_html)
        raw_file = re.search(rf"(https://media.fgo.wiki/./../){quote(each_file)}.png", raw_html)
        file = f"{raw_file.group(1)}{each_file}.png" if raw_file else ""
        cards_url.append(file)
    for card_index in range(len(all_files)):
        try:
            cards[paints[card_index]] = cards_url[card_index]
        except IndexError:
            sv_lib.logger.warning(f"unmatch len of url and card for {svt['id']}")
            sv_lib.logger.warning(f"url: {len(cards_url)}; card: {len(cards)}")
            svt["error"].append(
                f"unmatch len of url and card for {svt['id']}\n"
                f"url: {len(cards_url)}; card: {len(cards)}"
            )
            break
    svt["cards_url"] = cards


def get_fool(svt: dict, raw_data: str):
    fool_raw_data = re.search(r"===愚人节===([\s\S]+?)==牵绊(点数|等级)==", raw_data)
    fool_data = fool_raw_data.group(1).strip() if fool_raw_data else ""
    fool_cn = re.findall(r"\|中文=([\s\S]+?)\|日文", fool_data)
    fool_jp = re.findall(r"\|日文=([\s\S]+?)}}", fool_data)
    fool_cn = [fcn.strip() for fcn in fool_cn]
    fool_jp = [fjp.strip() for fjp in fool_jp]
    fools = {
        "资料": fool_cn,
        "原文": fool_jp
    }
    svt["fool"] = fools


def get_info(svt: dict, raw_data: str):
    base_info = re.search(r"\|详情=\n([\s\S]+?)\n\n\|", raw_data)
    all_info = re.findall(r"\|(资料\d)=\n([\s\S]+?)\n\n?\|", raw_data)
    base_info_jp = re.search(r"\|详情日文=\n([\s\S]+?)\n\n\|", raw_data)
    rule_jp = re.compile(r"\|资料\d日文=\n([\s\S]+?)\n\n?[|}]")
    if svt["id"] in ["240", "168"]:
        rule_jp = re.compile(r"资料\d日文=([\s\S]+?)\n\|")
    all_info_jp = re.findall(rule_jp, raw_data)
    all_request = re.findall(r"\|资料\d条件=\n([\s\S]+?)\n\n\|", raw_data)
    if re.match(r"^\|资料\d条件=\n|", raw_data):
        request_data = raw_data.replace("条件=\n|", "条件=\n\n|")
        all_request = re.findall(r"\|资料\d条件=\n(.+)?", request_data)
    renew_info_key = ""
    if len(all_info) > 6:
        renew_info = re.search(r";(通关.+后)", raw_data)
        renew_info_key = re.sub(
            r"/.+\|", " ", renew_info.group(1)
        ).replace("]", "").replace("[", "").strip() if renew_info else "通关特定关卡后"

    svt_detail = {
        "角色详情": {
            "中文": base_info.group(1).strip() if base_info else "",
            "日文": base_info_jp.group(1).strip() if base_info_jp else ""
        }
    }

    for info_index in range(len(all_info)):
        try:
            req_info = all_request[info_index].strip()
            req_info = re.sub(r"/.+\|", " ", req_info).replace("]", "").replace("[", "").strip()
            svt_detail[all_info[info_index][
                0].strip() if info_index < 6 else f"{all_info[info_index][0].strip()}（{renew_info_key}）"] = {
                "开放条件": req_info,
                "中文": all_info[info_index][1].strip(),
                "日文": all_info_jp[info_index].strip()
            }
        except IndexError:
            sv_lib.logger.warning(f"unmatch len of info for {svt['id']}")
            sv_lib.logger.warning(
                f"request: {len(all_request)}; cn: {len(all_info)}; jp: {len(all_info_jp)}"
            )
            svt["error"].append(
                f"unmatch len of info for {svt['id']}\n"
                f"request: {len(all_request)}; cn: {len(all_info)}; jp: {len(all_info_jp)}"
            )
            break

    svt["svt_detail"] = svt_detail


def get_ultimate(svt: dict, raw_data: str):
    ultimates = []
    raw_ultimates = re.search(r"==宝具==([\s\S]+?)==技能==", raw_data)

    if not raw_ultimates:
        if svt["id"] == "152":
            svt["宝具信息"] = ultimates
            return
        svt["error"].append(f"get ultimate error for {svt['id']}")
        return
    raw_ultimates = raw_ultimates.group(1)
    all_ultimates = re.findall(r"((.+?)=([\s\S]+?)?\n?)?{{宝具\n([\s\S]+?)\n}}", raw_ultimates)
    all_reqs = re.findall(r"(\n[^|<]+=([^{]+)?)", raw_ultimates)
    all_reqs = all_reqs if len(all_reqs) == len(all_ultimates) else []

    for ui in range(len(all_ultimates)):
        each_ultimate = all_ultimates[ui]
        if not each_ultimate[-1]:
            continue
        ultimate = each_ultimate[-1]
        req = ""
        if all_reqs:
            req = all_reqs[ui][0].strip()
            req = re.sub(r"\[\[.+\|", "", req).replace("]", "").replace("[", "") if req else ""
            req = req.replace("=", "/") if not req.endswith("=") else req.replace("=", "")
        level = re.search(r"\|阶级=(.+)", ultimate)
        level = level.group(1) if level else ""
        cn_upper = re.search(r"\|国服上标=(.+)", ultimate)
        jp_upper = re.search(r"\|日服上标=(.+)", ultimate)
        single_ultimate = {
            "中文": (re.search(r"\|中文名=(.+)", ultimate).group(1) + f" {level}").strip(),
            "日文": (re.search(r"\|日文名=(.+)", ultimate).group(1) + f" {level}").strip(),
            "国服上标": cn_upper.group(1) if cn_upper else "",
            "日服上标": jp_upper.group(1) if jp_upper else "",
            "卡色": re.search(r"\|卡色=(.+)", ultimate).group(1),
            "类型": re.search(r"\|类型=(.+)", ultimate).group(1),
            "阶级": level,
            "开放条件": req.strip()
        }
        ultimate_type = re.search(r"\|种类=(.+)", ultimate)
        single_ultimate["种类"] = ultimate_type.group(1) if ultimate_type else ""

        effect_types = re.findall(r"\|效果([A-Z])=(.+)<!--", ultimate)
        if not effect_types:
            effect_types = re.findall(r"\|效果([A-Z])=(.+)", ultimate)
            if not effect_types:
                continue
        for each_effect in effect_types:
            effect_values = re.findall(rf"\|数值{each_effect[0]}\d=(\d+%?|.)", ultimate)
            single_ultimate[each_effect[-1]] = effect_values
        ultimates.append(single_ultimate)

    svt["宝具信息"] = ultimates


def get_skills(svt: dict, raw_data: str):
    skills: dict = {}
    all_raw_skills = re.search(r"===持有技能===[\s\S]+?}}(\n</tabber>)?\n\n", raw_data)
    if all_raw_skills:
        all_raw_skills = all_raw_skills.group(0).replace("<br>", "")
    else:
        svt["技能"] = skills
        return

    all_raw_normal_skills_temp = re.findall(r"\'\'\'技能[\s\S]+?{{持有技能[\s\S]+?}}", all_raw_skills)
    all_raw_normal_skills = [ts for ts in all_raw_normal_skills_temp if "<tabber>" not in ts]
    all_normal_skills = []
    all_normal_names = []
    all_normal_reqs = []

    for normal_skill in all_raw_normal_skills:
        if svt["id"] == "332":
            normal_skill = re.sub(r"<!--.+\n.+-->\|", "|", normal_skill)
        if svt["id"] == "281":
            normal_skill = re.sub(r"<!--.+\n.+-->", "", normal_skill)
        name = re.search(r"\'\'\'(技能(.+)?)\'\'\'", normal_skill)
        name = name.group(1) if name else ""
        all_normal_names.append(name)

        req = re.search(r"\'\'\'技能(.+)?\'\'\'\n([\s\S]+?)\n{{持有技能", normal_skill)
        req = re.sub(r"\[\[.+\|", "", req.group(2)).replace("]", "").replace("[", "") if req else ""
        all_normal_reqs.append(req)

        temp = re.sub(r"<!--.+-->\n|\|.+=.+\n", "", normal_skill).replace("<nowiki", "$$")
        unmatch_skill = re.findall(r"\|\D[^|$]+?\n\|.+?\|", temp)
        if unmatch_skill:
            for each_us in unmatch_skill:
                origin = each_us
                repl = origin.replace("\n", "")
                temp = temp.replace(origin, repl)
        temp = re.sub(r"{{持有技能\n", "{{持有技能", temp).split("\n")
        single_normal_skill = []
        for each_temp in temp:
            if re.match(r"^{{|^\|", each_temp):
                single_normal_skill.append(each_temp.replace("{{", ""))
        all_normal_skills.append(single_normal_skill) if single_normal_skill else ""

    for ns_index in range(len(all_normal_skills)):
        skill = {}
        each_normal_skill = all_normal_skills[ns_index]
        try:
            for skill_index in range(len(each_normal_skill)):
                temp = each_normal_skill[skill_index].split("|")
                raw_skill_info = [t for t in temp if t]
                if skill_index == 0:
                    skill_type = raw_skill_info[1]
                    skill_name_cn = raw_skill_info[2]
                    skill_name_jp = raw_skill_info[3]
                    cooldown_init = re.match(r"\d+", raw_skill_info[-1])
                    cooldown = int(cooldown_init.group(0)) if cooldown_init else ""
                    skill["中文"] = skill_name_cn
                    skill["日文"] = skill_name_jp
                    skill["充能时间"] = f"{cooldown}→{cooldown - 1}→{cooldown - 2}" if cooldown else ""
                    skill["开放条件"] = all_normal_reqs[ns_index]
                    skill["类型"] = skill_type
                else:
                    effect = raw_skill_info.pop(0)
                    skill_info = [rsi.replace("}}", "") for rsi in raw_skill_info]
                    skill[effect] = skill_info
            if svt["id"] == "1" and all_normal_names[ns_index] in skills:
                skills[f"{all_normal_names[ns_index]}（第2部灵衣）"] = skill
            else:
                skills[all_normal_names[ns_index]] = skill
        except IndexError:
            sv_lib.logger.warning(f"unmatch len of skill and skill name for {svt['id']}")
            sv_lib.logger.warning(f"name: {len(all_normal_names)}; skill: {len(all_normal_skills)}")
            svt["error"].append(f"name: {len(all_normal_names)}; skill: {len(all_normal_skills)}")
            break

    get_tabber_skills(svt, all_raw_skills, skills)


def get_tabber_skills(svt: dict, all_raw_skills: str, skills: dict):
    all_raw_skills = all_raw_skills.replace("强化前={{持有技能", "强化前=\n{{持有技能")
    all_raw_multi_skills = re.findall(r"(\'\'\'技能.+?\n<tabber>[\s\S]+?}}\n</tabber>)", all_raw_skills)
    multi_skills_temp = [mst.split("|-|") for mst in all_raw_multi_skills]
    if not all_raw_multi_skills:
        svt["技能"] = skills
        return

    all_multi_names = []
    all_multi_skills = []
    multi_skills_req = []
    for each_multi in all_raw_multi_skills:
        multi_name = re.search(r"\'\'\'(技能(.+)?)\'\'\'", each_multi)
        all_multi_names.append(multi_name.group(1)) if multi_name else ""

    for each_ms in multi_skills_temp:
        skills_req = []
        multi_skills = []
        for ms in each_ms:
            req = re.search(r"(.+=(.+)?)\n{{持有技能", ms)
            req = re.sub(r"\[\[.+\||<!--.+-->", "", req.group(1)).replace("]", "") if req else ""
            req = req.replace("=", "/") if not req.endswith("=") else req.replace("=", "")
            skills_req.append(req)
            temp = re.sub(r"<!--.+-->\n(?!{{持有技能)|\|.+=.+\n", "", ms).replace("<nowiki", "$$")
            unmatch_skill = re.findall(r"\|\D[^|$]+?\n\|.+?\|", temp)
            if unmatch_skill:
                for each_us in unmatch_skill:
                    origin = each_us
                    repl = origin.replace("\n", "")
                    temp = temp.replace(origin, repl)
            temp = re.sub(r"{{持有技能\n", "{{持有技能", temp).split("\n")
            single_multi_skill = []
            for each_temp in temp:
                if re.match(r"^{{|^\|", each_temp):
                    single_multi_skill.append(each_temp.replace("{{", ""))
            multi_skills.append(single_multi_skill) if single_multi_skill else ""
        all_multi_skills.append(multi_skills)
        multi_skills_req.append(skills_req)

    m_skills = []
    try:
        for ns_index in range(len(all_multi_skills)):
            each_multi_skill = all_multi_skills[ns_index]
            multi = []
            for skill_index in range(len(each_multi_skill)):
                each_skill = each_multi_skill[skill_index]
                skill = {}
                for effects_index in range(len(each_skill)):
                    temp = each_skill[effects_index].split("|")
                    raw_skill_info = [t for t in temp if t]
                    if effects_index == 0:
                        skill_name_cn = raw_skill_info[2]
                        skill_name_jp = raw_skill_info[3]
                        cooldown_init = re.match(r"\d+", raw_skill_info[-1])
                        cooldown = int(cooldown_init.group(0)) if cooldown_init else ""
                        skill["中文"] = skill_name_cn
                        skill["日文"] = skill_name_jp
                        skill["充能时间"] = f"{cooldown}→{cooldown - 1}→{cooldown - 2}" if cooldown else ""
                        skill["开放条件"] = multi_skills_req[ns_index][skill_index]
                    else:
                        effect = raw_skill_info.pop(0)
                        skill[effect] = raw_skill_info
                multi.append(skill)
            m_skills.append(multi)

        for name_index in range(len(all_multi_names)):
            if svt["id"] == "1" and all_multi_names[name_index] in skills:
                skills[f"{all_multi_names[name_index]}（第2部灵衣）"] = m_skills[name_index]
            else:
                skills[all_multi_names[name_index]] = m_skills[name_index]
    except IndexError:
        sv_lib.logger.warning(f"unmatch len of multi skill and skill name for {svt['id']}")
        sv_lib.logger.warning(
            f"name: {len(all_multi_names)}; skill: {len(m_skills)}; req: {len(multi_skills_req)}"
        )
        svt["error"].append(
            f" multiname: {len(all_multi_names)}; skill: {len(m_skills)}; req: {len(multi_skills_req)}"
        )
        pass

    svt["技能"] = skills


def get_voice(svt: dict, soup: BeautifulSoup):
    voices = soup.find_all(class_="wikitable mw-collapsible mw-collapsed nomobile")

    svt_voice = {}
    voice_type = ""
    for each_soup in voices:
        for each_type in each_soup.find("tbody").find_all("tr"):
            voice_title = each_type.find("th").text.strip()
            soup_voice = each_type.find_all("td")
            if not soup_voice:
                voice_type = voice_title
                svt_voice[voice_type] = {}
                continue
            voice_text = soup_voice[0].text.strip()
            try:
                voice_file = f'https:{soup_voice[1].find_all("a")[1]["href"]}'
            except IndexError:
                voice_file = ""
            svt_voice[voice_type][voice_title] = {
                "文本": voice_text,
                "文件": unquote(voice_file)
            }

    for each_type in svt_voice:
        for each_voice in svt_voice[each_type]:
            text = svt_voice[each_type][each_voice]["文本"]
            svt_voice[each_type][each_voice]["文本"] = text

    svt["语音"] = svt_voice


async def get_pickup(svt: dict, origin_soup: BeautifulSoup, url: str, session: ClientSession):
    new_url = f"{url}/未来Pick_Up情况"

    try:
        soup = BeautifulSoup(await get_content(new_url, session), 'html.parser')
    except Exception as e:
        svt["error"].append(f"svt{svt['id']} get_pickup error: {e}")
        return

    try:
        pup = soup.find(class_="mw-parser-output")
    except Exception as e:
        if "error" in svt:
            svt["error"].append(f"svt{svt['id']} get_pickup error: {e}")
        else:
            svt["error"] = [f"svt{svt['id']} get_pickup error: {e}"]
        return

    if pup is None:
        try:
            all_method_dl = origin_soup.find(id="获得方法").find_next("dl")
            all_method_ul = origin_soup.find(id="获得方法").find_next("ul")
            methods = ""
            how = all_method_dl.find_all("dt")
            dd = all_method_dl.find_all("dd")
            li = all_method_ul.find_all("li")
            if len(how) == len(dd):
                for index in range(len(how)):
                    methods += f"{how[index].text}\n{dd[index].text}\n"
            elif len(how) == len(li):
                for index in range(len(how)):
                    methods += f"{how[index].text}\n{li[index].text}\n"
            else:
                for index in range(len(how)):
                    methods += f"{how[index].text}\n"
            methods = methods.strip()
            svt["method_get"] = methods
        except AttributeError:
            pass
        return

    methods = pup.text.strip()
    svt["method_get"] = methods
    pup_status = []

    all_tds = pup.find_all("td")
    for each_td in all_tds:
        if "页面不存在" in str(each_td):
            continue
        each_pool: BeautifulSoup = each_td.find("a")
        href = each_pool.get("href")
        pup_future = {
            "title": each_pool.get("title"),
            "href": unquote(href),
            "img_url": "",
            "time_start": "",
            "time_end": "",
            "time_delta": ""
        }
        try:
            new_href = href.replace("/w/", "")
            raw_time = BeautifulSoup(
                await get_content(f"https://fgo.wiki/index.php?title={new_href}&action=edit", session), 'html.parser'
            ).find("textarea").text
            try:
                img_soup = each_pool.find("img")
                try:
                    raw_img_url = img_soup.get("srcset").split(",")[-1].replace("/thumb", "").strip()
                except AttributeError:
                    raw_img_url = img_soup.get("data-srcset").split(",")[-1].replace("/thumb", "").strip()
                img = re.search(r"https://media.fgo.wiki/./../.+?\.png", raw_img_url).group(0)
            except AttributeError:
                img_file = re.search(r"\|卡池图文件名jp=(.+?\.png)", raw_time).group(1).replace(" ", "_")
                img = re.search(rf"https://media.fgo.wiki(/thumb)?/./../{quote(img_file)}", str(soup)).group(0).replace("/thumb", "")
            pup_future["img_url"] = unquote(img)
            time_start = datetime.strptime(re.search(r"\|卡池开始时间jp=(.+)", raw_time).group(1), "%Y-%m-%d %H:%M")
            time_end = datetime.strptime(re.search(r"\|卡池结束时间jp=(.+)", raw_time).group(1), "%Y-%m-%d %H:%M")
            time_delta = time_end - time_start
            pup_future["time_start"] = time_start.strftime(
                f"%Y年%m月%d日({week_list[time_start.weekday()]}) %H:%M（JST）"
            )
            pup_future["time_end"] = time_end.strftime(
                f"%Y年%m月%d日({week_list[time_end.weekday()]}) %H:%M（JST）"
            )
            sec = time_delta.seconds
            pup_future["time_delta"] = f'{time_delta.days}天{int(sec / 3600)}小时{int((sec % 3600) / 60)}分钟（JST）'
        except Exception as e:
            svt["error"].append(f"svt{svt['id']} get_pickup error: {e}")
            continue
        pup_status.append(pup_future)

    svt["pup"] = pup_status

# lib_svt_debug()
# errors = []
# for i in range(400, 0, -1):
#     data = lib_svt_debug(i)
#     if "error" in data:
#         sv_lib.logger.error(f"更新从者{i}出错：{data['error']}")
#         errors.append(i)
#
# print(errors)
