import re
from typing import Tuple

from ..path_and_json import *


async def get_all_svt(session: ClientSession) -> Union[Exception, Tuple[int, Union[None, list]]]:
    root_svt_url = "https://fgo.wiki/w/%E8%8B%B1%E7%81%B5%E5%9B%BE%E9%89%B4"
    try:
        raw_data = (await get_content(root_svt_url, session)).decode()
    except Exception as e:
        return e

    rule = re.compile(r'override_data(\s)?=(\s)?\".+tag=')
    data = re.search(rule, raw_data).group(0)
    data = re.sub(r'override_data(\s)?=(\s)?\"', "", data).split("\\n")
    for i in range(len(data) - 1, -1, -1):
        data[i] = data[i].replace('\\\"', '"')
        if data[i] == '':
            data.pop(i)

    updated_servants = []
    servants = []
    old_all_svt = []
    if os.path.exists(all_servant_path):
        try:
            old_all_svt = json.load(open(all_servant_path, encoding="utf-8"))
        except json.decoder.JSONDecodeError:
            old_all_svt = []

    rule_all_cmd = re.compile(r"raw_str(\s)?=(\s)?\"id.+//media.fgo.wiki/.+\.(png|jpg)")
    all_svt_icons = re.search(rule_all_cmd, raw_data).group(0).split(",")
    rule_png = re.compile(r"//media.fgo.wiki/.+\.(png|jpg)")
    for i in range(len(all_svt_icons) - 1, -1, -1):
        if not re.match(rule_png, all_svt_icons[i]):
            all_svt_icons.pop(i)
        else:
            all_svt_icons[i] = all_svt_icons[i].replace("//", "https://")

    for i in range(0, len(data), 8):
        svt: dict = {
            "id": data[i].replace("id=", ""),
            "name_cn": data[i + 1].replace("name_cn=", ""),
            "name_jp": data[i + 2].replace("name_jp=", ""),
            "name_en": data[i + 3].replace("name_en=", ""),
            "name_link": data[i + 4].replace("name_link=", ""),
            "name_other": data[i + 5].replace("name_other=", ""),
            "method": data[i + 6].replace("method=", ""),
            "tag": data[i + 7].replace("tag=", "")
        }
        cid = svt["id"]
        cid = cid.zfill(3)
        rule_cmd = re.compile(rf"https://media.fgo.wiki/.+Servant{cid}\.(png|jpg)")
        for each in all_svt_icons:
            if re.match(rule_cmd, each):
                i_each = all_svt_icons.index(each)
                if svt["id"] in banned_id:
                    svt["online"] = {
                        "svt_icon": each,
                        "class_icon": all_svt_icons[i_each + 1]
                    }
                    svt["local"] = {
                        "svt_icon": each.split("/").pop(),
                        "class_icon": all_svt_icons[i_each + 1].split("/").pop()
                    }
                    if svt["id"] == "240" or svt["id"] == "168":
                        path = "https://media.fgo.wiki/3/32/BeastⅢ.png"
                        svt["online"]["class_icon"] = path
                        svt["local"]["class_icon"] = path.split("/").pop()
                    if svt["id"] == "149":
                        path = "https://media.fgo.wiki/5/59/BeastⅡ.png"
                        svt["online"]["class_icon"] = path
                        svt["local"]["class_icon"] = path.split("/").pop()
                    if svt["id"] == "151":
                        path = "https://media.fgo.wiki/3/36/BeastⅠ.png"
                        svt["online"]["class_icon"] = path
                        svt["local"]["class_icon"] = path.split("/").pop()
                else:
                    svt["online"] = {
                        "svt_icon": each,
                        "card1_icon": all_svt_icons[i_each + 1],
                        "card2_icon": all_svt_icons[i_each + 2],
                        "card3_icon": all_svt_icons[i_each + 3],
                        "card4_icon": all_svt_icons[i_each + 4],
                        "card5_icon": all_svt_icons[i_each + 5],
                        "ultimate_icon": all_svt_icons[i_each + 6],
                        "class_icon": all_svt_icons[i_each + 7]
                    }
                    svt["local"] = {
                        "svt_icon": each.split("/").pop(),
                        "card1_icon": all_svt_icons[i_each + 1].split("/").pop(),
                        "card2_icon": all_svt_icons[i_each + 2].split("/").pop(),
                        "card3_icon": all_svt_icons[i_each + 3].split("/").pop(),
                        "card4_icon": all_svt_icons[i_each + 4].split("/").pop(),
                        "card5_icon": all_svt_icons[i_each + 5].split("/").pop(),
                        "ultimate_icon": all_svt_icons[i_each + 6].split("/").pop(),
                        "class_icon": all_svt_icons[i_each + 7].split("/").pop()
                    }
        if svt not in old_all_svt:
            updated_servants.append(int(svt["id"]))
        servants.append(svt)

    if old_all_svt == servants:
        return 1, None

    with open(all_servant_path, "w", encoding="utf-8") as f:
        f.write(json.dumps(servants, indent=2, ensure_ascii=False))

    return 0, updated_servants
