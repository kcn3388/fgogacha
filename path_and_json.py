import base64
import io
import os

from PIL import Image, ImageFont, ImageDraw

from hoshino import config

banned_id = ["333", "240", "168", "151", "152", "149", "83"]

basic_path = os.path.join(config.RES_DIR , "img", "fgo")
icon_path = os.path.join(basic_path , "icons")
svt_path = os.path.join(icon_path , "svt_icons")
cft_path = os.path.join(icon_path , "cft_icons")
skill_path = os.path.join(icon_path , "skill_icons")
cmd_path = os.path.join(icon_path , "cmd_icons")
card_path = os.path.join(icon_path , "card_icons")
class_path = os.path.join(icon_path , "class_icons")

res_paths = [basic_path, icon_path, svt_path, cft_path, skill_path, cmd_path, card_path, class_path]

runtime_path = os.path.dirname(__file__)

mooncellBackgroundUrl = 'https://fgo.wiki/images/bg/bg-mc-icon.png'
mooncellBackgroundPath = basic_path + 'bg-mc-icon.png'

data_path = os.path.join(runtime_path, 'data')
banner_path = os.path.join(data_path, 'banner.json')
config_path = os.path.join(data_path, 'config.json')
pools_path = os.path.join(data_path, 'pools.json')
gacha_path = os.path.join(data_path, 'gacha.json')
icons_path = os.path.join(data_path, 'icons.json')
banner_data_path = os.path.join(data_path, 'b_data.json')

old_pools_path = os.path.join(runtime_path, 'data/old_pools.json')

news_path = os.path.join(data_path, 'news.json')
news_detail_path = os.path.join(data_path, 'news_detail.json')

seal_path = os.path.join(runtime_path, 'res', '海の翁.jpg')
frame_path = os.path.join(runtime_path, 'res', 'background.png')
back_path = os.path.join(runtime_path, 'res', 'back.jpg')
back_cn_path = os.path.join(runtime_path, 'res', 'back_cn.png')
mask_path = os.path.join(runtime_path, 'res', 'mask.png')
font_path = os.path.join(runtime_path, 'res', 'SourceHanSansSC-Regular.otf')

all_json = [banner_path, config_path, pools_path, gacha_path, icons_path, banner_data_path]

crt_folder_path = os.path.join(runtime_path, "crt")
crt_path = "ca-certificates.crt"

all_servant_path = os.path.join(data_path, "all_svt.json")
all_command_path = os.path.join(data_path, "all_cmd.json")
all_craft_path = os.path.join(data_path, "all_cft.json")

lib_servant_path = os.path.join(data_path, "lib_svt.json")
lib_command_path = os.path.join(data_path, "lib_cmd.json")
lib_craft_path = os.path.join(data_path, "lib_cft.json")


def create_img(text):
    font_size = 30
    padding = 10

    font = ImageFont.truetype(font_path, font_size)

    wit, hei = font.getsize_multiline(text)
    img = Image.new("RGB", (wit + padding * 2, hei + padding * 2), "white")
    draw = ImageDraw.Draw(img)
    draw.multiline_text((padding / 2, padding / 2), text, font=font, fill="black")

    buffered = io.BytesIO()
    img.save(buffered, format="JPEG")
    base64_card = base64.b64encode(buffered.getvalue()).decode()
    pic = f'base64://{base64_card}'
    msg = f"[CQ:image,file={pic}]\n"
    return msg
