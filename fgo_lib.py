from .lib_local.cft_local import *
from .lib_local.cmd_local import *
from .lib_local.svt_local import *
from .lib_online.lib_fix import online_fix_lib
from .lib_online.lib_data_fetch import *


@sv_lib.on_fullmatch(("帮助fgo图书馆", "帮助FGO图书馆", "帮助bgo图书馆", "帮助BGO图书馆"))
@sv_lib.on_rex(re.compile(r"^[fb]go[图tl][书si][馆gb][帮b][助z]$", re.IGNORECASE))
async def bangzhu(bot: HoshinoBot, ev: CQEvent):
    helps = gen_node(sv_lib_help)
    await bot.send_group_forward_msg(group_id=ev['group_id'], messages=helps)


@sv_lib.on_rex(re.compile(r"^[获h更g][取q新x][fb]go[图tl][书si][馆gb](\s.+)?$", re.IGNORECASE))
async def update_lib(bot: HoshinoBot, ev: CQEvent):
    try:
        with open(all_servant_path, 'r', encoding="utf-8") as f:
            svt = json.load(f)
        with open(all_craft_path, 'r', encoding="utf-8") as f:
            cft = json.load(f)
        with open(all_command_path, 'r', encoding="utf-8") as f:
            cmd = json.load(f)
        with open(update_data_path, 'r', encoding="utf-8") as f:
            updates = json.load(f)
    except (json.decoder.JSONDecodeError, FileNotFoundError):
        await bot.send(ev, "本地没有数据~请先获取数据~\n指令：[更新fgo图书馆] 或 [获取全部内容]")
        return

    async with ClientSession(headers=headers) as session:
        update_svt = False
        update_cft = False
        update_cmd = False
        latest = False

        rule = re.compile(
            r"^[获h更g][取q新x][fb]go[图tl][书si][馆gb]\s?([最z][新x]|latest|recent)?$",
            re.IGNORECASE
        )
        rule_svt = re.compile(r"([从c][者z]|svt|servant)", re.IGNORECASE)
        rule_cft = re.compile(r"([礼l][装z]|cft|craft)", re.IGNORECASE)
        rule_cmd = re.compile(r"([纹w][章z]|cmd|command)", re.IGNORECASE)
        rule_latest = re.compile(r"([最z][新x]|latest|recent)", re.IGNORECASE)

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

        # await bot.send(ev, "开始更新大图书馆~")

        if update_svt:
            sv_lib.logger.info("开始更新从者……")
            errors = []
            if latest:
                try:
                    with open(lib_servant_path, 'r', encoding="utf-8") as f:
                        servants = json.load(f)
                except (json.decoder.JSONDecodeError, FileNotFoundError):
                    await bot.send(ev, "本地没有数据~请先获取数据~\n指令：[更新fgo图书馆 + 从者]")
                    return
                svt_latest_local = int(servants[0]["id"])
                svt_latest_remote = int(svt[0]["id"])
                svt_ids = jsonpath(servants, "$..id")
                svt_ids.sort(reverse=True)
                if not svt_latest_local == svt_latest_remote or updates["svt"]:
                    update_svt_list = jsonpath(updates, "$.svt")[0]
                    # update_svt_list.sort()
                    for each_update_svt_id in update_svt_list:
                        try:
                            ready_svt = jsonpath(svt, f"$..[?(@.id=='{each_update_svt_id}')]")[0]
                        except IndexError:
                            sv.logger.info(f"no id: {each_update_svt_id}")
                            await bot.send(ev, f"不存在的从者id：{each_update_svt_id}")
                            continue
                        svt_data = await lib_svt(ready_svt, session)
                        if each_update_svt_id in svt_ids:
                            servants[svt_ids.index(each_update_svt_id)] = svt_data
                        else:
                            servants.insert(0, svt_data)
                        if "error" in svt_data:
                            sv_lib.logger.error(f"更新从者{each_update_svt_id}出错：{svt_data['error']}")
                            errors.append(each_update_svt_id)
            else:
                servants = []
                # data = await lib_svt(svt[23], s)
                for each_svt in svt:
                    # if int(each_svt["id"]) > 168:
                    #     continue
                    # print(f"updating {each_svt['id']}")
                    data = await lib_svt(each_svt, session)
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
            updates["svt"] = []

        if update_cft:
            sv_lib.logger.info("开始更新礼装……")
            errors = []
            if latest:
                try:
                    with open(lib_craft_path, 'r', encoding="utf-8") as f:
                        crafts = json.load(f)
                except (json.decoder.JSONDecodeError, FileNotFoundError):
                    await bot.send(ev, "本地没有数据~请先获取数据~\n指令：[更新fgo图书馆]")
                    return
                cft_latest_local = int(crafts[0]["id"])
                cft_latest_remote = int(cft[0]["id"])
                cft_ids = jsonpath(crafts, "$..id")
                cft_ids.sort(reverse=True)
                if not cft_latest_local == cft_latest_remote or updates["cft"]:
                    update_cft_list = jsonpath(updates, "$.cft")[0]
                    # update_cft_list.sort()
                    # update_cft_list = list(map(str, update_cft_list))
                    for each_update_cft_id in update_cft_list:
                        try:
                            ready_cft = jsonpath(cft, f"$..[?(@.id=='{each_update_cft_id}')]")[0]
                        except IndexError:
                            sv.logger.info(f"no id: {each_update_cft_id}")
                            await bot.send(ev, f"不存在的礼装id：{each_update_cft_id}")
                            continue
                        cft_data = await lib_cft(ready_cft)
                        if each_update_cft_id in cft_ids:
                            crafts[cft_ids.index(each_update_cft_id)] = cft_data
                        else:
                            crafts.insert(0, cft_data)
                        if "error" in cft_data:
                            sv_lib.logger.error(f"更新礼装{each_update_cft_id}出错：{cft_data['error']}")
                            errors.append(each_update_cft_id)
            else:
                crafts = []
                # data = await lib_cft(cft[0])
                for each_cft in cft:
                    data = await lib_cft(each_cft)
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
            updates["cft"] = []

        if update_cmd:
            sv_lib.logger.info("开始更新纹章……")
            errors = []
            if latest:
                try:
                    with open(lib_command_path, 'r', encoding="utf-8") as f:
                        commands = json.load(f)
                except (json.decoder.JSONDecodeError, FileNotFoundError):
                    await bot.send(ev, "本地没有数据~请先获取数据~\n指令：[更新fgo图书馆]")
                    return
                cmd_latest_local = int(commands[0]["id"])
                cmd_latest_remote = int(cmd[0]["id"])
                cmd_ids = jsonpath(commands, "$..id")
                cmd_ids.sort(reverse=True)
                if not cmd_latest_local == cmd_latest_remote or updates["cmd"]:
                    update_cmd_list = jsonpath(updates, "$.cmd")[0]
                    # update_cmd_list.sort()
                    for each_update_cmd_id in update_cmd_list:
                        try:
                            ready_cmd = jsonpath(cmd, f"$..[?(@.id=='{each_update_cmd_id}')]")[0]
                        except IndexError:
                            sv.logger.info(f"no id: {each_update_cmd_id}")
                            await bot.send(ev, f"不存在的纹章id：{each_update_cmd_id}")
                            continue
                        cmd_data = await lib_cmd(ready_cmd)
                        if each_update_cmd_id in cmd_ids:
                            commands[cmd_ids.index(each_update_cmd_id)] = cmd_data
                        else:
                            commands.insert(0, cmd_data)
                        if "error" in cmd_data:
                            sv_lib.logger.error(f"更新纹章{each_update_cmd_id}出错：{cmd_data['error']}")
                            errors.append(each_update_cmd_id)
            else:
                commands = []
                # data = await lib_cmd(cft[0], s)
                for each_cmd in cmd:
                    data = await lib_cmd(each_cmd)
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
            updates["cmd"] = []

        with open(update_data_path, "w", encoding="utf-8") as f:
            f.write(json.dumps(updates, indent=2, ensure_ascii=False))


