import os.path
import re

from hoshino import Service, priv
from hoshino.typing import CQEvent
from typing import Tuple
from .lib_online.lib_online import get_card
from .lib_online.lib_svt import lib_svt, lib_svt_online
from .lib_online.lib_cft import lib_cft, lib_cft_online
from .lib_online.lib_cmd import lib_cmd, lib_cmd_online
from .path_and_json import *

sv_lib_help = '''
# fgo数据库相关
``[更新fgo图书馆]`` 获取从者/礼装/纹章的相关详细数据，包括属性、白值等
- 支持附带类型参数以更新指定内容
- 类型参数：从者/礼装/纹章/最新
  - 当参数含有最新时，只会获取本地不存在的内容
  - 支持种类与最新同时存在
- **※需要先执行``[获取全部内容]``**

``[增添fgo图书馆 + 类型 + id]`` 在本地已存在图书馆的情况下，手动增添新数据，以避免每次数据更新都需要重新爬一次全部内容
- 类型：从者、礼装、纹章

``[查询最新图书馆 + 类型]`` 获取最近的内容

``[修补fgo图书馆 + 类型 + id]`` 单独修补某张卡片的详细数据
- 类型为：从者、礼装、纹章
- **※需要先执行``[更新fgo图书馆]``**

``[fgo从者查询 + 关键词（至少一个）]`` 通过关键词搜索从者
- 若关键词大于两个，只会返回同时符合的
- 可以附带参数``详细``以获取卡面及游戏数据，附带参数``数据``则不显示卡面只显示游戏数据
- 当输入参数存在id{卡片id}时，直接返回对应id的卡片
  - 例子：``查询fgo从者 id312``

``[fgo礼装查询 + 关键词（至少一个）]`` 通过关键词搜索礼装
- 若关键词大于两个，只会搜索同时符合的
- 可以附带参数``详细``以获取卡面及游戏数据
- 查询特定id的礼装同上

``[fgo纹章查询 + 关键词（至少一个）]`` 通过关键词搜索礼装
- 若关键词大于两个，只会搜索同时符合的
- 可以附带参数``详细``以获取卡面及游戏数据
- 查询特定id的纹章同上
'''.strip()

sv_lib = Service(
    name='fgo图书馆',
    help_=sv_lib_help,
    bundle="娱乐",
    enable_on_default=True,
    visible=True,
    use_priv=priv.NORMAL,  # 使用权限
    manage_priv=priv.ADMIN,  # 管理权限
)


@sv_lib.on_fullmatch(("帮助fgo图书馆", "帮助FGO图书馆", "帮助bgo图书馆", "帮助BGO图书馆"))
@sv_lib.on_rex(r"(?i)^[fb]go[图tl][书si][馆gb][帮b][助z]$")
async def bangzhu(bot, ev):
    helps = gen_node(sv_lib_help)
    await bot.send_group_forward_msg(group_id=ev['group_id'], messages=helps)


@sv_lib.on_rex(r"(?i)^([获h更g][取q新x])?[fb]go[图tl][书si][馆gb]([获h更g][取q新x])?(\s.+)?$")
async def update_lib(bot, ev: CQEvent):
    try:
        with open(all_servant_path, 'r', encoding="utf-8") as f:
            svt = json.load(f)
        with open(all_craft_path, 'r', encoding="utf-8") as f:
            cft = json.load(f)
        with open(all_command_path, 'r', encoding="utf-8") as f:
            cmd = json.load(f)
        with open(update_data_path, 'r', encoding="utf-8") as f:
            updates = json.load(f)
    except json.decoder.JSONDecodeError:
        await bot.finish(ev, "本地没有数据~请先获取数据~\n指令：[更新fgo图书馆] 或 [获取全部内容]")
    except FileNotFoundError:
        await bot.finish(ev, "本地没有数据~请先获取数据~\n指令：[更新fgo图书馆] 或 [获取全部内容]")

    crt_file = False
    group_config = load_config(ev, True)
    if not group_config["crt_path"] == "False":
        crt_file = os.path.join(crt_folder_path, group_config["crt_path"])

    update_svt = False
    update_cft = False
    update_cmd = False
    latest = False

    rule = re.compile(
        r"(?i)^([获h更g][取q新x])?[fb]go[图tl][书si][馆gb]([获h更g][取q新x])?\s?([最z][新x]|latest|recent)?$")
    rule_svt = re.compile(r"(?i)([从c][者z]|svt|servant)")
    rule_cft = re.compile(r"(?i)([礼l][装z]|cft|craft)")
    rule_cmd = re.compile(r"(?i)([纹w][章z]|cmd|command)")
    rule_latest = re.compile(r"(?i)([最z][新x]|latest|recent)")

    msg = ev.message.extract_plain_text()

    if re.match(rule, msg):
        update_svt = True
        update_cft = True
        update_cmd = True

    if re.search(rule_svt, msg):
        update_svt = True

    if re.search(rule_cft, msg):
        update_cft = True

    if re.search(rule_cmd, msg):
        update_cmd = True

    if re.search(rule_latest, msg):
        latest = True

    await bot.send(ev, "开始更新大图书馆~")

    if update_svt:
        sv_lib.logger.info("开始更新从者……")
        errors = []

        if latest:
            try:
                with open(lib_servant_path, 'r', encoding="utf-8") as f:
                    servants = json.load(f)
            except json.decoder.JSONDecodeError:
                await bot.finish(ev, "本地没有数据~请先获取数据~\n指令：[更新fgo图书馆 + 从者]")
            except FileNotFoundError:
                await bot.finish(ev, "本地没有数据~请先获取数据~\n指令：[更新fgo图书馆 + 从者]")

            svt_latest_local = int(servants[0]["id"])
            svt_latest_remote = int(svt[0]["id"])
            svt_ids = [servants[i_svt]["id"] for i_svt in range(len(servants))]
            if not svt_latest_local == svt_latest_remote or updates["svt"]:
                update_svt_list = list(reversed(updates["svt"]))
                for each_update_svt_id in update_svt_list:
                    ready_svt = [each_svt for each_svt in svt if each_svt.get("id") == each_update_svt_id][0]
                    svt_data = await lib_svt(ready_svt, crt_file)
                    if each_update_svt_id in svt_ids:
                        servants[svt_ids.index(each_update_svt_id)] = svt_data
                    else:
                        servants.insert(0, svt_data)
                    if "error" in svt_data:
                        sv_lib.logger.error(f"更新从者{each_update_svt_id}出错：{svt_data['error']}")
                        errors.append(each_update_svt_id["id"])

            updates["svt"] = []

        else:
            servants = []

            # data = await lib_svt(svt[23], crt_file)
            for each_svt in svt:
                data = await lib_svt(each_svt, crt_file)
                if "error" in data:
                    sv_lib.logger.error(f"更新从者{each_svt['id']}出错：{data['error']}")
                    errors.append(each_svt["id"])
                servants.append(data)

        if os.path.exists(lib_servant_path):
            try:
                old_servants = json.load(open(lib_servant_path, encoding="utf-8"))
                if old_servants == servants:
                    await bot.send(ev, "从者无需更新~")
                else:
                    with open(lib_servant_path, "w", encoding="utf-8") as f:
                        f.write(json.dumps(servants, indent=2, ensure_ascii=False))
                    await bot.send(ev, "已获取从者数据~")
                    if errors:
                        e_msg = "以下从者出错，请单独获取："
                        for error in errors:
                            e_msg += f"{error}; "
                        await bot.send(ev, e_msg)
            except json.decoder.JSONDecodeError:
                pass
        else:
            with open(lib_servant_path, "w", encoding="utf-8") as f:
                f.write(json.dumps(servants, indent=2, ensure_ascii=False))
            await bot.send(ev, "已获取从者数据~")
            if errors:
                e_msg = "以下从者出错，请单独获取："
                for error in errors:
                    e_msg += f"\t{error}"
                await bot.send(ev, e_msg)

    if update_cft:
        sv_lib.logger.info("开始更新礼装……")
        errors = []

        if latest:
            try:
                with open(lib_craft_path, 'r', encoding="utf-8") as f:
                    crafts = json.load(f)
            except json.decoder.JSONDecodeError:
                await bot.finish(ev, "本地没有数据~请先获取数据~\n指令：[更新fgo图书馆]")
            except FileNotFoundError:
                await bot.finish(ev, "本地没有数据~请先获取数据~\n指令：[更新fgo图书馆]")

            cft_latest_local = int(crafts[0]["id"])
            cft_latest_remote = int(cft[0]["id"])
            cft_ids = [crafts[i_cft]["id"] for i_cft in range(len(crafts))]
            if not cft_latest_local == cft_latest_remote or updates["cft"]:
                update_cft_list = list(reversed(updates["cft"]))
                for each_update_cft_id in update_cft_list:
                    ready_cft = [each_cft for each_cft in cft if each_cft.get("id") == each_update_cft_id][0]
                    cft_data = await lib_cft(ready_cft, crt_file)
                    if each_update_cft_id in cft_ids:
                        crafts[cft_ids.index(each_update_cft_id)] = cft_data
                    else:
                        crafts.insert(0, cft_data)
                    if "error" in cft_data:
                        sv_lib.logger.error(f"更新礼装{each_update_cft_id}出错：{cft_data['error']}")
                        errors.append(each_update_cft_id)

            updates["cft"] = []

        else:
            crafts = []

            # data = await lib_cft(cft[0], crt_file)
            for each_cft in cft:
                data = await lib_cft(each_cft, crt_file)
                if "error" in data:
                    sv_lib.logger.error(f"更新礼装{each_cft['id']}出错：{data['error']}")
                    errors.append(each_cft["id"])
                crafts.append(data)

        if os.path.exists(lib_craft_path):
            try:
                old_crafts = json.load(open(lib_craft_path, encoding="utf-8"))
                if old_crafts == crafts:
                    await bot.send(ev, "礼装无需更新~")
                else:
                    with open(lib_craft_path, "w", encoding="utf-8") as f:
                        f.write(json.dumps(crafts, indent=2, ensure_ascii=False))
                    await bot.send(ev, "已获取礼装数据~")
                    if errors:
                        e_msg = "以下礼装出错，请单独获取："
                        for error in errors:
                            e_msg += f"{error}\t"
                        await bot.send(ev, e_msg)
            except json.decoder.JSONDecodeError:
                pass
        else:
            with open(lib_craft_path, "w", encoding="utf-8") as f:
                f.write(json.dumps(crafts, indent=2, ensure_ascii=False))
            await bot.send(ev, "已获取礼装数据~")
            if errors:
                e_msg = "以下礼装出错，请单独获取："
                for error in errors:
                    e_msg += f"{error}\t"
                await bot.send(ev, e_msg)

    if update_cmd:
        sv_lib.logger.info("开始更新纹章……")
        errors = []

        if latest:
            try:
                with open(lib_command_path, 'r', encoding="utf-8") as f:
                    commands = json.load(f)
            except json.decoder.JSONDecodeError:
                await bot.finish(ev, "本地没有数据~请先获取数据~\n指令：[更新fgo图书馆]")
            except FileNotFoundError:
                await bot.finish(ev, "本地没有数据~请先获取数据~\n指令：[更新fgo图书馆]")

            cmd_latest_local = int(commands[0]["id"])
            cmd_latest_remote = int(cmd[0]["id"])
            cmd_ids = [commands[i_cmd]["id"] for i_cmd in range(len(commands))]
            if not cmd_latest_local == cmd_latest_remote or updates["cmd"]:
                update_cmd_list = list(reversed(updates["cmd"]))
                for each_update_cmd_id in update_cmd_list:
                    ready_cmd = [each_cmd for each_cmd in cmd if each_cmd.get("id") == each_update_cmd_id][0]
                    cmd_data = await lib_cmd(ready_cmd, crt_file)
                    if each_update_cmd_id in cmd_ids:
                        commands[cmd_ids.index(each_update_cmd_id)] = cmd_data
                    else:
                        commands.insert(0, cmd_data)
                    if "error" in cmd_data:
                        sv_lib.logger.error(f"更新纹章{each_update_cmd_id}出错：{cmd_data['error']}")
                        errors.append(each_update_cmd_id)

            updates["cmd"] = []

        else:
            commands = []

            # data = await lib_cmd(cft[0], crt_file)
            for each_cmd in cmd:
                data = await lib_cmd(each_cmd, crt_file)
                if "error" in data:
                    sv_lib.logger.error(f"更新纹章{each_cmd['id']}出错：{data['error']}")
                    errors.append(each_cmd["id"])
                commands.append(data)

        if os.path.exists(lib_command_path):
            try:
                old_commands = json.load(open(lib_command_path, encoding="utf-8"))
                if old_commands == commands:
                    await bot.send(ev, "纹章无需更新~")
                else:
                    with open(lib_command_path, "w", encoding="utf-8") as f:
                        f.write(json.dumps(commands, indent=2, ensure_ascii=False))
                    await bot.send(ev, "已获取纹章数据~")
                    if errors:
                        e_msg = "以下纹章出错，请单独获取："
                        for error in errors:
                            e_msg += f"{error}\t"
                        await bot.send(ev, e_msg)
            except json.decoder.JSONDecodeError:
                pass
        else:
            with open(lib_command_path, "w", encoding="utf-8") as f:
                f.write(json.dumps(commands, indent=2, ensure_ascii=False))
            await bot.send(ev, "已获取纹章数据~")
            if errors:
                e_msg = "以下纹章出错，请单独获取："
                for error in errors:
                    e_msg += f"{error}\t"
                await bot.send(ev, e_msg)

    with open(update_data_path, "w", encoding="utf-8") as f:
        f.write(json.dumps(updates, indent=2, ensure_ascii=False))


