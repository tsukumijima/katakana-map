import re
from pathlib import Path

import requests


def download_cmudict() -> str:
    url = "https://github.com/cmusphinx/cmudict/raw/master/cmudict.dict"
    response = requests.get(url)
    return response.text


def extract_words(cmudict_content: str, output_file: Path) -> None:
    words = set()

    for line in cmudict_content.splitlines():
        # Skip comments and empty lines
        if line.startswith(";;;") or line.strip() == "":
            continue

        # Extract the word, removing pronunciation variants
        word = re.split(r"\s+", line)[0].split("(")[0].lower()

        # Remove apostrophes and periods from the word
        word = word.replace("'", "").replace(".", "")

        # Add the word to the set
        # 1文字以下の単語は除外
        if len(word) > 1:
            words.add(word)

    # Sort the words alphabetically
    sorted_words = sorted(words)

    # Write the sorted words to the output file
    with open(output_file, "w", encoding="utf-8") as f:
        for word in sorted_words:
            f.write(word + "\n")

    print(f"Extracted {len(sorted_words)} unique words.")


# Usage
current_dir = Path(__file__).parent
output_file = current_dir / "cmudict_words.txt"
cmudict_content = download_cmudict()
extract_words(cmudict_content, output_file)
