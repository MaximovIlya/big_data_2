#!/usr/bin/env python3
import subprocess
import time
from cassandra.cluster import Cluster


KEYSPACE = "search_engine"
INDEX_PATH = "/indexer/pipeline1/part-00000"


def wait_for_cassandra(host="cassandra-server", port=9042, retries=20, delay=5):
    for attempt in range(1, retries + 1):
        try:
            cluster = Cluster([host], port=port)
            session = cluster.connect()
            print(f"Connected to Cassandra on attempt {attempt}")
            return cluster, session
        except Exception as e:
            print(f"Waiting for Cassandra ({attempt}/{retries}): {e}")
            time.sleep(delay)
    raise RuntimeError("Could not connect to Cassandra")


def create_schema(session):
    session.execute(f"""
        CREATE KEYSPACE IF NOT EXISTS {KEYSPACE}
        WITH replication = {{'class': 'SimpleStrategy', 'replication_factor': 1}}
    """)

    session.set_keyspace(KEYSPACE)

    session.execute("""
        CREATE TABLE IF NOT EXISTS doc_stats (
            doc_id text PRIMARY KEY,
            title text,
            doc_len int
        )
    """)

    session.execute("""
        CREATE TABLE IF NOT EXISTS postings (
            term text,
            doc_id text,
            title text,
            tf int,
            PRIMARY KEY (term, doc_id)
        )
    """)

    session.execute("""
        CREATE TABLE IF NOT EXISTS corpus_stats (
            stat_name text PRIMARY KEY,
            stat_value double
        )
    """)


def truncate_tables(session):
    session.execute("TRUNCATE doc_stats")
    session.execute("TRUNCATE postings")
    session.execute("TRUNCATE corpus_stats")


def load_index(session):
    insert_doc = session.prepare("""
        INSERT INTO doc_stats (doc_id, title, doc_len)
        VALUES (?, ?, ?)
    """)

    insert_posting = session.prepare("""
        INSERT INTO postings (term, doc_id, title, tf)
        VALUES (?, ?, ?, ?)
    """)

    total_docs = 0
    total_doc_len = 0

    proc = subprocess.Popen(
        ["hdfs", "dfs", "-cat", INDEX_PATH],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )

    for raw_line in proc.stdout:
        line = raw_line.rstrip("\n")
        if not line.strip():
            continue

        parts = line.split("\t")
        record_type = parts[0]

        if record_type == "DOCSTAT":
            if len(parts) != 4:
                continue
            _, doc_id, title, doc_len = parts
            doc_len = int(doc_len)
            session.execute(insert_doc, (doc_id, title, doc_len))
            total_docs += 1
            total_doc_len += doc_len

        elif record_type == "POSTING":
            if len(parts) != 5:
                continue
            _, term, doc_id, title, tf = parts
            tf = int(tf)
            session.execute(insert_posting, (term, doc_id, title, tf))

    stderr = proc.stderr.read()
    return_code = proc.wait()
    if return_code != 0:
        raise RuntimeError(f"hdfs dfs -cat failed: {stderr}")

    avgdl = (total_doc_len / total_docs) if total_docs > 0 else 0.0

    session.execute(
        "INSERT INTO corpus_stats (stat_name, stat_value) VALUES (%s, %s)",
        ("N", float(total_docs))
    )
    session.execute(
        "INSERT INTO corpus_stats (stat_name, stat_value) VALUES (%s, %s)",
        ("avgdl", float(avgdl))
    )

    print(f"Loaded {total_docs} documents")
    print(f"Average document length = {avgdl:.4f}")


def main():
    cluster, session = wait_for_cassandra()
    try:
        create_schema(session)
        truncate_tables(session)
        load_index(session)
        print("Index successfully stored in Cassandra")
    finally:
        session.shutdown()
        cluster.shutdown()


if __name__ == "__main__":
    main()