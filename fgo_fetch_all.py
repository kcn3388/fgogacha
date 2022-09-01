import json

from hoshino import priv, Service
from . import CQEvent
from .download.download_all_res import download_svt, download_cft, download_cmd
from .get.get_all_cft import get_all_cft
from .get.get_all_cmd import get_all_cmd
from .get.get_all_svt import get_all_svt
from .path_and_json import *

sv_fetch_help = '''
# 数据管理相关
[获取全部内容] 获取从者/礼装/纹章的相关内容
- 从者包括职介和指令卡
- 礼装/纹章包括技能
- 子命令：
  - [获取全部从者]
  - [获取全部礼装]
  - [获取全部纹章]
[下载全部卡片资源] 从上述数据中下载对应静态资源
- 子命令：
  - [下载全部从者资源]
  - [下载全部礼装资源]
  - [下载全部纹章资源]
'''.strip()

sv_fetch = Service(
    name='fgo数据获取',
    help_=sv_fetch_help,
    bundle="娱乐",
    enable_on_default=True,
    visible=True,
    use_priv=priv.NORMAL,  # 使用权限
    manage_priv=priv.ADMIN,  # 管理权限
)


@sv_fetch.on_fullmatch(("帮助fgo数据获取", "帮助FGO数据获取", "帮助bgo数据获取", "帮助BGO数据获取"))
@sv_fetch.on_rex(r"(?i)^[fb]go[数s][据j][获h][取q][帮b][助z]$")
async def bangzhu(bot, ev):
    helps = gen_node(sv_fetch_help)
    await bot.send_group_forward_msg(group_id=ev['group_id'], messages=helps)


@sv_fetch.on_fullmatch("获取全部内容")
async def get_all_mooncell(bot, ev: CQEvent):
    if not priv.check_priv(ev, priv.ADMIN):
        await bot.finish(ev, '此命令仅群管可用~')
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

    sv_fetch.logger.info("开始获取从者")
    all_svt = await get_all_svt(crt_file)
    if not isinstance(all_svt, int):
        await bot.send(ev, f"获取全部从者出错，原因：{all_svt}")

    if all_svt:
        await bot.send(ev, "从者列表已是最新~稍后再来试试吧~")
    else:
        await bot.send(ev, "从者列表获取完成~")

    sv_fetch.logger.info("开始获取礼装")
    all_cft = await get_all_cft(crt_file)
    if not isinstance(all_cft, int):
        await bot.send(ev, f"获取全部礼装出错，原因：{all_cft}")

    if all_cft:
        await bot.send(ev, "礼装列表已是最新~稍后再来试试吧~")
    else:
        await bot.send(ev, "礼装列表获取完成~")

    sv_fetch.logger.info("开始获取纹章")
    all_cmd = await get_all_cmd(crt_file)
    if not isinstance(all_cmd, int):
        await bot.send(ev, f"获取全部纹章出错，原因：{all_cmd}")

    if all_cmd:
        await bot.send(ev, "纹章列表已是最新~稍后再来试试吧~")
    else:
        await bot.send(ev, "纹章列表获取完成~")


@sv_fetch.on_fullmatch("获取全部从者")
async def get_all_mooncell_svt(bot, ev: CQEvent):
    if not priv.check_priv(ev, priv.ADMIN):
        await bot.finish(ev, '此命令仅群管可用~')
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
    all_svt = await get_all_svt(crt_file)
    if not isinstance(all_svt, int):
        await bot.finish(ev, f"获取全部从者出错，原因：{all_svt}")

    if all_svt:
        await bot.finish(ev, "从者列表已是最新~稍后再来试试吧~")
    else:
        await bot.finish(ev, "从者列表获取完成~")


@sv_fetch.on_fullmatch("获取全部礼装")
async def get_all_mooncell_cft(bot, ev: CQEvent):
    if not priv.check_priv(ev, priv.ADMIN):
        await bot.finish(ev, '此命令仅群管可用~')
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
    all_cft = await get_all_cft(crt_file)
    if not isinstance(all_cft, int):
        await bot.finish(ev, f"获取全部礼装出错，原因：{all_cft}")

    if all_cft:
        await bot.finish(ev, "礼装列表已是最新~稍后再来试试吧~")
    else:
        await bot.finish(ev, "礼装列表获取完成~")


@sv_fetch.on_fullmatch("获取全部纹章")
async def get_all_mooncell_cmd(bot, ev: CQEvent):
    if not priv.check_priv(ev, priv.ADMIN):
        await bot.finish(ev, '此命令仅群管可用~')
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
    all_cmd = await get_all_cmd(crt_file)
    if not isinstance(all_cmd, int):
        await bot.finish(ev, f"获取全部纹章出错，原因：{all_cmd}")

    if all_cmd:
        await bot.finish(ev, "纹章列表已是最新~稍后再来试试吧~")
    else:
        await bot.finish(ev, "纹章列表获取完成~")


