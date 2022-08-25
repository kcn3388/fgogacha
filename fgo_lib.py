import json
import os.path
import re

import aiocqhttp

from hoshino import Service, priv
from hoshino.typing import CQEvent
from .lib_online.lib_online import get_card
from .lib_online.lib_svt import lib_svt, lib_svt_online
from .lib_online.lib_cft import lib_cft, lib_cft_online
from .lib_online.lib_cmd import lib_cmd, lib_cmd_online
from .path_and_json import *

sv_lib_help = '''
# fgo数据库相关
[更新fgo图书馆] 获取从者/礼装/纹章的相关详细数据，包括属性、白值等
- 支持附带类型参数以更新指定内容
- 类型参数：从者/礼装/纹章
- **※需要先执行[获取全部内容]**

[修补fgo图书馆 + 类型 + id] 单独修补某张卡片的详细数据
- 类型为：从者、礼装、纹章
- **※需要先执行[更新fgo图书馆]**

[fgo从者查询 + 关键词（至少一个）] 通过关键词搜索从者
- 若关键词大于两个，只会返回同时符合的
- 可以附带参数``详细``以获取卡面及游戏数据，附带参数``数据``则不显示卡面只显示游戏数据

[fgo礼装查询 + 关键词（至少一个）] 通过关键词搜索礼装
- 若关键词大于两个，只会搜索同时符合的
- 可以附带参数``详细``以获取卡面及游戏数据

[fgo纹章查询 + 关键词（至少一个）] 通过关键词搜索礼装
- 若关键词大于两个，只会搜索同时符合的
- 可以附带参数``详细``以获取卡面及游戏数据
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
    _name = "涩茄子"
    _uin = "2087332430"
    helps = {
        "type": "node",
        "data": {
            "name": _name,
            "uin": _uin,
            "content": sv_lib_help
        }
    }
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

    rule = re.compile(r"(?i)^([获h更g][取q新x])?[fb]go[图tl][书si][馆gb]([获h更g][取q新x])?$")
    rule_svt = re.compile(r"(?i)([从c][者z]|svt|servant)")
    rule_cft = re.compile(r"(?i)([礼l][装z]|cft|craft)")
    rule_cmd = re.compile(r"(?i)([纹w][章z]|cmd|command)")

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

    await bot.send(ev, "开始更新大图书馆~")

    if update_svt:
        sv_lib.logger.info("开始更新从者……")

        servants = []
        errors = []
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

        crafts = []
        errors = []
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

        commands = []
        errors = []
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


@sv_lib.on_rex(r"(?i)^([修x])?([补b])?[fb]go"
               r"([图tl][书si][馆gb]|([从c][者z]|svt|servant)|([礼l][装z]|cft|craft)|([纹w][章z]|cmd|command))"
               r"([修x])?([补b])?(\s.+)?$")
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
        for each_svt in svt:
            if each_svt["id"] == msg[0]:
                data = await lib_svt(each_svt, crt_file)
                if "error" in data:
                    sv_lib.logger.error(f"更新从者{each_svt['id']}出错：{data['error']}")
                else:
                    fixed = True
                svt[svt.index(each_svt)] = data
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
        for each_cft in cft:
            if each_cft["id"] == msg[0]:
                data = await lib_cft(each_cft, crt_file)
                if "error" in data:
                    sv_lib.logger.error(f"更新礼装{each_cft['id']}出错：{data['error']}")
                else:
                    fixed = True
                cft[cft.index(each_cft)] = data
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
        for each_cmd in cmd:
            if each_cmd["id"] == msg[0]:
                data = await lib_cmd(each_cmd, crt_file)
                if "error" in data:
                    sv_lib.logger.error(f"更新纹章{each_cmd['id']}出错：{data['error']}")
                else:
                    fixed = True
                cmd[cmd.index(each_cmd)] = data
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
    is_detail, remove_card, remove_data, remove_info, \
        remove_fool, remove_ultimate, remove_skill, remove_voice = get_keys(msg)

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
                            if each == "图标":
                                continue
                            trans[f"{skills}{each}"] = i[j][skills][each]
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
        _name = "涩茄子"
        _uin = "2087332430"
        counter = 1
        details = []
        for each in svt_data:
            img_path = os.path.join(svt_path, each["svt_icon"])
            if os.path.exists(img_path):
                if len(svt_data) < 2:
                    msg_send = f"你找的可能是：{each['name_link']}\n"
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
                #     with open(class_, "rb") as f:
                #         class_img = f.read()
                #     bio_card = io.BytesIO(class_img)
                #     base64_card = base64.b64encode(bio_card.getvalue()).decode()
                #     pic_card = f'base64://{base64_card}'
                #     msg_send += f"[CQ:image,file={pic_card}]\n"

                if os.path.exists(img_path):
                    with open(img_path, "rb") as f:
                        img = f.read()
                    bio = io.BytesIO(img)
                    base64_str = base64.b64encode(bio.getvalue()).decode()
                    pic_b64 = f'base64://{base64_str}'
                    msg_send += f"[CQ:image,file={pic_b64}]\n"

                msg_send += f"中文名：{each['name_cn']}\n原名：{each['name_jp']}\n稀有度：{each['rare']}\n" \
                            f"获取方法：{each['method']}\n职阶：{each['detail']['职阶']}\n"

                send = {
                    "type": "node",
                    "data": {
                        "name": _name,
                        "uin": _uin,
                        "content": msg_send.strip()
                    }
                }
                details.append(send)

                if not remove_card:
                    msg_card = ""
                    for cards in each["cards_url"]:
                        card = await get_card(each["cards_url"][cards], crt_file)
                        if isinstance(card, int) and card == 100:
                            continue
                        else:
                            bio_card = io.BytesIO(card)
                            base64_card = base64.b64encode(bio_card.getvalue()).decode()
                            pic_card = f'base64://{base64_card}'
                            msg_card += f"{cards}\n"
                            msg_card += f"[CQ:image,file={pic_card}]\n"

                    send_card = {
                        "type": "node",
                        "data": {
                            "name": _name,
                            "uin": _uin,
                            "content": msg_card.strip()
                        }
                    }
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
                    send_data = {
                        "type": "node",
                        "data": {
                            "name": _name,
                            "uin": _uin,
                            "content": create_img(msg_data).strip()
                        }
                    }
                    details.append(send_data)

                if not remove_info:
                    for data in each["svt_detail"]:
                        msg_info = f"{data}：\n{each['svt_detail'][data]['资料']}\n"
                        send_info = {
                            "type": "node",
                            "data": {
                                "name": _name,
                                "uin": _uin,
                                "content": create_img(msg_info).strip()
                            }
                        }
                        details.append(send_info)

                if not remove_fool:
                    if not each['fool']['资料'] == "" and not each['fool']['原文'] == "":
                        msg_fool = f"愚人节：\n{each['fool']['资料']}\n"
                        jp = each['fool']['原文'].replace('。', '。\n')
                        msg_fool += f"原文：\n{jp}\n"
                        send_fool = {
                            "type": "node",
                            "data": {
                                "name": _name,
                                "uin": _uin,
                                "content": create_img(msg_fool).strip()
                            }
                        }
                        details.append(send_fool)

                if not remove_ultimate:
                    msg_ultimate = ""
                    for index in range(len(each["宝具信息"])):
                        if len(each["宝具信息"]) > 1:
                            msg_ultimate += f"宝具{index + 1}：\n"
                        else:
                            msg_ultimate += "宝具：\n"
                        for data in each["宝具信息"][index]:
                            msg_ultimate += f"\t{data}：{each['宝具信息'][index][data]}\n"
                    send_ultimate = {
                        "type": "node",
                        "data": {
                            "name": _name,
                            "uin": _uin,
                            "content": create_img(msg_ultimate).strip()
                        }
                    }
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
                                    bio_card = io.BytesIO(icon)
                                    base64_card = base64.b64encode(bio_card.getvalue()).decode()
                                    pic_card = f'base64://{base64_card}'
                                    msg_skill_icon += f"[CQ:image,file={pic_card}]\n"
                                continue

                            msg_skill += f'\t{data}：{each["技能"][skills][data]}\n'

                        msg_skill = msg_skill_icon + create_img(msg_skill).strip()
                        send_skill = {
                            "type": "node",
                            "data": {
                                "name": _name,
                                "uin": _uin,
                                "content": msg_skill
                            }
                        }
                        details.append(send_skill)

                if not remove_voice:
                    for each_type in each["语音"]:
                        msg_voice = f"{each_type}：\n"
                        for each_voice in each["语音"][each_type]:
                            msg_voice += f'\t{each_voice}：{each["语音"][each_type][each_voice]["文本"]}\n\n'

                        msg_voice = create_img(msg_voice).strip()
                        send_voice = {
                            "type": "node",
                            "data": {
                                "name": _name,
                                "uin": _uin,
                                "content": msg_voice
                            }
                        }
                        details.append(send_voice)

            else:
                await bot.finish(ev, "没有本地资源~请先获取本地资源~")
        try:
            await bot.send_group_forward_msg(group_id=ev['group_id'], messages=details)
        except aiocqhttp.exceptions.ActionFailed as e:
            sv_lib.logger.error(f"转发群消息失败：{e}")
            await bot.finish(ev, "消息被风控，可能是消息太长，请尝试更精确指定从者，或单独指定内容")

    else:
        msg_send = "你找的可能是：\n"
        counter = 1
        _name = "涩茄子"
        _uin = "2087332430"
        details = []
        for each in svt_data:
            if counter == 1:
                if len(svt_data) == 1:
                    msg_send = f"你找的可能是：{each['name_link']}\n"
                else:
                    msg_send += f"{counter}：{each['name_link']}\n"
            else:
                msg_send = f"{counter}：{each['name_link']}\n"
            counter += 1

            # # 因为奇奇怪怪的风控，暂时屏蔽职阶图标
            # class_ = os.path.join(class_path, each["class_icon"])
            # if os.path.exists(class_):
            #     with open(class_, "rb") as f:
            #         class_img = f.read()
            #     bio_card = io.BytesIO(class_img)
            #     base64_card = base64.b64encode(bio_card.getvalue()).decode()
            #     pic_card = f'base64://{base64_card}'
            #     msg_send += f"[CQ:image,file={pic_card}]\n"

            img_path = os.path.join(svt_path, each["svt_icon"])
            if os.path.exists(img_path):
                with open(img_path, "rb") as f:
                    img = f.read()
                bio = io.BytesIO(img)
                base64_str = base64.b64encode(bio.getvalue()).decode()
                pic_b64 = f'base64://{base64_str}'
                msg_send += f"[CQ:image,file={pic_b64}]\n"

            msg_send += f"中文名：{each['name_cn']}\n原名：{each['name_jp']}\n稀有度：{each['rare']}\n" \
                        f"获取方法：{each['method']}\n职阶：{each['detail']['职阶']}\n"

            send = {
                "type": "node",
                "data": {
                    "name": _name,
                    "uin": _uin,
                    "content": msg_send.strip()
                }
            }
            details.append(send)
        try:
            if len(svt_data) > 1:
                await bot.send_group_forward_msg(group_id=ev['group_id'], messages=details)
            else:
                await bot.send(ev, msg_send.strip())
        except aiocqhttp.exceptions.ActionFailed as e:
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

    for i in cft:
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
                with open(img_path, "rb") as f:
                    img = f.read()
                bio = io.BytesIO(img)
                base64_str = base64.b64encode(bio.getvalue()).decode()
                pic_b64 = f'base64://{base64_str}'
                if counter < 2:
                    msg_send = "你找的可能是：\n"
                    msg_send += f"{counter}：{each['name_link']}\n"
                    counter += 1
                else:
                    msg_send = f"{counter}：{each['name']}\n"
                    counter += 1
                msg_send += f"[CQ:image,file={pic_b64}]\n"
                msg_send += f"名字：{each['name']}\n稀有度：{each['rare']}\n礼装类型：{each['type']}\n\n"

                msg_send += "卡面：\n"
                card = await get_card(each["cards_url"], crt_file)
                if isinstance(card, int) and card == 100:
                    sv_lib.logger.error(f"获取礼装{each['id']}卡面出错")
                else:
                    bio_card = io.BytesIO(card)
                    base64_card = base64.b64encode(bio_card.getvalue()).decode()
                    pic_card = f'base64://{base64_card}'
                    msg_send += f"[CQ:image,file={pic_card}]\n"

                msg_data = ""
                for data in each["detail"]:
                    # 按需选取，若风控很可能是因为大段日文
                    if "解说" in data:
                        continue
                    if data == "持有技能":
                        msg_data += f"{data}："
                        skill = os.path.join(skill_path, each["skill_icon"])
                        with open(skill, "rb") as f:
                            skill_img = f.read()
                        bio_card = io.BytesIO(skill_img)
                        base64_card = base64.b64encode(bio_card.getvalue()).decode()
                        pic_card = f'base64://{base64_card}'
                        msg_data += f"[CQ:image,file={pic_card}]\n"
                        msg_data += f"{each['detail'][data]}\n"
                    else:
                        msg_data += f"{data}：{each['detail'][data]}\n"

                msg_info = f"解说：{each['detail']['解说']}\n\n日文解说：{each['detail']['日文解说']}"

                _name = "涩茄子"
                _uin = "2087332430"
                detail1 = {
                    "type": "node",
                    "data": {
                        "name": _name,
                        "uin": _uin,
                        "content": msg_send.strip()
                    }
                }
                detail2 = {
                    "type": "node",
                    "data": {
                        "name": _name,
                        "uin": _uin,
                        "content": msg_data.strip()
                    }
                }
                detail3 = {
                    "type": "node",
                    "data": {
                        "name": _name,
                        "uin": _uin,
                        "content": create_img(msg_info).strip()
                    }
                }
                details.append(detail1)
                details.append(detail2)
                details.append(detail3)
            else:
                await bot.finish(ev, "没有本地资源~请先获取本地资源~")
        try:
            await bot.send_group_forward_msg(group_id=ev['group_id'], messages=details)
        except aiocqhttp.exceptions.ActionFailed as e:
            sv_lib.logger.error(f"转发群消息失败：{e}")
            await bot.finish(ev, "消息被风控，可能是消息太长，请尝试更精确指定礼装")

    else:
        msg_send = "你找的可能是：\n"
        counter = 1
        for each in cft_data:
            msg_send += f"{counter}：{each['name_link']}\n"
            counter += 1
            img_path = os.path.join(cft_path, each["cft_icon"])
            if os.path.exists(img_path):
                with open(img_path, "rb") as f:
                    img = f.read()
                bio = io.BytesIO(img)
                base64_str = base64.b64encode(bio.getvalue()).decode()
                pic_b64 = f'base64://{base64_str}'
                msg_send += f"[CQ:image,file={pic_b64}]\n"
                msg_send += f"名字：{each['name']}\n稀有度：{each['rare']}\n礼装类型：{each['type']}\n\n"
            else:
                await bot.finish(ev, "没有本地资源~请先获取本地资源~")
        try:
            await bot.send(ev, msg_send.strip())
        except aiocqhttp.exceptions.ActionFailed as e:
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

    for i in cmd:
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
                with open(img_path, "rb") as f:
                    img = f.read()
                bio = io.BytesIO(img)
                base64_str = base64.b64encode(bio.getvalue()).decode()
                pic_b64 = f'base64://{base64_str}'
                if counter < 2:
                    msg_send = "你找的可能是：\n"
                    msg_send += f"{counter}：{each['name_link']}\n"
                    counter += 1
                else:
                    msg_send = f"{counter}：{each['name']}\n"
                    counter += 1
                msg_send += f"[CQ:image,file={pic_b64}]\n"
                msg_send += f"名字：{each['name']}\n稀有度：{each['rare']}\n纹章类型：{each['type']}\n\n"

                msg_send += "卡面：\n"
                card = await get_card(each["cards_url"], crt_file)
                if isinstance(card, int) and card == 100:
                    sv_lib.logger.error(f"获取纹章{each['id']}卡面出错")
                else:
                    bio_card = io.BytesIO(card)
                    base64_card = base64.b64encode(bio_card.getvalue()).decode()
                    pic_card = f'base64://{base64_card}'
                    msg_send += f"[CQ:image,file={pic_card}]\n"

                msg_data = ""
                for data in each["detail"]:
                    # 按需选取，若风控很可能是因为大段日文
                    if "解说" in data:
                        continue
                    if data == "持有技能":
                        msg_data += f"{data}："
                        skill = os.path.join(skill_path, each["skill_icon"])
                        with open(skill, "rb") as f:
                            skill_img = f.read()
                        bio_card = io.BytesIO(skill_img)
                        base64_card = base64.b64encode(bio_card.getvalue()).decode()
                        pic_card = f'base64://{base64_card}'
                        msg_data += f"[CQ:image,file={pic_card}]\n"
                        msg_data += f"{each['detail'][data]}\n"
                    else:
                        msg_data += f"{data}：{each['detail'][data]}\n"

                msg_info = f"解说：{each['detail']['解说']}\n\n日文解说：{each['detail']['日文解说']}"

                _name = "涩茄子"
                _uin = "2087332430"
                detail1 = {
                    "type": "node",
                    "data": {
                        "name": _name,
                        "uin": _uin,
                        "content": msg_send.strip()
                    }
                }
                detail2 = {
                    "type": "node",
                    "data": {
                        "name": _name,
                        "uin": _uin,
                        "content": msg_data.strip()
                    }
                }
                detail3 = {
                    "type": "node",
                    "data": {
                        "name": _name,
                        "uin": _uin,
                        "content": create_img(msg_info).strip()
                    }
                }
                details.append(detail1)
                details.append(detail2)
                details.append(detail3)
            else:
                await bot.finish(ev, "没有本地资源~请先获取本地资源~")
        try:
            await bot.send_group_forward_msg(group_id=ev['group_id'], messages=details)
        except aiocqhttp.exceptions.ActionFailed as e:
            sv_lib.logger.error(f"转发群消息失败：{e}")
            await bot.finish(ev, "消息被风控，可能是消息太长，请尝试更精确指定纹章")

    else:
        msg_send = "你找的可能是：\n"
        counter = 1
        for each in cmd_data:
            msg_send += f"{counter}：{each['name_link']}\n"
            counter += 1
            img_path = os.path.join(cmd_path, each["cmd_icon"])
            if os.path.exists(img_path):
                with open(img_path, "rb") as f:
                    img = f.read()
                bio = io.BytesIO(img)
                base64_str = base64.b64encode(bio.getvalue()).decode()
                pic_b64 = f'base64://{base64_str}'
                msg_send += f"[CQ:image,file={pic_b64}]\n"
                msg_send += f"名字：{each['name']}\n稀有度：{each['rare']}\n纹章类型：{each['type']}\n\n"
            else:
                await bot.finish(ev, "没有本地资源~请先获取本地资源~")
        try:
            await bot.send(ev, msg_send.strip())
        except aiocqhttp.exceptions.ActionFailed as e:
            sv_lib.logger.error(f"转发群消息失败：{e}")
            await bot.finish(ev, "消息被风控，可能是消息太长，请尝试更精确指定礼装")


def get_keys(msg):
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

    return is_detail, remove_card, remove_data, remove_info, \
        remove_fool, remove_ultimate, remove_skill, remove_voice
