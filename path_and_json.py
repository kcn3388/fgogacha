import asyncio
import io
import json
import os

from jsonpath import jsonpath  # noqa
from typing import Union, List

from PIL import Image, ImageFont, ImageDraw
from aiocqhttp import MessageSegment
from playwright.async_api import async_playwright
from time import sleep

from hoshino import config, util, aiorequests, logger, Service, priv
from hoshino.typing import CQEvent

sv_help = '''
# 抽卡模拟相关
[fgo十连] fgo抽卡
[fgo百连] 100抽
[获取fgo卡池] 从mooncell获取卡池数据
[查询fgo卡池] 查询本地缓存的卡池以及本群卡池
[切换fgo卡池 + 卡池编号] 切换需要的卡池
[切换fgo日替卡池 + 卡池编号 + 日替卡池编号] 切换需要的日替卡池
'''.strip()

sv = Service(
    name='fgo抽卡',
    help_=sv_help,
    bundle="娱乐",
    enable_on_default=True,
    visible=True,
    use_priv=priv.NORMAL,  # 使用权限
    manage_priv=priv.ADMIN,  # 管理权限
)

sv_fetch_help = '''
# 数据管理相关
[获取全部内容] 获取从者/礼装/纹章的相关内容
- 从者包括职介和指令卡
- 礼装/纹章包括技能
- 子命令：
  - [获取全部从者]
  - [获取全部礼装]
  - [获取全部纹章]
[下载全部卡片资源] 从上述数据中下载对应静态资源
- 子命令：
  - [下载全部从者资源]
  - [下载全部礼装资源]
  - [下载全部纹章资源]
'''.strip()

sv_fetch = Service(
    name='fgo数据获取',
    help_=sv_fetch_help,
    bundle="娱乐",
    enable_on_default=True,
    visible=True,
    use_priv=priv.NORMAL,  # 使用权限
    manage_priv=priv.ADMIN,  # 管理权限
)

sv_lib_help = '''
# fgo数据库相关
``[更新fgo图书馆]`` 获取从者/礼装/纹章的相关详细数据，包括属性、白值等
- 支持附带类型参数以更新指定内容
- 类型参数：从者/礼装/纹章/最新
  - 当参数含有最新时，只会获取本地不存在的内容
  - 支持种类与最新同时存在
- **※需要先执行``[获取全部内容]``**

``[增添fgo图书馆 + 类型 + id]`` 在本地已存在图书馆的情况下，手动增添新数据，以避免每次数据更新都需要重新爬一次全部内容
- 类型：从者、礼装、纹章

``[查询最新图书馆 + 类型]`` 获取最近的内容

``[修补fgo图书馆 + 类型 + id]`` 单独修补某张卡片的详细数据
- 类型为：从者、礼装、纹章
- **※需要先执行``[更新fgo图书馆]``**

``[fgo从者查询 + 关键词（至少一个）]`` 通过关键词搜索从者
- 若关键词大于两个，只会返回同时符合的
- 可以附带参数``详细``以获取卡面及游戏数据，附带参数``数据``则不显示卡面只显示游戏数据
- 当输入参数存在id{卡片id}时，直接返回对应id的卡片
  - 例子：``查询fgo从者 id312``

``[fgo礼装查询 + 关键词（至少一个）]`` 通过关键词搜索礼装
- 若关键词大于两个，只会搜索同时符合的
- 可以附带参数``详细``以获取卡面及游戏数据
- 查询特定id的礼装同上

``[fgo纹章查询 + 关键词（至少一个）]`` 通过关键词搜索礼装
- 若关键词大于两个，只会搜索同时符合的
- 可以附带参数``详细``以获取卡面及游戏数据
- 查询特定id的纹章同上
'''.strip()

sv_lib = Service(
    name='fgo图书馆',
    help_=sv_lib_help,
    bundle="娱乐",
    enable_on_default=True,
    visible=True,
    use_priv=priv.NORMAL,  # 使用权限
    manage_priv=priv.ADMIN,  # 管理权限
)

sv_lucky_help = '''
[更新fgo福袋] 获取福袋信息
- 初次查询福袋之前务必先执行此命令
[查询fgo福袋 + 概况] 查询全部福袋的文字概况
[查询fgo福袋 + 国服/日服] 查询当前存在的福袋数据
- [查询fgo福袋 + 国服/日服 + 福袋编号] 查询对应顺序的福袋详细数据
- [查询fgo福袋 + 国服/日服 + 全部] 查询全部福袋详细数据
[查询fgo福袋 + 未来] 查询国服千里眼福袋数据
[抽fgo福袋 + 国服/日服 + 福袋编号 + 子池子编号（默认为1）] 抽福袋
'''.strip()

sv_lucky = Service(
    name='fgo福袋',
    help_=sv_lucky_help,
    bundle="娱乐",
    enable_on_default=True,
    visible=True,
    use_priv=priv.NORMAL,  # 使用权限
    manage_priv=priv.ADMIN,  # 管理权限
)

