from hoshino import aiorequests

headers = {
    "User-Agent": "Mozilla/5.0 (Windows; U; Windows NT 5.1; zh-CN; rv:1.9.1.6) ",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "zh-cn"
}


async def download(url, path, mute=False, crt_path=False):
    if not mute:
        print("start download img resources")
    try:
        png = await (await aiorequests.get(url, timeout=20, verify=crt_path, headers=headers)).content
        with open(path, "wb") as f:
            f.write(png)
        if not mute:
            print("finish")
        return 0
    except OSError:
        png = await (await aiorequests.get(url, timeout=20, verify=False, headers=headers)).content
        with open(path, "wb") as f:
            f.write(png)
        if not mute:
            print("finish")
        return 0
    except Exception as e:
        return e
        # you can use this comment when you do not know what exception to catch:
        # noinspection PyBroadException
