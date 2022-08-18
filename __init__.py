import base64
import io
import json
import random

from PIL import Image

from hoshino import priv, Service
from hoshino.typing import CQEvent
from hoshino.util import DailyNumberLimiter
from .gacha import gacha
from .getGachaPools import getgachapools
from .path_and_json import *

jewel_limit = DailyNumberLimiter(3000)
tenjo_limit = DailyNumberLimiter(10)

JEWEL_EXCEED_NOTICE = f"您今天已经抽过{jewel_limit.max}石头了，欢迎明早5点后再来！"
TENJO_EXCEED_NOTICE = f"您今天已经抽过{tenjo_limit.max}张百连券了，欢迎明早5点后再来！"

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
    _name = "涩茄子"
    _uin = "2087332430"
    helps = {
        "type": "node",
        "data": {
            "name": _name,
            "uin": _uin,
            "content": sv_help
        }
    }
    await bot.send_group_forward_msg(group_id=ev['group_id'], messages=helps)


async def check_jewel(bot, ev):
    if not jewel_limit.check(ev.user_id):
        await bot.finish(ev, JEWEL_EXCEED_NOTICE, at_sender=True)
    elif not tenjo_limit.check(ev.user_id):
        await bot.finish(ev, TENJO_EXCEED_NOTICE, at_sender=True)


@sv.on_rex(r"(?i)^([获h更g][取q新x])?[fb]go[卡k][池c]([获h更g][取q新x])?$")
async def get_fgo_pool(bot, ev: CQEvent):
    await bot.send(ev, "开始更新....")
    crt_file = False
    if os.path.exists(config_path):
        try:
            configs = json.load(open(config_path, encoding="utf-8"))
        except json.decoder.JSONDecodeError:
            basic_config = {
                "group": ev.group_id,
                "crt_path": crt_path
            }
            configs = {
                "follow_latest": True,
                "flush_hour": 0,
                "flush_minute": 60,
                "flush_second": 0,
                "groups": [basic_config]
            }
            with open(config_path, "w", encoding="utf-8") as f:
                f.write(json.dumps(configs, indent=2, ensure_ascii=False))

        for each in configs["groups"]:
            if each["group"] == ev.group_id:
                if not each["crt_path"] == "False":
                    crt_file = os.path.join(crt_folder_path, each["crt_path"])
                    break
    download_stat = await getgachapools(True, crt_file)
    if not isinstance(download_stat, int):
        await bot.finish(ev, f'更新失败，原因：\n{download_stat}')
    if not download_stat:
        await bot.send(ev, "获取卡池完成")
    elif download_stat:
        await bot.send(ev, "本地卡池和线上卡池是一样的啦~\n晚点再来看看吧~")


@sv.on_rex(r"(?i)^([查c])?([询x])?[fb]go[卡k][池c]([查c][询x])?$")
async def check_pool(bot, ev: CQEvent):
    pools = json.load(open(pools_path, encoding="utf-8"))
    if len(pools) == 0:
        sv.logger.info("no pool")
        await bot.finish(ev, "没有卡池！请先获取卡池！\n指令：[获取fgo卡池]")

    msg = "当前卡池："
    for each in pools:
        s = f"\n{each['id']}：{each['banner']}"
        msg += s
        if "sub_pool" in each:
            for sub_pools in each["sub_pool"]:
                s = f"\n\t{sub_pools['id']}：{sub_pools['sub_title']}"
                msg += s

    if os.path.exists(banner_path):
        banners = json.load(open(banner_path, encoding="utf-8"))
        banner = {}
        exists = False
        for each in banners:
            if each["group"] == ev.group_id:
                banner = each
                exists = True
                break

        if not exists:
            sv.logger.info("no banner")
        else:
            b_name = banner["banner"]["banner"]
            title = banner["banner"]["title"]
            if "sub_title" in banner["banner"]:
                b_name = banner["banner"]["sub_title"]
            group = f"\n\n本群{ev.group_id}卡池：\n{b_name}\n从属活动：\n{title}"
            msg += group

    if len(msg) > 200:
        _name = "涩茄子"
        _uin = "2087332430"
        _banner = {
            "type": "node",
            "data": {
                "name": _name,
                "uin": _uin,
                "content": msg
            }
        }
        await bot.send_group_forward_msg(group_id=ev['group_id'], messages=_banner)
    else:
        await bot.send(ev, msg)