@sv_lib.on_rex(r"(?i)^([查c][询x])?[fb]go[图tl][书si][馆gb]([查c][询x])?(\s[\s\S]+)?$")
async def add_lib(bot, ev: CQEvent):
    try:
        with open(all_servant_path, 'r', encoding="utf-8") as f:
            svt = json.load(f)
        with open(all_craft_path, 'r', encoding="utf-8") as f:
            cft = json.load(f)
        with open(all_command_path, 'r', encoding="utf-8") as f:
            cmd = json.load(f)
        with open(lib_servant_path, 'r', encoding="utf-8") as f:
            servants = json.load(f)
        with open(lib_craft_path, 'r', encoding="utf-8") as f:
            crafts = json.load(f)
        with open(lib_command_path, 'r', encoding="utf-8") as f:
            commands = json.load(f)
    except json.decoder.JSONDecodeError:
        await bot.finish(ev, "本地没有数据~请先获取数据~\n指令：[获取全部内容]")
    except FileNotFoundError:
        await bot.finish(ev, "本地没有数据~请先获取数据~\n指令：[获取全部内容]")

    rule_svt = re.compile(r"(?i)([从c][者z]|svt|servant)")
    rule_cft = re.compile(r"(?i)([礼l][装z]|cft|craft)")
    rule_cmd = re.compile(r"(?i)([纹w][章z]|cmd|command)")
    args = ev.message.extract_plain_text()
    msg = ""

    if re.search(rule_svt, args):
        msg += f"从者：\n远程：{svt[0]['name_cn']}\tid：{svt[0]['id']}\n"
        msg += f"从者：\n本地：{servants[0]['name_cn']}\tid：{servants[0]['id']}\n"

    if re.search(rule_cft, args):
        msg += f"礼装：\n远程：{cft[0]['name']}\tid：{cft[0]['id']}\n"
        msg += f"礼装：\n本地：{crafts[0]['name']}\tid：{crafts[0]['id']}\n"

    if re.search(rule_cmd, args):
        msg += f"纹章：\n远程：{cmd[0]['name']}\tid：{cmd[0]['id']}\n\n"
        msg += f"纹章：\n本地：{commands[0]['name']}\tid：{commands[0]['id']}\n\n"

    await bot.finish(ev, msg.strip())


