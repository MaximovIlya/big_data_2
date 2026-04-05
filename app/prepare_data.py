import os
import shutil
from pathvalidate import sanitize_filename
from pyspark.sql import SparkSession
from pyspark.sql.functions import col, trim, length
import unicodedata
import re



APP_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.dirname(APP_DIR)

LOCAL_DATA_DIR = os.path.join(APP_DIR, "data")
LOCAL_TMP_INPUT_DIR = os.path.join(APP_DIR, "prepared_input")

PARQUET_PATH = os.environ.get("PARQUET_PATH", "file:///app/a.parquet")
N_DOCS = int(os.environ.get("N_DOCS", "1000"))



def safe_title(title: str) -> str:
    title = title if title else "untitled"
    title = unicodedata.normalize("NFKD", title)
    title = title.encode("ascii", "ignore").decode("ascii")
    title = title.replace(" ", "_")
    title = re.sub(r"[^A-Za-z0-9._-]", "_", title)
    title = re.sub(r"_+", "_", title).strip("._")
    return title[:150] if title else "untitled"


def prepare_dirs():
    if os.path.exists(LOCAL_DATA_DIR):
        shutil.rmtree(LOCAL_DATA_DIR)
    if os.path.exists(LOCAL_TMP_INPUT_DIR):
        shutil.rmtree(LOCAL_TMP_INPUT_DIR)

    os.makedirs(LOCAL_DATA_DIR, exist_ok=True)
    os.makedirs(LOCAL_TMP_INPUT_DIR, exist_ok=True)


def main():
    spark = (
        SparkSession.builder
        .appName("data preparation")
        .master("local[*]")
        .config("spark.sql.parquet.enableVectorizedReader", "true")
        .getOrCreate()
    )

    df = spark.read.parquet(PARQUET_PATH)

    
    df = (
        df.select("id", "title", "text")
        .where(col("id").isNotNull())
        .where(col("title").isNotNull())
        .where(col("text").isNotNull())
        .where(length(trim(col("text"))) > 0)
        .where(length(trim(col("title"))) > 0)
    )

   
    sampled = df.limit(N_DOCS)

    rows = sampled.collect()

    prepare_dirs()

    prepared_lines = []

    for row in rows:
        doc_id = str(row["id"]).strip()
        title = str(row["title"]).strip()
        text = str(row["text"]).strip()

        clean_title = safe_title(title)
        filename = f"{doc_id}_{clean_title}.txt"
        filepath = os.path.join(LOCAL_DATA_DIR, filename)

        with open(filepath, "w", encoding="utf-8") as f:
            f.write(text)

        prepared_lines.append(f"{doc_id}\t{title}\t{text}")

   
    local_tsv_path = os.path.join(LOCAL_TMP_INPUT_DIR, "part-00000")
    with open(local_tsv_path, "w", encoding="utf-8") as f:
        for line in prepared_lines:
            f.write(line.replace("\n", " ").replace("\r", " ") + "\n")

    print(f"Prepared {len(rows)} documents")
    print(f"Documents saved to: {LOCAL_DATA_DIR}")
    print(f"Indexer input saved to: {local_tsv_path}")

    spark.stop()


if __name__ == "__main__":
    main()