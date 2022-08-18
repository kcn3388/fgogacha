import base64
import io
import json
import os.path
import re

from hoshino import Service, priv
from hoshino.typing import CQEvent
from .lib_online import get_card, lib_svt_online, lib_cft_online, lib_cmd_online
from .lib_online import lib_svt, lib_cft, lib_cmd
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
            for each in configs["groups"]:
                if each["group"] == ev.group_id:
                    if not each["crt_path"] == "False":
                        crt_file = os.path.join(crt_folder_path, each["crt_path"])
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
        for each in svt:
            data = await lib_svt(each, crt_file)
            if "error" in data:
                sv_lib.logger.error(f"更新从者{each['id']}出错：{data['error']}")
                errors.append(each["id"])
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
        for each in cft:
            data = await lib_cft(each, crt_file)
            if "error" in data:
                sv_lib.logger.error(f"更新礼装{each['id']}出错：{data['error']}")
                errors.append(each["id"])
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
        for each in cmd:
            data = await lib_cmd(each, crt_file)
            if "error" in data:
                sv_lib.logger.error(f"更新礼装{each['id']}出错：{data['error']}")
                errors.append(each["id"])
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


@sv_lib.on_rex(r"(?i)^([修x])?([补b])?[fb]go[图tl][书si][馆gb]([修x])?([补b])?(\s.+)?$")
async def fix_lib(bot, ev: CQEvent):
    msg = ev.message.extract_plain_text().split(" ")
    if not len(msg) == 3:
        await bot.finish(ev, "食用指南：[修补fgo图书馆 + 类型 + id]")

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
            for each in configs["groups"]:
                if each["group"] == ev.group_id:
                    if not each["crt_path"] == "False":
                        crt_file = os.path.join(crt_folder_path, each["crt_path"])
                        break
        except json.decoder.JSONDecodeError:
            pass

    rule_svt = re.compile(r"(?i)([从c][者z]|svt|servant)")

    fixed = False
    if re.match(rule_svt, msg[1]):
        for each in svt:
            if each["id"] == msg[2]:
                data = await lib_svt(each, crt_file)
                if "error" in data:
                    sv_lib.logger.error(f"更新从者{each['id']}出错：{data['error']}")
                else:
                    fixed = True
                svt[svt.index(each)] = data
                break

        with open(lib_servant_path, "w", encoding="utf-8") as f:
            f.write(json.dumps(svt, indent=2, ensure_ascii=False))
        if fixed:
            await bot.finish(ev, "已修补从者数据~")
        else:
            await bot.finish(ev, "从者数据错误，请再试一次~")

    rule_cft = re.compile(r"(?i)([礼l][装z]|cft|craft)")

    fixed = False
    if re.match(rule_cft, msg[1]):
        for each in cft:
            if each["id"] == msg[2]:
                data = await lib_cft(each, crt_file)
                if "error" in data:
                    sv_lib.logger.error(f"更新礼装{each['id']}出错：{data['error']}")
                else:
                    fixed = True
                cft[cft.index(each)] = data
                break

        with open(lib_craft_path, "w", encoding="utf-8") as f:
            f.write(json.dumps(cft, indent=2, ensure_ascii=False))
        if fixed:
            await bot.finish(ev, "已修补礼装数据~")
        else:
            await bot.finish(ev, "礼装数据错误，请再试一次~")

    rule_cmd = re.compile(r"(?i)([纹w][章z]|cmd|command)")

    fixed = False
    if re.match(rule_cmd, msg[1]):
        for each in cmd:
            if each["id"] == msg[2]:
                data = await lib_cmd(each, crt_file)
                if "error" in data:
                    sv_lib.logger.error(f"更新纹章{each['id']}出错：{data['error']}")
                else:
                    fixed = True
                cmd[cmd.index(each)] = data
                break

        with open(lib_craft_path, "w", encoding="utf-8") as f:
            f.write(json.dumps(cmd, indent=2, ensure_ascii=False))
        if fixed:
            await bot.finish(ev, "已修补纹章数据~")
        else:
            await bot.finish(ev, "纹章数据错误，请再试一次~")


