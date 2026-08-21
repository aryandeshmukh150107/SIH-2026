import re
import html
import unicodedata


def clean_text(text):
    # --------------------------------------------------
    # 1. Unicode normalization
    # --------------------------------------------------
    text = unicodedata.normalize("NFKC", text)

    # --------------------------------------------------
    # 2. Decode HTML entities
    # --------------------------------------------------
    text = html.unescape(text)

    # --------------------------------------------------
    # 3. Remove URLs
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
    # 5. Remove excessive dots
    # "hate.........." -> "hate"
    # --------------------------------------------------
    text = re.sub(r"\.{2,}", " ", text)

    # --------------------------------------------------
    # 6. Reduce repeated ! and ?
    # "terrible!!!!!!" -> "terrible!"
    # "why??????" -> "why?"
    # --------------------------------------------------
    text = re.sub(r"!{2,}", "!", text)
    text = re.sub(r"\?{2,}", "?", text)

    # --------------------------------------------------
    # 7. Remove sequences of obvious punctuation junk
    #
    # Example:
    # "because'];]" -> "because"
    # "[;;]"        -> ""
    #
    # Single apostrophes are preserved so:
    # "don't" stays "don't"
    # "can't" stays "can't"
    # --------------------------------------------------
    junk_pattern = r"""['\[\]{};:`"|\\/]{2,}"""
    text = re.sub(junk_pattern, " ", text)

    # --------------------------------------------------
    # 8. Normalize whitespace
    # --------------------------------------------------
    text = re.sub(r"\s+", " ", text)

    # --------------------------------------------------
    # 9. Remove spaces before punctuation
    # "good !" -> "good!"
    # --------------------------------------------------
    text = re.sub(r"\s+([,.!?%])", r"\1", text)

    # --------------------------------------------------
    # 10. Final cleanup
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