@sv_lib.on_rex(re.compile(r"^[查c][询x][fb]go[图tl][书si][馆gb](\s[\s\S]+)?$", re.IGNORECASE))
async def check_lib(bot: HoshinoBot, ev: CQEvent):
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
    except (json.decoder.JSONDecodeError, FileNotFoundError):
        await bot.send(ev, "本地没有数据~请先获取数据~\n指令：[获取全部内容]")
        return

    rule_svt = re.compile(r"([从c][者z]|svt|servant)", re.IGNORECASE)
    rule_cft = re.compile(r"([礼l][装z]|cft|craft)", re.IGNORECASE)
    rule_cmd = re.compile(r"([纹w][章z]|cmd|command)", re.IGNORECASE)
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

    await bot.send(ev, msg.strip())


@sv_lib.on_rex(re.compile(r"^(增添|add)[fb]go[图tl][书si][馆gb](\s.+)?(\s\d+)?$", re.IGNORECASE))
async def add_lib(bot: HoshinoBot, ev: CQEvent):
    try:
        with open(all_servant_path, 'r', encoding="utf-8") as f:
            svt = json.load(f)
        with open(all_craft_path, 'r', encoding="utf-8") as f:
            cft = json.load(f)
        with open(all_command_path, 'r', encoding="utf-8") as f:
            cmd = json.load(f)
    except (json.decoder.JSONDecodeError, FileNotFoundError):
        await bot.send(ev, "本地没有数据~请先获取数据~\n指令：[获取全部内容]")
        return

    async with ClientSession(headers=headers) as session:
        update_svt = False
        update_cft = False
        update_cmd = False

        rule_svt = re.compile(r"([从c][者z]|svt|servant)", re.IGNORECASE)
        rule_cft = re.compile(r"([礼l][装z]|cft|craft)", re.IGNORECASE)
        rule_cmd = re.compile(r"([纹w][章z]|cmd|command)", re.IGNORECASE)

        msg = ev.message.extract_plain_text().split()
        if not len(msg) == 3:
            await bot.send(ev, "食用指南：增添fgo图书馆 + 类型 + id")
            return

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
            except (json.decoder.JSONDecodeError, FileNotFoundError):
                await bot.send(ev, "本地没有数据~请先获取数据~\n指令：[更新fgo图书馆]")
                return

            # data = await lib_svt(svt[23], s)
            if not int(msg[2]) > int(servants[0]["id"]):
                await bot.send(ev, "此从者本地已有数据~更新从者数据请使用[修补fgo图书馆 + 从者 + id]")
                return

            if not int(msg[2]) == int(servants[0]["id"]) + 1:
                await bot.send(ev, f"此id前还存在未增添的从者~本地最新id：{servants[0]['id']}")
                return

            try:
                insert_svt = jsonpath(svt, f"$..[?(@.id=='{msg[2]}')]")[0]
                data = await lib_svt(insert_svt, session)
                if "error" in data:
                    sv_lib.logger.error(f"更新从者{insert_svt['id']}出错：{data['error']}")
                    await bot.send(ev, f"更新从者{insert_svt['id']}出错：{data['error']}")
            except ValueError:
                await bot.send(ev, "不存在此id~")
                return

            servants.insert(0, data)

            with open(lib_servant_path, "w", encoding="utf-8") as f:
                f.write(json.dumps(servants, indent=2, ensure_ascii=False))
            await bot.send(ev, "已获取从者数据~")
            return

        if update_cft:
            sv_lib.logger.info("开始更新礼装……")

            try:
                with open(lib_craft_path, 'r', encoding="utf-8") as f:
                    crafts = json.load(f)
            except (json.decoder.JSONDecodeError, FileNotFoundError):
                await bot.send(ev, "本地没有数据~请先获取数据~\n指令：[更新fgo图书馆]")
                return

            # data = await lib_cft(cft[0])
            if not int(msg[2]) > int(crafts[0]["id"]):
                await bot.send(ev, "此礼装本地已有数据~更新礼装数据请使用[修补fgo图书馆 + 礼装 + id]")
                return

            if not int(msg[2]) == int(crafts[0]["id"]) + 1:
                await bot.send(ev, f"此id前还存在未增添的礼装~本地最新id：{crafts[0]['id']}")
                return

            try:
                insert_cft = jsonpath(cft, f"$..[?(@.id=='{msg[2]}')]")[0]
                data = await lib_cft(insert_cft)
                if "error" in data:
                    sv_lib.logger.error(f"更新礼装{insert_cft['id']}出错：{data['error']}")
                    await bot.send(ev, f"更新礼装{insert_cft['id']}出错：{data['error']}")
            except ValueError:
                await bot.send(ev, "不存在此id~")
                return

            crafts.insert(0, data)

            with open(lib_craft_path, "w", encoding="utf-8") as f:
                f.write(json.dumps(crafts, indent=2, ensure_ascii=False))
            await bot.send(ev, "已获取礼装数据~")
            return

        if update_cmd:
            sv_lib.logger.info("开始更新纹章……")

            try:
                with open(lib_command_path, 'r', encoding="utf-8") as f:
                    commands = json.load(f)
            except (json.decoder.JSONDecodeError, FileNotFoundError):
                await bot.send(ev, "本地没有数据~请先获取数据~\n指令：[更新fgo图书馆]")
                return

            # data = await lib_cmd(cft[0])
            if not int(msg[2]) > int(commands[0]["id"]):
                await bot.send(ev, "此纹章本地已有数据~更新纹章数据请使用[修补fgo图书馆 + 纹章 + id]")
                return

            if not int(msg[2]) == int(commands[0]["id"]) + 1:
                await bot.send(ev, f"此id前还存在未增添的纹章~本地最新id：{commands[0]['id']}")
                return

            try:
                insert_cmd = jsonpath(cmd, f"$..[?(@.id=='{msg[2]}')]")[0]
                data = await lib_cmd(insert_cmd)
                if "error" in data:
                    sv_lib.logger.error(f"更新纹章{insert_cmd['id']}出错：{data['error']}")
                    await bot.send(ev, f"更新纹章{insert_cmd['id']}出错：{data['error']}")
            except ValueError:
                await bot.send(ev, "不存在此id~")
                return

            commands.insert(0, data)

            with open(lib_command_path, "w", encoding="utf-8") as f:
                f.write(json.dumps(commands, indent=2, ensure_ascii=False))
            await bot.send(ev, "已获取纹章数据~")
            return