@sv_lib.on_rex(r"(?i)^(增添|add)?[fb]go[图tl][书si][馆gb](增添|add)?(\s.+)?(\s\d+)?$")
async def add_lib(bot, ev: CQEvent):
    try:
        with open(all_servant_path, 'r', encoding="utf-8") as f:
            svt = json.load(f)
        with open(all_craft_path, 'r', encoding="utf-8") as f:
            cft = json.load(f)
        with open(all_command_path, 'r', encoding="utf-8") as f:
            cmd = json.load(f)
    except json.decoder.JSONDecodeError:
        await bot.finish(ev, "本地没有数据~请先获取数据~\n指令：[获取全部内容]")
    except FileNotFoundError:
        await bot.finish(ev, "本地没有数据~请先获取数据~\n指令：[获取全部内容]")

    crt_file = False
    if os.path.exists(config_path):
        try:
            configs = json.load(open(config_path, encoding="utf-8"))
            for each_group in configs["groups"]:
                if each_group["group"] == ev.group_id:
                    if not each_group["crt_path"] == "False":
                        crt_file = os.path.join(crt_folder_path, each_group["crt_path"])
                        break
        except json.decoder.JSONDecodeError:
            pass

    update_svt = False
    update_cft = False
    update_cmd = False

    rule_svt = re.compile(r"(?i)([从c][者z]|svt|servant)")
    rule_cft = re.compile(r"(?i)([礼l][装z]|cft|craft)")
    rule_cmd = re.compile(r"(?i)([纹w][章z]|cmd|command)")

    msg = ev.message.extract_plain_text().split()
    if not len(msg) == 3:
        await bot.finish("食用指南：增添fgo图书馆 + 类型 + id")

    if re.search(rule_svt, msg[1]):
        update_svt = True

    if re.search(rule_cft, msg[1]):
        update_cft = True

    if re.search(rule_cmd, msg[1]):
        update_cmd = True

    if update_svt:
        sv_lib.logger.info("开始增添从者……")

        try:
            with open(lib_servant_path, 'r', encoding="utf-8") as f:
                servants = json.load(f)
        except json.decoder.JSONDecodeError:
            await bot.finish(ev, "本地没有数据~请先获取数据~\n指令：[更新fgo图书馆]")
        except FileNotFoundError:
            await bot.finish(ev, "本地没有数据~请先获取数据~\n指令：[更新fgo图书馆]")

        # data = await lib_svt(svt[23], crt_file)
        data = None
        if not int(msg[2]) > int(servants[0]["id"]):
            await bot.finish(ev, "此从者本地已有数据~更新从者数据请使用[更新fgo图书馆 + 从者 + id]")

        if not int(msg[2]) == int(servants[0]["id"]) + 1:
            await bot.finish(ev, f"此id前还存在未增添的从者~本地最新id：{servants[0]['id']}")

        for each_svt in svt:
            if msg[2] == each_svt["id"]:
                data = await lib_svt(each_svt, crt_file)
                if "error" in data:
                    sv_lib.logger.error(f"更新从者{each_svt['id']}出错：{data['error']}")
                    await bot.send(ev, f"更新从者{each_svt['id']}出错：{data['error']}")
                break

        if data is None:
            await bot.finish(ev, "不存在此id~")

        servants.insert(0, data)

        with open(lib_servant_path, "w", encoding="utf-8") as f:
            f.write(json.dumps(servants, indent=2, ensure_ascii=False))
        await bot.finish(ev, "已获取从者数据~")

    if update_cft:
        sv_lib.logger.info("开始更新礼装……")

        try:
            with open(lib_craft_path, 'r', encoding="utf-8") as f:
                crafts = json.load(f)
        except json.decoder.JSONDecodeError:
            await bot.finish(ev, "本地没有数据~请先获取数据~\n指令：[更新fgo图书馆]")
        except FileNotFoundError:
            await bot.finish(ev, "本地没有数据~请先获取数据~\n指令：[更新fgo图书馆]")

        # data = await lib_cft(cft[0], crt_file)
        data = None
        if not int(msg[2]) > int(crafts[0]["id"]):
            await bot.finish(ev, "此礼装本地已有数据~更新礼装数据请使用[更新fgo图书馆 + 礼装 + id]")

        if not int(msg[2]) == int(crafts[0]["id"]) + 1:
            await bot.finish(ev, f"此id前还存在未增添的礼装~本地最新id：{crafts[0]['id']}")

        for each_cft in cft:
            if msg[2] == each_cft["id"]:
                data = await lib_cft(each_cft, crt_file)
                if "error" in data:
                    sv_lib.logger.error(f"更新礼装{each_cft['id']}出错：{data['error']}")
                    await bot.send(ev, f"更新礼装{each_cft['id']}出错：{data['error']}")
                break

        if data is None:
            await bot.finish(ev, "不存在此id~")

        crafts.insert(0, data)

        with open(lib_craft_path, "w", encoding="utf-8") as f:
            f.write(json.dumps(crafts, indent=2, ensure_ascii=False))
        await bot.finish(ev, "已获取礼装数据~")

    if update_cmd:
        sv_lib.logger.info("开始更新纹章……")

        try:
            with open(lib_command_path, 'r', encoding="utf-8") as f:
                commands = json.load(f)
        except json.decoder.JSONDecodeError:
            await bot.finish(ev, "本地没有数据~请先获取数据~\n指令：[更新fgo图书馆]")
        except FileNotFoundError:
            await bot.finish(ev, "本地没有数据~请先获取数据~\n指令：[更新fgo图书馆]")

        # data = await lib_cmd(cft[0], crt_file)
        data = None
        if not int(msg[2]) > int(commands[0]["id"]):
            await bot.finish(ev, "此纹章本地已有数据~更新纹章数据请使用[更新fgo图书馆 + 纹章 + id]")

        if not int(msg[2]) == int(commands[0]["id"]) + 1:
            await bot.finish(ev, f"此id前还存在未增添的纹章~本地最新id：{commands[0]['id']}")

        for each_cmd in cmd:
            if msg[2] == each_cmd["id"]:
                data = await lib_cmd(each_cmd, crt_file)
                if "error" in data:
                    sv_lib.logger.error(f"更新纹章{each_cmd['id']}出错：{data['error']}")
                    await bot.send(ev, f"更新纹章{each_cmd['id']}出错：{data['error']}")
                break

        if data is None:
            await bot.finish(ev, "不存在此id~")

        crafts.insert(0, data)

        with open(lib_command_path, "w", encoding="utf-8") as f:
            f.write(json.dumps(commands, indent=2, ensure_ascii=False))
        await bot.finish(ev, "已获取纹章数据~")


@sv_lib.on_rex(r"(?i)^([修x][补b])?[fb]go"
               r"([图tl][书si][馆gb]|([从c][者z]|svt|servant)|([礼l][装z]|cft|craft)|([纹w][章z]|cmd|command))"
               r"([修x][补b])?(\s.+)?$")
async def fix_lib(bot, ev: CQEvent):
    is_3_args = False
    if re.match(r"(?i)^([修x])?([补b])?[fb]go[图tl][书si][馆gb]([修x])?([补b])?(\s.+)?$", ev.raw_message):
        is_3_args = True

    msg = ev.message.extract_plain_text().split()

    if is_3_args:
        if not len(msg) == 3:
            await bot.finish(ev, "食用指南：[修补fgo图书馆 + 类型 + id]")

        if not msg[2].isdigit():
            await bot.finish(ev, "说了要id，宁这是填了个🔨")
    else:
        if not len(msg) == 2:
            await bot.finish(ev, "食用指南：[修补fgo(类型) + id]")

        if not msg[1].isdigit():
            await bot.finish(ev, "说了要id，宁这是填了个🔨")

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
    except json.decoder.JSONDecodeError or FileNotFoundError:
        await bot.finish(ev, "本地没有图书馆数据~请先更新图书馆~\n指令：[更新fgo图书馆]")
    except FileNotFoundError:
        await bot.finish(ev, "本地没有图书馆数据~请先更新图书馆~\n指令：[更新fgo图书馆]")

    crt_file = False
    if os.path.exists(config_path):
        try:
            configs = json.load(open(config_path, encoding="utf-8"))
            for each_group in configs["groups"]:
                if each_group["group"] == ev.group_id:
                    if not each_group["crt_path"] == "False":
                        crt_file = os.path.join(crt_folder_path, each_group["crt_path"])
                        break
        except json.decoder.JSONDecodeError:
            pass

    rule_svt = re.compile(r"(?i)([从c][者z]|svt|servant)")
    is_svt = False
    if re.search(rule_svt, msg[1]):
        is_svt = True
        msg = msg[2:]
    if re.search(rule_svt, msg[0]):
        is_svt = True
        msg = msg[1:]

    fixed = False
    if is_svt:
        max_id = svt[0]["id"]
        if int(msg[0]) > int(max_id):
            await bot.finish(ev, "不存在此id，如果要新增条目请使用[增添fgo图书馆]~")
        for each_svt in svt:
            if each_svt["id"] == msg[0]:
                svt_index = svt.index(each_svt)
                data = await lib_svt(servants[svt_index], crt_file)
                if "error" in data:
                    sv_lib.logger.error(f"更新从者{each_svt['id']}出错：{data['error']}")
                else:
                    fixed = True
                svt[svt_index] = data
                break

        with open(lib_servant_path, "w", encoding="utf-8") as f:
            f.write(json.dumps(svt, indent=2, ensure_ascii=False))
        if fixed:
            await bot.finish(ev, "已修补从者数据~")
        else:
            await bot.finish(ev, "从者数据错误，请再试一次~")

    rule_cft = re.compile(r"(?i)([礼l][装z]|cft|craft)")
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
            await bot.finish(ev, "不存在此id，如果要新增条目请使用[增添fgo图书馆]~")
        for each_cft in cft:
            if each_cft["id"] == msg[0]:
                cft_index = cft.index(each_cft)
                data = await lib_cft(crafts[cft_index], crt_file)
                if "error" in data:
                    sv_lib.logger.error(f"更新礼装{each_cft['id']}出错：{data['error']}")
                else:
                    fixed = True
                cft[cft_index] = data
                break

        with open(lib_craft_path, "w", encoding="utf-8") as f:
            f.write(json.dumps(cft, indent=2, ensure_ascii=False))
        if fixed:
            await bot.finish(ev, "已修补礼装数据~")
        else:
            await bot.finish(ev, "礼装数据错误，请再试一次~")

    rule_cmd = re.compile(r"(?i)([纹w][章z]|cmd|command)")
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
            await bot.finish(ev, "不存在此id，如果要新增条目请使用[增添fgo图书馆]~")
        for each_cmd in cmd:
            if each_cmd["id"] == msg[0]:
                cmd_index = cmd.index(each_cmd)
                data = await lib_cmd(commands[cmd_index], crt_file)
                if "error" in data:
                    sv_lib.logger.error(f"更新纹章{each_cmd['id']}出错：{data['error']}")
                else:
                    fixed = True
                cmd[cmd_index] = data
                break

        with open(lib_craft_path, "w", encoding="utf-8") as f:
            f.write(json.dumps(cmd, indent=2, ensure_ascii=False))
        if fixed:
            await bot.finish(ev, "已修补纹章数据~")
        else:
            await bot.finish(ev, "纹章数据错误，请再试一次~")


