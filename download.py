from hoshino import aiorequests
import traceback


async def download(url, path, mute=False, crt_path=False):
    if not mute:
        print("start download img resources")
    try:
        png = await (await aiorequests.get(url, timeout=20, verify=crt_path)).content
        with open(path, "wb") as f:
            f.write(png)
        if not mute:
            print("finish")
        return 0
    except OSError:
        png = await (await aiorequests.get(url, timeout=20, verify=False)).content
        with open(path, "wb") as f:
            f.write(png)
        if not mute:
            print("finish")
        return 0
    except Exception as e:
        print(traceback.format_exc())
        return e
        # you can use this comment when you do not know what exception to catch:
        # noinspection PyBroadException
