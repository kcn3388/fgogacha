import json
import os
import re

from hoshino import aiorequests

headers = {
    "User-Agent": "Mozilla/5.0 (Windows; U; Windows NT 5.1; zh-CN; rv:1.9.1.6) ",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "zh-cn"
}

runtime_path = os.path.dirname(__file__)
data_path = os.path.join(runtime_path, 'data')
all_servant_path = os.path.join(data_path, "all_svt.json")


async def get_all_svt(crt_file=False):
    root_svt_url = "https://fgo.wiki/w/%E8%8B%B1%E7%81%B5%E5%9B%BE%E9%89%B4"
    try:
        get_all = await aiorequests.get(root_svt_url, timeout=20, verify=crt_file, headers=headers)
    except OSError:
        get_all = await aiorequests.get(root_svt_url, timeout=20, verify=False, headers=headers)
    except Exception as e:
        return e

    rule = re.compile(r'override_data(\s)?=(\s)?\".+tag=')
    data = re.search(rule, await get_all.text).group(0)
    data = re.sub(r'override_data(\s)?=(\s)?\"', "", data).split("\\n")
    for i in range(len(data) - 1, -1, -1):
        if data[i] == '':
            data.pop(i)

    servants = []

    for i in range(0, len(data), 8):
        if '\\\"' in data[i + 3]:
            data[i + 3] = data[i + 3].replace('\\\"', '"')
        svt = {
            "id": data[i].replace("id=", ""),
            "name_cn": data[i + 1].replace("name_cn=", ""),
            "name_jp": data[i + 2].replace("name_jp=", ""),
            "name_en": data[i + 3].replace("name_en=", ""),
            "name_link": data[i + 4].replace("name_link=", ""),
            "name_other": data[i + 5].replace("name_other=", ""),
            "method": data[i + 6].replace("method=", ""),
            "tag": data[i + 7].replace("tag=", "")
        }
        servants.append(svt)

    old_all_svt = []
    if os.path.exists(all_servant_path):
        try:
            old_all_svt = json.load(open(all_servant_path, encoding="utf-8"))
        except json.decoder.JSONDecodeError:
            old_all_svt = []

    if old_all_svt == servants:
        return 1

    with open(all_servant_path, "w", encoding="utf-8") as f:
        f.write(json.dumps(servants, indent=2, ensure_ascii=False))

    return 0
