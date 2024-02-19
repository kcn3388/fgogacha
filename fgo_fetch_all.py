import copy
from aiocqhttp import ActionFailed

from hoshino import HoshinoBot
from .download.download_all_res import *
from .get.get_all_cft import *
from .get.get_all_cmd import *
from .get.get_all_svt import *


@sv_fetch.on_fullmatch(("帮助fgo数据获取", "帮助FGO数据获取", "帮助bgo数据获取", "帮助BGO数据获取"))
@sv_fetch.on_rex(re.compile(r"^[fb]go[数s][据j][获h][取q][帮b][助z]$", re.IGNORECASE))
async def bangzhu(bot: HoshinoBot, ev: CQEvent):
    helps = gen_node(sv_fetch_help)
    await bot.send_group_forward_msg(group_id=ev['group_id'], messages=helps)


@sv_fetch.on_fullmatch("获取全部内容")
async def get_all_mooncell(bot: HoshinoBot, ev: CQEvent):
    if not priv.check_priv(ev, priv.ADMIN):
        await bot.send(ev, '此命令仅群管可用~')
        return

    async with ClientSession(headers=headers) as session:
        sv_fetch.logger.info("开始获取从者")
        all_svt, updated_servant_list = await get_all_svt(session)
        if not isinstance(all_svt, int):
            await bot.send(ev, f"获取全部从者出错，原因：{all_svt}")

        if all_svt:
            await bot.send(ev, "从者列表已是最新~稍后再来试试吧~")
        else:
            await bot.send(ev, "从者列表获取完成~")
            msg = "本次更新的从者："
            for each_servant_id in updated_servant_list:
                msg += f"{each_servant_id}\t"
            try:
                await bot.send(ev, msg.strip())
            except ActionFailed:
                await bot.send(ev, "更新列表太长，请自行查询文件")

        sv_fetch.logger.info("开始获取礼装")
        all_cft, updated_cft_list = await get_all_cft(session)
        if not isinstance(all_cft, int):
            await bot.send(ev, f"获取全部礼装出错，原因：{all_cft}")

        if all_cft:
            await bot.send(ev, "礼装列表已是最新~稍后再来试试吧~")
        else:
            await bot.send(ev, "礼装列表获取完成~")
            msg = "本次更新的礼装："
            for each_cft_id in updated_cft_list:
                msg += f"{each_cft_id}\t"
            try:
                await bot.send(ev, msg.strip())
            except ActionFailed:
                await bot.send(ev, "更新列表太长，请自行查询文件")

        sv_fetch.logger.info("开始获取纹章")
        all_cmd, updated_cmd_list = await get_all_cmd(session)
        if not isinstance(all_cmd, int):
            await bot.send(ev, f"获取全部纹章出错，原因：{all_cmd}")

        if all_cmd:
            await bot.send(ev, "纹章列表已是最新~稍后再来试试吧~")
        else:
            await bot.send(ev, "纹章列表获取完成~")
            msg = "本次更新的纹章："
            for each_cmd_id in updated_cmd_list:
                msg += f"{each_cmd_id}\t"
            try:
                await bot.send(ev, msg.strip())
            except ActionFailed:
                await bot.send(ev, "更新列表太长，请自行查询文件")

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


@sv_fetch.on_fullmatch("获取全部从者")
async def get_all_mooncell_svt(bot: HoshinoBot, ev: CQEvent):
    if not priv.check_priv(ev, priv.ADMIN):
        await bot.send(ev, '此命令仅群管可用~')
        return

    async with ClientSession(headers=headers) as session:
        all_svt, updated_servant_list = await get_all_svt(session)
        if not isinstance(all_svt, int):
            await bot.send(ev, f"获取全部从者出错，原因：{all_svt}")
            return

        if all_svt:
            await bot.send(ev, "从者列表已是最新~稍后再来试试吧~")
            return

        else:
            await bot.send(ev, "从者列表获取完成~")
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

            temp_list = copy.deepcopy(updates["svt"])
            temp_list.sort()
            updates["svt"] = temp_list

            with open(update_data_path, "w", encoding="utf-8") as f:
                f.write(json.dumps(updates, indent=2, ensure_ascii=False))
            msg = "本次更新的从者："
            for each_servant_id in updated_servant_list:
                msg += f"{each_servant_id}\t"
            try:
                await bot.send(ev, msg.strip())
            except ActionFailed:
                await bot.send(ev, "更新列表太长，请自行查询文件")
            return