@sv_fetch.on_fullmatch("下载全部卡片资源")
async def down_all_card_res(bot, ev: CQEvent):
    if not priv.check_priv(ev, priv.ADMIN):
        await bot.finish(ev, '此命令仅群管可用~')
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

    await bot.send(ev, "开始下载，进度请查看后台~")
    # await bot.send(ev, "开始下载从者")
    svt_stat = await download_svt(crt_file)
    if not isinstance(svt_stat, int):
        await bot.finish(ev, f'下载从者资源失败，原因：\n{svt_stat}')
    if svt_stat:
        sv_fetch.logger.info('资源没有更新，跳过……')
        await bot.send(ev, "从者资源已是最新~稍后再来试试吧~")
    else:
        sv_fetch.logger.info("下载从者完成")
        await bot.send(ev, "下载从者完成~")

    # await bot.send(ev, "开始下载礼装")
    cft_stat = await download_cft(crt_file)
    if not isinstance(cft_stat, int):
        await bot.finish(ev, f'下载礼装资源失败，原因：\n{cft_stat}')
    if cft_stat:
        sv_fetch.logger.info('资源没有更新，跳过……')
        await bot.send(ev, "礼装资源已是最新~稍后再来试试吧~")
    else:
        sv_fetch.logger.info("下载礼装完成")
        await bot.send(ev, "下载礼装完成~")

    # await bot.send(ev, "开始下载纹章")
    cmd_stat = await download_cmd(crt_file)
    if not isinstance(cmd_stat, int):
        await bot.finish(ev, f'下载纹章资源失败，原因：\n{cmd_stat}')
    if cmd_stat:
        sv_fetch.logger.info('资源没有更新，跳过……')
        await bot.send(ev, "纹章资源已是最新~稍后再来试试吧~")
    else:
        sv_fetch.logger.info("下载纹章完成")
        await bot.send(ev, "下载纹章完成~")

    # await bot.finish(ev, "下载完成")


@sv_fetch.on_fullmatch("下载全部从者资源")
async def down_all_card_res(bot, ev: CQEvent):
    if not priv.check_priv(ev, priv.ADMIN):
        await bot.finish(ev, '此命令仅群管可用~')
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

    await bot.send(ev, "开始下载，进度请查看后台~")
    # await bot.send(ev, "开始下载从者")
    svt_stat = await download_svt(crt_file)
    if not isinstance(svt_stat, int):
        await bot.finish(ev, f'下载从者资源失败，原因：\n{svt_stat}')
    if svt_stat:
        sv_fetch.logger.info('资源没有更新，跳过……')
        await bot.send(ev, "从者资源已是最新~稍后再来试试吧~")
    else:
        sv_fetch.logger.info("下载从者完成")
        await bot.send(ev, "下载从者完成~")


@sv_fetch.on_fullmatch("下载全部礼装资源")
async def down_all_card_res(bot, ev: CQEvent):
    if not priv.check_priv(ev, priv.ADMIN):
        await bot.finish(ev, '此命令仅群管可用~')
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

    await bot.send(ev, "开始下载，进度请查看后台~")
    # await bot.send(ev, "开始下载礼装")
    cft_stat = await download_cft(crt_file)
    if not isinstance(cft_stat, int):
        await bot.finish(ev, f'下载礼装资源失败，原因：\n{cft_stat}')
    if cft_stat:
        sv_fetch.logger.info('资源没有更新，跳过……')
        await bot.send(ev, "礼装资源已是最新~稍后再来试试吧~")
    else:
        sv_fetch.logger.info("下载礼装完成")
        await bot.send(ev, "下载礼装完成~")


@sv_fetch.on_fullmatch("下载全部纹章资源")
async def down_all_card_res(bot, ev: CQEvent):
    if not priv.check_priv(ev, priv.ADMIN):
        await bot.finish(ev, '此命令仅群管可用~')
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

    await bot.send(ev, "开始下载，进度请查看后台~")
    # await bot.send(ev, "开始下载纹章")
    cmd_stat = await download_cmd(crt_file)
    if not isinstance(cmd_stat, int):
        await bot.finish(ev, f'下载纹章资源失败，原因：\n{cmd_stat}')
    if cmd_stat:
        sv_fetch.logger.info('资源没有更新，跳过……')
        await bot.send(ev, "纹章资源已是最新~稍后再来试试吧~")
    else:
        sv_fetch.logger.info("下载纹章完成")
        await bot.send(ev, "下载纹章完成~")