# noinspection PyTypeChecker
@sv.on_rex(r"(?i)^[切qs][换hw][fb]go[卡k][池c](\s\d+)?$|^[fb]go[卡k][池c][切qs][换hw](\s\d+)?$")
async def switch_pool(bot, ev: CQEvent):
    p_id = ev.message.extract_plain_text()
    p_id = p_id.split(" ")
    if len(p_id) > 1:
        p_id = p_id[1]
    else:
        p_id = p_id[0]
    if not p_id.isdigit():
        await bot.finish(ev, "食用指南：[切换fgo卡池 + 编号]", at_sender=True)

    pools = json.load(open(pools_path, encoding="utf-8"))
    if not os.path.exists(banner_path):
        sv.logger.info("初始化数据json...")
        open(banner_path, 'w')
        banners = []
    else:
        banners = json.load(open(banner_path, encoding="utf-8"))
    if len(pools) == 0:
        sv.logger.info("no pool")
        await bot.finish(ev, "没有卡池！请先获取卡池！\n指令：[获取fgo卡池]")

    banner = {
        "group": ev.group_id,
        "banner": []
    }
    for each in pools:
        if each["id"] == int(p_id):
            if each["type"] == "daily pickup":
                await bot.finish(ev, "日替卡池请使用指令：[切换fgo日替卡池 + 卡池编号 + 子卡池编号]")
            banner["banner"] = each
            break
    if banner == {"group": ev.group_id, "banner": []}:
        await bot.finish(ev, "卡池编号不存在")

    exists = False
    for i in range(len(banners)):
        if banners[i]["group"] == ev.group_id:
            banners[i] = banner
            exists = True
            break
    if not exists:
        banners.append(banner)
    with open(banner_path, "w", encoding="utf-8") as f:
        f.write(json.dumps(banners, indent=2, ensure_ascii=False))

    title = banner["banner"]["title"]
    b_name = banner["banner"]["banner"]
    await bot.send(ev, f"切换fgo卡池成功！当前卡池：\n{b_name}\n从属活动：\n{title}")


@sv.on_rex(r"(?i)^([切qs][换hw])?[fb]go[日rd][替tp][卡k][池c]([切qs][换hw])?(\s\d+\s\d+)?$")
async def switch_pool(bot, ev: CQEvent):
    ids = ev.message.extract_plain_text()
    if ids == "":
        await bot.finish(ev, "食用指南：[切换fgo日替卡池 + 编号 + 子编号]", at_sender=True)

    pools = json.load(open(pools_path, encoding="utf-8"))
    ids = ids.split(" ")
    p_id = ""
    s_id = ""
    if len(ids) > 2:
        p_id = ids[1]
        s_id = ids[2]
    else:
        await bot.finish(ev, "食用指南：[切换fgo日替卡池 + 卡池编号 + 子卡池编号]", at_sender=True)

    if not os.path.exists(banner_path):
        sv.logger.info("初始化数据json...")
        open(banner_path, 'w')
        banners = []
    else:
        banners = json.load(open(banner_path, encoding="utf-8"))
    if len(pools) == 0:
        sv.logger.info("no pool")
        await bot.finish(ev, "没有卡池！请先获取卡池！\n指令：[获取fgo卡池]")

    banner = {
        "group": ev.group_id,
        "banner": []
    }
    for each in pools:
        if each["id"] == int(p_id) and each["type"] == "daily pickup":
            for sub_pool in each["sub_pool"]:
                if sub_pool["id"] == int(s_id):
                    sp = {
                        "id": each["id"],
                        "title": each["title"],
                        "href": each["href"],
                        "banner": each["banner"],
                        "sub_title": sub_pool["sub_title"],
                        "type": each["type"],
                        "s_id": sub_pool["id"]
                    }
                    banner["banner"] = sp
                    break

    if banner == {"group": ev.group_id, "banner": []}:
        await bot.finish(ev, "卡池编号不存在")

    exists = False
    for i in range(len(banners)):
        if banners[i]["group"] == ev.group_id:
            banners[i] = banner
            exists = True
            break
    if not exists:
        banners.append(banner)
    with open(banner_path, "w", encoding="utf-8") as f:
        f.write(json.dumps(banners, indent=2, ensure_ascii=False))

    title = banner["banner"]["title"]
    b_name = banner["banner"]["banner"]
    if "sub_title" in banner["banner"]:
        b_name = banner["banner"]["sub_title"]
    await bot.send(ev, f"切换fgo卡池成功！当前卡池：\n{b_name}\n从属活动：\n{title}")