@sv_fetch.on_fullmatch("获取全部礼装")
async def get_all_mooncell_cft(bot: HoshinoBot, ev: CQEvent):
    if not priv.check_priv(ev, priv.ADMIN):
        await bot.send(ev, '此命令仅群管可用~')
        return

    async with ClientSession(headers=headers) as session:
        all_cft, updated_cft_list = await get_all_cft(session)
        if not isinstance(all_cft, int):
            await bot.send(ev, f"获取全部礼装出错，原因：{all_cft}")
            return

        if all_cft:
            await bot.send(ev, "礼装列表已是最新~稍后再来试试吧~")
            return

        else:
            await bot.send(ev, "礼装列表获取完成~")
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

            if not updates["cft"]:
                updates["cft"] = updated_cft_list if updated_cft_list is not None else []
            else:
                if updated_cft_list is not None:
                    updates["cft"].extend(updated_cft_list)

            temp_list = copy.deepcopy(updates["cft"])
            temp_list.sort()
            updates["cft"] = temp_list

            with open(update_data_path, "w", encoding="utf-8") as f:
                f.write(json.dumps(updates, indent=2, ensure_ascii=False))
            msg = "本次更新的礼装："
            for each_cft_id in updated_cft_list:
                msg += f"{each_cft_id}\t"
            try:
                await bot.send(ev, msg.strip())
            except ActionFailed:
                await bot.send(ev, "更新列表太长，请自行查询文件")
            return


@sv_fetch.on_fullmatch("获取全部纹章")
async def get_all_mooncell_cmd(bot: HoshinoBot, ev: CQEvent):
    if not priv.check_priv(ev, priv.ADMIN):
        await bot.send(ev, '此命令仅群管可用~')
        return

    async with ClientSession(headers=headers) as session:
        all_cmd, updated_cmd_list = await get_all_cmd(session)
        if not isinstance(all_cmd, int):
            await bot.send(ev, f"获取全部纹章出错，原因：{all_cmd}")
            return

        if all_cmd:
            await bot.send(ev, "纹章列表已是最新~稍后再来试试吧~")
            return

        else:
            await bot.send(ev, "纹章列表获取完成~")
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

            if not updates["cmd"]:
                updates["cmd"] = updated_cmd_list if updated_cmd_list is not None else []
            else:
                if updated_cmd_list is not None:
                    updates["cmd"].extend(updated_cmd_list)

            temp_list = copy.deepcopy(updates["cmd"])
            temp_list.sort()
            updates["cmd"] = temp_list

            with open(update_data_path, "w", encoding="utf-8") as f:
                f.write(json.dumps(updates, indent=2, ensure_ascii=False))
            msg = "本次更新的纹章："
            for each_cmd_id in updated_cmd_list:
                msg += f"{each_cmd_id}\t"
            try:
                await bot.send(ev, msg.strip())
            except ActionFailed:
                await bot.send(ev, "更新列表太长，请自行查询文件")
            return


@sv_fetch.on_fullmatch("下载全部卡片资源")
async def down_all_card_res(bot: HoshinoBot, ev: CQEvent):
    if not priv.check_priv(ev, priv.ADMIN):
        await bot.send(ev, '此命令仅群管可用~')
        return

    async with ClientSession(headers=headers) as session:
        await bot.send(ev, "开始下载，进度请查看后台~")
        # await bot.send(ev, "开始下载从者")
        svt_stat = await download_svt(session)
        if not isinstance(svt_stat, int):
            await bot.send(ev, f'下载从者资源失败，原因：\n{svt_stat}')
            return

        if svt_stat:
            sv_fetch.logger.info('资源没有更新，跳过……')
            await bot.send(ev, "从者资源已是最新~稍后再来试试吧~")
        else:
            sv_fetch.logger.info("下载从者完成")
            await bot.send(ev, "下载从者完成~")

        # await bot.send(ev, "开始下载礼装")
        cft_stat = await download_cft(session)
        if not isinstance(cft_stat, int):
            await bot.send(ev, f'下载礼装资源失败，原因：\n{cft_stat}')
            return

        if cft_stat:
            sv_fetch.logger.info('资源没有更新，跳过……')
            await bot.send(ev, "礼装资源已是最新~稍后再来试试吧~")
        else:
            sv_fetch.logger.info("下载礼装完成")
            await bot.send(ev, "下载礼装完成~")

        # await bot.send(ev, "开始下载纹章")
        cmd_stat = await download_cmd(session)
        if not isinstance(cmd_stat, int):
            await bot.send(ev, f'下载纹章资源失败，原因：\n{cmd_stat}')
            return

        if cmd_stat:
            sv_fetch.logger.info('资源没有更新，跳过……')
            await bot.send(ev, "纹章资源已是最新~稍后再来试试吧~")
        else:
            sv_fetch.logger.info("下载纹章完成")
            await bot.send(ev, "下载纹章完成~")

        # await bot.send(ev, "开始下载技能图标")
        icon_stat = await download_icon_skill(session)
        if not isinstance(icon_stat, int):
            await bot.send(ev, f'下载技能图标资源失败，原因：\n{icon_stat}')
            return

        if icon_stat:
            sv_fetch.logger.info('资源没有更新，跳过……')
            await bot.send(ev, "技能图标资源已是最新~稍后再来试试吧~")
        else:
            sv_fetch.logger.info("下载技能图标完成")
            await bot.send(ev, "下载技能图标完成~")


