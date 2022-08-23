import json
import re

from .download import download
from ..path_and_json import *


async def downloadicons(crt_file=False):
    download_stat = 1
    if not os.path.exists(svt_path):
        os.mkdir(svt_path)
    if not os.path.exists(cft_path):
        os.mkdir(cft_path)
    try:
        with open(icons_path, 'r', encoding="utf-8") as f:
            icons = json.load(f)
    except json.decoder.JSONDecodeError:
        icons = {
            "svtIcons": [],
            "cftIcons": [],
        }
    basic_url = "https://fgo.wiki"
    rule = re.compile("Servant.+jpg")
    print("从者路径解析完成")
    rule2 = re.compile("礼装.+jpg")
    print("礼装路径解析完成")
    try:
        for i in icons["svtIcons"]:
            ret = re.search(rule, i).group(0)
            if os.path.exists(svt_path + ret):
                continue
            download_stat = await download(basic_url + i, svt_path + ret, True, crt_file)
            if not isinstance(download_stat, int):
                print("download icons error, reason:" + str(download_stat))
        for j in icons["cftIcons"]:
            ret = re.search(rule2, j).group(0)
            if os.path.exists(cft_path + ret):
                continue
            download_stat = await download(basic_url + j, cft_path + ret, True, crt_file)
            if not isinstance(download_stat, int):
                print("download icons error, reason:" + str(download_stat))
        print("finish download icons")
        return download_stat
    except OSError:
        for i in icons["svtIcons"]:
            ret = re.search(rule, i).group(0)
            if os.path.exists(svt_path + ret):
                continue
            download_stat = await download(basic_url + i, svt_path + ret, True, crt_file)
            if not isinstance(download_stat, int):
                print("download icons error, reason:" + str(download_stat))
        for j in icons["cftIcons"]:
            ret = re.search(rule2, j).group(0)
            if os.path.exists(cft_path + ret):
                continue
            download_stat = await download(basic_url + j, cft_path + ret, True, crt_file)
            if not isinstance(download_stat, int):
                print("download icons error, reason:" + str(download_stat))
        print("finish download icons")
        return download_stat
    except Exception as e:
        return e