"""
Install the Google AI Python SDK

$ pip install google-generativeai
"""

import csv
import io
import json
import os
import time
import traceback
import unicodedata
from pathlib import Path

import google.generativeai as genai
from google.generativeai.types import HarmBlockThreshold, HarmCategory


genai.configure(api_key=os.environ["GEMINI_API_KEY"])

# Create the model
generation_config = {
    "temperature": 1,
    "top_p": 0.95,
    "top_k": 64,
    "max_output_tokens": 8192,
    "response_mime_type": "text/plain",
}

model = genai.GenerativeModel(
    model_name="gemini-1.5-flash-exp-0827",
    generation_config=generation_config,
    safety_settings={
        # 制限を全部解除
        HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
        HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
        HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
        HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
    },
    # See https://ai.google.dev/gemini-api/docs/safety-settings
    system_instruction="""あなたは英単語をカタカナ英語に変換する専門家です。以下の厳密なルールに従って変換を行ってください：

1. 入力: 改行区切りの英単語リストが与えられます。
2. 出力: 各単語をカタカナ英語に変換し、CSV形式で返してください。

変換ルール:
- 全ての入力単語を必ず変換すること。
- 単語数は必ず入力と出力で一致させること。例えば入力が100単語あれば出力も100単語でなければならない。このルールは絶対である。
- ミススペルや不自然な単語でも必ず変換すること。
- 日本で一般的に使用されるカタカナ英語を優先すること。例: "orange" → "オレンジ"
- 固有名詞も可能な限り一般的な読み方で変換すること。
- 略語やアクロニムは一般的な読み方で変換すること。例: "NASA" → "ナサ"
- 変換結果は必ずカタカナのみで構成すること。アルファベットや平仮名を含めないこと。
- 日本語への翻訳は行わないこと。例: "apple" → "アップル"（"りんご"ではない）
- "chugoku" のような日本語と思われるローマ字であっても、必ずカタカナ英語で変換すること。 例: "chugoku" → "チュウゴク"
- "directv" のような英語の固有名詞であっても、必ずアルファベットを用いず発音のカタカナ英語で変換すること。 例: "directv" → "ディレクティービー"
- "extrasensory" のような複雑な英語の名詞であっても、必ずアルファベットを用いず発音のカタカナ英語で変換すること。 例: "extrasensory" → "エクストラセンソリー"
- "fenech" のようなマイナーな人名であっても、必ずアルファベットを用いず発音のカタカナ英語で変換すること。 例: "fenech" → "フェネッチ"
- "honduran" のような国名や国の人々の名前であっても、"ホンジュラス人" とはせず、必ずカタカナ英語で変換すること。 例: "honduran" → "ホンジュラン", "kuwaiti" → "クウェーティ"
- 長音符（ー）を適切に使用すること。例: "computer" → "コンピューター"
- 促音や拗音を正確に表現すること。例: "application" → "アプリケーション"
- 複数形はちゃんと s をカタカナで表現すること。例: "apples" → "アップルズ"

出力フォーマット:
apple,アップル
banana,バナナ
cherry,チェリー
donut,ドーナツ
...

この任務は極めて重要です。一つでも間違いや抜け漏れがあると深刻な問題につながります。細心の注意を払って作業してください。""",
)


# send_message() すると不要な履歴がどんどん積もっていくため、都度新しいセッションを作成する
def get_chat_session():
    chat_session = model.start_chat(
        history=[
            {
                "role": "user",
                "parts": [
                    """
                    aaa
                    aaberg
                    aachen
                    aachener
                    aaker
                    aalborg
                    aalburg
                    aalen
                    aaliyah
                    aalseth
                    alpern
                    fenech
                    judo
                    jujitsu
                    kuwaiti
                    """.strip(),
                ],
            },
            {
                "role": "model",
                "parts": [
                    """
                    aaa,トリプルエー
                    aaberg,アーバーグ
                    aachen,アーヘン
                    aachener,アーヘナー
                    aaker,アーカー
                    aalborg,オールボー
                    aalburg,アールブルフ
                    aalen,アーレン
                    aaliyah,アリーヤ
                    aalseth,オルセス
                    alpern,アルペルン
                    fenech,フェネック
                    judo,ジュウドー
                    jujitsu,ジュジツ
                    kuwaiti,クウェーティ
                    """.strip(),
                ],
            },
        ]
    )
    return chat_session


current_dir = Path(__file__).parent

# cmudict_words.txtからの単語読み込み
with open(current_dir / "cmudict_words.txt", "r") as f:
    words = f.read().splitlines()

# 既存のkatakana_map.jsonの読み込み
katakana_map = {}
with open(current_dir / "katakana_map.json", "r") as f:
    katakana_map = json.load(f)