@sv_lib.on_rex(r"(?i)^([查c])?([询x])?[fb]go([从c][者z]|svt|servant)([查c][询x])?(\s.+)?$")
async def find_svt(bot, ev: CQEvent):
    msg = ev.message.extract_plain_text().split()
    if len(msg) < 2:
        await bot.finish(ev, "食用指南：[查询fgo从者 + 从者名字]")

    try:
        with open(lib_servant_path, 'r', encoding="utf-8") as f:
            svt = json.load(f)
    except json.decoder.JSONDecodeError or FileNotFoundError:
        await bot.finish(ev, "本地没有图书馆数据~请先更新图书馆~\n指令：[更新fgo图书馆]")
    except FileNotFoundError:
        await bot.finish(ev, "本地没有图书馆数据~请先更新图书馆~\n指令：[更新fgo图书馆]")

    del (msg[0])
    svt_data = []
    is_detail, remove_card, remove_data, remove_info, remove_fool, remove_ultimate, remove_skill, remove_voice \
        = get_keys(msg)

    is_search_id = False
    search_id = None
    for each_arg in msg:
        if re.match(r"id\d+", each_arg):
            search_id = each_arg.replace("id", "")
            is_search_id = True

    banned_keys = [
        "Hit信息括号内为每hit伤害百分比",
        "Quick",
        "Arts",
        "Buster",
        "Extra",
        "宝具",
        "受击",
        "出星率",
        "被即死率",
        "暴击星分配权重"
    ]

    for i in svt:
        if is_search_id and i["id"] == search_id:
            svt_data.append(i)
            break
        trans = {}
        tmp = []
        for j in i:
            if isinstance(i[j], str):
                trans[j] = i[j]

            elif isinstance(i[j], list):
                if j == "宝具信息":
                    for index in range(len(i[j])):
                        for each in i[j][index]:
                            trans[f"{each}{index}"] = i[j][index][each]
                counter = 1
                for k in i[j]:
                    if isinstance(k, list) or isinstance(k, dict):
                        continue
                    trans[f"{j}{counter}"] = k
                    counter += 1

            elif isinstance(i[j], dict):
                if j == "技能":
                    for skills in i[j]:
                        for each in i[j][skills]:
                            skill_info = i[j][skills][each]
                            if each == "图标":
                                continue
                            if isinstance(i[j][skills][each], list):
                                skill_info = i[j][skills][each][0]
                            trans[f"{skills}{each}"] = skill_info
                if j == "svt_detail" or j == "cards_url":
                    continue
                for k in i[j]:
                    if isinstance(i[j][k], list) or isinstance(i[j][k], dict):
                        continue
                    if k in banned_keys:
                        continue
                    trans[f"{k}"] = i[j][k]

        counter = 1
        for arg in msg:
            if re.match(r"^.星$", arg):
                arg = re.sub(r"[五⑤伍]", "5", arg)
                arg = re.sub(r"[四④肆]", "4", arg)
                arg = re.sub(r"[三③叁]", "3", arg)
                arg = re.sub(r"[二②贰]", "2", arg)
                arg = re.sub(r"[一①壹]", "1", arg)
            arg = arg.lower()
            for each in trans:
                if arg in trans[each].lower():
                    if len(msg) == 1:
                        if i not in svt_data:
                            svt_data.append(i)
                    else:
                        if i not in tmp:
                            tmp.append(i)
                            counter += 1
                        else:
                            if counter < len(msg):
                                tmp.append(i)
                                counter += 1
                            else:
                                svt_data.append(i)
                    break

    if len(svt_data) > 5:
        too_much = "描述太模糊，数据太多了qwq，只显示名字，有需要请直接搜索名字~\n"
        counter = 0
        for each in svt_data:
            too_much += f"{counter}：{each['name_link']}\t"
            counter += 1

        await bot.finish(ev, too_much)

    crt_file = False
    if os.path.exists(config_path):
        try:
            configs = json.load(open(config_path, encoding="utf-8"))
            for each_group in configs["groups"]:
                if each_group["group"] == ev.group_id:
                    if not each_group["crt_path"] == "False":
                        crt_file = os.path.join(crt_folder_path, each_group["crt_path"])
                        break
        except json.decoder.JSONDecodeError:
            pass

    if len(svt_data) == 0:
        await bot.send(ev, "无结果……尝试在线搜索")
        for each_msg in msg:
            url = "https://fgo.wiki/w/" + each_msg
            name, stat = await lib_svt_online(url, crt_file)
            if stat == -100:
                await bot.finish(ev, f"出错了！\n{name}")
            elif not stat:
                continue
            elif stat:
                for i in svt:
                    if name in i["name_link"]:
                        if i not in svt_data:
                            svt_data.append(i)
                            break

    if len(svt_data) == 0:
        await bot.finish(ev, "嘤嘤嘤，找不到~请重新选择关键词")
    if len(svt_data) > 5:
        too_much = "描述太模糊，数据太多了qwq，只显示名字，有需要请直接搜索名字~\n"
        counter = 0
        for each_svt_data in svt_data:
            too_much += f"{counter}：{each_svt_data['name_link']}\t"
            counter += 1

        await bot.finish(ev, too_much)

    if is_detail:
        counter = 1
        details = []
        for each in svt_data:
            img_path = os.path.join(svt_path, each["svt_icon"])
            if os.path.exists(img_path):
                msg_error = ""
                if "error" in each:
                    msg_error += f"从者{each['id']}数据存在错误，请使用[修补fgo图书馆 + 从者 + id]修补\n"
                    error_num = len(each["error"])
                    for each_error in each["error"]:
                        if each_error.startswith("aiorequest"):
                            if not error_num == 1:
                                msg_error += f'错误{each["error"].index(each_error) + 1}：'
                            msg_error += "基础数据错误\n"
                        if each_error.startswith("first bs error"):
                            if not error_num == 1:
                                msg_error += f'错误{each["error"].index(each_error) + 1}：'
                            msg_error += "从者数据错误\n"
                        if each_error.startswith("find power bs error"):
                            if not error_num == 1:
                                msg_error += f'错误{each["error"].index(each_error) + 1}：'
                            msg_error += "技能/宝具数据错误\n"
                        if each_error.startswith("get card img error"):
                            if not error_num == 1:
                                msg_error += f'错误{each["error"].index(each_error) + 1}：'
                            msg_error += "卡面数据错误\n"
                        if each_error.startswith("get star error"):
                            if not error_num == 1:
                                msg_error += f'错误{each["error"].index(each_error) + 1}：'
                            msg_error += "星级数据错误\n"
                        if each_error.startswith("svt_info_main"):
                            if not error_num == 1:
                                msg_error += f'错误{each["error"].index(each_error) + 1}：'
                            msg_error += "主描述数据错误\n"
                        if each_error.startswith("svt_info"):
                            if not error_num == 1:
                                msg_error += f'错误{each["error"].index(each_error) + 1}：'
                            msg_error += "描述数据错误\n"
                        if each_error.startswith("svt_detail"):
                            if not error_num == 1:
                                msg_error += f'错误{each["error"].index(each_error) + 1}：'
                            msg_error += "描述详情数据错误\n"

                    send_error = gen_node(msg_error.strip())
                    details.append(send_error)
                    continue

                if len(svt_data) < 2:
                    msg_send = f"你找的可能是：\n{each['name_link']}\n"
                else:
                    if counter == 1:
                        msg_send = f"{counter}：{each['name_link']}\n"
                    else:
                        msg_send = "你找的可能是：\n"
                        msg_send += f"{counter}：{each['name_link']}\n"
                    counter += 1

                # # 因为奇奇怪怪的风控，暂时屏蔽职阶图标
                # class_ = os.path.join(class_path, each["class_icon"])
                # if os.path.exists(class_):
                #     class_img = Image.open(class_)
                #     pic_card = util.pic2b64(class_img)
                #     msg_send += f"{MessageSegment.image(pic_card)}\n"

                if os.path.exists(img_path):
                    img = Image.open(img_path)
                    pic_b64 = util.pic2b64(img)
                    msg_send += f"{MessageSegment.image(pic_b64)}\n"

                msg_send += f"中文名：{each['name_cn']}\n原名：{each['name_jp']}\n稀有度：{each['rare']}\n" \
                            f"获取方法：{each['method']}\n职阶：{each['detail']['职阶']}\n"

                send = gen_node(msg_send.strip())
                details.append(send)

                if not remove_card:
                    msg_card = ""
                    for cards in each["cards_url"]:
                        card = await get_card(each["cards_url"][cards], crt_file)
                        if isinstance(card, int) and card == 100:
                            continue
                        else:
                            bio_card = Image.open(io.BytesIO(card))
                            pic_card = util.pic2b64(bio_card)
                            msg_card += f"{cards}\n"
                            msg_card += f"{MessageSegment.image(pic_card)}\n"

                    send_card = gen_node(msg_card.strip())
                    details.append(send_card)

                if not remove_data:
                    msg_data = ""
                    for data in each["detail"]:
                        if not data == "职阶":
                            if data == "NP获得率":
                                np = str(each['detail'][data]).replace(",", ",\n")
                                msg_data += f"{data}：{np}\n"
                            else:
                                msg_data += f"{data}：{each['detail'][data]}\n"
                    send_data = gen_node(create_img(msg_data.strip()))
                    details.append(send_data)

                if not remove_info:
                    for data in each["svt_detail"]:
                        msg_info = f"{data}：\n{each['svt_detail'][data]['资料']}\n"
                        send_info = gen_node(create_img(msg_info.strip()))
                        details.append(send_info)

                if not remove_fool:
                    if not each['fool']['资料'] == "" and not each['fool']['原文'] == "":
                        msg_fool = f"愚人节：\n{each['fool']['资料']}\n"
                        jp = each['fool']['原文'].replace('。', '。\n')
                        msg_fool += f"原文：\n{jp}\n"
                        send_fool = gen_node(create_img(msg_fool.strip()))
                        details.append(send_fool)

                if not remove_ultimate:
                    msg_ultimate = ""
                    for index in range(len(each["宝具信息"])):
                        if len(each["宝具信息"]) > 1:
                            msg_ultimate += f"宝具{index + 1}：\n"
                        else:
                            msg_ultimate += "宝具：\n"
                        for data in each["宝具信息"][index]:
                            msg_ultimate += f"\t\t\t\t{data}：{each['宝具信息'][index][data]}\n"
                    send_ultimate = gen_node(create_img(msg_ultimate.strip()))
                    details.append(send_ultimate)

                if not remove_skill:
                    for skills in each["技能"]:
                        if each["技能"] == {}:
                            break
                        msg_skill = f"{skills}\n"
                        msg_skill_icon = ""
                        for data in each["技能"][skills]:
                            if data == "图标":
                                icon = await get_card(each["技能"][skills][data], crt_file)
                                if not isinstance(icon, int) and not icon == 100:
                                    bio_card = Image.open(io.BytesIO(icon))
                                    pic_card = util.pic2b64(bio_card)
                                    msg_skill_icon += f"{MessageSegment.image(pic_card)}\n"
                                continue
                            if isinstance(each["技能"][skills][data], list):
                                msg_skill += f'\t\t\t\t{data}：\n'
                                for each_value in each["技能"][skills][data]:
                                    msg_skill += f'\t\t\t\t\t\t\t\t{each_value}\n'
                            else:
                                msg_skill += f'\t\t\t\t{data}：{each["技能"][skills][data]}\n'

                        msg_skill = msg_skill_icon + create_img(msg_skill.strip())
                        send_skill = gen_node(msg_skill)
                        details.append(send_skill)

                if not remove_voice:
                    for each_type in each["语音"]:
                        msg_voice = f"{each_type}：\n"
                        for each_voice in each["语音"][each_type]:
                            msg_voice += f'\t\t\t\t{each_voice}：' \
                                         f'\n\t\t\t\t\t\t\t\t{each["语音"][each_type][each_voice]["文本"]}\n'

                        msg_voice = create_img(msg_voice.strip())
                        send_voice = gen_node(msg_voice)
                        details.append(send_voice)

            else:
                await bot.finish(ev, "没有本地资源~请先获取本地资源~")
        try:
            await bot.send_group_forward_msg(group_id=ev['group_id'], messages=details)
        except ActionFailed as e:
            sv_lib.logger.error(f"转发群消息失败：{e}")
            await bot.finish(ev, "消息被风控，可能是消息太长，请尝试更精确指定从者，或单独指定内容")

    else:
        msg_send = "你找的可能是：\n"
        counter = 1
        details = []
        msg_error = ""
        for each in svt_data:
            if "error" in each:
                msg_error += f"从者{each['id']}数据存在错误，请使用[修补fgo图书馆 + 从者 + id]修补\n"
                error_num = len(each["error"])
                for each_error in each["error"]:
                    if each_error.startswith("aiorequest"):
                        if not error_num == 1:
                            msg_error += f'错误{each["error"].index(each_error) + 1}：'
                        msg_error += "基础数据错误\n"
                    if each_error.startswith("first bs error"):
                        if not error_num == 1:
                            msg_error += f'错误{each["error"].index(each_error) + 1}：'
                        msg_error += "从者数据错误\n"
                    if each_error.startswith("find power bs error"):
                        if not error_num == 1:
                            msg_error += f'错误{each["error"].index(each_error) + 1}：'
                        msg_error += "技能/宝具数据错误\n"
                    if each_error.startswith("get card img error"):
                        if not error_num == 1:
                            msg_error += f'错误{each["error"].index(each_error) + 1}：'
                        msg_error += "卡面数据错误\n"
                    if each_error.startswith("get star error"):
                        if not error_num == 1:
                            msg_error += f'错误{each["error"].index(each_error) + 1}：'
                        msg_error += "星级数据错误\n"
                    if each_error.startswith("svt_info_main"):
                        if not error_num == 1:
                            msg_error += f'错误{each["error"].index(each_error) + 1}：'
                        msg_error += "主描述数据错误\n"
                    if each_error.startswith("svt_info"):
                        if not error_num == 1:
                            msg_error += f'错误{each["error"].index(each_error) + 1}：'
                        msg_error += "描述数据错误\n"
                    if each_error.startswith("svt_detail"):
                        if not error_num == 1:
                            msg_error += f'错误{each["error"].index(each_error) + 1}：'
                        msg_error += "描述详情数据错误\n"
                send_error = gen_node(msg_error.strip())
                details.append(send_error)
                continue

            if counter == 1:
                if len(svt_data) == 1:
                    msg_send = f"你找的可能是：\n{each['name_link']}\n"
                else:
                    msg_send += f"{counter}：{each['name_link']}\n"
            else:
                msg_send = f"{counter}：{each['name_link']}\n"
            counter += 1

            # # 因为奇奇怪怪的风控，暂时屏蔽职阶图标
            # class_ = os.path.join(class_path, each["class_icon"])
            # if os.path.exists(class_):
            #     class_img = Image.open(class_)
            #     pic_card = util.pic2b64(class_img)
            #     msg_send += f"{MessageSegment.image(pic_card)}\n"

            img_path = os.path.join(svt_path, each["svt_icon"])
            if os.path.exists(img_path):
                img = Image.open(img_path)
                pic_b64 = util.pic2b64(img)
                msg_send += f"{MessageSegment.image(pic_b64)}\n"

            msg_send += f"中文名：{each['name_cn']}\n原名：{each['name_jp']}\n稀有度：{each['rare']}\n" \
                        f"获取方法：{each['method']}\n职阶：{each['detail']['职阶']}\n"

            send = gen_node(msg_send.strip())
            details.append(send)
        try:
            if len(svt_data) > 1:
                await bot.send_group_forward_msg(group_id=ev['group_id'], messages=details)
            else:
                if msg_error:
                    await bot.send(ev, msg_error.strip())
                else:
                    await bot.send(ev, msg_send.strip())
        except ActionFailed as e:
            sv_lib.logger.error(f"转发群消息失败：{e}")
            await bot.finish(ev, "消息被风控，可能是消息太长，请尝试更精确指定从者，或单独指定内容")


