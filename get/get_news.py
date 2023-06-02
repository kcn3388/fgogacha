from bs4 import BeautifulSoup
from typing import Tuple
from ..path_and_json import *


async def get_news(page_size: int = 6, crt_file: str = None) -> Tuple[int, Union[bool, Exception]]:
    list_news_url = f"https://api.biligame.com/news/" \
                    f"list.action?gameExtensionId=45&positionId=2&pageNum=1&pageSize={page_size} "
    try:
        list_news = await aiorequests.get(list_news_url, timeout=20, verify=crt_file, headers=headers)
    except OSError:
        list_news = await aiorequests.get(list_news_url, timeout=20, verify=False, headers=headers)
    except Exception as e:
        return -100, e

    list_news = json.loads(await list_news.text)["data"]
    for index_news in range(len(list_news)):
        new_content: str = list_news[index_news]["content"]
        new_content = f'{new_content.replace("...", "").replace("&nbsp;", "").strip()}...'
        list_news[index_news]["content"] = new_content

    with open(news_path, "w", encoding="utf-8") as f:
        f.write(json.dumps(list_news, indent=2, ensure_ascii=False))

    news_ids = []
    for each in list_news:
        if int(each["id"]) == 1509:
            continue
        news_ids.append(each["id"])

    all_news = []
    for each in news_ids:
        single_news_url = f"https://api.biligame.com/news/{each}.action"
        single_news_page = f"https://game.bilibili.com/fgo/news.html#!news/0/0/{each}"
        single_news_page_mobile = f"https://game.bilibili.com/fgo/h5/news.html#detailId={each}"
        try:
            single_news = await aiorequests.get(single_news_url, timeout=20, verify=crt_file, headers=headers)
        except OSError:
            single_news = await aiorequests.get(single_news_url, timeout=20, verify=False, headers=headers)
        except Exception as e:
            return -100, e
        single_news = json.loads(await single_news.text)["data"]
        single_news["content"] = await solve_content(single_news["content"])
        single_news["page"] = single_news_page
        single_news["mobile_page"] = single_news_page_mobile
        all_news.append(single_news)

    same = False
    try:
        news = json.load(open(news_detail_path, encoding="utf-8"))
        if news == all_news:
            same = True
    except json.decoder.JSONDecodeError:
        pass

    with open(news_detail_path, "w", encoding="utf-8") as f:
        f.write(json.dumps(all_news, indent=2, ensure_ascii=False))

    return len(all_news), same


async def solve_content(news_detail: str) -> str:
    soup = BeautifulSoup(news_detail, 'html.parser')
    all_text = soup.find_all("span")
    result = ""
    for each_text in all_text:
        get_text = each_text.text.strip()
        if not get_text or len(get_text) == 1:
            continue

        if get_text.startswith("※") or get_text.startswith("◆"):
            get_text = f"\n{get_text}"
        if get_text.endswith("。") or get_text.endswith("◆"):
            get_text = f"{get_text}\n"
        result += get_text
    return result
