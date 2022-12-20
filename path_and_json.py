import io
import json
import os
import platform
import time
from typing import Dict, Union

from PIL import Image, ImageFont, ImageDraw
from aiocqhttp import MessageSegment
from selenium import webdriver

from hoshino import config, util, aiorequests, logger
from hoshino.typing import CQEvent

headers = {
    "User-Agent": "Mozilla/5.0 (Windows; U; Windows NT 5.1; zh-CN; rv:1.9.1.6) ",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "zh-cn"
}

banned_id = ["333", "240", "168", "151", "152", "149", "83"]

basic_path = os.path.join(config.RES_DIR, "img", "fgo")
icon_path = os.path.join(basic_path, "icons")
svt_path = os.path.join(icon_path, "svt_icons")
cft_path = os.path.join(icon_path, "cft_icons")
skill_path = os.path.join(icon_path, "skill_icons")
cmd_path = os.path.join(icon_path, "cmd_icons")
card_path = os.path.join(icon_path, "card_icons")
class_path = os.path.join(icon_path, "class_icons")

res_paths = [basic_path, icon_path, svt_path, cft_path, skill_path, cmd_path, card_path, class_path]

runtime_path = os.path.dirname(__file__)

data_path = os.path.join(runtime_path, 'data')
news_img_path = os.path.join(runtime_path, 'news')
banner_path = os.path.join(data_path, 'banner.json')
config_path = os.path.join(data_path, 'config.json')
pools_path = os.path.join(data_path, 'pools.json')
gacha_path = os.path.join(data_path, 'gacha.json')
lucky_path = os.path.join(data_path, 'lucky_bag.json')
banner_data_path = os.path.join(data_path, 'b_data.json')
update_data_path = os.path.join(data_path, 'update.json')

old_pools_path = os.path.join(runtime_path, 'data/old_pools.json')

news_path = os.path.join(data_path, 'news.json')
news_detail_path = os.path.join(data_path, 'news_detail.json')

static_path = os.path.join(runtime_path, 'res')
seal_path = os.path.join(static_path, '海の翁.jpg')
frame_path = os.path.join(static_path, 'background.png')
back_path = os.path.join(static_path, 'back.jpg')
back_cn_path = os.path.join(static_path, 'back_cn.png')
mask_path = os.path.join(static_path, 'mask.png')
font_path = os.path.join(static_path, 'SourceHanSansSC-Regular.otf')

crt_folder_path = os.path.join(runtime_path, "crt")
crt_path = "ca-certificates.crt"

all_servant_path = os.path.join(data_path, "all_svt.json")
all_command_path = os.path.join(data_path, "all_cmd.json")
all_craft_path = os.path.join(data_path, "all_cft.json")

lib_servant_path = os.path.join(data_path, "lib_svt.json")
lib_command_path = os.path.join(data_path, "lib_cmd.json")
lib_craft_path = os.path.join(data_path, "lib_cft.json")

all_json = [
    banner_path, config_path, pools_path, gacha_path, lucky_path,
    banner_data_path, update_data_path, old_pools_path,
    news_path, news_detail_path,
    all_servant_path, all_command_path, all_craft_path,
    lib_servant_path, lib_command_path, lib_craft_path
]


def create_img(text) -> str:
    font_size = 30
    padding = 10

    font = ImageFont.truetype(font_path, font_size)

    wit, hei = font.getsize_multiline(text)
    img = Image.new("RGB", (wit + padding * 2, hei + padding * 2), "white")
    draw = ImageDraw.Draw(img)
    draw.multiline_text((padding / 2, padding / 2), text, font=font, fill="black")

    pic = util.pic2b64(img)
    msg = str(MessageSegment.image(pic))
    return msg


def gen_node(text, _name="涩茄子", _uin="2902388901") -> Dict:
    node = {
        "type": "node",
        "data": {
            "name": _name,
            "uin": _uin,
            "content": text
        }
    }

    return node


