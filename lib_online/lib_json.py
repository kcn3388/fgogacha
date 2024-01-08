from hoshino import HoshinoBot  # noqa

from ..path_and_json import *  # noqa

base_svt_detail = {
    # "画师": {},
    "声优": "",
    "职阶": "",
    "性别": "",
    "身高": "",
    "体重": "",
    "属性": "",
    "隐藏属性": "",
    "筋力": "",
    "耐久": "",
    "敏捷": "",
    "魔力": "",
    "幸运": "",
    "宝具": "",
    "能力": [
        "基础",
        "满级",
        "90级",
        "100级",
        "120级"
    ],
    "ATK": [
        "",
        "",
        "",
        "",
        ""
    ],
    "职阶补正后": [
        "",
        "",
        "",
        "",
        ""
    ],
    "HP": [
        "",
        "",
        "",
        "",
        ""
    ],
    "Hit信息（括号内为每hit伤害百分比）": {
        "Quick": "",
        "Arts": "",
        "Buster": "",
        "Extra": "",
        "宝具": "",
    },
    "NP获得率": {
        "Quick": "",
        "Arts": "",
        "Buster": "",
        "Extra": "",
        "宝具": "",
        "受击": ""
    },
    "出星率": "",
    "即死率": "",
    "暴击权重": "",
    "特性": [],
    "人型": "",
    "被EA特攻": "",
    "猪化无效": "",
    "昵称": ""
}

sp_svt_detail = {
    "画师": {},
    "声优": "",
    "职阶": "",
    "性别": "",
    "身高": "",
    "体重": "",
    "属性": "",
    "隐藏属性": "",
    "筋力": "",
    "耐久": "",
    "敏捷": "",
    "魔力": "",
    "幸运": "",
    "宝具": "",
    "特性": [],
    "人型": "",
    "被EA特攻": "",
    "昵称": ""
}


def atk_coefficient(class_name: str) -> float:
    if class_name == "Archer":
        return 0.95
    elif class_name == "Lancer":
        return 1.05
    elif class_name == "Caster":
        return 0.9
    elif class_name == "Assassin":
        return 0.9
    elif class_name == "Berserker":
        return 1.1
    elif class_name == "Ruler":
        return 1.1
    elif class_name == "Avenger":
        return 1.1
    else:
        return 1
