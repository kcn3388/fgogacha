import copy
from hoshino import HoshinoBot
from .download.download_all_res import download_icon_skill
from .download.download_icons import *
from .get.get_all_cft import *
from .get.get_all_cmd import *
from .get.get_all_svt import *
from .get.get_gacha_pools import *
from .get.get_news import *
from .loop import Counter  # 借助 use_reloader 实现当模块发生变化时自动重载整个 Python

# 更新时间间隔，单位为秒
flush_second = 0
# 更新时间间隔，单位为分钟
flush_minute = 60
# 更新时间间隔，单位为小时
flush_hour = 0

FOLLOW_LATEST_POOL = True

try:
    configs_schedule = json.load(open(config_path, encoding="utf-8"))
    flush_hour = configs_schedule["flush_hour"]
    flush_minute = configs_schedule["flush_minute"]
    flush_second = configs_schedule["flush_second"]
except json.decoder.JSONDecodeError:
    pass
except FileNotFoundError:
    pass
except KeyError:
    pass


@sv_manage.on_fullmatch(("帮助fgo管理", "帮助FGO管理", "帮助bgo管理", "帮助BGO管理"))
@sv_manage.on_rex(re.compile(r"^[fb]go[管g][理l][帮b][助z]$", re.IGNORECASE))
async def bangzhu(bot: HoshinoBot, ev: CQEvent):
    if not priv.check_priv(ev, priv.ADMIN):
        await bot.send(ev, '此命令仅群管可用~')
        return

    helps = gen_node(sv_manage_help)
    await bot.send_group_forward_msg(group_id=ev['group_id'], messages=helps)


@sv_manage.on_rex(re.compile(r"^[fb]go[数s][据j][初ci][始sn][化hi]|fgo\sinit$", re.IGNORECASE))
async def init(bot: HoshinoBot, ev: CQEvent):
    if not priv.check_priv(ev, priv.ADMIN):
        await bot.send(ev, '此命令仅群管可用~')
        return

    if not os.path.exists(basic_path):
        sv_manage.logger.info("数据初始化...")
        sv_manage.logger.info("初始化资源根目录...")
        os.mkdir(basic_path)
    for each in res_paths:
        if not os.path.exists(each):
            sv_manage.logger.info(f"初始化{each}...")
            os.mkdir(each)
    if not os.path.exists(data_path):
        sv_manage.logger.info("初始化data目录...")
        os.mkdir(data_path)
        os.mkdir(os.path.join(data_path, "data"))
        os.mkdir(mc_path)
    for each in all_json:
        if not os.path.exists(each):
            sv_manage.logger.info("初始化配置文件json...")
            open(each, 'w')
            if each == config_path:
                basic_config = {
                    "style": "图片"
                }
                configs = {
                    "follow_latest": FOLLOW_LATEST_POOL,
                    "flush_hour": flush_hour,
                    "flush_minute": flush_minute,
                    "flush_second": flush_second,
                    "groups": {
                        str(ev.group_id): basic_config
                    }
                }
                with open(config_path, "w", encoding="utf-8") as f:
                    f.write(json.dumps(configs, indent=2, ensure_ascii=False))

    msg = "初始化完成！"
    await bot.send(ev, msg)


@sv_manage.on_rex(re.compile(r"^[fb]go[数s][据j][下xd][载zl]$", re.IGNORECASE))
async def get_fgo_data(bot: HoshinoBot, ev: CQEvent):
    if not priv.check_priv(ev, priv.ADMIN):
        await bot.send(ev, '此命令仅群管可用~')
        return

    if not os.path.exists(basic_path) or not os.path.exists(data_path):
        sv_manage.logger.info("资源路径未初始化...")
        await bot.send(ev, "资源路径未初始化！你是不是想下到你ass里？请先初始化资源路径\n指令：[fgo数据初始化]")
        return

    sv_manage.logger.info("Downloaded bg-mc-icon.png")
    await bot.send(ev, "开始下载....")

    async with ClientSession(headers=headers) as session:
        sv_manage.logger.info("开始下载icon")
        icon_stat = await download_icons(session)
        if not isinstance(icon_stat, int):
            await bot.send(ev, f'下载icons失败，原因：\n{icon_stat}')
        if icon_stat:
            sv_manage.logger.info(f'icon没有更新，跳过……')

        if icon_stat:
            await bot.send(ev, "没有新的资源~晚点再来看看吧~")
        else:
            await bot.send(ev, "下载完成")