# 500 単語ずつ処理
total_words = len(words)
SIMUL_WORD_COUNT = 500


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


for i in range(0, total_words, SIMUL_WORD_COUNT):
    chunk = words[i : i + SIMUL_WORD_COUNT]
    input_text = "\n".join(chunk)

    # 既存のkatakana_map.jsonを再読み込み
    with open(current_dir / "katakana_map.json", "r") as f:
        katakana_map = json.load(f)

    # 既に処理済みの単語をスキップ
    chunk = [word for word in chunk if word not in katakana_map]
    if not chunk:
        print(
            f"Skipping words {i+1} to {min(i+SIMUL_WORD_COUNT, total_words)} as they are already processed."
        )
        continue

    input_text = "\n".join(chunk)
    new_entries = {}

    max_retries = 30
    retry_delay = 5  # seconds

    while chunk:
        retry_count = 0
        while retry_count < max_retries:
            try:
                print(
                    f"Processing words {i+1} to {min(i+SIMUL_WORD_COUNT, total_words)} out of {total_words}. (chunk: {len(chunk)})"
                )
                # ダミー単語を追加
                # 処理対象の単語リストに含まれないダミーワードを追加
                dummy_words = ['apple', 'banana', 'cherry', 'date', 'watermelon']
                dummy_words = [word for word in dummy_words if word not in chunk]
                input_text_with_dummy = "\n".join(chunk + dummy_words)
                response = get_chat_session().send_message(input_text_with_dummy)

                # レスポンスの解析
                csv_reader = csv.reader(io.StringIO(response.text))
                current_entries = {
                    row[0]: row[1].replace(' ', '') for row in csv_reader if len(row) == 2
                }

                # ダミー単語を除去
                for dummy in dummy_words:
                    current_entries.pop(dummy, None)

                # カタカナ以外の文字が含まれている単語を特定
                non_katakana_words = {
                    word: value
                    for word, value in current_entries.items()
                    if not is_katakana(value)
                }

                # 不足している単語を特定
                missing_words = set(chunk) - set(current_entries.keys())

                # 余分な単語を特定
                extra_words = set(current_entries.keys()) - set(chunk)

                # 問題のない単語を new_entries に追加
                valid_entries = {
                    word: value
                    for word, value in current_entries.items()
                    if word in chunk and is_katakana(value)
                }
                new_entries.update(valid_entries)

                # 問題のある単語のみを次のイテレーションで処理
                chunk = list(non_katakana_words.keys()) + list(missing_words)

                if extra_words:
                    print(f'Extra words: {", ".join(extra_words)}')
                    print(f"Number of extra words: {len(extra_words)}")

                if not chunk:
                    break  # 全ての単語が正しく処理された場合

                print(
                    f'Retrying {len(chunk)} problematic words {", ".join(chunk)} (katakana: {", ".join(non_katakana_words.values())}, missing: {", ".join(missing_words)}) in {retry_delay} seconds...'
                )
                time.sleep(retry_delay)
                break  # 成功したらwhile retry_count ループを抜ける

            except Exception as e:
                retry_count += 1
                print(f"Error processing words: {str(e)}")
                print("Stacktrace:")
                traceback.print_exc()
                if retry_count < max_retries:
                    print(
                        f"Retrying in {retry_delay} seconds... (Attempt {retry_count + 1} of {max_retries})"
                    )
                    time.sleep(retry_delay)
                else:
                    print(
                        f'Max retries reached. Skipping problematic words: {", ".join(chunk)}'
                    )
                    chunk = []  # 最大リトライ回数に達した場合、問題のある単語をスキップ

        if retry_count == max_retries:
            print("Moving to the next chunk due to persistent errors.")
            break

    # 念のためカタカナ語に対し正規化を実行
    sorted_entries = {
        key: normalize_katakana(value) for key, value in new_entries.items()
    }

    # katakana_map.jsonの更新
    katakana_map.update(sorted_entries)
    print(
        f"Added {len(sorted_entries)} new entries to katakana_map. Total entries: {len(katakana_map)}"
    )

    # アルファベット順にソート（キーのみ）
    katakana_map = dict(sorted(katakana_map.items(), key=lambda x: x[0].lower()))

    # 途中経過の保存
    with open(current_dir / "katakana_map.json", "w", encoding="utf-8") as f:
        json.dump(katakana_map, f, ensure_ascii=False, indent=4)

    print(
        f"Response generated successfully. {total_words - (i+SIMUL_WORD_COUNT)} words remaining ({(i+SIMUL_WORD_COUNT)/total_words*100:.2f}% completed)"
    )

print("Processing complete. Results saved to katakana_map.json")
