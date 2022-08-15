import json
import re

from .download import download
from .path_and_json import *


async def download_svt(crt_file=False):
    download_stat = 1
    basic_url = "https://fgo.wiki"
    for each in res_paths:
        if not os.path.exists(each):
            os.mkdir(each)

    print("开始下载从者相关……")
    if os.path.exists(svt_path):
        try:
            with open(all_servant_path, 'r', encoding="utf-8") as f:
                svt = json.load(f)
            for i in svt:
                for j in i["online"]:
                    # 如果是从者
                    if j == "svt_icon":
                        local = svt_path + i["local"][j]
                        online = basic_url + i["online"][j]
                        if os.path.exists(local):
                            continue
                        print(f"======开始下载：{local}======")
                        download_stat = await download(
                            online, local, True, crt_file
                        )
                        if not isinstance(download_stat, int):
                            print("download icons error, reason: " + str(download_stat))
                    # 如果是指令卡
                    rule = re.compile(r"(ultimate|card\d)_icon")
                    if re.match(rule, j):
                        local = card_path + i["local"][j]
                        online = basic_url + i["online"][j]
                        if os.path.exists(local):
                            continue
                        print(f"======开始下载：{local}======")
                        download_stat = await download(
                            online, local, True, crt_file
                        )
                        if not isinstance(download_stat, int):
                            print("download icons error, reason: " + str(download_stat))
                    # 如果是职介
                    if j == "class_icon":
                        local = class_path + i["local"][j]
                        online = basic_url + i["online"][j]
                        if os.path.exists(local):
                            continue
                        print(f"======开始下载：{local}======")
                        download_stat = await download(
                            online, local, True, crt_file
                        )
                        if not isinstance(download_stat, int):
                            print("download icons error, reason: " + str(download_stat))
        except json.decoder.JSONDecodeError:
            print("不存在从者数据……跳过")
    else:
        print("不存在从者数据……跳过")

    if not isinstance(download_stat, int):
        print("存在下载错误：" + str(download_stat))
        return download_stat

    if download_stat:
        print("没有新的资源")
        return download_stat
    else:
        print("从者下载完成")
        return download_stat


async def download_cft(crt_file=False):
    download_stat = 1
    basic_url = "https://fgo.wiki"
    for each in res_paths:
        if not os.path.exists(each):
            os.mkdir(each)

    print("开始下载礼装相关……")
    if os.path.exists(cft_path):
        try:
            with open(all_craft_path, 'r', encoding="utf-8") as f:
                cft = json.load(f)
            for i in cft:
                for j in i["online"]:
                    # 如果是礼装
                    if j == "cft_icon":
                        local = cft_path + i["local"][j]
                        online = basic_url + i["online"][j]
                        if os.path.exists(local):
                            continue
                        print(f"======开始下载：{local}======")
                        download_stat = await download(
                            online, local, True, crt_file
                        )
                        if not isinstance(download_stat, int):
                            print("download icons error, reason: " + str(download_stat))
                    # 如果是技能
                    if j == "skill_icon":
                        local = skill_path + i["local"][j]
                        online = basic_url + i["online"][j]
                        if os.path.exists(local):
                            continue
                        print(f"======开始下载：{local}======")
                        download_stat = await download(
                            online, local, True, crt_file
                        )
                        if not isinstance(download_stat, int):
                            print("download icons error, reason: " + str(download_stat))
        except json.decoder.JSONDecodeError:
            print("不存在礼装数据……跳过")
    else:
        print("不存在礼装数据……跳过")

    if not isinstance(download_stat, int):
        print("存在下载错误：" + str(download_stat))
        return download_stat

    if download_stat:
        print("没有新的资源")
        return download_stat
    else:
        print("礼装下载完成")
        return download_stat


async def download_cmd(crt_file=False):
    download_stat = 1
    basic_url = "https://fgo.wiki"
    for each in res_paths:
        if not os.path.exists(each):
            os.mkdir(each)

    print("开始下载纹章相关……")
    if os.path.exists(cft_path):
        try:
            with open(all_command_path, 'r', encoding="utf-8") as f:
                cmd = json.load(f)
            for i in cmd:
                for j in i["online"]:
                    # 如果是纹章
                    if j == "cmd_icon":
                        local = cmd_path + i["local"][j]
                        online = basic_url + i["online"][j]
                        if os.path.exists(local):
                            continue
                        print(f"======开始下载：{local}======")
                        download_stat = await download(
                            online, local, True, crt_file
                        )
                        if not isinstance(download_stat, int):
                            print("download icons error, reason: " + str(download_stat))
                    # 如果是技能
                    if j == "skill_icon":
                        local = skill_path + i["local"][j]
                        online = basic_url + i["online"][j]
                        if os.path.exists(local):
                            continue
                        print(f"======开始下载：{local}======")
                        download_stat = await download(
                            online, local, True, crt_file
                        )
                        if not isinstance(download_stat, int):
                            print("download icons error, reason: " + str(download_stat))
        except json.decoder.JSONDecodeError:
            print("不存在纹章数据……跳过")
    else:
        print("不存在纹章数据……跳过")

    if not isinstance(download_stat, int):
        print("存在下载错误：" + str(download_stat))
        return download_stat

    if download_stat:
        print("没有新的资源")
        return download_stat
    else:
        print("纹章下载完成")
        return download_stat