@sv_manage.on_rex(re.compile(r"^[g跟][s随][z最j剧][x新q情][k卡][c池]$", re.IGNORECASE))
async def follow_latest(bot: HoshinoBot, ev: CQEvent):
    if not priv.check_priv(ev, priv.ADMIN):
        await bot.send(ev, '此命令仅群管可用~')
        return

    global FOLLOW_LATEST_POOL
    args = ev.message.extract_plain_text()
    configs = load_config(ev)

    rule_latest = re.compile(r"^[g跟][s随][z最][x新][k卡][c池]$", re.IGNORECASE)
    rule_story = re.compile(r"^[g跟][s随][j剧][q情][k卡][c池]$", re.IGNORECASE)
    if re.match(rule_latest, args):
        FOLLOW_LATEST_POOL = True
    if re.match(rule_story, args):
        FOLLOW_LATEST_POOL = False

    configs["follow_latest"] = FOLLOW_LATEST_POOL

    with open(config_path, "w", encoding="utf-8") as f:
        f.write(json.dumps(configs, indent=2, ensure_ascii=False))

    if FOLLOW_LATEST_POOL:
        await bot.send(ev, "切换成功，当前跟随最新卡池")
    else:
        await bot.send(ev, "切换成功，当前跟随剧情卡池")


@sv_manage.on_rex(re.compile(r"^[切qs][换hw][抽c][卡k][样y][式s]\s(text|img|文字|图片)$", re.IGNORECASE))
async def switch_10roll_style(bot: HoshinoBot, ev: CQEvent):
    gid = str(ev.group_id)
    style = ev.message.extract_plain_text().split()

    if not os.path.exists(config_path):
        await bot.send(ev, "未初始化配置文件")
        return

    if re.match(re.compile(r"(text|文字)", re.IGNORECASE), style[1]):
        style = "文字"

    if re.match(re.compile(r"(img|图片)", re.IGNORECASE), style[1]):
        style = "图片"

    if not style == "图片":
        if not style == "文字":
            await bot.send(ev, "参数错误")
            return

    configs = load_config(ev)
    if gid in configs:
        configs["groups"][gid]["style"] = style
    else:
        style_config = {
            "style": style
        }
        configs["groups"][gid] = style_config

    with open(config_path, "w", encoding="utf-8") as f:
        f.write(json.dumps(configs, indent=2, ensure_ascii=False))

    await bot.send(ev, f"已修改十连样式，当前样式：{style}")


@sv_manage.on_rex(re.compile(r"^([重c][载z]|reload)\s?([配p][置z][文w][件j]|config)$", re.IGNORECASE))
async def reload_config(bot: HoshinoBot, ev: CQEvent):
    gid = str(ev.group_id)
    if not priv.check_priv(ev, priv.ADMIN):
        await bot.send(ev, '此命令仅群管可用~')
        return

    configs = load_config(ev)
    configs["groups"][gid] = {
        "style": "图片"
    }

    with open(config_path, "w", encoding="utf-8") as f:
        f.write(json.dumps(configs, indent=2, ensure_ascii=False))

    await bot.send(ev, "已重载配置文件")


