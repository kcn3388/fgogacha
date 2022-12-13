import json.encoder
import os.path

from hoshino import priv, Service
from hoshino.typing import CQEvent
from hoshino.util import DailyNumberLimiter, FreqLimiter
from .get.gacha import gacha
from .get.getGachaPools import getgachapools
from .path_and_json import *

jewel_limit = DailyNumberLimiter(3000)
tenjo_limit = DailyNumberLimiter(10)
lmt = FreqLimiter(15)  # 冷却时间15秒

JEWEL_EXCEED_NOTICE = f"您今天已经抽过{jewel_limit.max}石头了，欢迎明早5点后再来！"
TENJO_EXCEED_NOTICE = f"您今天已经抽过{tenjo_limit.max}张百连券了，欢迎明早5点后再来！"

height = 194
width = 178
dis = 23
floor = 48
st1w = 92
st1h = 200
st2 = 192

boxlist = []

box1 = (st1w, st1h)
for box_i in range(6):
    boxlist.append(box1)
    lst = list(box1)
    lst[0] += width + dis
    box1 = tuple(lst)

box2 = (st2, st1h + height + floor)
for box_i in range(5):
    boxlist.append(box2)
    lst = list(box2)
    lst[0] += width + dis
    box2 = tuple(lst)

sv_help = '''
# 抽卡模拟相关
[fgo十连] fgo抽卡
[fgo百连] 100抽
[获取fgo卡池] 从mooncell获取卡池数据
[查询fgo卡池] 查询本地缓存的卡池以及本群卡池
[切换fgo卡池 + 卡池编号] 切换需要的卡池
[切换fgo日替卡池 + 卡池编号 + 日替卡池编号] 切换需要的日替卡池
'''.strip()

sv = Service(
    name='fgo抽卡',
    help_=sv_help,
    bundle="娱乐",
    enable_on_default=True,
    visible=True,
    use_priv=priv.NORMAL,  # 使用权限
    manage_priv=priv.ADMIN,  # 管理权限
)


@sv.on_fullmatch(("帮助fgo抽卡", "帮助FGO抽卡", "帮助bgo抽卡", "帮助BGO抽卡"))
@sv.on_rex(r"(?i)^[fb]go[抽c][卡k][帮b][助z]$")
async def bangzhu(bot, ev):
    helps = gen_node(sv_help)
    await bot.send_group_forward_msg(group_id=ev['group_id'], messages=helps)


@sv.on_rex(r"(?i)^([获h更g][取q新x])?[fb]go[卡k][池c]([获h更g][取q新x])?$")
async def get_fgo_pool(bot, ev: CQEvent):
    await bot.send(ev, "开始更新....")
    crt_file = False
    group_config = load_config(ev, True)
    if not group_config["crt_path"] == "False":
        crt_file = os.path.join(crt_folder_path, group_config["crt_path"])
    download_stat = await getgachapools(True, crt_file)
    if not isinstance(download_stat, int):
        await bot.finish(ev, f'更新失败，原因：\n{download_stat}')
    if not download_stat:
        await bot.send(ev, "获取卡池完成")
    elif download_stat:
        await bot.send(ev, "本地卡池和线上卡池是一样的啦~\n晚点再来看看吧~")


