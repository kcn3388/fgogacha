from hoshino import aiorequests, config
import traceback


async def download(url, path, mute=False, crt_path=None):
    if not mute:
        print("start download img resources")
    try:
        if crt_path is not None:
            png = await (await aiorequests.get(url, timeout=20, verify=config.RES_DIR + crt_path)).content
        else:
            png = await (await aiorequests.get(url, timeout=20)).content
        with open(path, "wb") as f:
            f.write(png)
        if not mute:
            print("finish")
        return 0
    except OSError:
        png = await (await aiorequests.get(url, timeout=20)).content
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
