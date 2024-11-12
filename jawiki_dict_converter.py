""" Special Thanks: https://github.com/tokuhirom/jawiki-kana-kanji-dict"""

import json
import jaconv
import re
import requests
from pathlib import Path


def download_mecab_dict() -> str:
    """MeCab辞書データをダウンロードして内容を返す"""
    url = 'https://raw.githubusercontent.com/tokuhirom/jawiki-kana-kanji-dict/refs/heads/master/mecab-userdic.csv'
    response = requests.get(url)
    return response.text

def is_valid_word(word: str) -> bool:
    """英数字と「-」「&」「+」「'」「’」のみで構成される単語かチェック。アルファベットが必須"""
    # 英数字と記号のみで構成されているかチェック
    pattern = r'^[a-zA-Z0-9\-&+\'’]+$'
    if not re.match(pattern, word):
        return False

    # アルファベットが含まれているかチェック
    alpha_pattern = r'[a-zA-Z]'
    return bool(re.search(alpha_pattern, word))

def process_line(line: str) -> tuple[str, str] | None:
    """CSVの1行を処理し、条件に合致する場合は(単語, カタカナ)のタプルを返す"""
    try:
        parts = line.strip().split(',')
        word = parts[0]
        if not is_valid_word(word):
            return None
        # 3文字以下は除外
        if len(word) <= 3:
            return None

        # 最後の要素（ひらがな）をカタカナに変換
        kana = jaconv.hira2kata(parts[-1])
        return (word, kana)

    except Exception:
        return None

def main() -> None:
    current_dir = Path(__file__).parent
    output_file = current_dir / 'katakana_map_jawiki.json'

    # MeCab辞書をダウンロードして処理
    csv_content = download_mecab_dict()

    # CSVを1行ずつ処理
    katakana_map = {}
    for line in csv_content.splitlines():
        result = process_line(line)
        if result:
            word, kana = result
            katakana_map[word] = kana

    # ブラックリストキーを削除
    BLACKLIST = [
        "'else",
        "'Estacion",
        "'TAKA6",
        "'VOGA'",
        "00min",
        "030804-01",
        "-ISM",
        "1+1",
        "100m",
        "100s",
        "10cc",
        "12+",
        "13cm",
        "17-14",
        "33x",
        "2m",
        "17's-SEVENTEEN'S-",
        "63x",
        "1F",
        "24B",
        "24C",
        "29-10",
        "2A",
        "84x",
        "16francs",
        "diamonds",
        "DMAS",
        "drops",
        "Forms",
        "pamS",
        "raids",
        "Reports",
        "SESSIONS",
        "tears",
        "STC-Sus",
        "Moments",
        "abra",
        "Tears",
        "Image",
        "image",
        "IMAGE",
        "TODO",
        "UTF-7",
        "UTF-8",
        "VOICE",
        "versailles",
        "x264",
        "ACRI",
        "YAML",
        "Yuta",
        "TOMMY",
        "Terminus",
        "SMOOTH",
        "Siren",
        "SIREN",
        "Sachi",
        "Overload",
        "neuron",
        "MSGR",
        "meme",
        "Medium",
        "MATRIX",
        "MATLAB",
        "MACHINE",
        "machine",
        "Lass",
        "Langsam",
        "Jose",
        "JOHN",
        "Jaguar",
        "iPhone",
        "HILO",
        "ELECTRIC",
        "Editor",
        "droll",
        "DOOR",
        "Door",
        "Doberman",
        "DIFFUSER",
        "delectable",
        "coop",
        "canal",
        "cAMP",
        "C-CAS",
        "BREW",
        "Bonecrusher",
        "BASF",
        "AviUtl",
        "Apex",
        "Aoki",
        "active",
    ]
    katakana_map = {k: v for k, v in katakana_map.items() if k not in BLACKLIST}

    # アルファベット順にソート
    katakana_map = dict(sorted(katakana_map.items(), key=lambda x: x[0].lower()))

    # 結果を保存
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(katakana_map, f, ensure_ascii=False, indent=4)

    print(f'Processed dictionary saved to {output_file}')

if __name__ == '__main__':
    main()
