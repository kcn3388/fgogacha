import os.path

from ..path_and_json import *

headers = {
    "User-Agent": "Mozilla/5.0 (Windows; U; Windows NT 5.1; zh-CN; rv:1.9.1.6) ",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "zh-cn"
}


async def download(
        url: str, path: str, mute: bool = False, crt_file: Union[str, bool] = False
) -> Union[int, Exception]:
    if not mute:
        print("start download img resources")
    png = await get_content(url, crt_file)
    if isinstance(png, Exception):
        return png
    if not os.path.exists(path):
        with open(path, "wb") as f:
            f.write(png)
        if not mute:
            print("finish")
        return 0
    else:
        return 1
        # you can use this comment when you do not know what exception to catch:
        # noinspection PyBroadException
