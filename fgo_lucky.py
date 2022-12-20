import json.encoder
import os.path
import re
from typing import List

from aiocqhttp import ActionFailed

from hoshino import HoshinoBot
from hoshino.util import DailyNumberLimiter
from .get.get_lucky_bag import get_all_lucky_bag, send_lucky_bag, get_lucky_gacha
from .path_and_json import *

lucky_limit = DailyNumberLimiter(1)
LUCKY_EXCEED_NOTICE = f"您今天已经抽过{lucky_limit.max}次福袋了，欢迎明早5点后再来！"


@lucky_sv.on_rex(r"(?i)^[更g][新x][fb]go[福f][袋d]$")
async def update_lucky_bag(bot: HoshinoBot, ev: CQEvent):
    crt_file = False
    group_config = load_config(ev, True)
    if not group_config["crt_path"] == "False":
        crt_file = os.path.join(crt_folder_path, group_config["crt_path"])

    lucky_bag = await get_all_lucky_bag(crt_file)
    if isinstance(lucky_bag, dict):
        with open(lucky_path, "w", encoding="utf-8") as f:
            f.write(json.dumps(lucky_bag, indent=2, ensure_ascii=False))
        await bot.finish(ev, "已更新福袋信息")
    else:
        await bot.finish(ev, "福袋信息获取错误")


@lucky_sv.on_rex(r"(?i)^[查c][询x][fb]go[福f][袋d](\s("
                 r"jp(\s.+)?|日(服)?(\s.+)?|"
                 r"cn(\s.+)?|国(服)?(\s.+)?|"
                 r"abstract|概况|"
                 r"next|未来"
                 r"))?$")
async def check_lucky_bag(bot: HoshinoBot, ev: CQEvent):
    msg = ev.message.extract_plain_text().split()
    if len(msg) < 2:
        await bot.finish(ev, "食用指南：查询fgo福袋 + 国服/日服/概况/未来/更新")

    crt_file = False
    group_config = load_config(ev, True)
    if not group_config["crt_path"] == "False":
        crt_file = os.path.join(crt_folder_path, group_config["crt_path"])

    if not os.path.exists(lucky_path):
        lucky_sv.logger.info("初始化数据json...")
        open(lucky_path, 'w')
        lucky_bag = {
            "abstract": "",
            "cn": [],
            "jp": []
        }
    else:
        try:
            lucky_bag = json.load(open(lucky_path, encoding="utf-8"))
        except json.decoder.JSONDecodeError:
            lucky_bag = {
                "abstract": "",
                "cn": [],
                "jp": []
            }

    if re.match(r"jp|日(服)?|cn|国(服)?", msg[1]):
        if len(lucky_bag['jp']) == 0:
            await bot.finish(ev, "请先获取福袋：[更新fgo福袋]")
        if len(msg) < 3:
            await bot.finish(
                ev,
                f"食用指南：查询fgo福袋 + 国服/日服 + 编号/全部\n国服已结束的福袋召唤：{len(lucky_bag['cn'])}个；\n"
                f"日服已结束的福袋召唤：{len(lucky_bag['jp'])}个；\n"
                f"国服千里眼福袋：{len(lucky_bag['jp']) - len(lucky_bag['cn'])}个"
            )
        lucky_id: str = msg[2]
        if re.match(r"jp|日(服)?", msg[1]):
            try:
                if lucky_id.isdigit():
                    select_lucky: Dict = lucky_bag['jp'][int(lucky_id) - 1]
                else:
                    if re.match(r"all|全部", lucky_id):
                        select_lucky: List = lucky_bag['jp']
                    else:
                        await bot.send(ev, "编号错误")
                        return
            except IndexError:
                await bot.send(ev, "编号错误")
                return
        else:
            try:
                if lucky_id.isdigit():
                    select_lucky: Dict = lucky_bag['cn'][int(lucky_id) - 1]
                else:
                    if re.match(r"all|全部", lucky_id):
                        select_lucky: List = lucky_bag['cn']
                    else:
                        await bot.send(ev, "编号错误")
                        return
            except IndexError:
                await bot.send(ev, "编号错误")
                return

        lucky_nodes = await send_lucky_bag(select_lucky, crt_file)
        try:
            await bot.send_group_forward_msg(group_id=ev['group_id'], messages=lucky_nodes)
            return
        except ActionFailed:
            await bot.finish(ev, "合并转发失败，请尝试获取单独福袋信息")

    if re.match(r"abstract|概况", msg[1]):
        if not lucky_bag["abstract"]:
            await bot.finish(ev, "请先获取福袋：[更新fgo福袋]")

        abstract_msg = gen_node(lucky_bag["abstract"].strip())
        try:
            await bot.send_group_forward_msg(group_id=ev['group_id'], messages=abstract_msg)
            return
        except ActionFailed:
            await bot.finish(ev, lucky_bag["abstract"].strip())

    if re.match(r"next|未来", msg[1]):
        if len(lucky_bag['jp']) == 0:
            await bot.finish(ev, "请先获取福袋：[更新fgo福袋]")
        select_lucky: List = lucky_bag['jp'][-2:]

        lucky_nodes = await send_lucky_bag(select_lucky, crt_file, is_next=True)
        try:
            await bot.send_group_forward_msg(group_id=ev['group_id'], messages=lucky_nodes)
            return
        except ActionFailed:
            await bot.finish(ev, "合并转发失败，请尝试获取单独福袋信息")