# @sv.on_prefix("fgo十连", only_to_me=True)
@sv.on_rex(r'(?i)^[fb]go(十|10|s)[连l]$')
async def gacha_10(bot, ev: CQEvent):
    gid = ev.group_id

    # barrier
    await check_jewel(bot, ev)
    jewel_limit.increase(ev.user_id, 30)

    gacha_result, has_pup5, has_pup4 = await gacha(gid)
    if gacha_result == 12:
        await bot.finish(ev, "没有选择卡池！请先选择卡池！")
    if gacha_result == 13:
        await bot.finish(ev, "卡池数据错误！请更新卡池！")

    img_path = []
    get_pup5 = 0
    get_pup4 = 0
    get_5 = 0
    get_4 = 0
    for each in gacha_result:
        if each[0] == "svt":
            svt = int(random.choice(each[2]))
            if int(each[1] == "up5"):
                get_pup5 += 1
            if int(each[1] == "up4"):
                get_pup4 += 1
            if int(each[1] == "5"):
                get_5 += 1
            if int(each[1] == "4"):
                get_4 += 1
            if int(svt) > 99:
                img_path.append(svt_path + "Servant" + str(svt) + ".jpg")
            if 9 < int(svt) < 100:
                img_path.append(svt_path + "Servant" + "0" + str(svt) + ".jpg")
            if int(svt) < 10:
                img_path.append(svt_path + "Servant" + "00" + str(svt) + ".jpg")
        if each[0] == "cft":
            cft = int(random.choice(each[2]))
            if int(cft) > 99:
                img_path.append(cft_path + "礼装" + str(cft) + ".jpg")
            if 9 < int(cft) < 100:
                img_path.append(cft_path + "礼装" + "0" + str(cft) + ".jpg")
            if int(cft) < 10:
                img_path.append(cft_path + "礼装" + "00" + str(cft) + ".jpg")

    cards = []
    for each in img_path:
        cards.append(Image.open(each).resize((66, 72)))
    rows = 3
    cols = 4
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

    bio = io.BytesIO()
    target.save(bio, format='PNG')
    base64_str = base64.b64encode(bio.getvalue()).decode()
    pic_b64 = f'base64://{base64_str}'
    cqcode = f'[CQ:image,file={pic_b64}]\n'
    msg = "\n您本次的抽卡结果：\n" + cqcode
    stars = ""
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
    is_seal = False
    if get_pup5 == 0 and not get_5 == 0:
        if get_5 < 2 and has_pup5:
            msg += "“常驻等歪.jpg”不亏！\n"
        if get_5 < 2 and not has_pup5:
            msg += "有五星就行\n"
        if get_5 > 1 and has_pup5:
            msg += "欧了，但是没有完全欧\n"
            is_seal = True
        if get_5 > 1 and not has_pup5:
            msg += "这么多五星，还说你不是海豹？\n"
        if not get_pup4 == 0:
            msg += "出了up四星，还歪了常驻，血赚\n"
        if get_pup4 == 5:
            msg += "十连满宝四星，血赚\n"
        if get_5 + get_pup4 + get_4 > 1:
            msg += "多黄不亏\n"

    if get_pup5 == 0 and get_5 == 0:
        if not get_pup4 == 0:
            msg += "起码出了up四星，不亏\n"
        if get_pup4 == 0 and not get_4 == 0 and has_pup4:
            msg += "不是吧，四星也能歪？\n"
        if get_pup4 == 5:
            msg += "十连满宝四星，血赚\n"
            is_seal = True
        if not get_pup4 == 5 and get_pup4 > 1:
            msg += "up四星多黄，血赚\n"
            is_seal = True
        if get_pup4 + get_4 > 1:
            msg += "多黄不亏\n"
        if get_pup4 == 0 and get_4 == 0:
            msg += "零鸡蛋！酋长咱们回非洲吧\n"
        if 0 < get_4 < 2 and not has_pup4:
            msg += "出金就行.jpg\n"
        if get_4 > 1 and not has_pup4:
            msg += "什么四星大放送啊\n"
            is_seal = True

    if not get_pup5 == 0:
        if get_pup5 > 1:
            if not get_5 == 0:
                msg += "又多宝又歪常驻，什么臭海豹\n"
                is_seal = True
            if get_5 == 0:
                msg += "多黄臭海豹，建议击杀\n"
                is_seal = True
            if get_pup5 == 5:
                msg += "十连满宝，小心出门被车创死\n"
                is_seal = True
            if get_pup4 == 0 and has_pup4:
                msg += "众所周知，四星好出\n"
        if get_pup5 < 2:
            msg += "出了就好，补不补宝这是一个问题~\n"
            if not get_pup4 == 0:
                if get_pup4 == 5:
                    msg += "一发毕业四星还出了五星，你是狗吧？\n"
                    is_seal = True
                else:
                    msg += "十连卡池毕业~这你还不补宝？\n"
                    is_seal = True
    if is_seal:
        with open(seal_path, "rb") as f:
            seal = f.read()
        bio = io.BytesIO(seal)
        base64_str = base64.b64encode(bio.getvalue()).decode()
        pic_b64 = f'base64://{base64_str}'
        cqcode = f'\n[CQ:image,file={pic_b64}]'
        msg += cqcode

    await bot.send(ev, msg, at_sender=True)