@sv.on_rex(r"(?i)^([查c])?([询x])?[fb]go[卡k][池c]([查c][询x])?$")
async def check_pool(bot, ev: CQEvent):
    if os.path.exists(pools_path):
        try:
            pools = json.load(open(pools_path, encoding="utf-8"))
        except json.decoder.JSONDecodeError:
            pools = []
    else:
        pools = []
    if not pools:
        sv.logger.info("No pools exist")
        await bot.finish(ev, "没有卡池你查个🔨！请先获取卡池！\n指令：[获取fgo卡池]")

    msg = "当前卡池："
    for each in pools:
        s = f"\n{each['id']}：{each['banner']}({each['server']})"
        msg += s
        if "sub_pool" in each:
            for sub_pools in each["sub_pool"]:
                s = f"\n\t{sub_pools['id']}：{sub_pools['sub_title']}"
                msg += s

    if os.path.exists(banner_path):
        banners = json.load(open(banner_path, encoding="utf-8"))
        banner = [each_banner for each_banner in banners if each_banner["group"] == ev.group_id]
        if not banner:
            sv.logger.info(f"no banner in group {ev.group_id}")
        else:
            b_name = banner[0]["banner"]["banner"]
            title = banner[0]["banner"]["title"]
            if "sub_title" in banner[0]["banner"]:
                b_name = banner[0]["banner"]["sub_title"]
            group = f"\n\n本群{ev.group_id}卡池：\n{b_name}({banner[0]['banner']['server']})\n从属活动：\n{title}"
            msg += group

    if len(msg) > 200:
        _banner = gen_node(msg)
        await bot.send_group_forward_msg(group_id=ev['group_id'], messages=_banner)
    else:
        await bot.send(ev, msg)


# noinspection PyTypeChecker
@sv.on_rex(r"(?i)^[切qs][换hw][fb]go[卡k][池c](\s\d+)?$|^[fb]go[卡k][池c][切qs][换hw](\s\d+)?$")
async def switch_pool(bot, ev: CQEvent):
    p_ids = ev.message.extract_plain_text().split()
    if len(p_ids) > 1:
        p_id = p_ids[1]
    else:
        p_id = p_ids[0]
    if not p_id.isdigit():
        await bot.finish(ev, "食用指南：[切换fgo卡池 + 编号]", at_sender=True)

    if os.path.exists(pools_path):
        try:
            pools = json.load(open(pools_path, encoding="utf-8"))
        except json.decoder.JSONDecodeError:
            pools = []
    else:
        pools = []
    if not pools:
        sv.logger.info("No pools exist")
        await bot.finish(ev, "没有卡池你切换个🐔8️⃣！请先获取卡池！\n指令：[获取fgo卡池]")

    if not os.path.exists(banner_path):
        sv.logger.info("初始化数据json...")
        open(banner_path, 'w')
        banners = []
    else:
        banners = json.load(open(banner_path, encoding="utf-8"))

    banner = {
        "group": ev.group_id,
        "banner": []
    }

    dp_pool = [each for each in pools if each["id"] == int(p_id)]
    if not dp_pool:
        await bot.finish(ev, "卡池编号不存在")
    banner["banner"] = dp_pool[0]
    if banner["banner"]["type"] == "daily pickup":
        await bot.finish(ev, "日替卡池请使用指令：[切换fgo日替卡池 + 卡池编号 + 子卡池编号]")

    gb_index = [i for i in range(len(banners)) if banners[i]["group"] == ev.group_id]
    if not gb_index:
        banners.append(banner)
    else:
        banners[gb_index[0]] = banner
    with open(banner_path, "w", encoding="utf-8") as f:
        f.write(json.dumps(banners, indent=2, ensure_ascii=False))

    title = banner["banner"]["title"]
    b_name = banner["banner"]["banner"]
    await bot.send(ev, f"切换fgo卡池成功！当前卡池：\n{b_name}({banner['banner']['server']})\n从属活动：\n{title}")