@sv_manage.scheduled_job('interval', hours=flush_hour, minutes=flush_minute, seconds=flush_second)
async def update_pool():
    if not os.path.exists(data_path):
        sv_manage.logger.info("资源未初始化……结束")
        return
    sv_manage.logger.info("开始自动更新fgo")

    async with ClientSession(headers=headers) as session:
        # 自动更新卡池
        r = await get_gacha_pools(True, session)
        if not isinstance(r, int):
            sv_manage.logger.error(f"获取卡池失败，原因：{r}")

        # 自动更新新闻
        news, status = await get_news(6, session)
        if isinstance(status, Exception):
            sv_manage.logger.error(f"获取新闻失败，原因：{status}")

        # 自动下载资源
        _, updated_servant_list = await get_all_svt(session)
        _, updated_cft_list = await get_all_cft(session)
        _, updated_cmd_list = await get_all_cmd(session)
        icon_stat = await download_icons(session)
        icon_skill_stat = await download_icon_skill(session)

        if not isinstance(icon_stat, int):
            sv_manage.logger.error(f'下载icons失败，原因：{icon_stat}')
        if icon_stat:
            sv_manage.logger.info(f'icon没有更新，跳过……')

        if not isinstance(icon_skill_stat, int):
            sv_manage.logger.error(f'下载skill icons失败，原因：{icon_skill_stat}')
        if icon_skill_stat:
            sv_manage.logger.info(f'skill icon没有更新，跳过……')

        updates = {
            "svt": [],
            "cft": [],
            "cmd": []
        }
        if not os.path.exists(update_data_path):
            sv_fetch.logger.info("初始化数据json...")
            open(update_data_path, 'w')
        else:
            try:
                updates = json.load(open(update_data_path, encoding="utf-8"))
            except json.decoder.JSONDecodeError:
                pass

        if not updates["svt"]:
            updates["svt"] = updated_servant_list if updated_servant_list is not None else []
        else:
            if updated_servant_list is not None:
                updates["svt"].extend(updated_servant_list)

        if not updates["cft"]:
            updates["cft"] = updated_cft_list if updated_cft_list is not None else []
        else:
            if updated_cft_list is not None:
                updates["cft"].extend(updated_cft_list)

        if not updates["cmd"]:
            updates["cmd"] = updated_cmd_list if updated_cmd_list is not None else []
        else:
            if updated_cmd_list is not None:
                updates["cmd"].extend(updated_cmd_list)

        for each_attr in updates:
            temp_list = copy.deepcopy(updates[each_attr])
            temp_list.sort()
            updates[each_attr] = temp_list

        with open(update_data_path, "w", encoding="utf-8") as f:
            f.write(json.dumps(updates, indent=2, ensure_ascii=False))

        sv_manage.logger.info("结束自动更新fgo")


@sv_manage.on_rex(re.compile(
    r"^[设s][置z][fb]go[时s][间j]"
    r"\s?(\d+(h((our)?s?)?|小时))?"
    r"\s?(\d+(m((inute)?s?)?|分钟))?"
    r"\s?(\d+(s((econd)?s?)?|秒))?$", re.IGNORECASE
))
async def set_update_time(bot: HoshinoBot, ev: CQEvent):
    if not priv.check_priv(ev, priv.ADMIN):
        await bot.send(ev, '此命令仅群管可用~')
        return

    msg = ev.message.extract_plain_text()
    times = msg.strip()

    configs = load_config(ev)

    rule_c = re.compile("^([设s][置z])?[fb]go[时s][间j]([设s][置z])?$", re.IGNORECASE)
    if re.search(rule_c, times[0]) and len(times) == 1:
        await bot.send(ev, "食用指南：设置fgo时间 + 小时 + 分钟 + 秒（至少存在一个）")
        await bot.send(ev, f"当前自动更新时间：{configs['flush_hour']}小时"
                           f"{configs['flush_minute']}分钟{configs['flush_second']}秒")
        return

    rule_h = re.compile(r"\d+(h((our)?s?)?|小时)", re.IGNORECASE)
    rule_m = re.compile(r"\d+(m((inute)?s?)?|分钟)", re.IGNORECASE)
    rule_s = re.compile(r"\d+(s((econd)?s?)?|秒)", re.IGNORECASE)

    for each in times:
        if re.findall(rule_h, each):
            hour = re.search(rule_h, each).group(0)
            hour = re.findall(r"\d+", hour)
            configs["flush_hour"] = int(hour[0])
        if re.findall(rule_m, each):
            minute = re.search(rule_m, each).group(0)
            minute = re.findall(r"\d+", minute)
            configs["flush_minute"] = int(minute[0])
        if re.findall(rule_s, each):
            second = re.search(rule_s, each).group(0)
            second = re.findall(r"\d+", second)
            configs["flush_second"] = int(second[0])

    with open(config_path, "w", encoding="utf-8") as f:
        f.write(json.dumps(configs, indent=2, ensure_ascii=False))

    reload_path = os.path.join(os.path.dirname(__file__), 'loop.py')
    count = Counter.count + 1
    _content = f"class Counter:\n    count = {count}\n"
    with open(reload_path, 'w') as f:
        f.write(_content)

    await bot.send(ev, f"设置完成，当前自动更新时间：{configs['flush_hour']}小时"
                       f"{configs['flush_minute']}分钟{configs['flush_second']}秒\n"
                       f"机器人重启中~")
    return