@sv_lib.on_rex(r"(?i)^([查c])?([询x])?[fb]go([从c][者z]|svt|servant)([查c][询x])?(\s.+)?$")
async def find_svt(bot, ev: CQEvent):
    msg = ev.message.extract_plain_text().split(" ")
    if len(msg) < 2:
        await bot.finish(ev, "食用指南：[查询fgo从者 + 从者名字]")

    try:
        with open(lib_servant_path, 'r', encoding="utf-8") as f:
            svt = json.load(f)
    except json.decoder.JSONDecodeError or FileNotFoundError:
        await bot.finish(ev, "本地没有图书馆数据~请先更新图书馆~\n指令：[更新fgo图书馆]")
    except FileNotFoundError:
        await bot.finish(ev, "本地没有图书馆数据~请先更新图书馆~\n指令：[更新fgo图书馆]")

    del(msg[0])
    svt_data = []
    tmp = None
    is_detail = False
    remove_card = False
    rule = re.compile(r"(?i)(详细|detail)")
    if re.match(rule, msg[-1]):
        is_detail = True
        msg.pop()
    rule2 = re.compile(r"(?i)(数据|data)")
    if re.match(rule2, msg[-1]):
        is_detail = True
        remove_card = True
        msg.pop()

    for i in svt:
        for j in i:
            if j == "detail":
                for each in i[j]:
                    for arg in msg:
                        if re.match(r"^.星$", arg):
                            arg = re.sub(r"[五⑤伍]", "5", arg)
                            arg = re.sub(r"[四④肆]", "4", arg)
                            arg = re.sub(r"[三③叁]", "3", arg)
                            arg = re.sub(r"[二②贰]", "2", arg)
                            arg = re.sub(r"[一①壹]", "1", arg)
                        arg = arg.lower()
                        if isinstance(i[j][each], str):
                            judge = i[j][each].lower()
                        elif isinstance(i[j][each], list):
                            judge = i[j][each].copy()
                            for index in range(len(i[j][each])):
                                judge[index] = i[j][each][index].lower()
                        else:
                            judge = i[j][each]
                        if arg in judge:
                            if isinstance(judge, list):
                                for names in judge:
                                    if arg in names:
                                        if len(msg) > 1:
                                            if not tmp == i:
                                                tmp = i
                                                break
                                            else:
                                                if i in svt_data:
                                                    break
                                                else:
                                                    svt_data.append(i)
                                                    break
                                        else:
                                            if i in svt_data:
                                                break
                                            else:
                                                svt_data.append(i)
                                                break
                            elif len(msg) > 1:
                                if not tmp == i:
                                    tmp = i
                                    break
                                else:
                                    if i in svt_data:
                                        break
                                    else:
                                        svt_data.append(i)
                                        break
                            else:
                                if i in svt_data:
                                    break
                                else:
                                    svt_data.append(i)
                                    break
                tmp = None
            else:
                for each in msg:
                    arg = each.lower()
                    if isinstance(i[j], str):
                        judge = i[j].lower()
                    elif isinstance(i[j], list):
                        judge = i[j].copy()
                        for index in range(len(i[j])):
                            judge[index] = i[j][index].lower()
                    else:
                        judge = i[j]
                    if arg in judge:
                        if isinstance(judge, list):
                            for names in judge:
                                if arg in names:
                                    if len(msg) > 1:
                                        if not tmp == i:
                                            tmp = i
                                            break
                                        else:
                                            if i in svt_data:
                                                break
                                            else:
                                                svt_data.append(i)
                                                break
                                    else:
                                        if i in svt_data:
                                            break
                                        else:
                                            svt_data.append(i)
                                            break
                        elif len(msg) > 1:
                            if not tmp == i:
                                # noinspection PyUnusedLocal
                                tmp = i
                                break
                            else:
                                if i in svt_data:
                                    break
                                else:
                                    svt_data.append(i)
                                    break
                        else:
                            if i in svt_data:
                                break
                            else:
                                svt_data.append(i)
                                break
                tmp = None

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
            for each in configs["groups"]:
                if each["group"] == ev.group_id:
                    if not each["crt_path"] == "False":
                        crt_file = os.path.join(crt_folder_path, each["crt_path"])
                        break
        except json.decoder.JSONDecodeError:
            pass

    if len(svt_data) == 0:
        await bot.send(ev, "无结果……尝试在线搜索")
        for each in msg:
            url = "https://fgo.wiki/w/" + each
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
        for each in svt_data:
            too_much += f"{counter}：{each['name_link']}\t"
            counter += 1

        await bot.finish(ev, too_much)

    if is_detail:
        counter = 1
        details = []
        for each in svt_data:
            img_path = svt_path + each["svt_icon"]
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
                    msg_send = f"{counter}：{each['name_cn']}\n"
                    counter += 1
                msg_send += f"[CQ:image,file={pic_b64}]\n"
                msg_send += f"中文名：{each['name_cn']}\n原名：{each['name_jp']}\n稀有度：{each['rare']}\n" \
                            f"获取方法：{each['method']}\n\n"

                if not remove_card:
                    msg_send += "卡面：\n"
                    for cards in each["cards_url"]:
                        card = await get_card(cards, crt_file)
                        if isinstance(card, int) and card == 100:
                            continue
                        else:
                            bio_card = io.BytesIO(card)
                            base64_card = base64.b64encode(bio_card.getvalue()).decode()
                            pic_card = f'base64://{base64_card}'
                            msg_send += f"[CQ:image,file={pic_card}]\n"

                msg_data = ""
                for data in each["detail"]:
                    if data == "职阶":
                        msg_data += f"{data}：{each['detail'][data]}"
                        class_ = class_path + each["class_icon"]
                        with open(class_, "rb") as f:
                            class_img = f.read()
                        bio_card = io.BytesIO(class_img)
                        base64_card = base64.b64encode(bio_card.getvalue()).decode()
                        pic_card = f'base64://{base64_card}'
                        msg_data += f"[CQ:image,file={pic_card}]\n"
                    else:
                        msg_data += f"{data}：{each['detail'][data]}\n"

                _name = "涩茄子"
                _uin = "2087332430"
                detail1 = {
                    "type": "node",
                    "data": {
                        "name": _name,
                        "uin": _uin,
                        "content": msg_send
                    }
                }
                detail2 = {
                    "type": "node",
                    "data": {
                        "name": _name,
                        "uin": _uin,
                        "content": msg_data
                    }
                }
                details.append(detail1)
                details.append(detail2)
            else:
                await bot.finish(ev, "没有本地资源~请先获取本地资源~")
        await bot.send_group_forward_msg(group_id=ev['group_id'], messages=details)

    else:
        msg_send = "你找的可能是：\n"
        counter = 1
        for each in svt_data:
            msg_send += f"{counter}：{each['name_link']}\n"
            counter += 1
            img_path = svt_path + each["svt_icon"]
            if os.path.exists(img_path):
                with open(img_path, "rb") as f:
                    img = f.read()
                bio = io.BytesIO(img)
                base64_str = base64.b64encode(bio.getvalue()).decode()
                pic_b64 = f'base64://{base64_str}'
                msg_send += f"[CQ:image,file={pic_b64}]\n"
                msg_send += f"中文名：{each['name_cn']}\n原名：{each['name_jp']}\n稀有度：{each['rare']}\n" \
                            f"获取方法：{each['method']}\n\n"
            else:
                await bot.finish(ev, "没有本地资源~请先获取本地资源~")
        await bot.send(ev, msg_send)