@sv_fetch.on_fullmatch("下载全部从者资源")
async def down_all_card_res(bot: HoshinoBot, ev: CQEvent):
    if not priv.check_priv(ev, priv.ADMIN):
        await bot.send(ev, '此命令仅群管可用~')
        return

    async with ClientSession(headers=headers) as session:
        await bot.send(ev, "开始下载，进度请查看后台~")
        # await bot.send(ev, "开始下载从者")
        svt_stat = await download_svt(session)
        if not isinstance(svt_stat, int):
            await bot.send(ev, f'下载从者资源失败，原因：\n{svt_stat}')
            return

        if svt_stat:
            sv_fetch.logger.info('资源没有更新，跳过……')
            await bot.send(ev, "从者资源已是最新~稍后再来试试吧~")
        else:
            sv_fetch.logger.info("下载从者完成")
            await bot.send(ev, "下载从者完成~")


@sv_fetch.on_fullmatch("下载全部礼装资源")
async def down_all_card_res(bot: HoshinoBot, ev: CQEvent):
    if not priv.check_priv(ev, priv.ADMIN):
        await bot.send(ev, '此命令仅群管可用~')
        return

    async with ClientSession(headers=headers) as session:
        await bot.send(ev, "开始下载，进度请查看后台~")
        # await bot.send(ev, "开始下载礼装")
        cft_stat = await download_cft(session)
        if not isinstance(cft_stat, int):
            await bot.send(ev, f'下载礼装资源失败，原因：\n{cft_stat}')
            return

        if cft_stat:
            sv_fetch.logger.info('资源没有更新，跳过……')
            await bot.send(ev, "礼装资源已是最新~稍后再来试试吧~")
        else:
            sv_fetch.logger.info("下载礼装完成")
            await bot.send(ev, "下载礼装完成~")


@sv_fetch.on_fullmatch("下载全部纹章资源")
async def down_all_card_res(bot: HoshinoBot, ev: CQEvent):
    if not priv.check_priv(ev, priv.ADMIN):
        await bot.send(ev, '此命令仅群管可用~')
        return

    async with ClientSession(headers=headers) as session:
        await bot.send(ev, "开始下载，进度请查看后台~")
        # await bot.send(ev, "开始下载纹章")
        cmd_stat = await download_cmd(session)
        if not isinstance(cmd_stat, int):
            await bot.send(ev, f'下载纹章资源失败，原因：\n{cmd_stat}')
            return

        if cmd_stat:
            sv_fetch.logger.info('资源没有更新，跳过……')
            await bot.send(ev, "纹章资源已是最新~稍后再来试试吧~")
        else:
            sv_fetch.logger.info("下载纹章完成")
            await bot.send(ev, "下载纹章完成~")


@sv_fetch.on_fullmatch("下载全部图标资源")
async def down_all_icon_res(bot: HoshinoBot, ev: CQEvent):
    if not priv.check_priv(ev, priv.ADMIN):
        await bot.send(ev, '此命令仅群管可用~')
        return

    async with ClientSession(headers=headers) as session:
        await bot.send(ev, "开始下载，进度请查看后台~")
        # await bot.send(ev, "开始下载技能图标")
        icon_stat = await download_icon_skill(session)
        if not isinstance(icon_stat, int):
            await bot.send(ev, f'下载技能图标资源失败，原因：\n{icon_stat}')
            return

        if icon_stat:
            sv_fetch.logger.info('资源没有更新，跳过……')
            await bot.send(ev, "技能图标资源已是最新~稍后再来试试吧~")
        else:
            sv_fetch.logger.info("下载技能图标完成")
            await bot.send(ev, "下载技能图标完成~")

# updates = json.load(open(update_data_path, encoding="utf-8"))
# for each_attr in updates:
#     updates[each_attr] = [int(x) for x in updates[each_attr]]
#     updates[each_attr].sort()
#
# with open(update_data_path, "w", encoding="utf-8") as f:
#     f.write(json.dumps(updates, indent=2, ensure_ascii=False))