@sv_lib.on_rex(r"(?i)^([查c])?([询x])?[fb]go([礼l][装z]|cft|craft)([查c][询x])?(\s.+)?$")
async def find_cft(bot, ev: CQEvent):
    msg = ev.message.extract_plain_text().split()
    if len(msg) < 2:
        await bot.finish(ev, "食用指南：[查询fgo礼装 + 礼装名字]")

    try:
        with open(lib_craft_path, 'r', encoding="utf-8") as f:
            cft = json.load(f)
    except json.decoder.JSONDecodeError or FileNotFoundError:
        await bot.finish(ev, "本地没有图书馆数据~请先更新图书馆~\n指令：[更新fgo图书馆]")
    except FileNotFoundError:
        await bot.finish(ev, "本地没有图书馆数据~请先更新图书馆~\n指令：[更新fgo图书馆]")

    del (msg[0])
    cft_data = []
    is_detail = False
    rule = re.compile(r"(?i)(详细|detail)")
    if re.match(rule, msg[-1]):
        is_detail = True
        msg.pop()

    if "羁绊" in msg:
        msg[msg.index("羁绊")] = "牵绊"

    is_search_id = False
    search_id = None
    for each_arg in msg:
        if re.match(r"id\d+", each_arg):
            search_id = each_arg.replace("id", "")
            is_search_id = True

    for i in cft:
        if is_search_id and i["id"] == search_id:
            cft_data.append(i)
            break
        trans = {}
        tmp = []
        for j in i:
            if isinstance(i[j], str):
                trans[j] = i[j]

            elif isinstance(i[j], list):
                counter = 1
                for k in i[j]:
                    if isinstance(k, list) or isinstance(k, dict):
                        continue
                    trans[f"{j}{counter}"] = k
                    counter += 1

            elif isinstance(i[j], dict):
                for k in i[j]:
                    if isinstance(i[j][k], list) or isinstance(i[j][k], dict):
                        continue
                    if not k == "画师" or not k == "持有技能":
                        continue
                    trans[f"{k}"] = i[j][k]

        counter = 1
        for arg in msg:
            if re.match(r"^.星$", arg):
                arg = re.sub(r"[五⑤伍]", "5", arg)
                arg = re.sub(r"[四④肆]", "4", arg)
                arg = re.sub(r"[三③叁]", "3", arg)
                arg = re.sub(r"[二②贰]", "2", arg)
                arg = re.sub(r"[一①壹]", "1", arg)
            arg = arg.lower()
            for each in trans:
                if arg in trans[each].lower():
                    if len(msg) == 1:
                        if i not in cft_data:
                            cft_data.append(i)
                    else:
                        if i not in tmp:
                            tmp.append(i)
                            counter += 1
                        else:
                            if counter < len(msg):
                                tmp.append(i)
                                counter += 1
                            else:
                                cft_data.append(i)
                    break

    if len(cft_data) > 5:
        too_much = "描述太模糊，数据太多了qwq，只显示名字，有需要请直接搜索名字~\n"
        counter = 0
        for each in cft_data:
            too_much += f"{counter}：{each['name_link']}\t"
            counter += 1

        await bot.finish(ev, too_much)

    crt_file = False
    if os.path.exists(config_path):
        try:
            configs = json.load(open(config_path, encoding="utf-8"))
            for each in configs["groups"]:
                if each["group"] == ev.group_id:
                    if not each["crt_path"] == "False":
                        crt_file = os.path.join(crt_folder_path, each["crt_path"])
                        break
        except json.decoder.JSONDecodeError:
            pass

    if len(cft_data) == 0:
        await bot.send(ev, "无结果……尝试在线搜索")
        for each in msg:
            url = "https://fgo.wiki/w/" + each
            name, stat = await lib_cft_online(url, crt_file)
            if stat == -100:
                await bot.finish(ev, f"出错了！\n{name}")
            elif not stat:
                continue
            elif stat:
                for i in cft:
                    if name in i["name_link"]:
                        if i not in cft_data:
                            cft_data.append(i)
                            break

    if len(cft_data) == 0:
        await bot.finish(ev, "嘤嘤嘤，找不到~请重新选择关键词")
    if len(cft_data) > 5:
        too_much = "描述太模糊，数据太多了qwq，只显示名字，有需要请直接搜索名字~\n"
        counter = 0
        for each in cft_data:
            too_much += f"{counter}：{each['name_link']}\t"
            counter += 1

        await bot.finish(ev, too_much)

    if is_detail:
        counter = 1
        details = []
        for each in cft_data:
            img_path = os.path.join(cft_path, each["cft_icon"])
            if os.path.exists(img_path):
                msg_error = ""
                if "error" in each:
                    msg_error += f"礼装{each['id']}数据存在错误，请使用[修补fgo图书馆 + 礼装 + id]修补\n"
                    error_num = len(each["error"])
                    for each_error in each["error"]:
                        if each_error.startswith("aiorequest"):
                            if not error_num == 1:
                                msg_error += f'错误{each["error"].index(each_error) + 1}：'
                            msg_error += "基础数据错误\n"
                        if each_error.startswith("first bs error"):
                            if not error_num == 1:
                                msg_error += f'错误{each["error"].index(each_error) + 1}：'
                            msg_error += "从者数据错误\n"
                        if each_error.startswith("find power bs error"):
                            if not error_num == 1:
                                msg_error += f'错误{each["error"].index(each_error) + 1}：'
                            msg_error += "技能/宝具数据错误\n"
                        if each_error.startswith("get card img error"):
                            if not error_num == 1:
                                msg_error += f'错误{each["error"].index(each_error) + 1}：'
                            msg_error += "卡面数据错误\n"
                        if each_error.startswith("get star error"):
                            if not error_num == 1:
                                msg_error += f'错误{each["error"].index(each_error) + 1}：'
                            msg_error += "星级数据错误\n"

                    send_error = gen_node(msg_error.strip())
                    details.append(send_error)
                    continue

                img = Image.open(img_path)
                pic_b64 = util.pic2b64(img)
                if counter < 2:
                    msg_send = "你找的可能是：\n"
                    msg_send += f"{counter}：{each['name_link']}\n"
                    counter += 1
                else:
                    msg_send = f"{counter}：{each['name']}\n"
                    counter += 1
                if len(cft_data) == 1:
                    msg_send = f"你找的可能是：\n{each['name_link']}\n"
                msg_send += f"{MessageSegment.image(pic_b64)}\n"
                msg_send += f"名字：{each['name']}\n稀有度：{each['rare']}\n礼装类型：{each['type']}\n\n"

                msg_send += "卡面：\n"
                card = await get_card(each["cards_url"], crt_file)
                if isinstance(card, int) and card == 100:
                    sv_lib.logger.error(f"获取礼装{each['id']}卡面出错")
                else:
                    bio_card = Image.open(io.BytesIO(card))
                    pic_card = util.pic2b64(bio_card)
                    msg_send += f"{MessageSegment.image(pic_card)}\n"

                msg_data = ""
                for data in each["detail"]:
                    # 按需选取，若风控很可能是因为大段日文
                    if "解说" in data:
                        continue
                    if data == "持有技能":
                        msg_data += f"{data}："
                        skill = os.path.join(skill_path, each["skill_icon"])
                        skill_img = Image.open(skill)
                        pic_card = util.pic2b64(skill_img)
                        msg_data += f"\n{MessageSegment.image(pic_card)}\n"
                        if isinstance(each['detail'][data], list):
                            for each_skill in each['detail'][data]:
                                each_skill = each_skill.replace("\n+", "+").replace("+", "\n")
                                msg_data += f"{each_skill}\n"
                        else:
                            msg_data += f"{each['detail'][data]}\n"
                    else:
                        msg_data += f"{data}：{each['detail'][data]}\n"

                msg_info = f"解说：\n{each['detail']['解说']}\n\n日文解说：\n{each['detail']['日文解说']}"

                detail1 = gen_node(msg_send.strip())
                detail2 = gen_node(msg_data.strip())
                detail3 = gen_node(create_img(msg_info.strip()))
                details.append(detail1)
                details.append(detail2)
                details.append(detail3)
            else:
                await bot.finish(ev, "没有本地资源~请先获取本地资源~")
        try:
            await bot.send_group_forward_msg(group_id=ev['group_id'], messages=details)
        except ActionFailed as e:
            sv_lib.logger.error(f"转发群消息失败：{e}")
            await bot.finish(ev, "消息被风控，可能是消息太长，请尝试更精确指定礼装")

    else:
        msg_send = "你找的可能是：\n"
        counter = 1
        msg_error = ""
        for each in cft_data:
            if "error" in each:
                msg_error += f"礼装{each['id']}数据存在错误，请使用[修补fgo图书馆 + 礼装 + id]修补\n"
                error_num = len(each["error"])
                for each_error in each["error"]:
                    if each_error.startswith("aiorequest"):
                        if not error_num == 1:
                            msg_error += f'错误{each["error"].index(each_error) + 1}：'
                        msg_error += "基础数据错误\n"
                    if each_error.startswith("first bs error"):
                        if not error_num == 1:
                            msg_error += f'错误{each["error"].index(each_error) + 1}：'
                        msg_error += "从者数据错误\n"
                    if each_error.startswith("find power bs error"):
                        if not error_num == 1:
                            msg_error += f'错误{each["error"].index(each_error) + 1}：'
                        msg_error += "技能/宝具数据错误\n"
                    if each_error.startswith("get card img error"):
                        if not error_num == 1:
                            msg_error += f'错误{each["error"].index(each_error) + 1}：'
                        msg_error += "卡面数据错误\n"
                    if each_error.startswith("get star error"):
                        if not error_num == 1:
                            msg_error += f'错误{each["error"].index(each_error) + 1}：'
                        msg_error += "星级数据错误\n"

                continue

            msg_send += f"{counter}：{each['name_link']}\n"
            counter += 1
            if len(cft_data) == 1:
                msg_send = f"你找的可能是：\n{each['name_link']}\n"
            img_path = os.path.join(cft_path, each["cft_icon"])
            if os.path.exists(img_path):
                img = Image.open(img_path)
                pic_b64 = util.pic2b64(img)
                msg_send += f"{MessageSegment.image(pic_b64)}\n"
                msg_send += f"名字：{each['name']}\n稀有度：{each['rare']}\n礼装类型：{each['type']}\n\n"
            else:
                await bot.finish(ev, "没有本地资源~请先获取本地资源~")
        try:
            if msg_error:
                await bot.send(ev, msg_error.strip())
            else:
                await bot.send(ev, msg_send.strip())
        except ActionFailed as e:
            sv_lib.logger.error(f"转发群消息失败：{e}")
            await bot.finish(ev, "消息被风控，可能是消息太长，请尝试更精确指定礼装")