@sv_lib.on_rex(r"(?i)^([查c])?([询x])?[fb]go([礼l][装z]|cft|craft)([查c][询x])?(\s.+)?$")
async def find_cft(bot, ev: CQEvent):
    msg = ev.message.extract_plain_text().split(" ")
    if len(msg) < 2:
        await bot.finish(ev, "食用指南：[查询fgo礼装 + 礼装名字]")

    try:
        with open(lib_craft_path, 'r', encoding="utf-8") as f:
            cft = json.load(f)
    except json.decoder.JSONDecodeError or FileNotFoundError:
        await bot.finish(ev, "本地没有图书馆数据~请先更新图书馆~\n指令：[更新fgo图书馆]")
    except FileNotFoundError:
        await bot.finish(ev, "本地没有图书馆数据~请先更新图书馆~\n指令：[更新fgo图书馆]")

    del(msg[0])
    cft_data = []
    tmp = None
    is_detail = False
    rule = re.compile(r"(?i)(详细|detail)")
    if re.match(rule, msg[-1]):
        is_detail = True
        msg.pop()

    if "羁绊" in msg:
        msg[msg.index("羁绊")] = "牵绊"

    for i in cft:
        for j in i:
            if j == "detail":
                for each in i[j]:
                    for arg in msg:
                        if re.match(r"^.星$", arg):
                            arg = re.sub(r"[五⑤伍]", "5", arg)
                            arg = re.sub(r"[四④肆]", "4", arg)
                            arg = re.sub(r"[三③叁]", "3", arg)
                            arg = re.sub(r"[二②贰]", "2", arg)
                            arg = re.sub(r"[一①壹]", "1", arg)
                        arg = arg.lower()
                        if isinstance(i[j][each], str):
                            judge = i[j][each].lower()
                        elif isinstance(i[j][each], list):
                            judge = i[j][each].copy()
                            for index in range(len(i[j][each])):
                                judge[index] = i[j][each][index].lower()
                        else:
                            judge = i[j][each]
                        if arg in judge:
                            if isinstance(judge, list):
                                for names in judge:
                                    if arg in names:
                                        if len(msg) > 1:
                                            if not tmp == i:
                                                tmp = i
                                                break
                                            else:
                                                if i in cft_data:
                                                    break
                                                else:
                                                    cft_data.append(i)
                                                    break
                                        else:
                                            if i in cft_data:
                                                break
                                            else:
                                                cft_data.append(i)
                                                break
                            elif len(msg) > 1:
                                if not tmp == i:
                                    tmp = i
                                    break
                                else:
                                    if i in cft_data:
                                        break
                                    else:
                                        cft_data.append(i)
                                        break
                            else:
                                if i in cft_data:
                                    break
                                else:
                                    cft_data.append(i)
                                    break
                tmp = None
            else:
                for each in msg:
                    arg = each.lower()
                    if isinstance(i[j], str):
                        judge = i[j].lower()
                    elif isinstance(i[j], list):
                        judge = i[j].copy()
                        for index in range(len(i[j])):
                            judge[index] = i[j][index].lower()
                    else:
                        judge = i[j]
                    if arg in judge:
                        if isinstance(judge, list):
                            for names in judge:
                                if arg in names:
                                    if len(msg) > 1:
                                        if not tmp == i:
                                            tmp = i
                                            break
                                        else:
                                            if i in cft_data:
                                                break
                                            else:
                                                cft_data.append(i)
                                                break
                                    else:
                                        if i in cft_data:
                                            break
                                        else:
                                            cft_data.append(i)
                                            break
                        elif len(msg) > 1:
                            if not tmp == i:
                                # noinspection PyUnusedLocal
                                tmp = i
                                break
                            else:
                                if i in cft_data:
                                    break
                                else:
                                    cft_data.append(i)
                                    break
                        else:
                            if i in cft_data:
                                break
                            else:
                                cft_data.append(i)
                                break
                tmp = None

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
            img_path = cft_path + each["cft_icon"]
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
                    if data == "日文解说":
                        continue
                    if data == "持有技能":
                        msg_data += f"{data}："
                        skill = skill_path + each["skill_icon"]
                        with open(skill, "rb") as f:
                            skill_img = f.read()
                        bio_card = io.BytesIO(skill_img)
                        base64_card = base64.b64encode(bio_card.getvalue()).decode()
                        pic_card = f'base64://{base64_card}'
                        msg_data += f"[CQ:image,file={pic_card}]\n"
                        msg_data += f"{each['detail'][data]}\n"
                    else:
                        msg_data += f"{data}：{each['detail'][data]}\n"

                _name = "涩茄子"
                _uin = "2087332430"
                detail1 = {
                    "type": "node",
                    "data": {
                        "name": _name,
                        "uin": _uin,
                        "content": msg_send
                    }
                }
                detail2 = {
                    "type": "node",
                    "data": {
                        "name": _name,
                        "uin": _uin,
                        "content": msg_data
                    }
                }
                details.append(detail1)
                details.append(detail2)
            else:
                await bot.finish(ev, "没有本地资源~请先获取本地资源~")
        await bot.send_group_forward_msg(group_id=ev['group_id'], messages=details)

    else:
        msg_send = "你找的可能是：\n"
        counter = 1
        for each in cft_data:
            msg_send += f"{counter}：{each['name_link']}\n"
            counter += 1
            img_path = cft_path + each["cft_icon"]
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
        await bot.send(ev, msg_send)