def load_config(ev: CQEvent, get_group=False) -> Dict:
    if os.path.exists(config_path):
        try:
            configs = json.load(open(config_path, encoding="utf-8"))
            group = [gs for gs in configs["groups"] if gs["group"] == ev.group_id]
            if not group:
                basic_config = {
                    "group": ev.group_id,
                    "crt_path": crt_path,
                    "style": "图片"
                }
                configs["groups"].append(basic_config)
                with open(config_path, "w", encoding="utf-8") as f:
                    f.write(json.dumps(configs, indent=2, ensure_ascii=False))
            if get_group:
                if group:
                    return group[0]
            else:
                return configs
        except json.decoder.JSONDecodeError:
            pass

    basic_config = {
        "group": ev.group_id,
        "crt_path": crt_path,
        "style": "图片"
    }
    configs = {
        "follow_latest": True,
        "flush_hour": 0,
        "flush_minute": 60,
        "flush_second": 0,
        "groups": [basic_config]
    }
    with open(config_path, "w", encoding="utf-8") as f:
        f.write(json.dumps(configs, indent=2, ensure_ascii=False))

    if get_group:
        return basic_config
    else:
        return configs


def getpic(url, save_img_name, _type="") -> bool:
    curr_platform = platform.system().lower()
    if curr_platform == "windows":
        options = webdriver.EdgeOptions()
        options.add_argument('--headless')
        options.add_argument('--disable-gpu')
        options.add_argument('--no-sandbox')
        msedgedriver = os.path.join(static_path, "msedgedriver.exe")
        driver = webdriver.Edge(options=options, executable_path=msedgedriver)
    elif curr_platform == "linux":
        options = webdriver.ChromeOptions()
        options.add_argument('--headless')
        options.add_argument('--disable-gpu')
        options.add_argument('--no-sandbox')
        chromedriver = os.path.join(static_path, "chromedriver")
        driver = webdriver.Chrome(options=options, executable_path=chromedriver)
    else:
        return False

    driver.maximize_window()
    js_height = "return document.body.clientHeight"
    picname = save_img_name
    link = url
    try:
        # print(link)
        driver.get(link)
        k = 1
        height = driver.execute_script(js_height)
        while True:
            if k * 500 < height:
                js_move = "window.scrollTo(0,{})".format(k * 500)
                # print(js_move)
                driver.execute_script(js_move)
                time.sleep(0.2)
                height = driver.execute_script(js_height)
                k += 1
            else:
                break
        scroll_width = driver.execute_script('return document.body.parentNode.scrollWidth')
        scroll_height = driver.execute_script('return document.body.parentNode.scrollHeight')
        if not _type == "":
            scroll_width = 600
        driver.set_window_size(scroll_width, scroll_height)
        driver.get_screenshot_as_file(picname)
        return True
    except Exception as e:
        print(e)
        return False


def gen_ms_img(image: Union[bytes, Image.Image]) -> MessageSegment:
    if isinstance(image, bytes):
        return MessageSegment.image(
            util.pic2b64(Image.open(io.BytesIO(image)))
        )
    else:
        return MessageSegment.image(
            util.pic2b64(image)
        )


async def gen_img_from_url(img_url: str, crt_file) -> Union[Exception, MessageSegment]:
    img_url = f"https://fgo.wiki{img_url}"
    image_bytes = await get_content(img_url, crt_file)
    if isinstance(image_bytes, Exception):
        return image_bytes
    return gen_ms_img(image_bytes)


async def get_content(url: str, crt_file) -> Union[Exception, bytes]:
    try:
        return await (
            await aiorequests.get(url, headers=headers, verify=crt_file)
        ).content
    except OSError:
        return await (
            await aiorequests.get(url, timeout=20, verify=False, headers=headers)
        ).content
    except Exception as e:
        logger.warning(f"aiorequest error: {e}")
        return e