@sv_lib.on_rex(r"(?i)^([查c])?([询x])?[fb]go([纹w][章z]|cmd|command)([查c][询x])?(\s.+)?$")
async def find_cmd(bot, ev: CQEvent):
    msg = ev.message.extract_plain_text().split()
    if len(msg) < 2:
        await bot.finish(ev, "食用指南：[查询fgo纹章 + 纹章名字]")

    try:
        with open(lib_command_path, 'r', encoding="utf-8") as f:
            cmd = json.load(f)
    except json.decoder.JSONDecodeError or FileNotFoundError:
        await bot.finish(ev, "本地没有图书馆数据~请先更新图书馆~\n指令：[更新fgo图书馆]")
    except FileNotFoundError:
        await bot.finish(ev, "本地没有图书馆数据~请先更新图书馆~\n指令：[更新fgo图书馆]")

    del (msg[0])
    cmd_data = []
    is_detail = False
    rule = re.compile(r"(?i)(详细|detail)")
    if re.match(rule, msg[-1]):
        is_detail = True
        msg.pop()

    is_search_id = False
    search_id = None
    for each_arg in msg:
        if re.match(r"id\d+", each_arg):
            search_id = each_arg.replace("id", "")
            is_search_id = True

    for i in cmd:
        if is_search_id and i["id"] == search_id:
            cmd_data.append(i)
            break
        trans = {}
        tmp = []
        for j in i:
            if isinstance(i[j], str):
                trans[j] = i[j]

            elif isinstance(i[j], list):
                counter = 1
                for k in i[j]:
                    if isinstance(k, list) or isinstance(k, dict):
                        continue
                    trans[f"{j}{counter}"] = k
                    counter += 1

            elif isinstance(i[j], dict):
                for k in i[j]:
                    if isinstance(i[j][k], list) or isinstance(i[j][k], dict):
                        continue
                    if not k == "画师" or not k == "持有技能":
                        continue
                    trans[f"{k}"] = i[j][k]

        counter = 1
        for arg in msg:
            if re.match(r"^.星$", arg):
                arg = re.sub(r"[五⑤伍]", "5", arg)
                arg = re.sub(r"[四④肆]", "4", arg)
                arg = re.sub(r"[三③叁]", "3", arg)
                arg = re.sub(r"[二②贰]", "2", arg)
                arg = re.sub(r"[一①壹]", "1", arg)
            arg = arg.lower()
            for each in trans:
                if arg in trans[each].lower():
                    if len(msg) == 1:
                        if i not in cmd_data:
                            cmd_data.append(i)
                    else:
                        if i not in tmp:
                            tmp.append(i)
                            counter += 1
                        else:
                            if counter < len(msg):
                                tmp.append(i)
                                counter += 1
                            else:
                                cmd_data.append(i)
                    break

    if len(cmd_data) > 5:
        too_much = "描述太模糊，数据太多了qwq，只显示名字，有需要请直接搜索名字~\n"
        counter = 0
        for each in cmd_data:
            too_much += f"{counter}：{each['name_link']}\t"
            counter += 1

        await bot.finish(ev, too_much)

    crt_file = False
    if os.path.exists(config_path):
        try:
            configs = json.load(open(config_path, encoding="utf-8"))
            for each in configs["groups"]:
                if each["group"] == ev.group_id:
                    if not each["crt_path"] == "False":
                        crt_file = os.path.join(crt_folder_path, each["crt_path"])
                        break
        except json.decoder.JSONDecodeError:
            pass

    if len(cmd_data) == 0:
        await bot.send(ev, "无结果……尝试在线搜索")
        for each in msg:
            url = "https://fgo.wiki/w/" + each
            name, stat = await lib_cmd_online(url, crt_file)
            if stat == -100:
                await bot.finish(ev, f"出错了！\n{name}")
            elif not stat:
                continue
            elif stat:
                for i in cmd:
                    if name in i["name_link"]:
                        if i not in cmd_data:
                            cmd_data.append(i)
                            break

    if len(cmd_data) == 0:
        await bot.finish(ev, "嘤嘤嘤，找不到~请重新选择关键词")
    if len(cmd_data) > 5:
        too_much = "描述太模糊，数据太多了qwq，只显示名字，有需要请直接搜索名字~\n"
        counter = 0
        for each in cmd_data:
            too_much += f"{counter}：{each['name_link']}\t"
            counter += 1

        await bot.finish(ev, too_much)

    if is_detail:
        counter = 1
        details = []
        for each in cmd_data:
            img_path = os.path.join(cmd_path, each["cmd_icon"])
            if os.path.exists(img_path):
                msg_error = ""
                if "error" in each:
                    msg_error += f"礼装{each['id']}数据存在错误，请使用[修补fgo图书馆 + 礼装 + id]修补\n"
                    error_num = len(each["error"])
                    for each_error in each["error"]:
                        if each_error.startswith("aiorequest"):
                            if not error_num == 1:
                                msg_error += f'错误{each["error"].index(each_error) + 1}：'
                            msg_error += "基础数据错误\n"
                        if each_error.startswith("first bs error"):
                            if not error_num == 1:
                                msg_error += f'错误{each["error"].index(each_error) + 1}：'
                            msg_error += "从者数据错误\n"
                        if each_error.startswith("find power bs error"):
                            if not error_num == 1:
                                msg_error += f'错误{each["error"].index(each_error) + 1}：'
                            msg_error += "技能/宝具数据错误\n"
                        if each_error.startswith("get card img error"):
                            if not error_num == 1:
                                msg_error += f'错误{each["error"].index(each_error) + 1}：'
                            msg_error += "卡面数据错误\n"
                        if each_error.startswith("get star error"):
                            if not error_num == 1:
                                msg_error += f'错误{each["error"].index(each_error) + 1}：'
                            msg_error += "星级数据错误\n"

                    send_error = gen_node(msg_error.strip())
                    details.append(send_error)
                    continue

                img = Image.open(img_path)
                pic_b64 = util.pic2b64(img)
                if counter < 2:
                    msg_send = "你找的可能是：\n"
                    msg_send += f"{counter}：{each['name_link']}\n"
                    counter += 1
                else:
                    msg_send = f"{counter}：{each['name']}\n"
                    counter += 1
                if len(cmd_data) == 1:
                    msg_send = f"你找的可能是：\n{each['name_link']}\n"
                msg_send += f"{MessageSegment.image(pic_b64)}\n"
                msg_send += f"名字：{each['name']}\n稀有度：{each['rare']}\n纹章类型：{each['type']}\n\n"

                msg_send += "卡面：\n"
                card = await get_card(each["cards_url"], crt_file)
                if isinstance(card, int) and card == 100:
                    sv_lib.logger.error(f"获取纹章{each['id']}卡面出错")
                else:
                    bio_card = Image.open(io.BytesIO(card))
                    pic_card = util.pic2b64(bio_card)
                    msg_send += f"{MessageSegment.image(pic_card)}\n"

                msg_data = ""
                for data in each["detail"]:
                    # 按需选取，若风控很可能是因为大段日文
                    if "解说" in data:
                        continue
                    if data == "持有技能":
                        msg_data += f"{data}："
                        skill = os.path.join(skill_path, each["skill_icon"])
                        skill_img = Image.open(skill)
                        pic_card = util.pic2b64(skill_img)
                        msg_data += f"\n{MessageSegment.image(pic_card)}\n"
                        msg_data += f"{each['detail'][data]}\n"
                    else:
                        msg_data += f"{data}：{each['detail'][data]}\n"

                msg_info = f"解说：\n{each['detail']['解说']}\n\n日文解说：\n{each['detail']['日文解说']}"

                detail1 = gen_node(msg_send.strip())
                detail2 = gen_node(msg_data.strip())
                detail3 = gen_node(create_img(msg_info.strip()))
                details.append(detail1)
                details.append(detail2)
                details.append(detail3)
            else:
                await bot.finish(ev, "没有本地资源~请先获取本地资源~")
        try:
            await bot.send_group_forward_msg(group_id=ev['group_id'], messages=details)
        except ActionFailed as e:
            sv_lib.logger.error(f"转发群消息失败：{e}")
            await bot.finish(ev, "消息被风控，可能是消息太长，请尝试更精确指定纹章")

    else:
        msg_send = "你找的可能是：\n"
        counter = 1
        msg_error = ""
        for each in cmd_data:
            if "error" in each:
                msg_error += f"礼装{each['id']}数据存在错误，请使用[修补fgo图书馆 + 礼装 + id]修补\n"
                error_num = len(each["error"])
                for each_error in each["error"]:
                    if each_error.startswith("aiorequest"):
                        if not error_num == 1:
                            msg_error += f'错误{each["error"].index(each_error) + 1}：'
                        msg_error += "基础数据错误\n"
                    if each_error.startswith("first bs error"):
                        if not error_num == 1:
                            msg_error += f'错误{each["error"].index(each_error) + 1}：'
                        msg_error += "从者数据错误\n"
                    if each_error.startswith("find power bs error"):
                        if not error_num == 1:
                            msg_error += f'错误{each["error"].index(each_error) + 1}：'
                        msg_error += "技能/宝具数据错误\n"
                    if each_error.startswith("get card img error"):
                        if not error_num == 1:
                            msg_error += f'错误{each["error"].index(each_error) + 1}：'
                        msg_error += "卡面数据错误\n"
                    if each_error.startswith("get star error"):
                        if not error_num == 1:
                            msg_error += f'错误{each["error"].index(each_error) + 1}：'
                        msg_error += "星级数据错误\n"

                continue

            msg_send += f"{counter}：{each['name_link']}\n"
            counter += 1
            if len(cmd_data) == 1:
                msg_send = f"你找的可能是：\n{each['name_link']}\n"
            img_path = os.path.join(cmd_path, each["cmd_icon"])
            if os.path.exists(img_path):
                img = Image.open(img_path)
                pic_b64 = util.pic2b64(img)
                msg_send += f"{MessageSegment.image(pic_b64)}\n"
                msg_send += f"名字：{each['name']}\n稀有度：{each['rare']}\n纹章类型：{each['type']}\n\n"
            else:
                await bot.finish(ev, "没有本地资源~请先获取本地资源~")
        try:
            if msg_error:
                await bot.send(ev, msg_error.strip())
            else:
                await bot.send(ev, msg_send.strip())
        except ActionFailed as e:
            sv_lib.logger.error(f"转发群消息失败：{e}")
            await bot.finish(ev, "消息被风控，可能是消息太长，请尝试更精确指定礼装")


