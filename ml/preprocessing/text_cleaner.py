import re
import html
import unicodedata
import emoji


def clean_text(text):
    # --------------------------------------------------
    # 1. Unicode normalization
    # --------------------------------------------------
    text = unicodedata.normalize("NFKC", text)

    # --------------------------------------------------
    # 2. Convert to lowercase
    # --------------------------------------------------
    text = text.lower()

    # --------------------------------------------------
    # 3. Decode HTML entities
    # --------------------------------------------------
    text = html.unescape(text)

    # --------------------------------------------------
    # 4. Remove URLs
    # --------------------------------------------------
    text = re.sub(
        r"https?://\S+|www\.\S+",
        "",
        text,
        flags=re.IGNORECASE
    )

    # --------------------------------------------------
    # 4. Remove invisible/control characters
    # --------------------------------------------------
    cleaned_chars = []

    for char in text:
        category = unicodedata.category(char)

        if category.startswith("C") and char not in ("\n", "\t"):
            continue

        cleaned_chars.append(char)

    text = "".join(cleaned_chars)

    # --------------------------------------------------
    # 5. Translate emojis
    # "😡" -> "[pouting face]"
    # --------------------------------------------------
    text = emoji.demojize(text, delimiters=(" [", "] "))
    text = re.sub(r"\[([a-zA-Z0-9_]+)\]", lambda m: f"[{m.group(1).replace('_', ' ')}]", text)

    # --------------------------------------------------
    # 6. Remove special characters (e.g., #, @)
    # --------------------------------------------------
    text = re.sub(r"[@#^&*+~|<>]", " ", text)

    # --------------------------------------------------
    # 7. Reduce repeating letters
    # "sooooo" -> "soo"
    # --------------------------------------------------
    text = re.sub(r"([a-zA-Z])\1{2,}", r"\1\1", text)

    # --------------------------------------------------
    # 8. Remove excessive dots
    # "hate.........." -> "hate"
    # --------------------------------------------------
    text = re.sub(r"\.{2,}", " ", text)

    # --------------------------------------------------
    # 9. Reduce repeated ! and ?
    # "terrible!!!!!!" -> "terrible!"
    # "why??????" -> "why?"
    # --------------------------------------------------
    text = re.sub(r"!{2,}", "!", text)
    text = re.sub(r"\?{2,}", "?", text)

    # --------------------------------------------------
    # 10. Remove sequences of obvious punctuation junk
    # --------------------------------------------------
    junk_pattern = r"""['\[\]{};:`"|\\/]{2,}"""
    text = re.sub(junk_pattern, " ", text)

    # --------------------------------------------------
    # 11. Normalize whitespace
    # --------------------------------------------------
    text = re.sub(r"\s+", " ", text)

    # --------------------------------------------------
    # 12. Remove spaces before punctuation
    # "good !" -> "good!"
    # --------------------------------------------------
    text = re.sub(r"\s+([,.!?%])", r"\1", text)

    # --------------------------------------------------
    # 13. Final cleanup
    # --------------------------------------------------
    text = text.strip()

    return text


def main():

    print("=" * 60)
    print("           SIH-2026 TEXT PREPROCESSOR")
    print("=" * 60)
    print("Enter a comment to preprocess.")
    print("Type 'exit' to stop.")
    print()

    while True:

        original = input("Enter comment: ")

        if original.strip().lower() == "exit":
            print("\nExiting...")
            break

        if not original.strip():
            print("Please enter a comment.\n")
            continue

        cleaned = clean_text(original)

        print()
        print("-" * 60)

        print("ORIGINAL:")
        print(original)

        print()
        print("CLEANED:")
        print(cleaned)

        print("-" * 60)
        print()


if __name__ == "__main__":
    main()