@sv.on_rex(r"(?i)^([切qs][换hw])?[fb]go[日rd][替tp][卡k][池c]([切qs][换hw])?(\s\d+\s\d+)?$")
async def switch_pool(bot, ev: CQEvent):
    ids = ev.message.extract_plain_text()
    if not ids:
        await bot.finish(ev, "食用指南：[切换fgo日替卡池 + 编号 + 子编号]", at_sender=True)

    ids = ids.split()
    p_id = ""
    s_id = ""
    if len(ids) > 2:
        p_id = ids[1]
        s_id = ids[2]
    else:
        await bot.finish(ev, "食用指南：[切换fgo日替卡池 + 卡池编号 + 子卡池编号]", at_sender=True)

    if os.path.exists(pools_path):
        try:
            pools = json.load(open(pools_path, encoding="utf-8"))
        except json.decoder.JSONDecodeError:
            pools = []
    else:
        pools = []
    if not pools:
        sv.logger.info("No pools exist")
        await bot.finish(ev, "没有卡池你切换个🐔8️⃣！请先获取卡池！\n指令：[获取fgo卡池]")

    if not os.path.exists(banner_path):
        sv.logger.info("初始化数据json...")
        open(banner_path, 'w')
        banners = []
    else:
        banners = json.load(open(banner_path, encoding="utf-8"))

    banner = {
        "group": ev.group_id,
        "banner": []
    }

    gp = [each for each in pools if each["id"] == int(p_id) and each["type"] == "daily pickup"]
    if not gp:
        await bot.finish(ev, "卡池参数错误")
    gps = [sub_pool for sub_pool in gp[0]["sub_pool"] if sub_pool["id"] == int(s_id)]
    if not gps:
        await bot.finish(ev, "卡池参数错误")

    sp = {
        "id": gp[0]["id"],
        "title": gp[0]["title"],
        "href": gp[0]["href"],
        "banner": gp[0]["banner"],
        "sub_title": gps[0]["sub_title"],
        "server": gp[0]["server"],
        "type": gp[0]["type"],
        "s_id": gps[0]["id"]
    }
    banner["banner"] = sp

    if not banner["banner"]:
        await bot.finish(ev, "卡池编号不存在")

    gb_index = [i for i in range(len(banners)) if banners[i]["group"] == ev.group_id]
    if not gb_index:
        banners.append(banner)
    else:
        banners[gb_index[0]] = banner
    with open(banner_path, "w", encoding="utf-8") as f:
        f.write(json.dumps(banners, indent=2, ensure_ascii=False))

    title = banner["banner"]["title"]
    b_name = banner["banner"]["banner"]
    if "sub_title" in banner["banner"]:
        b_name = banner["banner"]["sub_title"]
    await bot.send(ev, f"切换fgo卡池成功！当前卡池：\n{b_name}({banner['banner']['server']})\n从属活动：\n{title}")