def get_keys(msg) -> Tuple:
    is_detail = False
    remove_card = False
    remove_data = False
    remove_info = False
    remove_fool = False
    remove_ultimate = False
    remove_skill = False
    remove_voice = False
    rule = re.compile(r"(?i)(详细|detail)")
    if re.match(rule, msg[-1]):
        is_detail = True
        msg.pop()
    rule1 = re.compile(r"(?i)(卡面|card)")
    if re.match(rule1, msg[-1]):
        is_detail = True
        remove_data = True
        remove_info = True
        remove_fool = True
        remove_ultimate = True
        remove_skill = True
        remove_voice = True
        msg.pop()
    rule2 = re.compile(r"(?i)(数据|data)")
    if re.match(rule2, msg[-1]):
        is_detail = True
        remove_card = True
        remove_info = True
        remove_fool = True
        remove_ultimate = True
        remove_skill = True
        remove_voice = True
        msg.pop()
    rule3 = re.compile(r"(?i)(资料|info)")
    if re.match(rule3, msg[-1]):
        is_detail = True
        remove_data = True
        remove_card = True
        remove_fool = True
        remove_ultimate = True
        remove_skill = True
        remove_voice = True
        msg.pop()
    rule4 = re.compile(r"(?i)(愚人节|fool)")
    if re.match(rule4, msg[-1]):
        is_detail = True
        remove_data = True
        remove_card = True
        remove_info = True
        remove_ultimate = True
        remove_skill = True
        remove_voice = True
        msg.pop()
    rule5 = re.compile(r"(?i)(宝具|bj|ultimate)")
    if re.match(rule5, msg[-1]):
        is_detail = True
        remove_data = True
        remove_card = True
        remove_info = True
        remove_fool = True
        remove_skill = True
        remove_voice = True
        msg.pop()
    rule6 = re.compile(r"(?i)(技能|skill)")
    if re.match(rule6, msg[-1]):
        is_detail = True
        remove_data = True
        remove_card = True
        remove_info = True
        remove_fool = True
        remove_ultimate = True
        remove_voice = True
        msg.pop()
    rule7 = re.compile(r"(?i)(语音|voice)")
    if re.match(rule7, msg[-1]):
        is_detail = True
        remove_data = True
        remove_card = True
        remove_info = True
        remove_fool = True
        remove_ultimate = True
        remove_skill = True
        msg.pop()

    return is_detail, remove_card, remove_data, remove_info, remove_fool, remove_ultimate, remove_skill, remove_voice
