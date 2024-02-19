from aiocqhttp import ActionFailed

from ..lib_online.lib_svt import *


async def local_find_svt(bot: HoshinoBot, ev: CQEvent):
    msg = ev.message.extract_plain_text().split()
    if len(msg) < 2:
        await bot.send(ev, "食用指南：[查询fgo从者 + 从者名字]")
        return

    try:
        with open(lib_servant_path, 'r', encoding="utf-8") as f:
            svt = json.load(f)
    except (json.decoder.JSONDecodeError, FileNotFoundError):
        await bot.send(ev, "本地没有图书馆数据~请先更新图书馆~\n指令：[更新fgo图书馆]")
        return

    del (msg[0])
    svt_data = []
    is_detail, remove_card, remove_data, \
        remove_info, remove_fool, remove_ultimate, \
        remove_skill, remove_voice, remove_pup = get_keys(msg)

    is_search_id = False
    search_id = None
    for each_arg in msg:
        if re.match(r"id\d+", each_arg):
            search_id = each_arg.replace("id", "")
            is_search_id = True

    banned_keys = [
        "detail",
        "rare",
        "cards_url",
        "fool",
        "svt_detail",
        "method_get",
        "pup",
        "语音"
    ]

    for i in svt:
        if is_search_id:
            try:
                svt_data.append(jsonpath(svt, f"$..[?(@.id=='{search_id}')]")[0])
                break
            except ValueError:
                pass
        trans = {}
        tmp = []
        for j in i:
            if isinstance(i[j], str):
                trans[j] = i[j]

            elif isinstance(i[j], list):
                if j == "宝具信息":
                    for index in range(len(i[j])):
                        for each in i[j][index]:
                            if not each == "中文" and not each == "日文":
                                continue
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
                            try:
                                skill_info = i[j][skills][each]
                            except TypeError:
                                continue
                            if not each == "中文" and not each == "日文":
                                continue
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
            too_much += f"【{counter}】：{each['name_link']}\t"
            counter += 1

        await bot.send(ev, too_much)
        return

    async with ClientSession(headers=headers) as session:
        if len(svt_data) == 0:
            await bot.send(ev, "无结果……尝试在线搜索")
            for each_msg in msg:
                url = "https://fgo.wiki/w/" + each_msg
                name, stat = await lib_svt_online(url, session)
                if stat == -100:
                    await bot.send(ev, f"出错了！\n{name}")
                    return
                elif not stat:
                    continue
                elif stat:
                    try:
                        ready_svt = svt[jsonpath(svt, "$..name_link").index(name)]
                        if ready_svt not in svt_data:
                            svt_data.append(ready_svt)
                    except ValueError:
                        pass

        if len(svt_data) == 0:
            await bot.send(ev, "嘤嘤嘤，找不到~请重新选择关键词")
            return
        if len(svt_data) > 5:
            too_much = "描述太模糊，数据太多了qwq，只显示名字，有需要请直接搜索名字~\n"
            counter = 0
            for each_svt_data in svt_data:
                too_much += f"【{counter}】：{each_svt_data['name_link']}\t"
                counter += 1

            await bot.send(ev, too_much)
            return

        if is_detail:
            counter = 1
            details = []
            for each in svt_data:
                img_path = os.path.join(svt_path, each["svt_icon"])
                if os.path.exists(img_path):
                    if "error" in each:
                        msg_error = f"从者{each['id']}数据存在错误，请使用[修补fgo图书馆 + 从者 + id]修补\n"
                        await bot.send(ev, msg_error)
                        return

                    if len(svt_data) < 2:
                        msg_send = f"你找的可能是：\n{each['name_link']}\n"
                    else:
                        if counter == 1:
                            msg_send = f"【{counter}】：{each['name_link']}\n"
                        else:
                            msg_send = "你找的可能是：\n"
                            msg_send += f"【{counter}】：{each['name_link']}\n"
                        counter += 1

                    # 因为奇奇怪怪的风控，暂时屏蔽职阶图标
                    class_ = os.path.join(class_path, each["class_icon"])
                    if os.path.exists(class_):
                        class_img = Image.open(class_)
                        pic_card = util.pic2b64(class_img)
                        msg_send += f"{MessageSegment.image(pic_card)}\n"

                    if os.path.exists(img_path):
                        msg_send += f"{gen_ms_img(Image.open(img_path))}\n"

                    msg_send += f"中文名：{each['name_cn']}\n原名：{each['name_jp']}\n稀有度：{each['rare']}\n" \
                                f"获取方法：{each['method']}\n职阶：{each['detail']['职阶']}\n"

                    send = gen_node(msg_send.strip())
                    details.append(send)

                    if not remove_card:
                        msg_card = ""
                        for cards in each["cards_url"]:
                            card = await gen_img_from_url(each["cards_url"][cards], session)
                            if isinstance(card, Exception):
                                continue
                            else:
                                msg_card += f"{card}\n"

                        send_card = gen_node(msg_card.strip())
                        details.append(send_card)

                    if not remove_data:
                        msg_data = str(each["detail"]).replace(",", ",\n")
                        send_data = gen_node(create_img(msg_data.strip()))
                        details.append(send_data)

                    if not remove_info:
                        for data in each["svt_detail"]:
                            msg_info = f"{data}：\n{each['svt_detail'][data]['中文']}\n" \
                                       f"\n{each['svt_detail'][data]['日文']}\n"
                            send_info = gen_node(create_img(msg_info.strip()))
                            details.append(send_info)

                    if not remove_fool:
                        if each['fool']['资料']:
                            for each_fool_cn in each['fool']['资料']:
                                msg_fool = f"愚人节资料：\n{each_fool_cn}\n"
                                send_fool = gen_node(create_img(msg_fool.strip()))
                                details.append(send_fool)
                        if each['fool']['原文']:
                            for each_fool_jp in each['fool']['原文']:
                                msg_fool = f"愚人节原文：\n{each_fool_jp}\n"
                                jp = msg_fool.replace('。', '。\n')
                                send_fool = gen_node(create_img(jp.strip()))
                                details.append(send_fool)

                    if not remove_ultimate:
                        msg_ultimate = str(each["宝具信息"]).replace(",", ",\n")
                        send_ultimate = gen_node(create_img(msg_ultimate.strip()))
                        details.append(send_ultimate)

                    if not remove_skill:
                        for skills in each["技能"]:
                            if each["技能"] == {}:
                                break
                            msg_skill = f"{skills}\n"
                            msg_skill_icon = MessageSegment.image(os.path.join(skill_path, f"{skills['类型']}"))
                            msg_skill = msg_skill_icon + create_img(msg_skill.strip())
                            send_skill = gen_node(msg_skill)
                            details.append(send_skill)

                    if not remove_voice:
                        msg_voice = str(each["语音"]).replace(",", ",\n")
                        msg_voice = create_img(msg_voice.strip())
                        send_voice = gen_node(msg_voice)
                        details.append(send_voice)
                    if not remove_pup:
                        if "method_get" in each:
                            how = f"获得方法：\n{each['method_get']}".strip()
                            details.append(gen_node(how))
                        if "pup" in each:
                            details.append(gen_node("国服未来Pick Up情况："))
                            pool_counter = 1
                            for each_pool in each["pup"]:
                                if len(each["pup"]) == 1:
                                    msg_pup = f"{each_pool['title']}\n" \
                                              f"开放时间：{each_pool['time_start']}\n" \
                                              f"结束时间：{each_pool['time_end']}\n" \
                                              f"卡池时长：{each_pool['time_delta']}\n"
                                else:
                                    msg_pup = f"【{pool_counter}】:{each_pool['title']}\n" \
                                              f"开放时间：{each_pool['time_start']}\n" \
                                              f"结束时间：{each_pool['time_end']}\n" \
                                              f"卡池时长：{each_pool['time_delta']}\n"
                                pup_img = await gen_img_from_url(each_pool['img_url'], session)
                                if isinstance(pup_img, Exception):
                                    continue
                                pool_counter += 1
                                msg_pup += pup_img
                                send_pup = gen_node(msg_pup)
                                details.append(send_pup)

                else:
                    await bot.send(ev, "没有本地资源~请先获取本地资源~")
                    return
            try:
                await bot.send_group_forward_msg(group_id=ev['group_id'], messages=details)
            except ActionFailed as e:
                sv_lib.logger.error(f"转发群消息失败：{e}")
                await bot.send(ev, "消息被风控，可能是消息太长，请尝试更精确指定从者，或单独指定内容")
                return

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
                class_ = os.path.join(class_path, each["class_icon"])
                if os.path.exists(class_):
                    class_img = Image.open(class_)
                    pic_card = util.pic2b64(class_img)
                    msg_send += f"{MessageSegment.image(pic_card)}\n"

                img_path = os.path.join(svt_path, each["svt_icon"])
                if os.path.exists(img_path):
                    msg_send += f"{gen_ms_img(Image.open(img_path))}\n"

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
                await bot.send(ev, "消息被风控，可能是消息太长，请尝试更精确指定从者，或单独指定内容")
                return


