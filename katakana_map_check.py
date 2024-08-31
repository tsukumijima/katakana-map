import json
import unicodedata
from pathlib import Path


def normalize_katakana(text):
    text = unicodedata.normalize("NFKC", text)  # 正規化
    text = text.replace("\u3099", "")  # 結合文字の濁点を削除、る゙ → る
    text = text.replace("\u309A", "")  # 結合文字の半濁点を削除、な゚ → な
    return text


def is_katakana(text):
    text = normalize_katakana(text)
    return all(
        (
            unicodedata.category(char) in ["Lo", "Lm", "Sk", "Mn", "Pd"]
            and unicodedata.name(char).startswith(("KATAKANA", "HALFWIDTH KATAKANA"))
        )
        or char == "ー"  # 伸ばす棒はカタカナ以外でも OK
        or char == "・"  # 中点はカタカナ以外でも OK
        for char in text
    )


# 不正なキーを格納するリスト
invalid_keys = []

current_dir = Path(__file__).parent
with open(current_dir / "katakana_map.json", "r") as f:
    KATAKANA_MAP = json.load(f)

# KATAKANA_MAP の各エントリーをチェック
for key, value in KATAKANA_MAP.items():
    if not is_katakana(value):
        invalid_keys.append(key)

# 結果の出力
if invalid_keys:
    print("Following keys have non-katakana values:")
    for key in invalid_keys:
        print(f"- {key}: {KATAKANA_MAP[key]}")
else:
    print("All values in KATAKANA_MAP are valid katakana.")

# 末尾が 's' で終わる単語のチェック
invalid_plural_keys = []

for key, value in KATAKANA_MAP.items():
    if key.endswith("s") and not (
        value.endswith("ス")
        or value.endswith("ズ")
        or value.endswith("ツ")
        or value.endswith("ヅ")
    ):
        invalid_plural_keys.append(key)

# 結果の出力
if invalid_plural_keys:
    print(
        "\nFollowing keys ending with 's' have values not ending with 'ス' or 'ズ' or 'ツ' or 'ヅ':"
    )
    for key in invalid_plural_keys:
        print(f"- {key}: {KATAKANA_MAP[key]}")
else:
    print(
        "\nAll plural words (ending with 's') have correct katakana endings ('ス' or 'ズ' or 'ツ' or 'ヅ')."
    )