sv_manage_help = '''
# 抽卡管理命令:
[fgo数据初始化] 初始化数据文件及目录，务必安装后先执行此命令！
[fgo数据下载] 下载从者及礼装图标，务必先初始化数据再执行下载！
[跟随最新/剧情卡池] 设置卡池数据更新后跟随最新国服卡池还是国服剧情卡池
[fgo_enable_crt + crt文件路径] 为下载配置crt文件以规避拒绝访问，留空为默认，False为禁用
[fgo_check_crt] 检查本群crt文件配置状态
[重载配置文件] 为本群新建默认配置或还原至默认配置，同时修补其他群的配置
[切换抽卡样式 + 样式] 切换抽卡样式，可选样式：
- 文字：旧版简约图标
- 图片：仿真实抽卡
[设置fgo时间 + 小时 + 分钟 + 秒] 设置自动更新时间间隔，至少输入其中一个参数
- 例如：``设置fgo时间 1小时60分钟60秒``
'''.strip()

sv_manage = Service(
    name='fgo管理',
    help_=sv_manage_help,
    bundle="娱乐",
    enable_on_default=True,
    visible=True,
    use_priv=priv.NORMAL,  # 使用权限
    manage_priv=priv.ADMIN,  # 管理权限
)

sv_news_help = '''
# 新闻相关：
[获取fgo新闻 + 数量] 从官网获取公告新闻，默认6条，置顶的概率公告会去掉
[查询fgo新闻 + 编号/all] 从本地查询公告具体内容，all代表全部获取
- 可以在末尾附加参数``pic``不使用截图
[清除新闻缓存] 移除新闻截图
'''.strip()

sv_news = Service(
    name='fgo新闻获取',
    help_=sv_news_help,
    bundle="娱乐",
    enable_on_default=True,
    visible=True,
    use_priv=priv.NORMAL,  # 使用权限
    manage_priv=priv.ADMIN,  # 管理权限
)

height = 194
width = 178
dis = 23
floor = 48
st1w = 92
st1h = 200
st2 = 192

box_list = []

box1 = (st1w, st1h)
for box_i in range(6):
    box_list.append(box1)
    lst = list(box1)
    lst[0] += width + dis
    box1 = tuple(lst)

box2 = (st2, st1h + height + floor)
for box_i in range(5):
    box_list.append(box2)
    lst = list(box2)
    lst[0] += width + dis
    box2 = tuple(lst)

headers = {
    "User-Agent": "Mozilla/5.0 (Windows; U; Windows NT 5.1; zh-CN; rv:1.9.1.6) ",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "zh-cn"
}

banned_id = ["333", "240", "168", "151", "152", "149", "83"]

basic_path = os.path.join(config.RES_DIR, "img", "fgo")
runtime_path = os.path.dirname(__file__)

data_path = os.path.join(runtime_path, 'data')
mc_path = os.path.join(data_path, "data", "mooncell")

icon_path = os.path.join(basic_path, "icons")
svt_path = os.path.join(icon_path, "svt_icons")
cft_path = os.path.join(icon_path, "cft_icons")
skill_path = os.path.join(icon_path, "skill_icons")
cmd_path = os.path.join(icon_path, "cmd_icons")
card_path = os.path.join(icon_path, "card_icons")
class_path = os.path.join(icon_path, "class_icons")

res_paths = [
    basic_path, icon_path, svt_path, cft_path, skill_path,
    cmd_path, card_path, class_path, mc_path
]
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


def create_img(text: str) -> str:
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


def gen_node(text: Union[str, List[str]], _name: str = "涩茄子", _uin: str = "2902388901") -> dict:
    node = {
        "type": "node",
        "data": {
            "name": _name,
            "uin": _uin,
            "content": text
        }
    }

    return node


def load_config(ev: CQEvent, get_group: bool = False) -> dict:
    gid = str(ev.group_id)
    if os.path.exists(config_path):
        try:
            configs = json.load(open(config_path, encoding="utf-8"))
            if gid not in configs["groups"]:
                basic_config = {
                    "crt_path": crt_path,
                    "style": "图片"
                }
                configs["groups"][gid] = basic_config
                with open(config_path, "w", encoding="utf-8") as f:
                    f.write(json.dumps(configs, indent=2, ensure_ascii=False))

            if get_group:
                if gid in configs["groups"]:
                    return configs["groups"][gid]
            else:
                return configs
        except json.decoder.JSONDecodeError:
            pass

    basic_config = {
        "crt_path": crt_path,
        "style": "图片"
    }
    configs = {
        "follow_latest": True,
        "flush_hour": 0,
        "flush_minute": 60,
        "flush_second": 0,
        "groups": {
            gid: basic_config
        }
    }
    with open(config_path, "w", encoding="utf-8") as f:
        f.write(json.dumps(configs, indent=2, ensure_ascii=False))

    if get_group:
        return basic_config
    else:
        return configs


