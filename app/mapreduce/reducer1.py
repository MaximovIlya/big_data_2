import sys
from collections import defaultdict

doc_stats = {}
term_doc_tf = defaultdict(int)
term_doc_title = {}

for raw_line in sys.stdin:
    line = raw_line.rstrip("\n")
    if not line.strip():
        continue

    parts = line.split("\t")
    record_type = parts[0]

    if record_type == "DOC":
        if len(parts) != 4:
            continue
        _, doc_id, doc_title, doc_len = parts
        try:
            doc_len = int(doc_len)
        except ValueError:
            continue
        doc_stats[doc_id] = (doc_title, doc_len)

    elif record_type == "TERM":
        if len(parts) != 5:
            continue
        _, term, doc_id, doc_title, one = parts
        try:
            one = int(one)
        except ValueError:
            continue

        term_doc_tf[(term, doc_id)] += one
        term_doc_title[(term, doc_id)] = doc_title


for doc_id, (doc_title, doc_len) in doc_stats.items():
    print(f"DOCSTAT\t{doc_id}\t{doc_title}\t{doc_len}")


for (term, doc_id), tf in term_doc_tf.items():
    doc_title = term_doc_title[(term, doc_id)]
    print(f"POSTING\t{term}\t{doc_id}\t{doc_title}\t{tf}")