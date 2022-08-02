import base64
import io

from PIL import Image

from hoshino import priv, Service
from hoshino.typing import *
from hoshino.util import DailyNumberLimiter

from .download import *
from .getGachaPools import *
from .downloadIcons import *
from .gacha import *

jewel_limit = DailyNumberLimiter(3000)
tenjo_limit = DailyNumberLimiter(10)

JEWEL_EXCEED_NOTICE = f"您今天已经抽过{jewel_limit.max}石头了，欢迎明早5点后再来！"
TENJO_EXCEED_NOTICE = f"您今天已经抽过{tenjo_limit.max}张百连券了，欢迎明早5点后再来！"

FOLLOW_LATEST_POOL = True

basic_path = config.RES_DIR + "img/fgo/"
icon_path = basic_path + "icons/"
svt_path = icon_path + "svt_icons/Servant"
cft_path = icon_path + "cft_icons/礼装"
res_init_path = basic_path + ".init/"
runtime_path = os.path.dirname(__file__)
mooncellBackgroundUrl = 'https://fgo.wiki/images/bg/bg-mc-icon.png'
mooncellBackgroundPath = basic_path + 'bg-mc-icon.png'
data_path = os.path.join(runtime_path, 'data/')
banner_path = os.path.join(runtime_path, 'data/banner.json')
config_path = os.path.join(runtime_path, 'data/config.json')
pools_path = os.path.join(runtime_path, 'data/pools.json')
gacha_path = os.path.join(runtime_path, 'data/gacha.json')
icons_path = os.path.join(runtime_path, 'data/icons.json')
banner_data_path = os.path.join(runtime_path, 'data/b_data.json')
seal_path = os.path.join(runtime_path, '海の翁.jpg')
frame_path = os.path.join(runtime_path, 'background.png')
all_json = [banner_path, config_path, pools_path, gacha_path, icons_path, banner_data_path]
crt_path = "ca-certificates.crt"

