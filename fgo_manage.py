import json
import re

from hoshino import priv, Service
from hoshino.typing import CQEvent
from .download import download
from .downloadIcons import downloadicons
from .fgo_news import get_news
from .getGachaPools import getgachapools
from .loop import Counter  # 借助 use_reloader 实现当模块发生变化时自动重载整个 Python
from .path_and_json import *

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
except KeyError:
    pass

sv_manage_help = '''
# 抽卡管理命令:
[fgo数据初始化] 初始化数据文件及目录，务必安装后先执行此命令！
[fgo数据下载] 下载从者及礼装图标，务必先初始化数据再执行下载！
[跟随最新/剧情卡池] 设置卡池数据更新后跟随最新国服卡池还是国服剧情卡池
[fgo_enable_crt + crt文件路径] 为下载配置crt文件以规避拒绝访问，留空为默认，False为禁用
[fgo_check_crt] 检查本群crt文件配置状态
[设置fgo时间 + 小时 + 分钟 + 秒] 设置自动更新时间间隔，至少输入其中一个参数
- 例如：``设置fgo时间 1小时60分钟60秒``
'''.strip()

sv_manage = Service(
    name='fgo管理',
    help_=sv_manage_help,
    bundle="娱乐",
    enable_on_default=True,
    visible=True,
    use_priv=priv.NORMAL,  # 使用权限
    manage_priv=priv.ADMIN,  # 管理权限
)


@sv_manage.on_fullmatch(("帮助fgo管理", "帮助FGO管理", "帮助bgo管理", "帮助BGO管理"))
@sv_manage.on_rex(r"(?i)^[fb]go[管g][理l][帮b][助z]$")
async def bangzhu(bot, ev):
    _name = "涩茄子"
    _uin = "2087332430"
    helps = {
        "type": "node",
        "data": {
            "name": _name,
            "uin": _uin,
            "content": sv_manage_help
        }
    }
    await bot.send_group_forward_msg(group_id=ev['group_id'], messages=helps)


@sv_manage.on_rex(r"(?i)^[fb]go[数s][据j][初ci][始sn][化hi]$")
async def init(bot, ev: CQEvent):
    if not priv.check_priv(ev, priv.ADMIN):
        await bot.finish(ev, '此命令仅群管可用~')
    if not os.path.exists(os.path.join(crt_folder_path, crt_path)):
        await bot.finish(ev, "未配置默认crt文件！请从GitHub获取默认crt文件再运行此插件！")
    if not os.path.exists(basic_path):
        sv_manage.logger.info("数据初始化...")
        sv_manage.logger.info("初始化资源根目录...")
        os.mkdir(basic_path)
    for each in res_paths:
        if not os.path.exists(each):
            sv_manage.logger.info(f"初始化{str(each)}...")
            os.mkdir(each)
    if not os.path.exists(data_path):
        sv_manage.logger.info("初始化data目录...")
        os.mkdir(data_path)
    for each in all_json:
        if not os.path.exists(each):
            sv_manage.logger.info("初始化配置文件json...")
            open(each, 'w')
            if each == config_path:
                basic_config = {
                    "group": ev.group_id,
                    "crt_path": crt_path
                }
                configs = {
                    "follow_latest": FOLLOW_LATEST_POOL,
                    "flush_hour": flush_hour,
                    "flush_minute": flush_minute,
                    "flush_second": flush_second,
                    "groups": [basic_config]
                }
                with open(config_path, "w", encoding="utf-8") as f:
                    f.write(json.dumps(configs, indent=2, ensure_ascii=False))

    msg = "初始化完成！"
    await bot.send(ev, msg)