@sv_lib.on_rex(re.compile(
    r"^[修x][补b][fb]go"
    r"([图tl][书si][馆gb]|([从c][者z]|svt|servant)|([礼l][装z]|cft|craft)|([纹w][章z]|cmd|command))"
    r"(\s.+)?$", re.IGNORECASE
))
async def fix_lib(bot: HoshinoBot, ev: CQEvent):
    await online_fix_lib(bot, ev)


@sv_lib.on_rex(re.compile(r"^[查c][询x][fb]go([从c][者z]|svt|servant)(\s.+)?$", re.IGNORECASE))
async def find_svt(bot: HoshinoBot, ev: CQEvent):
    await local_find_svt(bot, ev)


@sv_lib.on_rex(re.compile(r"^[查c][询x][fb]go([礼l][装z]|cft|craft)(\s.+)?$", re.IGNORECASE))
async def find_cft(bot: HoshinoBot, ev: CQEvent):
    await local_find_cft(bot, ev)


@sv_lib.on_rex(re.compile(r"^[查c][询x][fb]go([纹w][章z]|cmd|command)(\s.+)?$", re.IGNORECASE))
async def find_cmd(bot: HoshinoBot, ev: CQEvent):
    await local_find_cmd(bot, ev)


@sv_lib.on_fullmatch("强制抓取全部数据")
async def force_fetch_data(bot: HoshinoBot, ev: CQEvent):
    await fetch_mooncell(bot, ev, 1, force=True)
    await fetch_mooncell(bot, ev, 2, force=True)
    await fetch_mooncell(bot, ev, 3, force=True)