@sv.on_rex(r'(?i)^[fb]go(百|100|b)[连l]$')
async def gacha_100(bot, ev: CQEvent):
    gid = ev.group_id

    # barrier
    await check_jewel(bot, ev)
    tenjo_limit.increase(ev.user_id, 1)

    g100 = []
    g_counter = 0
    has_pup5 = False
    has_pup4 = False
    while g_counter < 11:
        g_counter += 1
        result, has_pup5, has_pup4 = await gacha(gid)
        g100.append(result)

    if g100[0] == 12:
        await bot.finish(ev, "没有选择卡池！请先选择卡池！")
    if g100[0] == 13:
        await bot.finish(ev, "卡池数据错误！请更新卡池！")

    img_path = []
    get_pup5 = 0
    get_pup4 = 0
    get_5 = 0
    get_4 = 0
    for gacha_result in g100:
        for each in gacha_result:
            if each[0] == "svt":
                svt = int(random.choice(each[2]))
                if int(each[1] == "up5"):
                    get_pup5 += 1
                if int(each[1] == "up4"):
                    get_pup4 += 1
                if int(each[1] == "5"):
                    get_5 += 1
                if int(each[1] == "4"):
                    get_4 += 1
                if int(each[1] == "3"):
                    continue
                if int(svt) > 99:
                    img_path.append(svt_path + "Servant" + str(svt) + ".jpg")
                if 9 < int(svt) < 100:
                    img_path.append(svt_path + "Servant" + "0" + str(svt) + ".jpg")
                if int(svt) < 10:
                    img_path.append(svt_path + "Servant" + "00" + str(svt) + ".jpg")

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

    if not cards == []:
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

        bio = io.BytesIO()
        target.save(bio, format='PNG')
        base64_str = base64.b64encode(bio.getvalue()).decode()
        pic_b64 = f'base64://{base64_str}'
        cqcode = f'[CQ:image,file={pic_b64}]\n\n'
        msg = "\n您本次的抽卡结果：\n\n" + cqcode
    else:
        msg = "\n您本次的抽卡结果：\n\n"

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

    if get_pup5 == 0 and not get_5 == 0:
        if has_pup5:
            msg += "百连你都能不出up5星，洗洗睡吧\n"
        else:
            msg += "百连你都能不出5星，什么天选之子\n"
        if get_pup4 == 0 and not get_4 == 0 and has_pup4:
            msg += "甚至没有up四星\n"
        if get_pup4 == 0 and get_4 == 0:
            msg += "甚至没出四星\n"

    if get_pup5 == 0 and get_5 == 0:
        msg += "百连零鸡蛋！酋长，考虑一下转生呗？\n"
        if get_pup4 == 0 and not get_4 == 0 and has_pup4:
            msg += "甚至没有up四星\n"
        if get_pup4 == 0 and get_4 == 0:
            msg = "百连零鸡蛋！酋长，考虑一下转生呗？\n"
            msg += "一张金卡都没有？这你还不转生\n"
        if get_pup4 >= 5:
            msg += "up四星满宝啊，那没事了\n"
            is_seal = True

    if not get_pup5 == 0:
        if get_pup5 > 1:
            is_seal = True
            if get_pup5 == 5:
                msg += "百连满宝，小心出门被车创死\n"
            if not get_pup5 == 0 and not get_pup5 == 5:
                msg += "百连多宝不亏，这你还不补宝？\n"
            if get_pup4 == 0 and has_pup4:
                msg += "众所周知，up四星好出\n"
            if get_pup4 == 0 and get_4 == 0:
                msg += "没出四星啊，那没事了\n"
        if get_pup5 < 2:
            msg += "出了就好，补不补宝这是一个问题~\n"
            if not get_pup4 == 0:
                if get_pup4 == 5:
                    msg += "百连毕业四星还出了五星，速度补宝赚金方块啊\n"
                    is_seal = True
                else:
                    msg += "百连卡池毕业~这你还不补宝？\n"
                    is_seal = True

    if is_seal:
        with open(seal_path, "rb") as f:
            seal = f.read()
        bio = io.BytesIO(seal)
        base64_str = base64.b64encode(bio.getvalue()).decode()
        pic_b64 = f'base64://{base64_str}'
        cqcode = f'\n[CQ:image,file={pic_b64}]'
        msg += cqcode

    await bot.send(ev, msg, at_sender=True)


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