@sv_manage.on_rex(r"(?i)^([下xd][载zl])?[fb]go[数s][据j]([下xd][载zl])?$")
async def get_fgo_data(bot, ev: CQEvent):
    if not priv.check_priv(ev, priv.ADMIN):
        await bot.finish(ev, '此命令仅群管可用~')
    if not os.path.exists(basic_path) or not os.path.exists(data_path):
        sv_manage.logger.info("资源路径未初始化...")
        await bot.finish(ev, "资源路径未初始化！请先初始化资源路径\n指令：fgo数据初始化")

    sv_manage.logger.info("Downloaded bg-mc-icon.png")
    await bot.send(ev, "开始下载....")
    sv_manage.logger.info("开始下载bg")

    crt_file = False
    if os.path.exists(config_path):
        try:
            configs = json.load(open(config_path, encoding="utf-8"))
            for each in configs["groups"]:
                if each["group"] == ev.group_id:
                    if not crt_file == "False":
                        crt_file = os.path.join(crt_folder_path, each["crt_path"])
                        break
        except json.decoder.JSONDecodeError:
            pass

    bg_stat = await download(mooncellBackgroundUrl, mooncellBackgroundPath, False, crt_file)
    if not isinstance(bg_stat, int):
        await bot.send(ev, f'下载bg失败，原因：\n{bg_stat}')
    if bg_stat:
        sv_manage.logger.info(f'bg已存在，跳过……')
    sv_manage.logger.info("开始下载icon")
    icon_stat = await downloadicons(crt_file)
    if not isinstance(icon_stat, int):
        await bot.send(ev, f'下载icons失败，原因：\n{icon_stat}')
    if icon_stat:
        sv_manage.logger.info(f'icon没有更新，跳过……')

    if bg_stat and icon_stat:
        await bot.send(ev, "没有新的资源~晚点再来看看吧~")
    else:
        await bot.send(ev, "下载完成")


@sv_manage.on_rex(r"(?i)^([获h更g][取q新x])?[fb]go[卡k][池c]([获h更g][取q新x])?$")
async def get_fgo_pool(bot, ev: CQEvent):
    global FOLLOW_LATEST_POOL
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
                "follow_latest": FOLLOW_LATEST_POOL,
                "flush_hour": flush_hour,
                "flush_minute": flush_minute,
                "flush_second": flush_second,
                "groups": [basic_config]
            }
            with open(config_path, "w", encoding="utf-8") as f:
                f.write(json.dumps(configs, indent=2, ensure_ascii=False))

        FOLLOW_LATEST_POOL = configs["follow_latest"]
        for each in configs["groups"]:
            if each["group"] == ev.group_id:
                if not crt_file == "False":
                    crt_file = os.path.join(crt_folder_path, each["crt_path"])
                    break
    download_stat = await getgachapools(FOLLOW_LATEST_POOL, crt_file)
    if not isinstance(download_stat, int):
        await bot.finish(ev, f'更新失败，原因：\n{download_stat}')
    if not download_stat:
        await bot.send(ev, "获取卡池完成")
    elif download_stat:
        await bot.send(ev, "本地卡池和线上卡池是一样的啦~\n晚点再来看看吧~")


@sv_manage.on_rex(r"(?i)^[g跟][s随][z最j剧][x新q情][k卡][c池]$")
async def follow_latest(bot, ev: CQEvent):
    if not priv.check_priv(ev, priv.ADMIN):
        await bot.finish(ev, '此命令仅群管可用~')
    global FOLLOW_LATEST_POOL
    args = ev.message.extract_plain_text()
    if not os.path.exists(config_path):
        sv_manage.logger.info("初始化配置文件json...")
        open(config_path, 'w')
        basic_config = {
            "group": ev.group_id,
            "crt_path": crt_path
        }
        configs = {
            "follow_latest": FOLLOW_LATEST_POOL,
            "flush_hour": flush_hour,
            "flush_minute": flush_minute,
            "flush_second": flush_second,
            "groups": [basic_config]
        }
    else:
        try:
            configs = json.load(open(config_path, encoding="utf-8"))
        except json.decoder.JSONDecodeError:
            basic_config = {
                "group": ev.group_id,
                "crt_path": crt_path
            }
            configs = {
                "follow_latest": FOLLOW_LATEST_POOL,
                "groups": [basic_config]
            }
            with open(config_path, "w", encoding="utf-8") as f:
                f.write(json.dumps(configs, indent=2, ensure_ascii=False))

    rule_latest = re.compile(r"(?i)^[g跟][s随][z最][x新][k卡][c池]$")
    rule_story = re.compile(r"(?i)^[g跟][s随][j剧][q情][k卡][c池]$")
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


