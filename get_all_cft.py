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
all_craft_path = os.path.join(data_path, "all_cft.json")


async def get_all_cft(crt_file=False):
    root_cft_url = "https://fgo.wiki/w/%E7%A4%BC%E8%A3%85%E5%9B%BE%E9%89%B4"
    try:
        get_all = await aiorequests.get(root_cft_url, timeout=20, verify=crt_file, headers=headers)
    except OSError:
        get_all = await aiorequests.get(root_cft_url, timeout=20, verify=False, headers=headers)
    except Exception as e:
        return e

    rule = re.compile(r'override_data(\s)?=(\s)?\".+event=0')
    data = re.search(rule, await get_all.text).group(0)
    data = re.sub(r'override_data(\s)?=(\s)?\"', "", data).split("\\n")
    for i in range(len(data) - 1, -1, -1):
        if data[i] == '':
            data.pop(i)

    crafts = []

    for i in range(0, len(data), 9):
        if '\\\"' in data[i + 3]:
            data[i + 3] = data[i + 3].replace('\\\"', '"')
        cft = {
            "id": data[i].replace("id=", ""),
            "name": data[i + 1].replace("name=", ""),
            "name_link": data[i + 2].replace("name_link=", ""),
            "name_other": data[i + 3].replace("name_other=", ""),
            "des": data[i + 4].replace("des=", ""),
            "des_max": data[i + 5].replace("des_max=", ""),
            "tag": data[i + 6].replace("tag=", ""),
            "type": data[i + 7].replace("type=", ""),
            "event": data[i + 8].replace("event=", "")
        }
        crafts.append(cft)

    old_all_cft = []
    if os.path.exists(all_craft_path):
        try:
            old_all_cft = json.load(open(all_craft_path, encoding="utf-8"))
        except json.decoder.JSONDecodeError:
            old_all_cft = []

    if old_all_cft == crafts:
        return 1

    with open(all_craft_path, "w", encoding="utf-8") as f:
        f.write(json.dumps(crafts, indent=2, ensure_ascii=False))

    return 0
