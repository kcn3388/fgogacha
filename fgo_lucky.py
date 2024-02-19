import json.encoder

from aiocqhttp import ActionFailed

from hoshino import HoshinoBot
from hoshino.util import DailyNumberLimiter
from .get.get_lucky_bag import *
from .path_and_json import *

lucky_limit = DailyNumberLimiter(1)
LUCKY_EXCEED_NOTICE = f"您今天已经抽过{lucky_limit.max}次福袋了，欢迎明早5点后再来！"


@sv_lucky.on_fullmatch(("帮助fgo福袋", "帮助FGO福袋", "帮助bgo福袋", "帮助BGO福袋"))
@sv_lucky.on_rex(re.compile(r"^[fb]go[福f][袋d][帮b][助z]$", re.IGNORECASE))
async def bangzhu(bot: HoshinoBot, ev: CQEvent):
    if not priv.check_priv(ev, priv.ADMIN):
        await bot.send(ev, '此命令仅群管可用~')
        return

    helps = gen_node(sv_lucky_help)
    await bot.send_group_forward_msg(group_id=ev['group_id'], messages=helps)


@sv_lucky.on_rex(re.compile(r"^[更g][新x][fb]go[福f][袋d]$", re.IGNORECASE))
async def update_lucky_bag(bot: HoshinoBot, ev: CQEvent):
    async with ClientSession(headers=headers) as session:
        lucky_bag = await get_all_lucky_bag(session)
        if isinstance(lucky_bag, dict):
            with open(lucky_path, "w", encoding="utf-8") as f:
                f.write(json.dumps(lucky_bag, indent=2, ensure_ascii=False))
            await bot.send(ev, "已更新福袋信息")
            return

        else:
            await bot.send(ev, "福袋信息获取错误")
            return


@sv_lucky.on_rex(re.compile(
    r"^[查c][询x][fb]go[福f][袋d](\s("
    r"jp(\s.+)?|日(服)?(\s.+)?|"
    r"cn(\s.+)?|国(服)?(\s.+)?|"
    r"abstract|概况|"
    r"next|未来"
    r"))?$",
    re.IGNORECASE
))
async def check_lucky_bag(bot: HoshinoBot, ev: CQEvent):
    msg = ev.message.extract_plain_text().split()
    if len(msg) < 2:
        await bot.send(ev, "食用指南：查询fgo福袋 + 国服/日服/概况/未来")
        return

    async with ClientSession(headers=headers) as session:
        if not os.path.exists(lucky_path):
            sv_lucky.logger.info("初始化数据json...")
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
                await bot.send(ev, "请先获取福袋：[更新fgo福袋]")
                return

            if len(msg) < 3:
                await bot.send(
                    ev,
                    f"食用指南：查询fgo福袋 + 国服/日服 + 编号/全部\n国服已结束的福袋召唤：{len(lucky_bag['cn'])}个；\n"
                    f"日服已结束的福袋召唤：{len(lucky_bag['jp'])}个；\n"
                    f"国服千里眼福袋：{len(lucky_bag['jp']) - len(lucky_bag['cn'])}个"
                )
                return

            lucky_id: str = msg[2]
            if re.match(r"jp|日(服)?", msg[1]):
                try:
                    if lucky_id.isdigit():
                        select_lucky: dict = lucky_bag['jp'][int(lucky_id) - 1]
                    else:
                        if re.match(r"all|全部", lucky_id):
                            select_lucky: list = lucky_bag['jp']
                        else:
                            await bot.send(ev, "编号错误")
                            return
                except IndexError:
                    await bot.send(ev, "编号错误")
                    return
            else:
                try:
                    if lucky_id.isdigit():
                        select_lucky: dict = lucky_bag['cn'][int(lucky_id) - 1]
                    else:
                        if re.match(r"all|全部", lucky_id):
                            select_lucky: list = lucky_bag['cn']
                        else:
                            await bot.send(ev, "编号错误")
                            return
                except IndexError:
                    await bot.send(ev, "编号错误")
                    return

            lucky_nodes = await send_lucky_bag(select_lucky, session)
            try:
                await bot.send_group_forward_msg(group_id=ev['group_id'], messages=lucky_nodes)
                return
            except ActionFailed:
                await bot.send(ev, "合并转发失败，请尝试获取单独福袋信息")
                return

        if re.match(r"abstract|概况", msg[1]):
            if not lucky_bag["abstract"]:
                await bot.send(ev, "请先获取福袋：[更新fgo福袋]")
                return

            abstract_msg = gen_node(lucky_bag["abstract"].strip())
            try:
                await bot.send_group_forward_msg(group_id=ev['group_id'], messages=abstract_msg)
                return
            except ActionFailed:
                await bot.send(ev, lucky_bag["abstract"].strip())
                return

        if re.match(r"next|未来", msg[1]):
            if len(lucky_bag['jp']) == 0:
                await bot.send(ev, "请先获取福袋：[更新fgo福袋]")
                return

            select_lucky: list = lucky_bag['jp'][-2:]

            lucky_nodes = await send_lucky_bag(select_lucky, session, is_next=True)
            try:
                await bot.send_group_forward_msg(group_id=ev['group_id'], messages=lucky_nodes)
                return
            except ActionFailed:
                await bot.send(ev, "合并转发失败，请尝试获取单独福袋信息")
                return


@sv_lucky.on_rex(re.compile(
    r"^[抽c][fb]go[福f][袋d](\s("
    r"jp((\s\d+)+)?|日(服)?((\s\d+)+)?|"
    r"cn((\s\d+)+)?|国(服)?((\s\d+)+)?"
    r"))?$", re.IGNORECASE
))
async def gacha_lucky_bag(bot: HoshinoBot, ev: CQEvent):
    if not lucky_limit.check(f"{ev.user_id}@{ev.group_id}"):
        await bot.send(ev, LUCKY_EXCEED_NOTICE, at_sender=True)
        return

    lucky_limit.increase(f"{ev.user_id}@{ev.group_id}", 1)
    msg = ev.message.extract_plain_text().split()
    if len(msg) < 3:
        await bot.send(ev, "食用指南：抽fgo福袋 + 国服/日服 + 福袋编号 + 子池子编号（默认为1）")
        return

    try:
        lucky_bag = json.load(open(lucky_path, encoding="utf-8"))
    except Exception as e:
        sv_lucky.logger.error(f"获取福袋数据出错：{e}")
        await bot.send(ev, "获取福袋数据出错，请先获取福袋：[更新fgo福袋]")
        return

    lucky_id = msg[2]
    sub_id = msg[3] if len(msg) > 3 else 1
    server = "国服"

    if re.match(r"jp|日(服)?", msg[1]):
        server = "日服"
        try:
            select_lucky: dict = lucky_bag['jp'][int(lucky_id) - 1]
        except IndexError:
            await bot.send(ev, "编号错误")
            return
    else:
        try:
            select_lucky: dict = lucky_bag['cn'][int(lucky_id) - 1]
        except IndexError:
            await bot.send(ev, "编号错误")
            return

    if "detail" not in select_lucky:
        await bot.send(ev, "该卡池不支持模拟抽卡")
        return

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

    base_img = await gen_gacha_img(style, img_path, server)

    msg = f"\n抽取的福袋：{select_lucky['name']}\n" \
          f"抽取的子福袋：{select_lucky_pool['sub_title']}\n" \
          f"抽卡结果：\n" \
          f"{gen_ms_img(base_img)}\n"

    await bot.send(ev, msg.strip(), at_sender=True)
