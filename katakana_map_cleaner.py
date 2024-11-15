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

# 手動で作られた data.py 内の KATAKANA_MAP 内の値と一致しないものをチェック
from data import KATAKANA_MAP as DATA_KATAKANA_MAP

for key, value in sorted(DATA_KATAKANA_MAP.items()):
    if key not in KATAKANA_MAP:
        pass
    elif KATAKANA_MAP[key] != value:
        # print(f"Value mismatch for key '{key}': KATAKANA_MAP has '{KATAKANA_MAP[key]}', data.py has '{value}'.")
        pass

# data.py の KATAKANA_MAP と元の KATAKANA_MAP をマージ
merged_katakana_map = KATAKANA_MAP.copy()
for key, value in DATA_KATAKANA_MAP.items():
    # 値に "トゥ" が含まれ、かつ元の KATAKANA_MAP にキーが存在する場合は元の KATAKANA_MAP の値を優先
    if "トゥ" in value and key in merged_katakana_map:
        continue
    merged_katakana_map[key] = value

# fix_s の内容で上書き
with open(current_dir / "katakana_map_fix_s.json", "r") as f:
    fix_s_map = json.load(f)
for key, value in fix_s_map.items():
    merged_katakana_map[key] = value

# manual_proper_noun の内容で上書き
with open(current_dir / "katakana_map_manual_proper_noun.json", "r") as f:
    manual_proper_noun_map = json.load(f)
# manual_proper_noun_map の内容のうち、半角スペースを含む (=複数単語の) ものを除外
manual_proper_noun_map = {k: v for k, v in manual_proper_noun_map.items() if " " not in k}
# この状態の manual_proper_noun_map をソートして katakana_map_manual_proper_noun.json に保存
with open(current_dir / "katakana_map_manual_proper_noun.json", "w", encoding="utf-8") as f:
    manual_proper_noun_map = dict(sorted(manual_proper_noun_map.items(), key=lambda x: x[0].lower()))
    json.dump(manual_proper_noun_map, f, ensure_ascii=False, indent=4)

for key, value in manual_proper_noun_map.items():
    merged_katakana_map[key.lower()] = value

# katakana_map_jawiki.json の内容を追加
with open(current_dir / 'katakana_map_jawiki.json', 'r', encoding='utf-8') as f:
    jawiki_map = json.load(f)

# 全てのキーを小文字に変換して追加。既存のキーと読みが異なる場合は jawiki 版を優先
for key, value in jawiki_map.items():
    lower_key = key.lower()
    if lower_key in merged_katakana_map and merged_katakana_map[lower_key] != value:
        print(f"Value mismatch: Original has '{merged_katakana_map[lower_key]}', Jawiki has '{value}' / {lower_key}")
    merged_katakana_map[lower_key] = value

# katakana_map_manual_acronym.json の内容を追加
with open(current_dir / 'katakana_map_manual_acronym.json', 'r', encoding='utf-8') as f:
    acronym_map = json.load(f)

# acronym_map から小文字を含むキーを削除
acronym_map = {k: v for k, v in acronym_map.items() if k.isupper()}

# acronym_map をソートして重複を削除
acronym_map = dict(sorted(acronym_map.items(), key=lambda x: x[0].lower()))

# ソート済みの acronym_map を保存
with open(current_dir / 'katakana_map_manual_acronym.json', 'w', encoding='utf-8') as f:
    json.dump(acronym_map, f, ensure_ascii=False, indent=4)

# 頭字語は全て大文字キーとして追加
for key, value in acronym_map.items():
    upper_key = key.upper()
    merged_katakana_map[upper_key] = value

# アルファベット順にソート（キーのみ）
merged_katakana_map = dict(sorted(merged_katakana_map.items(), key=lambda x: x[0].lower()))

# マージされた辞書を katakana_map_merged.json に保存
with open(current_dir / "katakana_map_merged.json", "w", encoding="utf-8") as f:
    json.dump(merged_katakana_map, f, ensure_ascii=False, indent=4)

print("Merged katakana map has been saved to katakana_map_merged.json")

# 末尾が 's' で終わる単語のチェック
invalid_plural_keys = []

for key, value in merged_katakana_map.items():
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
        print(f"- {key}: {merged_katakana_map[key]}")
else:
    print(
        "\nAll plural words (ending with 's') have correct katakana endings ('ス' or 'ズ' or 'ツ' or 'ヅ')."
    )

