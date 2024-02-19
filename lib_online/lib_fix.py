import re
from hoshino import HoshinoBot

from .lib_svt import lib_svt
from .lib_cft import lib_cft
from .lib_cmd import lib_cmd
from ..path_and_json import *


async def online_fix_lib(bot: HoshinoBot, ev: CQEvent):
    is_3_args = False
    rule_raw = re.compile(r"^([修x])?([补b])?[fb]go[图tl][书si][馆gb]([修x])?([补b])?(\s.+)?$", re.IGNORECASE)
    if re.match(rule_raw, ev.raw_message):
        is_3_args = True

    msg = ev.message.extract_plain_text().split()

    if is_3_args:
        if not len(msg) == 3:
            await bot.send(ev, "食用指南：[修补fgo图书馆 + 类型 + id]")
            return

        if not msg[2].isdigit():
            await bot.send(ev, "说了要id，宁这是填了个🔨")
            return

    else:
        if not len(msg) == 2:
            await bot.send(ev, "食用指南：[修补fgo(类型) + id]")
            return

        if not msg[1].isdigit():
            await bot.send(ev, "说了要id，宁这是填了个🔨")
            return

    try:
        with open(lib_servant_path, 'r', encoding="utf-8") as f:
            svt = json.load(f)
        with open(lib_craft_path, 'r', encoding="utf-8") as f:
            cft = json.load(f)
        with open(lib_command_path, 'r', encoding="utf-8") as f:
            cmd = json.load(f)
        with open(all_servant_path, 'r', encoding="utf-8") as f:
            servants = json.load(f)
        with open(all_craft_path, 'r', encoding="utf-8") as f:
            crafts = json.load(f)
        with open(all_command_path, 'r', encoding="utf-8") as f:
            commands = json.load(f)
    except (json.decoder.JSONDecodeError, FileNotFoundError):
        await bot.send(ev, "本地没有图书馆数据~请先更新图书馆~\n指令：[更新fgo图书馆]")
        return

    rule_svt = re.compile(r"([从c][者z]|svt|servant)", re.IGNORECASE)
    is_svt = False
    if re.search(rule_svt, msg[1]):
        is_svt = True
        msg = msg[2:]
    if re.search(rule_svt, msg[0]):
        is_svt = True
        msg = msg[1:]

    async with ClientSession(headers=headers) as session:
        fixed = False
        if is_svt:
            max_id = svt[0]["id"]
            if int(msg[0]) > int(max_id):
                await bot.send(ev, "不存在此id，如果要新增条目请使用[增添fgo图书馆]~")
                return

            svt_index = jsonpath(svt, "$..id").index(msg[0])
            select_servant = jsonpath(servants, f"$..[?(@.id=='{msg[0]}')]")[0]
            data = await lib_svt(select_servant, session)
            if "error" in data:
                sv_lib.logger.error(f"更新从者{select_servant['id']}出错：{data['error']}")
            else:
                fixed = True
            svt[svt_index] = data

            with open(lib_servant_path, "w", encoding="utf-8") as f:
                f.write(json.dumps(svt, indent=2, ensure_ascii=False))
            if fixed:
                await bot.send(ev, "已修补从者数据~")
            else:
                await bot.send(ev, "从者数据错误，请再试一次~")
            return

        rule_cft = re.compile(r"([礼l][装z]|cft|craft)", re.IGNORECASE)
        is_cft = False
        if re.search(rule_cft, msg[1]):
            is_cft = True
            msg = msg[2:]
        if re.search(rule_cft, msg[0]):
            is_cft = True
            msg = msg[1:]

        fixed = False
        if is_cft:
            max_id = cft[0]["id"]
            if int(msg[0]) > int(max_id):
                await bot.send(ev, "不存在此id，如果要新增条目请使用[增添fgo图书馆]~")
                return

            cft_index = jsonpath(cft, "$..id").index(msg[0])
            select_craft = jsonpath(crafts, f"$..[?(@.id=='{msg[0]}')]")[0]
            data = await lib_cft(select_craft)
            if "error" in data:
                sv_lib.logger.error(f"更新礼装{cft[cft_index]['id']}出错：{data['error']}")
            else:
                fixed = True
            cft[cft_index] = data

            with open(lib_craft_path, "w", encoding="utf-8") as f:
                f.write(json.dumps(cft, indent=2, ensure_ascii=False))
            if fixed:
                await bot.send(ev, "已修补礼装数据~")
            else:
                await bot.send(ev, "礼装数据错误，请再试一次~")
            return

        rule_cmd = re.compile(r"([纹w][章z]|cmd|command)", re.IGNORECASE)
        is_cmd = False
        if re.search(rule_cmd, msg[1]):
            is_cmd = True
            msg = msg[2:]
        if re.search(rule_cmd, msg[0]):
            is_cmd = True
            msg = msg[1:]

        fixed = False
        if is_cmd:
            max_id = cmd[0]["id"]
            if int(msg[0]) > int(max_id):
                await bot.send(ev, "不存在此id，如果要新增条目请使用[增添fgo图书馆]~")
                return

            cmd_index = jsonpath(cmd, "$..id").index(msg[0])
            select_command = jsonpath(commands, f"$..[?(@.id=='{msg[0]}')]")[0]
            data = await lib_cmd(select_command)
            if "error" in data:
                sv_lib.logger.error(f"更新纹章{cmd[cmd_index]['id']}出错：{data['error']}")
            else:
                fixed = True
            cmd[cmd_index] = data

            with open(lib_craft_path, "w", encoding="utf-8") as f:
                f.write(json.dumps(cmd, indent=2, ensure_ascii=False))
            if fixed:
                await bot.send(ev, "已修补纹章数据~")
            else:
                await bot.send(ev, "纹章数据错误，请再试一次~")
            return