# @sv.on_prefix("fgo十连", only_to_me=True)
@sv.on_rex(r'(?i)^[fb]go(十|10|s)[连l]$')
async def gacha_10(bot, ev: CQEvent):
    gid = ev.group_id
    # barrier
    if not jewel_limit.check(ev.user_id):
        await bot.finish(ev, JEWEL_EXCEED_NOTICE, at_sender=True)
    jewel_limit.increase(ev.user_id, 30)

    if not lmt.check(ev.user_id):
        await bot.send(ev, f'冷却中,剩余时间{round(lmt.left_time(ev.user_id))}秒', at_sender=True)
        return
    # lmt.start_cd(ev.user_id)

    gacha_result, server, pool_list = await gacha(gid)
    if gacha_result == 12:
        await bot.finish(ev, "卡池都没选宁搁这抽空气呢！请先选择卡池！")
    if gacha_result == 13:
        await bot.finish(ev, "卡池数据错误！请更新卡池或重新选择卡池！")

    if not gacha_result:
        return

    img_path = []
    get_pup5_id = []
    get_pup4_id = []
    get_5_id = []
    get_4_id = []

    for each in pool_list["servants"]:
        if each["type"] == "svt_pup_5":
            for each_id in each["ids"]:
                get_pup5_id.append([0, int(each_id)])
        if each["type"] == "svt_pup_4":
            for each_id in each["ids"]:
                get_pup4_id.append([0, int(each_id)])
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

    pic_b64 = util.pic2b64(base_img)
    msg = "\n您本次的抽卡结果：\n" + f"{MessageSegment.image(pic_b64)}\n"

    full_pup5 = False
    get_pup5 = 0
    for each in get_pup5_id:
        get_pup5 += each[0]
        if each[0] == 5:
            full_pup5 = True

    full_pup4 = False
    get_pup4 = 0
    for each in get_pup4_id:
        get_pup4 += each[0]
        if each[0] == 5:
            full_pup4 = True

    full_get_5 = False
    get_5 = 0
    for each in get_5_id:
        get_5 += each[0]
        if each[0] == 5:
            full_get_5 = True

    full_get_4 = False
    get_4 = 0
    for each in get_4_id:
        get_4 += each[0]
        if each[0] == 5:
            full_get_4 = True

    stars = ""
    if get_pup5:
        stars += f"UP5☆×{get_pup5};\t"

    if get_5:
        stars += f"5☆×{get_5};\t"

    if get_pup4:
        stars += f"UP4☆×{get_pup4};\t"

    if get_4:
        stars += f"4☆×{get_4};\t"

    stars += "\n"
    msg += stars
    is_seal = False

    if get_5 and not get_pup5:
        if get_5 == 1 and get_pup5_id:
            msg += "“常驻等歪.jpg”不亏！\n"
        if get_5 == 1 and not get_pup5_id:
            msg += "有五星就行\n"
        if full_get_5:
            msg += "不是，常驻五星你也能一发抽满的？"
            is_seal = True
        if full_get_4:
            msg += "什么狗东西才能一发抽满常驻四星？"
            is_seal = True
        if get_5 > 1:
            if get_pup5_id:
                msg += "欧了，但是没有完全欧\n"
            else:
                msg += "这么多五星，还说你不是海豹？\n"
            is_seal = True
        if get_pup4:
            msg += "出了up四星，还歪了常驻，血赚\n"
        if get_pup4 + get_4 > 1:
            msg += "多黄不亏\n"

    if not get_pup5 and not get_5:
        if get_pup4:
            msg += "起码出了up四星，不亏\n"
        if not get_pup4 and get_4 and get_pup4_id:
            msg += "不是吧，四星也能歪？\n"
        if full_pup4:
            msg += "十连满宝四星，这是人干事？\n"
            is_seal = True
        if full_get_4:
            msg += "什么狗东西才能一发抽满常驻四星？"
            is_seal = True
        if get_pup4 > 1:
            msg += "up四星多黄，血赚\n"
            is_seal = True
        if get_pup4 + get_4 > 1:
            msg += "多黄不亏\n"
        if not get_pup4 and not get_4:
            msg += "零鸡蛋！酋长，咱们回非洲吧！\n"
        if not get_pup4_id and get_4:
            if get_4 == 1:
                msg += "出金就行.jpg\n"
            else:
                msg += "什么四星大放送啊\n"
                is_seal = True

    if get_pup5:
        if full_pup5:
            msg += "十连满宝，小心出门被车创死"
            is_seal = True
        if get_pup5 > 1:
            if not get_5 == 0:
                msg += "又多宝又歪常驻，什么臭海豹\n"
            if get_5 == 0:
                msg += "多黄臭海豹，建议击杀\n"
            if not get_pup4 and get_pup4_id:
                msg += "众所周知，四星好出\n"
            if full_pup4:
                msg += "up四星满宝？这是可能存在的吗？"
            is_seal = True
        if get_pup5 == 1:
            msg += "出了就好，补不补宝这是一个问题~\n"
            if get_pup4:
                if full_pup4:
                    msg += "一发毕业四星还出了五星，你是狗吧？\n"
                    is_seal = True
                else:
                    msg += "十连卡池毕业~这你还不补宝？\n"
                    is_seal = True
    if is_seal:
        img = Image.open(seal_path)
        pic_b64 = util.pic2b64(img)
        msg += f'\n{MessageSegment.image(pic_b64)}'

    await bot.send(ev, msg.strip(), at_sender=True)


