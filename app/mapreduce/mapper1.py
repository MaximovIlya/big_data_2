import sys
import re

TOKEN_PATTERN = re.compile(r"[a-z0-9]+")


def tokenize(text: str):
    text = text.lower()
    return TOKEN_PATTERN.findall(text)


def main():
    for raw_line in sys.stdin:
        line = raw_line.rstrip("\n")

        if not line.strip():
            continue

        parts = line.split("\t", 2)
        if len(parts) != 3:
            continue

        doc_id, doc_title, doc_text = parts
        doc_id = doc_id.strip()
        doc_title = doc_title.strip()
        doc_text = doc_text.strip()

        if not doc_id or not doc_title or not doc_text:
            continue

        tokens = tokenize(doc_text)
        doc_len = len(tokens)

        if doc_len == 0:
            continue

        
        print(f"DOC\t{doc_id}\t{doc_title}\t{doc_len}")

        
        for term in tokens:
            print(f"TERM\t{term}\t{doc_id}\t{doc_title}\t1")


if __name__ == "__main__":
    main()