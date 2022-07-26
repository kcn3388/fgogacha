from hoshino import aiorequests, config
import traceback


async def download(url, path, mute=False):
    if not mute:
        print("start download img resources")
    try:
        png = await (await aiorequests.get(url, timeout=20, verify=config.RES_DIR + "ca-certificates.crt")).content
        with open(path, "wb") as f:
            f.write(png)
        if not mute:
            print("finish")
        return 0
    except Exception as e:
        print(traceback.format_exc())
        return e
