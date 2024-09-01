categories = {
    "BlueArchive": {
        "local_path": "ブルーアーカイブ",
        "remote_path": "BlueArchive",
        "tags": {
            "調月リオ": "調月リオ",
            "调月莉音": "調月リオ",
            "早瀬ユウカ": "早瀬ユウカ",
            "一之瀬アスナ": "一之瀬アスナ",
            "一之瀨亞絲娜(兔女郎)": "一之瀬アスナ",
            "亞絲娜": "一之瀬アスナ",
            "飛鳥馬トキ": "飛鳥馬トキ",
            "飛鳥馬時": "飛鳥馬トキ",
            "角楯カリン": "角楯カリン",
            "仲正一花": "仲正一花",
            "七神リン": "七神リン",
            "羽川ハスミ": "羽川ハスミ",
            "生鹽諾雅": "生鹽諾雅",
            "陸八魔アル": "陸八魔アル",
            "錠前サオリ": "錠前サオリ",
            "天雨アコ": "天雨アコ",
            "十六夜ノノミ": "十六夜ノノミ",
            "砂狼シロコ": "砂狼シロコ",
            "others": "其他角色",
        },
    },
    "IdolMaster": {
        "local_path": "IdolMaster",
        "remote_path": "IdolMaster",
        "children": [
	    "アイドルマスター",
	    "アイドルマスターシャイニーカラーズ",
	    "アイドルマスターシンデレラガールズ",
            "学園アイドルマスター"
        ],
        "tags": {
            "黛冬優子": "黛冬優子",
            "桑山千雪": "桑山千雪",
            "市川雛菜": "市川雛菜",
            "樋口円香": "樋口円香",
            "七草羽月": "七草羽月",
            "七草にちか": "七草日花",
            "和泉愛依": "和泉愛依",
            "白瀨咲耶": "白瀨咲耶",
            "浅倉透": "浅倉透",
            "有栖川夏葉": "有栖川夏葉",
            "月岡戀鍾": "月岡戀鍾",
            "大崎甘奈": "大崎甘奈",
            "大崎甜花": "大崎甘奈",
            "櫻木真乃": "櫻木真乃",
            "西城樹里": "西城樹里",
            "風野灯織": "風野灯織",
            "園田智代子": "園田智代子",
            "八宮めぐる": "八宮めぐる",
            "姫崎莉波": "姫崎莉波",
            "本田未央": "本田未央",
            "北条加蓮": "北条加蓮",
            "鷺澤文香": "鷺澤文香",
            "城崎美嘉": "城崎美嘉",
            "新田美波": "新田美波",
            "三船美優": "三船美優",
            "千川ちひろ": "千川ちひろ",
            "速水奏": "速水奏",
            "高桓楓": "高桓楓",
            "島村卯月": "島村卯月",
            "澀谷凜": "澀谷凜",
            "others": "其他角色",
        },
    },
    "Genshin": {
        "local_path": "原神",
        "remote_path": "原神",
    },
    "Marin":{
        "local_path": "喜多川海夢",
        "remote_path": "others/喜多川海夢",
    },
    "Others":{
        "local_path": "others",
        "remote_path": "others/雜圖",
    }
}

config = {
    "BASE_PATHS": {
        "local_path": r"C:\Users\demo\P5D\local-demo2",
        "remote_path": r"C:\Users\demo\P5D\remote-demo",
    },
    "categories": categories,
    "tag_delimiter": {
        "front": "{}_",
        "between": ",",
    },
    "file_type":{
        "type": ["jpg", "png", "webm"]
    },
    "custom":{
        # "rsync": "-aAXHv --remove-source-files"
    }
}
# print(config.get("BASE_PATHS"))