def get_keys(msg) -> Tuple:
    is_detail = False
    remove_card = False
    remove_data = False
    remove_info = False
    remove_fool = False
    remove_ultimate = False
    remove_skill = False
    remove_voice = False
    remove_pup = False
    rule = re.compile(r"(详细|detail)", re.IGNORECASE)
    if re.match(rule, msg[-1]):
        is_detail = True
        msg.pop()
    rule1 = re.compile(r"(卡面|card)", re.IGNORECASE)
    if re.match(rule1, msg[-1]):
        is_detail = True
        remove_data = True
        remove_info = True
        remove_fool = True
        remove_ultimate = True
        remove_skill = True
        remove_voice = True
        remove_pup = True
        msg.pop()
    rule2 = re.compile(r"(数据|data)", re.IGNORECASE)
    if re.match(rule2, msg[-1]):
        is_detail = True
        remove_card = True
        remove_info = True
        remove_fool = True
        remove_ultimate = True
        remove_skill = True
        remove_voice = True
        remove_pup = True
        msg.pop()
    rule3 = re.compile(r"(资料|info)", re.IGNORECASE)
    if re.match(rule3, msg[-1]):
        is_detail = True
        remove_data = True
        remove_card = True
        remove_fool = True
        remove_ultimate = True
        remove_skill = True
        remove_voice = True
        remove_pup = True
        msg.pop()
    rule4 = re.compile(r"(愚人节|fool)", re.IGNORECASE)
    if re.match(rule4, msg[-1]):
        is_detail = True
        remove_data = True
        remove_card = True
        remove_info = True
        remove_ultimate = True
        remove_skill = True
        remove_voice = True
        remove_pup = True
        msg.pop()
    rule5 = re.compile(r"(宝具|bj|ultimate)", re.IGNORECASE)
    if re.match(rule5, msg[-1]):
        is_detail = True
        remove_data = True
        remove_card = True
        remove_info = True
        remove_fool = True
        remove_skill = True
        remove_voice = True
        remove_pup = True
        msg.pop()
    rule6 = re.compile(r"(技能|skill)", re.IGNORECASE)
    if re.match(rule6, msg[-1]):
        is_detail = True
        remove_data = True
        remove_card = True
        remove_info = True
        remove_fool = True
        remove_ultimate = True
        remove_voice = True
        remove_pup = True
        msg.pop()
    rule7 = re.compile(r"(语音|voice)", re.IGNORECASE)
    if re.match(rule7, msg[-1]):
        is_detail = True
        remove_data = True
        remove_card = True
        remove_info = True
        remove_fool = True
        remove_ultimate = True
        remove_skill = True
        remove_pup = True
        msg.pop()
    rule8 = re.compile(r"(未来|pup)", re.IGNORECASE)
    if re.match(rule8, msg[-1]):
        is_detail = True
        remove_data = True
        remove_card = True
        remove_info = True
        remove_fool = True
        remove_ultimate = True
        remove_voice = True
        remove_skill = True
        msg.pop()

    return (
        is_detail, remove_card, remove_data,
        remove_info, remove_fool, remove_ultimate,
        remove_skill, remove_voice, remove_pup
    )