@sv_lib.on_fullmatch("抓取全部从者数据")
async def fetch_data_svt(bot: HoshinoBot, ev: CQEvent):
    await fetch_mooncell(bot, ev, 1)


@sv_lib.on_prefix("抓取指定从者数据")
async def fetch_data_svt_single(bot: HoshinoBot, ev: CQEvent):
    try:
        sid = int(ev.message.extract_plain_text())
    except Exception as e:
        sv_lib.logger.warning(f"wrong sid when get servant data: {e}")
        await bot.send(ev, "请输入正确的从者ID")
        return
    await fetch_mooncell(bot, ev, 1, sid)


@sv_lib.on_fullmatch("抓取全部礼装数据")
async def fetch_data_cft(bot: HoshinoBot, ev: CQEvent):
    await fetch_mooncell(bot, ev, 2)


@sv_lib.on_prefix("抓取指定礼装数据")
async def fetch_data_cft_single(bot: HoshinoBot, ev: CQEvent):
    try:
        sid = int(ev.message.extract_plain_text())
    except Exception as e:
        sv_lib.logger.warning(f"wrong sid when get craft data: {e}")
        await bot.send(ev, "请输入正确的礼装ID")
        return
    await fetch_mooncell(bot, ev, 2, sid)


@sv_lib.on_fullmatch("抓取全部纹章数据")
async def fetch_data_cmd(bot: HoshinoBot, ev: CQEvent):
    await fetch_mooncell(bot, ev, 3)


@sv_lib.on_prefix("抓取指定纹章数据")
async def fetch_data_cmd_single(bot: HoshinoBot, ev: CQEvent):
    try:
        sid = int(ev.message.extract_plain_text())
    except Exception as e:
        sv_lib.logger.warning(f"wrong sid when get command data: {e}")
        await bot.send(ev, "请输入正确的纹章ID")
        return
    await fetch_mooncell(bot, ev, 3, sid)
