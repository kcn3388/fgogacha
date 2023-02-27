from .download import *


async def download_icons(crt_file: Union[str, bool] = False) -> Union[int, Exception]:
    download_stat = 1
    if not os.path.exists(svt_path):
        os.mkdir(svt_path)
    if not os.path.exists(cft_path):
        os.mkdir(cft_path)
    if not os.path.exists(cmd_path):
        os.mkdir(cmd_path)

    try:
        with open(all_servant_path, 'r', encoding="utf-8") as f:
            svt = json.load(f)
        with open(all_craft_path, 'r', encoding="utf-8") as f:
            cft = json.load(f)
        with open(all_command_path, 'r', encoding="utf-8") as f:
            cmd = json.load(f)
    except json.decoder.JSONDecodeError:
        return 1

    basic_url = "https://fgo.wiki"
    try:
        for each_svt in svt:
            local_svt = os.path.join(svt_path, each_svt["local"]["svt_icon"])
            if os.path.exists(local_svt):
                continue
            download_stat = await download(
                basic_url + each_svt["online"]["svt_icon"], local_svt, True, crt_file
            )
            if not isinstance(download_stat, int):
                print("download icons error, reason:" + str(download_stat))
        for each_cft in cft:
            local_cft = os.path.join(cft_path, each_cft["local"]["cft_icon"])
            if os.path.exists(local_cft):
                continue
            download_stat = await download(
                basic_url + each_cft["online"]["cft_icon"], local_cft, True, crt_file
            )
            if not isinstance(download_stat, int):
                print("download icons error, reason:" + str(download_stat))
        for each_cmd in cmd:
            local_cmd = os.path.join(cmd_path, each_cmd["local"]["cmd_icon"])
            if os.path.exists(local_cmd):
                continue
            download_stat = await download(
                basic_url + each_cmd["online"]["cmd_icon"], local_cmd, True, crt_file
            )
            if not isinstance(download_stat, int):
                print("download icons error, reason:" + str(download_stat))
        print("finish download icons")
        return download_stat
    except OSError:
        for each_svt in svt:
            local_svt = os.path.join(svt_path, each_svt["local"]["svt_icon"])
            if os.path.exists(local_svt):
                continue
            download_stat = await download(
                basic_url + each_svt["online"]["svt_icon"], local_svt, True, crt_file
            )
            if not isinstance(download_stat, int):
                print("download icons error, reason:" + str(download_stat))
        for each_cft in cft:
            local_cft = os.path.join(cft_path, each_cft["local"]["cft_icon"])
            if os.path.exists(local_cft):
                continue
            download_stat = await download(
                basic_url + each_cft["online"]["cft_icon"], local_cft, True, crt_file
            )
            if not isinstance(download_stat, int):
                print("download icons error, reason:" + str(download_stat))
        for each_cmd in cmd:
            local_cmd = os.path.join(cmd_path, each_cmd["local"]["cmd_icon"])
            if os.path.exists(local_cmd):
                continue
            download_stat = await download(
                basic_url + each_cmd["online"]["cmd_icon"], local_cmd, True, crt_file
            )
            if not isinstance(download_stat, int):
                print("download icons error, reason:" + str(download_stat))
        print("finish download icons")
        return download_stat
    except Exception as e:
        return e
