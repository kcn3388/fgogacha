import re

from aiocqhttp import ActionFailed

from ..lib_online.lib_cft import *


async def local_find_cft(bot: HoshinoBot, ev: CQEvent):
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
    rule = re.compile(r"(详细|detail)", re.IGNORECASE)
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

                if counter < 2:
                    msg_send = "你找的可能是：\n"
                    msg_send += f"{counter}：{each['name_link']}\n"
                    counter += 1
                else:
                    msg_send = f"{counter}：{each['name']}\n"
                    counter += 1
                if len(cft_data) == 1:
                    msg_send = f"你找的可能是：\n{each['name_link']}\n"
                msg_send += f"{gen_ms_img(Image.open(img_path))}\n"
                msg_send += f"名字：{each['name']}\n稀有度：{each['rare']}\n礼装类型：{each['type']}\n\n"

                msg_send += "卡面：\n"
                card = await gen_img_from_url(each["cards_url"], crt_file)
                if isinstance(card, Exception):
                    sv_lib.logger.error(f"获取礼装{each['id']}卡面出错")
                else:
                    msg_send += f"{card}\n"

                msg_data = ""
                for data in each["detail"]:
                    # 按需选取，若风控很可能是因为大段日文
                    if "解说" in data:
                        continue
                    if data == "持有技能":
                        msg_data += f"{data}："
                        skill = os.path.join(skill_path, each["skill_icon"])
                        msg_data += f"\n{gen_ms_img(Image.open(skill))}\n"
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
                msg_send += f"{gen_ms_img(Image.open(img_path))}\n"
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