@sv_manage.on_prefix("fgo_enable_crt")
async def enable_crt(bot, ev: CQEvent):
    if not priv.check_priv(ev, priv.SUPERUSER):
        await bot.finish(ev, '此命令仅主さま可用~')
    crt = ev.message.extract_plain_text()

    if crt == "":
        await bot.send(ev, "食用指南：指令 + crt文件路径，留空设置为默认路径")
        crt = crt_path

    rule = re.compile(r"^(?i)false$")
    match = re.match(rule, crt)
    if match:
        crt = "False"

    if not os.path.exists(config_path):
        sv_manage.logger.info("初始化配置文件json...")
        open(config_path, 'w')
        basic_config = {
            "group": ev.group_id,
            "crt_path": crt_path
        }
        configs = {
            "follow_latest": FOLLOW_LATEST_POOL,
            "flush_hour": flush_hour,
            "flush_minute": flush_minute,
            "flush_second": flush_second,
            "groups": [basic_config]
        }
    else:
        try:
            configs = json.load(open(config_path, encoding="utf-8"))
        except json.decoder.JSONDecodeError:
            basic_config = {
                "group": ev.group_id,
                "crt_path": crt_path
            }
            configs = {
                "follow_latest": FOLLOW_LATEST_POOL,
                "flush_hour": flush_hour,
                "flush_minute": flush_minute,
                "flush_second": flush_second,
                "groups": [basic_config]
            }
            with open(config_path, "w", encoding="utf-8") as f:
                f.write(json.dumps(configs, indent=2, ensure_ascii=False))

    crt_config = {
        "group": ev.group_id,
        "crt_path": crt
    }

    exists = False
    for each in configs["groups"]:
        if each["group"] == ev.group_id:
            each["crt_path"] = crt
            exists = True
            break

    if not exists:
        configs["groups"].append(crt_config)

    with open(config_path, "w", encoding="utf-8") as f:
        f.write(json.dumps(configs, indent=2, ensure_ascii=False))

    if not crt == "False":
        await bot.finish(ev, f"已配置crt文件，文件路径：{crt}")
    else:
        await bot.finish(ev, f"已禁用crt文件")


@sv_manage.on_fullmatch("fgo_check_crt")
async def enable_crt(bot, ev: CQEvent):
    if not priv.check_priv(ev, priv.SUPERUSER):
        await bot.finish(ev, '此命令仅主さま可用~')

    if not os.path.exists(config_path):
        await bot.finish(ev, "未配置crt文件")

    try:
        configs = json.load(open(config_path, encoding="utf-8"))
    except json.decoder.JSONDecodeError:
        basic_config = {
            "group": ev.group_id,
            "crt_path": crt_path
        }
        configs = {
            "follow_latest": FOLLOW_LATEST_POOL,
            "flush_hour": flush_hour,
            "flush_minute": flush_minute,
            "flush_second": flush_second,
            "groups": [basic_config]
        }
        with open(config_path, "w", encoding="utf-8") as f:
            f.write(json.dumps(configs, indent=2, ensure_ascii=False))

    crt_config = {}

    exists = False
    for each in configs["groups"]:
        if each["group"] == ev.group_id:
            exists = True
            crt_config = each
            break
    if not exists:
        await bot.finish(ev, "本群未配置crt")
    else:
        if crt_config['crt_path'] == "False":
            await bot.finish(ev, "本群已禁用crt文件")
        else:
            await bot.finish(ev, f"本群已配置crt文件，文件路径：{crt_config['crt_path']}")


