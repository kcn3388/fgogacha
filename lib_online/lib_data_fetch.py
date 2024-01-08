import os.path

from bs4 import BeautifulSoup
from urllib.parse import quote

from .lib_json import *


async def fetch_mooncell(bot: HoshinoBot, ev: CQEvent, select: int, _id: int = 0, force: bool = False):
    if not os.path.exists(mc_path):
        os.mkdir(mc_path)
    crt_file = False
    if os.path.exists(config_path):
        try:
            configs = json.load(open(config_path, encoding="utf-8"))
            for each_group in configs["groups"]:
                if int(each_group) == ev.group_id:
                    if not configs["groups"][each_group]["crt_path"] == "False":
                        crt_file = os.path.join(crt_folder_path, configs["groups"][each_group]["crt_path"])
                        break
        except json.decoder.JSONDecodeError:
            pass
    try:
        if select == 1:
            with open(all_servant_path, 'r', encoding="utf-8") as f:
                card_data = json.load(f)
            folder_path = os.path.join(mc_path, "svt")
            if not os.path.exists(folder_path):
                os.mkdir(folder_path)
            card_type = "svt"
        elif select == 2:
            with open(all_craft_path, 'r', encoding="utf-8") as f:
                card_data = json.load(f)
            folder_path = os.path.join(mc_path, "cft")
            if not os.path.exists(folder_path):
                os.mkdir(folder_path)
            card_type = "cft"
        elif select == 3:
            with open(all_command_path, 'r', encoding="utf-8") as f:
                card_data = json.load(f)
            folder_path = os.path.join(mc_path, "cmd")
            if not os.path.exists(folder_path):
                os.mkdir(folder_path)
            card_type = "cmd"
        else:
            with open(all_servant_path, 'r', encoding="utf-8") as f:
                card_data = json.load(f)
            folder_path = os.path.join(mc_path, "svt")
            if not os.path.exists(folder_path):
                os.mkdir(folder_path)
            card_type = "svt"
    except json.decoder.JSONDecodeError:
        await bot.finish(ev, "本地没有数据~请先获取数据~\n指令：[更新fgo图书馆] 或 [获取全部内容]")
        return
    except FileNotFoundError:
        await bot.finish(ev, "本地没有数据~请先获取数据~\n指令：[更新fgo图书馆] 或 [获取全部内容]")
        return
    _ids = jsonpath(card_data, "$..id")
    links = jsonpath(card_data, "$..name_link")
    loss = []
    for index in range(len(_ids)):
        # for svt_index in range(2):
        if _id:
            index = _ids.index(str(_id))
        elif force:
            pass
        else:
            if os.path.exists(
                    os.path.join(folder_path, f"{_ids[index]}.html")
            ) or os.path.exists(
                os.path.join(folder_path, f"{_ids[index]}.txt")
            ):
                sv_lib.logger.info(f"Skip {card_type} {_ids[index]} since exists.")
                continue
        sv_lib.logger.info(f"Fetching {card_type} {_ids[index]}.")
        url = f"https://fgo.wiki/w/{quote(links[index], 'utf-8')}"
        root_url = f"https://fgo.wiki/index.php?title={quote(links[index], 'utf-8')}&action=edit"
        try:
            raw_html = await (await aiorequests.get(url, timeout=20, verify=crt_file, headers=headers)).text
            root_text = BeautifulSoup(
                await (await aiorequests.get(root_url, timeout=20, verify=crt_file, headers=headers)).text,
                'html.parser'
            ).find("textarea").text
        except aiorequests.exceptions.SSLError:
            try:
                raw_html = await (await aiorequests.get(url, timeout=20, headers=headers)).text
                root_text = BeautifulSoup(
                    await (await aiorequests.get(root_url, timeout=20, headers=headers)).text,
                    'html.parser'
                ).find("textarea").text
            except (
                    aiorequests.exceptions.ReadTimeout,
                    aiorequests.exceptions.ConnectionError,
                    aiorequests.exceptions.SSLError
            ):
                continue
        except aiorequests.exceptions.ReadTimeout:
            continue
        except Exception as e:
            sv_lib.logger.warning(f"Fetch {card_type} {_ids[index]} error: {e}")
            loss.append(_ids[index])
            if _id:
                break
            continue
        try:
            with open(os.path.join(folder_path, f"{_ids[index]}.html"), "w", encoding="utf-8") as mooncell_html:
                mooncell_html.write(raw_html)
            with open(os.path.join(folder_path, f"{_ids[index]}.txt"), "w", encoding="utf-8") as mooncell_raw:
                mooncell_raw.write(root_text)
        except Exception as e:
            sv_lib.logger.warning(f"Saving {card_type} {_ids[index]} error: {e}")
            loss.append(_ids[index])
            if _id:
                break
            continue
        if _id:
            break

    await bot.send(
        ev, f"已抓取完成{len(_ids)}项{card_type}资料~" if not _id else f"已抓取完成{card_type}{_id}的资料~"
    )
    await bot.send(ev, f"以下数据抓取失败：{loss}") if loss else ""