sv_help = '''
[fgo数据初始化] 初始化数据文件及目录
[fgo数据下载] 下载从者及礼装图标
 - 务必先初始化数据再执行下载！
[获取fgo卡池] 从mooncell获取卡池数据
[查询fgo卡池] 查询本地缓存的卡池以及本群卡池
[切换fgo卡池 + 卡池编号] 切换需要的卡池
[切换fgo日替卡池 + 卡池编号 + 日替卡池编号] 切换需要的日替卡池
[fgo十连/fgo百连] 紧张刺激的抽卡
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


@sv.on_fullmatch(("帮助fgo抽卡", "帮助FGO抽卡"))
@sv.on_rex(r"^[fFbB][gG][oO][抽cC][卡kK][帮bB][助zZ]$")
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


@sv.on_rex(r"^[fFbB][gG][oO][数sS][据jJ][初cCiI][始sSnN][化hHiI]$")
async def init(bot, ev: CQEvent):
    if not priv.check_priv(ev, priv.ADMIN):
        await bot.finish(ev, '此命令仅群管可用~')
    if not os.path.exists(basic_path):
        print("数据初始化...")
        print("初始化资源根目录...")
        os.mkdir(basic_path)
    if not os.path.exists(icon_path):
        print("初始化图标目录...")
        os.mkdir(icon_path)
    if not os.path.exists(data_path):
        print("初始化data目录...")
        os.mkdir(data_path)
    for each in all_json:
        if not os.path.exists(each):
            print("初始化配置文件json...")
            open(each, 'w')
            if each == config_path:
                configs = []
                basic_config = {
                    "group": ev.group_id,
                    "crt_path": "None",
                    "follow_latest": FOLLOW_LATEST_POOL
                }
                configs.append(basic_config)
                with open(config_path, "w", encoding="utf-8") as f:
                    f.write(json.dumps(configs, indent=2, ensure_ascii=False))

    msg = "初始化完成！"
    await bot.send(ev, msg)


@sv.on_rex(r"^[fFbB][gG][oO][数sS][据jJ][下xXdD][载zZlL]")
async def get_fgo_data(bot, ev: CQEvent):
    if not priv.check_priv(ev, priv.ADMIN):
        await bot.finish(ev, '此命令仅群管可用~')
    if not os.path.exists(basic_path) or not os.path.exists(data_path):
        print("资源路径未初始化...")
        await bot.finish(ev, "资源路径未初始化！请先初始化资源路径\n指令：fgo数据初始化")

    print("Downloaded bg-mc-icon.png")
    await bot.send(ev, "开始下载....")
    print("开始下载bg")

    crt_file = None
    if os.path.exists(config_path):
        try:
            configs = json.load(open(config_path, encoding="utf-8"))
            for each in configs:
                if each["group"] == ev.group_id:
                    if not crt_file == "None":
                        crt_file = each["crt_path"]
        except json.decoder.JSONDecodeError:
            pass

    bg_stat = await download(mooncellBackgroundUrl, mooncellBackgroundPath, False, crt_file)
    if not bg_stat == 0:
        await bot.send(ev, f'下载bg失败……{bg_stat}')
    print("开始下载icon")
    icon_stat = await downloadicons(crt_file)
    if not icon_stat == 0:
        await bot.send(ev, f'下载icons失败……{bg_stat}')
    await bot.send(ev, "下载完成")


@sv.on_rex(r"^[获hH更gG][取qQ新xX][fFbB][gG][oO][卡kK][池cC]$|^[fFbB][gG][oO][卡kK][池cC][获hH更gG][取qQ新xX]$")
async def get_fgo_pool(bot, ev: CQEvent):
    global FOLLOW_LATEST_POOL
    await bot.send(ev, "开始更新....")
    if os.path.exists(config_path):
        configs = json.load(open(config_path, encoding="utf-8"))
        for each in configs:
            if each["group"] == ev.group_id:
                FOLLOW_LATEST_POOL = each["follow_latest"]
    download_stat = await getgachapools(FOLLOW_LATEST_POOL)
    if not download_stat == 0:
        await bot.send(ev, f'更新失败……{download_stat}')
    else:
        await bot.send(ev, "获取卡池完成")


@sv.on_rex(r"^[gG跟][sS随][zZ最jJ剧][xX新qQ情][kK卡][cC池]$")
async def follow_latest(bot, ev: CQEvent):
    global FOLLOW_LATEST_POOL
    args = ev.message.extract_plain_text()
    if not os.path.exists(config_path):
        print("初始化配置文件json...")
        open(config_path, 'w')
        configs = []
    else:
        configs = json.load(open(config_path, encoding="utf-8"))

    rule_latest = re.compile(r"^[gG跟][sS随][zZ最][xX新][kK卡][cC池]$")
    rule_story = re.compile(r"^[gG跟][sS随][jJ剧][qQ情][kK卡][cC池]$")
    if re.match(rule_latest, args):
        FOLLOW_LATEST_POOL = True
    if re.match(rule_story, args):
        FOLLOW_LATEST_POOL = False

    crt_config = {
        "group": ev.group_id,
        "crt_path": "ca-certificates.crt",
        "follow_latest": FOLLOW_LATEST_POOL
    }

    exists = False
    for i in range(len(configs)):
        if configs[i]["group"] == ev.group_id:
            crt_config["crt_path"] = configs[i]["crt_path"]
            configs[i] = crt_config
            exists = True

    if not exists:
        configs.append(crt_config)

    with open(config_path, "w", encoding="utf-8") as f:
        f.write(json.dumps(configs, indent=2, ensure_ascii=False))

    if FOLLOW_LATEST_POOL:
        await bot.send(ev, "切换成功，当前跟随最新卡池")
    else:
        await bot.send(ev, "切换成功，当前跟随剧情卡池")


async def check_jewel(bot, ev):
    if not jewel_limit.check(ev.user_id):
        await bot.finish(ev, JEWEL_EXCEED_NOTICE, at_sender=True)
    elif not tenjo_limit.check(ev.user_id):
        await bot.finish(ev, TENJO_EXCEED_NOTICE, at_sender=True)


@sv.on_rex(r"^[查cC][询xX][fFbB][gG][oO][卡kK][池cC]|^[fFbB][gG][oO][卡kK][池cC][查cC][询xX]$")
async def check_pool(bot, ev: CQEvent):
    pools = json.load(open(pools_path, encoding="utf-8"))
    if len(pools) == 0:
        print("no pool")
        await bot.finish(ev, "没有卡池！请先获取卡池！")

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

        if not exists:
            print("no banner")
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
@sv.on_rex(r"^[切qQsS][换hHwW][fFbB][gG][oO][卡kK][池cC](\s\d+)?$|^[fFbB][gG][oO][卡kK][池cC][切qQsS][换hHwW](\s\d+)?$")
async def switch_pool(bot, ev: CQEvent):
    p_id = ev.message.extract_plain_text()
    p_id = p_id.split(" ")
    if len(p_id) > 1:
        p_id = p_id[1]
    else:
        p_id = p_id[0]
    if not p_id.isdigit():
        await bot.finish(ev, "食用指南：切换fgo卡池 + 编号", at_sender=True)

    pools = json.load(open(pools_path, encoding="utf-8"))
    if not os.path.exists(banner_path):
        print("初始化数据json...")
        open(banner_path, 'w')
        banners = []
    else:
        banners = json.load(open(banner_path, encoding="utf-8"))
    if len(pools) == 0:
        print("no pool")
        await bot.finish(ev, "没有卡池！请先获取卡池！")

    banner = {
        "group": ev.group_id,
        "banner": []
    }
    for each in pools:
        if each["id"] == int(p_id):
            if each["type"] == "daily pickup":
                await bot.finish(ev, "日替卡池请使用指令：切换fgo日替卡池 + 卡池编号 + 日替卡池编号")
            banner["banner"] = each
            break
    if banner == {"group": ev.group_id, "banner": []}:
        await bot.finish(ev, "卡池编号不存在")

    exists = False
    for i in range(len(banners)):
        if banners[i]["group"] == ev.group_id:
            banners[i] = banner
            exists = True
    if not exists:
        banners.append(banner)
    with open(banner_path, "w", encoding="utf-8") as f:
        f.write(json.dumps(banners, indent=2, ensure_ascii=False))

    title = banner["banner"]["title"]
    b_name = banner["banner"]["banner"]
    await bot.send(ev, f"切换fgo卡池成功！当前卡池：\n{b_name}\n从属活动：\n{title}")


@sv.on_rex(r"^[切qQsS][换hHwW][fFbB][gG][oO][日rRdD][替tTpP][卡kK][池cC](\s\d+\s\d+)?$"
           r"|^[fFbB][gG][oO][日rRdD][替tTpP][卡kK][池cC][切qQsS][换hHwW](\s\d+\s\d+)?$")
async def switch_pool(bot, ev: CQEvent):
    ids = ev.message.extract_plain_text()
    if ids == "":
        await bot.finish(ev, "食用指南：切换fgo日替卡池 + 编号", at_sender=True)

    pools = json.load(open(pools_path, encoding="utf-8"))
    ids = ids.split(" ")
    p_id = ""
    s_id = ""
    if len(ids) > 2:
        p_id = ids[1]
        s_id = ids[2]
    else:
        await bot.finish(ev, "食用指南：切换fgo日替卡池 + 卡池编号 + 日替卡池编号", at_sender=True)

    if not os.path.exists(banner_path):
        print("初始化数据json...")
        open(banner_path, 'w')
        banners = []
    else:
        banners = json.load(open(banner_path, encoding="utf-8"))
    if len(pools) == 0:
        print("no pool")
        await bot.finish(ev, "没有卡池！请先获取卡池！")

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
                        "s_id": sub_pool["id"],
                        "title": each["title"],
                        "href": each["href"],
                        "banner": each["banner"],
                        "sub_title": sub_pool["sub_title"],
                        "type": each["type"]
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
@sv.on_rex(r'^[fFbB][gG][oO](十|10|s|S)(连|l|L)')
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
                img_path.append(svt_path + str(svt) + ".jpg")
            if 9 < int(svt) < 100:
                img_path.append(svt_path + "0" + str(svt) + ".jpg")
            if int(svt) < 10:
                img_path.append(svt_path + "00" + str(svt) + ".jpg")
        if each[0] == "cft":
            cft = int(random.choice(each[2]))
            if int(cft) > 99:
                img_path.append(cft_path + str(cft) + ".jpg")
            if 9 < int(cft) < 100:
                img_path.append(cft_path + "0" + str(cft) + ".jpg")
            if int(cft) < 10:
                img_path.append(cft_path + "00" + str(cft) + ".jpg")

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


@sv.on_rex(r'^[fFbB][gG][oO](百|100|b|B)(连|l|L)')
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
                    img_path.append(svt_path + str(svt) + ".jpg")
                if 9 < int(svt) < 100:
                    img_path.append(svt_path + "0" + str(svt) + ".jpg")
                if int(svt) < 10:
                    img_path.append(svt_path + "00" + str(svt) + ".jpg")

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


@sv.on_prefix("fgo_enable_crt")
async def enable_crt(bot, ev: CQEvent):
    if not priv.check_priv(ev, priv.SUPERUSER):
        await bot.finish(ev, '此命令仅主さま可用~')
    crt = ev.message.extract_plain_text()

    if crt == "":
        await bot.send(ev, "食用指南：指令 + crt文件路径，留空设置为默认路径")
        crt = crt_path

    rule = re.compile(r"^[nN][oO][nN][eE]$")
    match = re.match(rule, crt)
    if match:
        crt = "None"

    if not os.path.exists(config_path):
        print("初始化配置文件json...")
        open(config_path, 'w')
        configs = []
    else:
        configs = json.load(open(config_path, encoding="utf-8"))

    crt_config = {
        "group": ev.group_id,
        "crt_path": crt,
        "follow_latest": FOLLOW_LATEST_POOL
    }

    exists = False
    for i in range(len(configs)):
        if configs[i]["group"] == ev.group_id:
            crt_config["follow_latest"] = configs[i]["follow_latest"]
            configs[i] = crt_config
            exists = True

    if not exists:
        configs.append(crt_config)

    with open(config_path, "w", encoding="utf-8") as f:
        f.write(json.dumps(configs, indent=2, ensure_ascii=False))

    if not crt == "None":
        await bot.finish(ev, f"已配置crt文件，文件路径：{crt}")
    else:
        await bot.finish(ev, f"已禁用crt文件")


@sv.on_fullmatch("fgo_check_crt")
async def enable_crt(bot, ev: CQEvent):
    if not priv.check_priv(ev, priv.SUPERUSER):
        await bot.finish(ev, '此命令仅主さま可用~')

    if not os.path.exists(config_path):
        await bot.finish(ev, "未配置crt文件")

    configs = json.load(open(config_path, encoding="utf-8"))
    crt_config = {}

    exists = False
    for each in configs:
        if each["group"] == ev.group_id:
            exists = True
            crt_config = each
    if not exists:
        await bot.finish(ev, "本群未配置crt")
    else:
        if crt_config['crt_path'] == "None":
            await bot.finish(ev, "本群已禁用crt文件")
        else:
            await bot.finish(ev, f"本群已配置crt文件，文件路径：{crt_config['crt_path']}")


@sv.scheduled_job('cron', hour=8)
async def update_pool():
    # 自动更新卡池
    await getgachapools(True)
    crt_file = os.path.join(runtime_path, crt_path)
    bg_stat = await download(mooncellBackgroundUrl, mooncellBackgroundPath, False, crt_file)
    if not bg_stat == 0:
        print(f'下载bg失败……{bg_stat}')
    print("开始下载icon")
    icon_stat = await downloadicons(crt_file)
    if not icon_stat == 0:
        print(f'下载icons失败……{bg_stat}')