@sv_manage.scheduled_job('interval', hours=flush_hour, minutes=flush_minute, seconds=flush_second)
async def update_pool():
    if not os.path.exists(data_path):
        sv_manage.logger.info("资源未初始化……结束")
        return
    sv_manage.logger.info("开始自动更新fgo")

    # 寻找crt
    if not os.path.exists(config_path):
        crt_file = os.path.join(crt_folder_path, crt_path)
        if not os.path.exists(crt_file):
            crt_file = False
    else:
        try:
            configs = json.load(open(config_path, encoding="utf-8"))
            crt_file = configs["groups"][0]["crt_path"]
            if not crt_file == "False":
                crt_file = os.path.join(crt_folder_path, crt_file)
            else:
                crt_file = os.path.join(crt_folder_path, crt_path)
                if not os.path.exists(crt_file):
                    crt_file = False
        except json.decoder.JSONDecodeError:
            crt_file = os.path.join(crt_folder_path, crt_path)
            if not os.path.exists(crt_file):
                crt_file = False

    # 自动更新卡池
    r = await getgachapools(True, crt_file)
    if not isinstance(r, int):
        sv_manage.logger.warning(f"获取卡池失败，原因：{str(r)}")

    # 自动更新新闻
    news, same = await get_news(6, crt_file)
    if not isinstance(same, bool) and news == -100:
        sv_manage.logger.warning(f"获取新闻失败，原因：{str(same)}")

    # 自动下载资源
    bg_stat = await download(mooncellBackgroundUrl, mooncellBackgroundPath, True, crt_file)
    if not isinstance(bg_stat, int):
        sv_manage.logger.warning(f'下载bg失败，原因：{bg_stat}')
    if bg_stat:
        sv_manage.logger.info(f'bg已存在，跳过……')
    icon_stat = await downloadicons(crt_file)
    if not isinstance(icon_stat, int):
        sv_manage.logger.warning(f'下载icons失败，原因：{icon_stat}')
    if icon_stat:
        sv_manage.logger.info(f'icon没有更新，跳过……')

    sv_manage.logger.info("结束自动更新fgo")


@sv_manage.on_rex(r"(?i)^([设s][置z])?[fb]go[时s][间j]([设s][置z])?"
                  r"\s?(\d+(h((our)?s?)?|小时))?"
                  r"\s?(\d+(m((inute)?s?)?|分钟))?"
                  r"\s?(\d+(s((econd)?s?)?|秒))?$")
async def set_update_time(bot, ev: CQEvent):
    if not priv.check_priv(ev, priv.ADMIN):
        await bot.finish(ev, '此命令仅群管可用~')
    msg = ev.message.extract_plain_text()
    times = msg.split(" ")
    try:
        configs = json.load(open(config_path, encoding="utf-8"))
    except json.decoder.JSONDecodeError:
        basic_config = {
            "group": ev.group_id,
            "crt_path": crt_path
        }
        configs = {
            "follow_latest": FOLLOW_LATEST_POOL,
            "flush_hour": flush_hour,
            "flush_minute": flush_minute,
            "flush_second": flush_second,
            "groups": [basic_config]
        }
    rule_c = re.compile("(?i)^([设s][置z])?[fb]go[时s][间j]([设s][置z])?$")
    if re.search(rule_c, times[0]) and len(times) == 1:
        await bot.send(ev, "食用指南：设置fgo时间 + 小时 + 分钟 + 秒（至少存在一个）")
        await bot.finish(ev, f"当前自动更新时间：{configs['flush_hour']}小时"
                             f"{configs['flush_minute']}分钟{configs['flush_second']}秒")

    rule_h = re.compile(r"(?i)\d+(h((our)?s?)?|小时)")
    rule_m = re.compile(r"(?i)\d+(m((inute)?s?)?|分钟)")
    rule_s = re.compile(r"(?i)\d+(s((econd)?s?)?|秒)")

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

    await bot.finish(ev, f"设置完成，当前自动更新时间：{configs['flush_hour']}小时"
                         f"{configs['flush_minute']}分钟{configs['flush_second']}秒\n"
                         f"机器人重启中~")
