import json
import re

from hoshino import aiorequests
from ..path_and_json import *

headers = {
    "User-Agent": "Mozilla/5.0 (Windows; U; Windows NT 5.1; zh-CN; rv:1.9.1.6) ",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "zh-cn"
}


async def get_all_cmd(crt_file=False):
    root_cmd_url = "https://fgo.wiki/w/%E6%8C%87%E4%BB%A4%E7%BA%B9%E7%AB%A0%E5%9B%BE%E9%89%B4"
    try:
        get_all = await aiorequests.get(root_cmd_url, timeout=20, verify=crt_file, headers=headers)
    except OSError:
        get_all = await aiorequests.get(root_cmd_url, timeout=20, verify=False, headers=headers)
    except Exception as e:
        return e

    raw_data = await get_all.text
    rule = re.compile(r'override_data(\s)?=(\s)?\".+method_link_text=')
    data = re.search(rule, raw_data).group(0)
    data = re.sub(r'override_data(\s)?=(\s)?\"', "", data).split("\\n")
    for i in range(len(data) - 1, -1, -1):
        data[i] = data[i].replace('\\\"', '"')
        if data[i] == '':
            data.pop(i)

    updated_commands = []
    commands = []
    old_all_cmd = []
    if os.path.exists(all_command_path):
        try:
            old_all_cmd = json.load(open(all_command_path, encoding="utf-8"))
        except json.decoder.JSONDecodeError:
            old_all_cmd = []

    rule_all_cmd = re.compile(r"raw_str(\s)?=(\s)?\"id.+/images/.+\.(png|jpg)")
    all_cmd_icons = re.search(rule_all_cmd, raw_data).group(0).split(",")
    rule_png = re.compile(r"/images/.+\.(png|jpg)")
    for i in range(len(all_cmd_icons) - 1, -1, -1):
        if not re.match(rule_png, all_cmd_icons[i]):
            all_cmd_icons.pop(i)

    for i in range(0, len(data), 10):
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
        cid = cmd["id"]
        cid = cid.zfill(3)
        rule_cmd = re.compile(rf"/images/.+纹章{cid}\.(png|jpg)")
        for each in all_cmd_icons:
            if re.match(rule_cmd, each):
                i_each = all_cmd_icons.index(each)
                cmd["online"] = {
                    "cmd_icon": each,
                    "skill_icon": all_cmd_icons[i_each + 1]
                }
                cmd["local"] = {
                    "cmd_icon": each.split("/").pop(),
                    "skill_icon": all_cmd_icons[i_each + 1].split("/").pop()
                }
        if cmd not in old_all_cmd:
            updated_commands.append(cmd["id"])
        commands.append(cmd)

    if old_all_cmd == commands:
        return 1, None

    with open(all_command_path, "w", encoding="utf-8") as f:
        f.write(json.dumps(commands, indent=2, ensure_ascii=False))

    return 0, updated_commands