@lucky_sv.on_rex(r"(?i)^[抽c][fb]go[福f][袋d](\s("
                 r"jp((\s\d+)+)?|日(服)?((\s\d+)+)?|"
                 r"cn((\s\d+)+)?|国(服)?((\s\d+)+)?"
                 r"))?$")
async def gacha_lucky_bag(bot: HoshinoBot, ev: CQEvent):
    if not lucky_limit.check(f"{ev.user_id}@{ev.group_id}"):
        await bot.finish(ev, LUCKY_EXCEED_NOTICE, at_sender=True)
    lucky_limit.increase(f"{ev.user_id}@{ev.group_id}", 1)
    msg = ev.message.extract_plain_text().split()
    if len(msg) < 3:
        await bot.finish(ev, "食用指南：抽fgo福袋 + 国服/日服 + 福袋编号 + 子池子编号（默认为1）")

    try:
        lucky_bag = json.load(open(lucky_path, encoding="utf-8"))
    except Exception as e:
        lucky_sv.logger.warning(f"获取福袋数据出错：{e}")
        await bot.send(ev, "获取福袋数据出错，请先获取福袋：[更新fgo福袋]")
        return

    lucky_id = msg[2]
    sub_id = msg[3] if len(msg) > 3 else 1
    server = "国服"

    if re.match(r"jp|日(服)?", msg[1]):
        server = "日服"
        try:
            select_lucky: Dict = lucky_bag['jp'][int(lucky_id) - 1]
        except IndexError:
            await bot.send(ev, "编号错误")
            return
    else:
        try:
            select_lucky: Dict = lucky_bag['cn'][int(lucky_id) - 1]
        except IndexError:
            await bot.send(ev, "编号错误")
            return

    if "detail" not in select_lucky:
        await bot.finish(ev, "该卡池不支持模拟抽卡")

    try:
        select_lucky_pool = select_lucky["detail"][int(sub_id) - 1]
    except IndexError:
        await bot.send(ev, "编号错误")
        return
    gacha_result = await get_lucky_gacha(select_lucky_pool)

    img_path = []
    get_pup5_id = []
    get_pup4_id = []
    get_5_id = []
    get_4_id = []

    for each in select_lucky_pool["servants"]:
        if each["type"] == "svt_5":
            for each_id in each["ids"]:
                get_5_id.append([0, int(each_id)])
        if each["type"] == "svt_4":
            for each_id in each["ids"]:
                get_4_id.append([0, int(each_id)])

    for each in gacha_result:
        if each[0] == "svt":
            svt = int(each[2])
            for each_card in get_pup5_id:
                if each_card[1] == svt:
                    each_card[0] += 1
            for each_card in get_pup4_id:
                if each_card[1] == svt:
                    each_card[0] += 1
            for each_card in get_5_id:
                if each_card[1] == svt:
                    each_card[0] += 1
            for each_card in get_4_id:
                if each_card[1] == svt:
                    each_card[0] += 1
            img_path.append(os.path.join(svt_path, f"Servant{str(svt).zfill(3)}.jpg"))
        if each[0] == "cft":
            cft = int(each[2])
            img_path.append(os.path.join(cft_path, f"礼装{str(cft).zfill(3)}.jpg"))

    group_config = load_config(ev, True)
    style = group_config["style"]

    # 文字图标版，更快
    if not style == "图片":
        cards = []
        for each in img_path:
            cards.append(Image.open(each).resize((66, 72)))
        rows = 3
        cols = 4
        base_img = Image.open(frame_path).resize(((66 * cols) + 40, (72 * rows) + 40))
        r_counter = 0
        c_counter = 0
        for each in cards:
            base_img.paste(each, ((66 * c_counter) + 20, (72 * r_counter) + 20))
            c_counter += 1
            if c_counter >= cols:
                r_counter += 1
                if r_counter >= rows:
                    break
                else:
                    c_counter = 0

    else:
        # 图片版，较慢
        if server == "国服":
            base_img = Image.open(back_cn_path).convert("RGBA")
        else:
            base_img = Image.open(back_path).convert("RGBA")
        masker = Image.open(mask_path).resize((width, height))

        for i, picpath in enumerate(img_path):
            tmp_img = Image.open(picpath).resize((width, height))
            tmp_img = tmp_img.convert('RGBA')
            base_img.paste(tmp_img, boxlist[i], mask=masker)

    msg = f"\n抽取的福袋：{select_lucky['name']}\n" \
          f"抽取的子福袋：{select_lucky_pool['sub_title']}\n" \
          f"抽卡结果：\n" \
          f"{gen_ms_img(base_img)}\n"

    await bot.send(ev, msg.strip(), at_sender=True)
