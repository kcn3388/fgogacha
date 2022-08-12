import json
import os
import re

from hoshino import config
from .download import *

runtime_path = os.path.dirname(__file__)
basic_path = config.RES_DIR + "img/fgo/"
icon_path = basic_path + "icons/"
svt_path = icon_path + "svt_icons/"
cft_path = icon_path + "cft_icons/"
skill_path = icon_path + "skill_icons/"
cmd_path = icon_path + "cmd_icons/"
card_path = icon_path + "card_icons/"
class_path = icon_path + "class_icons/"

all_path = [svt_path, cft_path, skill_path, cmd_path, card_path, class_path]

svt_json = os.path.join(runtime_path, "data/all_svt.json")
cft_json = os.path.join(runtime_path, "data/all_cft.json")
cmd_json = os.path.join(runtime_path, "data/all_cmd.json")


async def download_all_res(crt_file=False):
    download_stat = 0
    basic_url = "https://fgo.wiki"
    for each in all_path:
        if not os.path.exists(each):
            os.mkdir(each)

    print("开始下载从者相关……")
    if os.path.exists(svt_path):
        try:
            with open(svt_json, 'r', encoding="utf-8") as f:
                svt = json.load(f)
            for i in svt:
                for j in i["online"]:
                    # 如果是从者
                    if j == "svt_icon":
                        download_stat = await download(
                            basic_url + i["online"][j], svt_path + i["local"][j], True, crt_file
                        )
                        if not isinstance(download_stat, int):
                            print("download icons error")
                            return download_stat
                    # 如果是指令卡
                    rule = re.compile(r"(ultimate|card\d)_icon")
                    if re.match(rule, j):
                        download_stat = await download(
                            basic_url + i["online"][j], card_path + i["local"][j], True, crt_file
                        )
                        if not isinstance(download_stat, int):
                            print("download icons error")
                            return download_stat
                    # 如果是职介
                    if j == "class_icon":
                        download_stat = await download(
                            basic_url + i["online"][j], class_path + i["local"][j], True, crt_file
                        )
                        if not isinstance(download_stat, int):
                            print("download icons error")
                            return
            if download_stat:
                print("没有更新数据……")
            else:
                print("从者下载完成")
        except json.decoder.JSONDecodeError:
            print("不存在从者数据……跳过")
    else:
        print("不存在从者数据……跳过")

    print("开始下载礼装相关……")
    if os.path.exists(cft_path):
        try:
            with open(cft_json, 'r', encoding="utf-8") as f:
                cft = json.load(f)
            for i in cft:
                for j in i["online"]:
                    # 如果是礼装
                    if j == "cft_icon":
                        download_stat = await download(
                            basic_url + i["online"][j], cft_path + i["local"][j], True, crt_file
                        )
                        if not isinstance(download_stat, int):
                            print("download icons error")
                            return download_stat
                    # 如果是技能
                    if j == "skill_icon":
                        download_stat = await download(
                            basic_url + i["online"][j], skill_path + i["local"][j], True, crt_file
                        )
                        if not isinstance(download_stat, int):
                            print("download icons error")
                            return
            if download_stat:
                print("没有更新数据……")
            else:
                print("礼装下载完成")
        except json.decoder.JSONDecodeError:
            print("不存在礼装数据……跳过")
    else:
        print("不存在礼装数据……跳过")

    print("开始下载纹章相关……")
    if os.path.exists(cft_path):
        try:
            with open(cmd_json, 'r', encoding="utf-8") as f:
                cmd = json.load(f)
            for i in cmd:
                for j in i["online"]:
                    # 如果是纹章
                    if j == "cmd_icon":
                        download_stat = await download(
                            basic_url + i["online"][j], cmd_path + i["local"][j], True, crt_file
                        )
                        if not isinstance(download_stat, int):
                            print("download icons error")
                            return download_stat
                    # 如果是技能
                    if j == "skill_icon":
                        download_stat = await download(
                            basic_url + i["online"][j], skill_path + i["local"][j], True, crt_file
                        )
                        if not isinstance(download_stat, int):
                            print("download icons error")
                            return
            if download_stat:
                print("没有更新数据……")
            else:
                print("纹章下载完成")
        except json.decoder.JSONDecodeError:
            print("不存在纹章数据……跳过")
    else:
        print("不存在纹章数据……跳过")

    if not isinstance(download_stat, int):
        print("存在下载错误~")
        return download_stat

    if download_stat:
        print("没有新的资源")
        return download_stat
    else:
        print("全部下载完成")
        return download_stat
