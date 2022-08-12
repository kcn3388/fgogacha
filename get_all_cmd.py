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
all_command_path = os.path.join(data_path, "all_cmd.json")


async def get_all_cmd(crt_file=False):
    root_cmd_url = "https://fgo.wiki/w/%E6%8C%87%E4%BB%A4%E7%BA%B9%E7%AB%A0%E5%9B%BE%E9%89%B4"
    try:
        get_all = await aiorequests.get(root_cmd_url, timeout=20, verify=crt_file, headers=headers)
    except OSError:
        get_all = await aiorequests.get(root_cmd_url, timeout=20, verify=False, headers=headers)
    except Exception as e:
        return e

    rule = re.compile(r'override_data(\s)?=(\s)?\".+method_link_text=')
    data = re.search(rule, await get_all.text).group(0)
    data = re.sub(r'override_data(\s)?=(\s)?\"', "", data).split("\\n")
    for i in range(len(data) - 1, -1, -1):
        if data[i] == '':
            data.pop(i)

    commands = []

    for i in range(0, len(data), 10):
        if '\\\"' in data[i + 3]:
            data[i + 3] = data[i + 3].replace('\\\"', '"')
        cmd = {
            "id": data[i].replace("id=", ""),
            "name": data[i + 1].replace("name=", ""),
            "name_link": data[i + 2].replace("name_link=", ""),
            "name_other": data[i + 3].replace("name_other=", ""),
            "des": data[i + 4].replace("des=", ""),
            "tag": data[i + 5].replace("tag=", ""),
            "type": data[i + 6].replace("type=", ""),
            "method": data[i + 7].replace("method=", ""),
            "method_link": data[i + 8].replace("method_link=", ""),
            "method_link_text": data[i + 9].replace("method_link_text=", "")
        }
        commands.append(cmd)

    old_all_cmd = []
    if os.path.exists(all_command_path):
        try:
            old_all_cmd = json.load(open(all_command_path, encoding="utf-8"))
        except json.decoder.JSONDecodeError:
            old_all_cmd = []

    if old_all_cmd == commands:
        return 1

    with open(all_command_path, "w", encoding="utf-8") as f:
        f.write(json.dumps(commands, indent=2, ensure_ascii=False))

    return 0