@sv_lib.on_rex(r"(?i)^([查c])?([询x])?[fb]go([纹w][章z]|cmd|command)([查c][询x])?(\s.+)?$")
async def find_cmd(bot, ev: CQEvent):
    msg = ev.message.extract_plain_text().split(" ")
    if len(msg) < 2:
        await bot.finish(ev, "食用指南：[查询fgo纹章 + 纹章名字]")

    try:
        with open(lib_command_path, 'r', encoding="utf-8") as f:
            cmd = json.load(f)
    except json.decoder.JSONDecodeError or FileNotFoundError:
        await bot.finish(ev, "本地没有图书馆数据~请先更新图书馆~\n指令：[更新fgo图书馆]")
    except FileNotFoundError:
        await bot.finish(ev, "本地没有图书馆数据~请先更新图书馆~\n指令：[更新fgo图书馆]")

    del(msg[0])
    cmd_data = []
    tmp = None
    is_detail = False
    rule = re.compile(r"(?i)(详细|detail)")
    if re.match(rule, msg[-1]):
        is_detail = True
        msg.pop()

    for i in cmd:
        for j in i:
            if j == "detail":
                for each in i[j]:
                    for arg in msg:
                        if re.match(r"^.星$", arg):
                            arg = re.sub(r"[五⑤伍]", "5", arg)
                            arg = re.sub(r"[四④肆]", "4", arg)
                            arg = re.sub(r"[三③叁]", "3", arg)
                            arg = re.sub(r"[二②贰]", "2", arg)
                            arg = re.sub(r"[一①壹]", "1", arg)
                        arg = arg.lower()
                        if isinstance(i[j][each], str):
                            judge = i[j][each].lower()
                        elif isinstance(i[j][each], list):
                            judge = i[j][each].copy()
                            for index in range(len(i[j][each])):
                                judge[index] = i[j][each][index].lower()
                        else:
                            judge = i[j][each]
                        if arg in judge:
                            if isinstance(judge, list):
                                for names in judge:
                                    if arg in names:
                                        if len(msg) > 1:
                                            if not tmp == i:
                                                tmp = i
                                                break
                                            else:
                                                if i in cmd_data:
                                                    break
                                                else:
                                                    cmd_data.append(i)
                                                    break
                                        else:
                                            if i in cmd_data:
                                                break
                                            else:
                                                cmd_data.append(i)
                                                break
                            elif len(msg) > 1:
                                if not tmp == i:
                                    tmp = i
                                    break
                                else:
                                    if i in cmd_data:
                                        break
                                    else:
                                        cmd_data.append(i)
                                        break
                            else:
                                if i in cmd_data:
                                    break
                                else:
                                    cmd_data.append(i)
                                    break
                tmp = None
            else:
                for each in msg:
                    arg = each.lower()
                    if isinstance(i[j], str):
                        judge = i[j].lower()
                    elif isinstance(i[j], list):
                        judge = i[j].copy()
                        for index in range(len(i[j])):
                            judge[index] = i[j][index].lower()
                    else:
                        judge = i[j]
                    if arg in judge:
                        if isinstance(judge, list):
                            for names in judge:
                                if arg in names:
                                    if len(msg) > 1:
                                        if not tmp == i:
                                            tmp = i
                                            break
                                        else:
                                            if i in cmd_data:
                                                break
                                            else:
                                                cmd_data.append(i)
                                                break
                                    else:
                                        if i in cmd_data:
                                            break
                                        else:
                                            cmd_data.append(i)
                                            break
                        elif len(msg) > 1:
                            if not tmp == i:
                                # noinspection PyUnusedLocal
                                tmp = i
                                break
                            else:
                                if i in cmd_data:
                                    break
                                else:
                                    cmd_data.append(i)
                                    break
                        else:
                            if i in cmd_data:
                                break
                            else:
                                cmd_data.append(i)
                                break
                tmp = None

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
            img_path = cmd_path + each["cmd_icon"]
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
                    if data == "日文解说":
                        continue
                    if data == "持有技能":
                        msg_data += f"{data}："
                        skill = skill_path + each["skill_icon"]
                        with open(skill, "rb") as f:
                            skill_img = f.read()
                        bio_card = io.BytesIO(skill_img)
                        base64_card = base64.b64encode(bio_card.getvalue()).decode()
                        pic_card = f'base64://{base64_card}'
                        msg_data += f"[CQ:image,file={pic_card}]\n"
                        msg_data += f"{each['detail'][data]}\n"
                    else:
                        msg_data += f"{data}：{each['detail'][data]}\n"

                _name = "涩茄子"
                _uin = "2087332430"
                detail1 = {
                    "type": "node",
                    "data": {
                        "name": _name,
                        "uin": _uin,
                        "content": msg_send
                    }
                }
                detail2 = {
                    "type": "node",
                    "data": {
                        "name": _name,
                        "uin": _uin,
                        "content": msg_data
                    }
                }
                details.append(detail1)
                details.append(detail2)
            else:
                await bot.finish(ev, "没有本地资源~请先获取本地资源~")
        await bot.send_group_forward_msg(group_id=ev['group_id'], messages=details)

    else:
        msg_send = "你找的可能是：\n"
        counter = 1
        for each in cmd_data:
            msg_send += f"{counter}：{each['name_link']}\n"
            counter += 1
            img_path = cmd_path + each["cmd_icon"]
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
        await bot.send(ev, msg_send)