@sv.on_rex(r'(?i)^[fb]go(百|100|b)[连l]$')
async def gacha_100(bot, ev: CQEvent):
    gid = ev.group_id
    # barrier
    if not tenjo_limit.check(ev.user_id):
        await bot.finish(ev, TENJO_EXCEED_NOTICE, at_sender=True)
    tenjo_limit.increase(ev.user_id, 1)

    if not lmt.check(ev.user_id):
        await bot.send(ev, f'冷却中,剩余时间{round(lmt.left_time(ev.user_id))}秒', at_sender=True)
        return
    lmt.start_cd(ev.user_id)

    g100 = []
    g_counter = 0
    pool_list = None
    # 如需图片版请取消注释
    # server = ""
    while g_counter < 11:
        g_counter += 1
        result, server, pool_list = await gacha(gid)
        g100.append(result)

    # 如需图片版请取消注释
    # group_config = load_config(ev, True)
    # style = group_config["style"]

    msg = ""

    if g100[0] == 12:
        await bot.finish(ev, "卡池都没选宁搁这抽空气呢！请先选择卡池！")
    if g100[0] == 13:
        await bot.finish(ev, "卡池数据错误！请更新卡池或重新选择卡池！")

    img_path = []
    get_pup5_id = []
    get_pup4_id = []
    get_5_id = []
    get_4_id = []

    for each in pool_list["servants"]:
        if each["type"] == "svt_pup_5":
            for each_id in each["ids"]:
                get_pup5_id.append([0, int(each_id)])
        if each["type"] == "svt_pup_4":
            for each_id in each["ids"]:
                get_pup4_id.append([0, int(each_id)])
        if each["type"] == "svt_5":
            for each_id in each["ids"]:
                get_5_id.append([0, int(each_id)])
        if each["type"] == "svt_4":
            for each_id in each["ids"]:
                get_4_id.append([0, int(each_id)])

    # 如需图片版请取消注释
    # b64s = []
    for gacha_result in g100:
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
                if int(each[1] == "3"):
                    continue
                # 如需图片版请取消注释，并将之后一行增加一个缩进
                # if not style == "图片":
                img_path.append(os.path.join(svt_path, f"Servant{str(svt).zfill(3)}.jpg"))

    cards = []
    for each in img_path:
        cards.append(Image.open(each).resize((66, 72)))

    if len(cards) % 4 == 0:
        rows = int(len(cards) / 4)
    else:
        rows = int(len(cards) / 4) + 1
    if len(cards) < 4:
        cols = len(cards)
    else:
        cols = 4

    # 如需图片版请取消注释，并注释之后一行
    # if not style == "图片":
    if cards:
        target = Image.open(frame_path).resize(((66 * cols) + 40, (72 * rows) + 40))
        r_counter = 0
        c_counter = 0
        for each in cards:
            target.paste(each, ((66 * c_counter) + 20, (72 * r_counter) + 20))
            c_counter += 1
            if c_counter >= cols:
                r_counter += 1
                if r_counter >= rows:
                    break
                else:
                    c_counter = 0

        pic_b64 = util.pic2b64(target)
        msg += f'\n您本次的抽卡结果：\n\n{MessageSegment.image(pic_b64)}\n\n'

    else:
        # 如需图片版请取消之后一行的注释，并注释下一行
        msg += f'\n您本次的抽卡结果：\n\n'
        # for each_result in g100:
        #     img_path = []
        #     for each_gacha in each_result:
        #         if each_gacha[0] == "svt":
        #             svt = int(each_gacha[2])
        #             img_path.append(os.path.join(svt_path, f"Servant{str(svt).zfill(3)}.jpg"))
        #         if each_gacha[0] == "cft":
        #             cft = int(each_gacha[2])
        #             img_path.append(os.path.join(cft_path, f"礼装{str(cft).zfill(3)}.jpg"))
        #     # 图片版，较慢
        #     if server == "国服":
        #         base_img = Image.open(back_cn_path).convert("RGBA")
        #     else:
        #         base_img = Image.open(back_path).convert("RGBA")
        #     masker = Image.open(mask_path).resize((width, height))
        #
        #     for i, picpath in enumerate(img_path):
        #         tmp_img = Image.open(picpath).resize((width, height))
        #         tmp_img = tmp_img.convert('RGBA')
        #         base_img.paste(tmp_img, boxlist[i], mask=masker)
        #
        #     b64s.append(util.pic2b64(base_img))

    full_pup5 = False
    get_pup5 = 0
    for each in get_pup5_id:
        get_pup5 += each[0]
        if each[0] == 5:
            full_pup5 = True

    full_pup4 = False
    get_pup4 = 0
    for each in get_pup4_id:
        get_pup4 += each[0]
        if each[0] == 5:
            full_pup4 = True

    full_get_5 = False
    get_5 = 0
    for each in get_5_id:
        get_5 += each[0]
        if each[0] == 5:
            full_get_5 = True

    full_get_4 = False
    get_4 = 0
    for each in get_4_id:
        get_4 += each[0]
        if each[0] == 5:
            full_get_4 = True

    stars = ""
    is_seal = False
    if not get_pup5 == 0:
        stars += f"UP5☆×{get_pup5};\t"

    if not get_5 == 0:
        stars += f"5☆×{get_5};\t"

    if not get_pup4 == 0:
        stars += f"UP4☆×{get_pup4};\t"

    if not get_4 == 0:
        stars += f"4☆×{get_4};\t"
    stars += "\n"
    msg += stars

    if not get_pup5 and get_5:
        if full_get_5:
            msg += "满宝常驻五星？人干事？"
            is_seal = True
        if get_pup5_id:
            msg += "百连你都能不出up5星，洗洗睡吧\n"
        else:
            if get_5 > 1:
                msg += "某种意义上，也是歪的离谱（\n"
            else:
                msg += "常驻等歪.jpg\n"
        if not get_pup4 and get_4 and get_pup4_id:
            msg += "甚至没有up四星\n"
            if full_get_4:
                msg += "不是，你怎么做到满宝常驻的？"
        if not get_pup4 and not get_4:
            msg += "甚至没出四星\n"

    if not get_pup5 and not get_5:
        msg += "百连零鸡蛋！酋长，考虑一下转生呗？\n"
        if not get_pup4 and get_4 and get_pup4_id:
            msg += "甚至没有up四星\n"
        if not get_pup4 and not get_4:
            msg += "一张金卡都没有？这你还不转生\n"
        if full_pup4:
            msg += "up四星满宝啊，那没事了\n"
            is_seal = True

    if get_pup5:
        if get_pup5 > 1:
            is_seal = True
            if full_pup5:
                msg += "百连满宝，小心出门被车创死\n"
            if get_pup5 and not full_pup5:
                msg += "百连多宝不亏，这你还不补宝？\n"
            if not get_pup4 and get_pup4_id:
                msg += "众所周知，up四星好出\n"
            if not get_pup4 and not get_4:
                msg += "没出四星啊，那没事了\n"
        if get_pup5 == 1:
            msg += "出了就好，补不补宝这是一个问题~\n"
            if get_pup4:
                if full_pup4:
                    msg += "百连毕业四星还出了五星，速度补宝赚金方块啊\n"
                    is_seal = True
                else:
                    msg += "百连卡池毕业~这你还不补宝？\n"
                    is_seal = True

    if is_seal:
        img = Image.open(seal_path)
        pic_b64 = util.pic2b64(img)
        msg += f'\n{MessageSegment.image(pic_b64)}'

    # 如需图片版请取消注释，并将之后一行加一次缩进
    # if not style == "图片":
    await bot.send(ev, msg.strip(), at_sender=True)
    # 如需图片版请取消注释
    # else:
    #     nodes = [gen_node("您本次的抽卡结果：")]
    #     for each_b64 in b64s:
    #         nodes.append(gen_node(f'{MessageSegment.image(each_b64)}'))
    #     nodes.append(gen_node(msg.replace("您本次的抽卡结果：", "").strip()))
    #     await bot.send_group_forward_msg(group_id=ev['group_id'], messages=nodes)


@sv.on_prefix('氪圣晶石')
async def kakin(bot, ev: CQEvent):
    if ev.user_id not in bot.config.SUPERUSERS:
        bot.finish(ev, "小孩子别在游戏里氪金！", at_sender=True)
    count = 0
    for m in ev.message:
        if m.type == 'at' and m.data['qq'] != 'all':
            uid = int(m.data['qq'])
            jewel_limit.reset(uid)
            tenjo_limit.reset(uid)
            count += 1
    if count:
        await bot.send(ev, f"已为{count}位用户充值完毕！谢谢惠顾～")
