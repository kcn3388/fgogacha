import re
import shutil
from hoshino import priv, Service
from . import CQEvent
from .get.getnews import get_news
from .path_and_json import *

sv_news_help = '''
# 新闻相关：
[获取fgo新闻 + 数量] 从官网获取公告新闻，默认6条，置顶的概率公告会去掉
[查询fgo新闻 + 编号/all] 从本地查询公告具体内容，all代表全部获取
- 可以在末尾附加参数``nopic``不使用截图
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


@sv_news.on_fullmatch(("帮助fgo新闻获取", "帮助FGO新闻获取", "帮助bgo新闻获取", "帮助BGO新闻获取"))
@sv_news.on_rex(r"(?i)^[fb]go[新x][闻w][获h][取q][帮b][助z]$")
async def bangzhu(bot, ev):
    helps = gen_node(sv_news_help.strip())
    await bot.send_group_forward_msg(group_id=ev['group_id'], messages=helps)


@sv_news.on_rex(r"(?i)^([获h更g][取q新x])?[fb]go[新x][闻w]([获h更g][取q新x])?(\s\d+)?$")
async def get_offical_news(bot, ev: CQEvent):
    crt_file = False
    group_config = load_config(ev, True)
    if not group_config["crt_path"] == "False":
        crt_file = os.path.join(crt_folder_path, group_config["crt_path"])

    num = ev.message.extract_plain_text().split()
    if len(num) > 1:
        num = int(num[1])
    else:
        num = 6
    news, same = await get_news(num, crt_file)
    if not isinstance(same, bool) and news == -100:
        await bot.finish(ev, f"获取新闻出错，原因：\n{str(same)}")
    if same:
        await bot.send(ev, f"没有新的新闻~本地共有{news}条新闻~")
    else:
        await bot.send(ev, f"下载完成，本次共获取了{news}条新闻~")


@sv_news.on_rex(r"(?i)^([查c])?([询x])?[fb]go[新x][闻w]([查c][询x])?(\s.+)?$")
async def get_local_news(bot, ev: CQEvent):
    if not os.path.exists(news_detail_path):
        await bot.finish(ev, "没有本地新闻~请先获取官网新闻~")
    args = ev.message.extract_plain_text()
    no_pic = False
    get_all = False
    index = 0
    if "nopic" in args:
        no_pic = True
    if "all" in args:
        get_all = True

    match = re.search(r"\d+", args)
    if match:
        index = int(match.group(0))
    try:
        news = json.load(open(news_detail_path, encoding="utf-8"))
    except json.decoder.JSONDecodeError:
        await bot.finish(ev, "没有本地新闻~请先获取官网新闻~")

    if not os.path.exists(news_img_path):
        sv_news.logger.info("初始化新闻图片目录...")
        os.mkdir(news_img_path)
    # noinspection PyUnboundLocalVariable
    news_num = len(news)
    if not get_all:
        if not index:
            await bot.finish(ev, f"本地共有{news_num}条新闻，请用编号查对应新闻~")
        index = int(index) - 1
        link = f"标题：{news[index]['title']}\n电脑版网页：{news[index]['page']}\n手机版网页：{news[index]['mobile_page']}\n\n"
        msg = ""
        if not no_pic:
            img_path = os.path.join(news_img_path, f"{news[index]['id']}.png")
            if not os.path.exists(img_path):
                getpic(news[index]['page'], img_path)
            if os.path.exists(img_path):
                news_img = Image.open(img_path)
                pic_b64 = util.pic2b64(news_img)
                msg = f"{MessageSegment.image(pic_b64)}\n"
            else:
                sv_news.logger.warning("获取新闻截图出错")
                msg = "截图出错，请自行查看~"
        _news = gen_node((link + msg).strip())
        try:
            await bot.send_group_forward_msg(group_id=ev['group_id'], messages=_news)
        except ActionFailed:
            await bot.send(ev, "转发消息失败……尝试直接发送~")
            try:
                await bot.send(ev, msg)
            except ActionFailed:
                await bot.send(ev, f"转发消息失败……可能是新闻太长了，试试直接去官网看看吧~\n"
                                   f"标题：{news[index]['title']}\n"
                                   f"电脑版网页：{news[index]['page']}\n"
                                   f"手机版网页：{news[index]['mobile_page']}")
    if get_all:
        news_all = []
        # noinspection PyUnboundLocalVariable
        for i in range(news_num):
            link = f"标题：{news[i]['title']}\n电脑版网页：{news[i]['page']}\n手机版网页：{news[i]['mobile_page']}\n\n"
            _news = gen_node(link.strip())
            news_all.append(_news)
        try:
            await bot.send_group_forward_msg(group_id=ev['group_id'], messages=news_all)
        except ActionFailed:
            if news_num < 10:
                await bot.send(ev, f"发送合集失败，尝试拆分发送！\n共有{news_num}条新闻~")
                for i in range(news_num):
                    link = f"标题：{news[i]['title']}\n电脑版网页：{news[i]['page']}\n手机版网页：{news[i]['mobile_page']}\n\n"
                    _news = gen_node(link.strip())
                    try:
                        await bot.send_group_forward_msg(group_id=ev['group_id'], messages=_news)
                    except ActionFailed:
                        await bot.send(ev, f"转发消息失败……可能是新闻太长了，试试直接去官网看看吧~\n"
                                           f"标题：{news[i]['title']}\n"
                                           f"电脑版网页：{news[i]['page']}\n"
                                           f"手机版网页：{news[i]['mobile_page']}")
            else:
                await bot.send(ev, f"新闻太多啦！\n共有{news_num}条新闻，请尝试用编号查对应新闻~")


@sv_news.on_fullmatch("清除新闻缓存")
async def delete_news_cache(bot, ev: CQEvent):
    shutil.rmtree(news_img_path)
    await bot.finish(ev, "已清理新闻缓存")
