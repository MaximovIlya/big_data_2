#!/usr/bin/env python3
import math
import re
import sys
from collections import defaultdict

from cassandra.cluster import Cluster

KEYSPACE = "search_engine"
K1 = 1.5
B = 0.75

TOKEN_PATTERN = re.compile(r"[a-z0-9]+")


def tokenize(text: str):
    return TOKEN_PATTERN.findall(text.lower())


def connect():
    cluster = Cluster(["cassandra-server"], port=9042)
    session = cluster.connect(KEYSPACE)
    return cluster, session


def get_corpus_stats(session):
    rows = session.execute("SELECT stat_name, stat_value FROM corpus_stats")
    stats = {row.stat_name: row.stat_value for row in rows}
    return stats


def get_postings_for_term(session, term: str):
    rows = session.execute(
        "SELECT term, doc_id, title, tf FROM postings WHERE term = %s",
        (term,)
    )
    return list(rows)


def get_doc_len(session, doc_id: str):
    row = session.execute(
        "SELECT doc_len FROM doc_stats WHERE doc_id = %s",
        (doc_id,)
    ).one()
    return row.doc_len if row else None


def bm25_score(tf, df, N, dl, avgdl, k1=K1, b=B):
    if df == 0 or avgdl == 0:
        return 0.0

    idf = math.log(N / df)
    numerator = (k1 + 1) * tf
    denominator = k1 * ((1 - b) + b * (dl / avgdl)) + tf
    return idf * (numerator / denominator)


def main():
    if len(sys.argv) > 1:
        query_text = " ".join(sys.argv[1:])
    else:
        query_text = sys.stdin.read().strip()

    if not query_text:
        print("Empty query")
        return

    query_terms = tokenize(query_text)
    if not query_terms:
        print("No valid query terms")
        return

    cluster, session = connect()
    try:
        stats = get_corpus_stats(session)
        N = stats.get("N", 0.0)
        avgdl = stats.get("avgdl", 0.0)

        if N == 0 or avgdl == 0:
            print("Corpus stats are missing")
            return

        scores = defaultdict(float)
        titles = {}

        for term in query_terms:
            postings = get_postings_for_term(session, term)
            df = len(postings)

            if df == 0:
                continue

            for row in postings:
                doc_id = row.doc_id
                title = row.title
                tf = row.tf

                dl = get_doc_len(session, doc_id)
                if dl is None:
                    continue

                score = bm25_score(tf=tf, df=df, N=N, dl=dl, avgdl=avgdl)
                scores[doc_id] += score
                titles[doc_id] = title

        ranked = sorted(scores.items(), key=lambda x: x[1], reverse=True)[:10]

        if not ranked:
            print("No matching documents found")
            return

        for rank, (doc_id, score) in enumerate(ranked, start=1):
            print(f"{rank}\t{doc_id}\t{titles[doc_id]}\t{score:.6f}")

    finally:
        session.shutdown()
        cluster.shutdown()


if __name__ == "__main__":
    main()