async def getpic(url: str, img_path: str) -> bool:
    if os.path.exists(img_path):
        return True
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page()
        try:
            await page.goto(url)
        except Exception as e:
            sv.logger.error(f"访问网站超时{type(e)}\n`{e}`")
            return False
        await asyncio.sleep(1)
        sv.logger.info("正在保存图片...")
        await page.screenshot(
            path=img_path,
            full_page=True
        )
        sv.logger.info("正在压缩图片...")
        img_convert = Image.open(img_path)
        img_convert.save(img_path, quality=70)
        sv.logger.info("图片保存成功！")
        await browser.close()
        return True


def gen_ms_img(image: Union[bytes, Image.Image]) -> MessageSegment:
    if isinstance(image, bytes):
        return MessageSegment.image(
            util.pic2b64(Image.open(io.BytesIO(image)))
        )
    else:
        return MessageSegment.image(
            util.pic2b64(image)
        )


async def gen_img_from_url(img_url: str, crt_file: Union[bool, str]) -> Union[Exception, MessageSegment]:
    img_url = f"https://fgo.wiki{img_url}"
    image_bytes = await get_content(img_url, crt_file)
    if isinstance(image_bytes, Exception):
        return image_bytes
    return gen_ms_img(image_bytes)


async def get_content(url: str, crt_file: Union[bool, str]) -> Union[Exception, bytes]:
    try:
        return await (
            await aiorequests.get(url, timeout=20, headers=headers, verify=crt_file)
        ).content
    except OSError:
        try:
            sleep(10)
            return await (
                await aiorequests.get(url, timeout=20, headers=headers)
            ).content
        except Exception as e2:
            logger.error(f"aiorequest error: {e2}")
            return e2
    except Exception as e:
        logger.error(f"aiorequest error: {e}")
        return e


async def gen_gacha_img(style: str, img_path: List[str], server: str) -> Image:
    # 文字图标版，更快
    if not style == "图片":
        cards = []
        for each in img_path:
            cards.append(Image.open(each).resize((66, 72)))
        rows = 3
        cols = 4
        base_img = Image.open(frame_path).resize(((66 * cols) + 40, (72 * rows) + 40))
        r_counter = 0
        c_counter = 0
        for each in cards:
            base_img.paste(each, ((66 * c_counter) + 20, (72 * r_counter) + 20))
            c_counter += 1
            if c_counter >= cols:
                r_counter += 1
                if r_counter >= rows:
                    break
                else:
                    c_counter = 0

    else:
        # 图片版，较慢
        if server == "国服":
            base_img = Image.open(back_cn_path).convert("RGBA")
        else:
            base_img = Image.open(back_path).convert("RGBA")
        masker = Image.open(mask_path).resize((width, height))

        for i, pic_path in enumerate(img_path):
            tmp_img = Image.open(pic_path).resize((width, height))
            tmp_img = tmp_img.convert('RGBA')
            base_img.paste(tmp_img, box_list[i], mask=masker)

    return base_img


def gen_pool_data(banner: dict, ev: CQEvent = None, gid: int = None) -> Union[str, dict]:
    if gid is None and ev is None:
        return ""
    if ev is not None:
        gid = ev.group_id
    gacha_data = json.load(open(gacha_path, encoding="utf-8"))
    svt_data = {}
    for each in gacha_data:
        if each["p_id"] == banner["banner"]["id"]:
            if "s_id" in each:
                if each["s_id"] == banner["banner"]["s_id"]:
                    svt_data = each
                    break
            else:
                svt_data: dict = each
                break
    if len(svt_data) == 0:
        print("data error")
        return ""
    pool_data = {
        "group": gid,
        "data": {}
    }
    for each in svt_data["servants"]:
        each["weight"] /= 100
        each["weight"] = round(each["weight"], 3)
        d = {
            each["type"]: each["ids"],
            each["type"] + "_rate": each["weight"]
        }
        pool_data["data"].update(d)

    for each in svt_data["crafts"]:
        each["weight"] /= 100
        each["weight"] = round(each["weight"], 3)
        d = {
            each["type"]: each["ids"],
            each["type"] + "_rate": each["weight"]
        }
        pool_data["data"].update(d)

    if not os.path.exists(banner_data_path):
        print("初始化数据json...")
        open(banner_data_path, 'w')
        pool_detail_data = []
    else:
        try:
            pool_detail_data = json.load(open(banner_data_path, encoding="utf-8"))
        except json.decoder.JSONDecodeError:
            pool_detail_data = []

    exists = False
    for i in range(len(pool_detail_data)):
        if pool_detail_data[i]["group"] == gid:
            pool_detail_data[i] = pool_data
            exists = True
    if not exists:
        pool_detail_data.append(pool_data)

    with open(banner_data_path, "w", encoding="utf-8") as f:
        f.write(json.dumps(pool_detail_data, indent=2, ensure_ascii=False))

    return pool_detail_data
