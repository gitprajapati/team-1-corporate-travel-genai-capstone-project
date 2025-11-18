from pymilvus import connections, utility, Collection, FieldSchema, CollectionSchema, DataType
from src.config.settings import settings

MILVUS_URI = settings.MILVUS_URI
MILVUS_TOKEN = settings.MILVUS_TOKEN
COLLECTION_NAME = settings.MILVUS_COLLECTION_NAME
DIM = settings.MILVUS_DIM
VECTOR_FIELD = settings.MILVUS_VECTOR_FIELD
TEXT_FIELD = settings.MILVUS_TEXT_FIELD

def connect():
    connections.connect(uri=MILVUS_URI, token=MILVUS_TOKEN)

def ensure_collection():
    connect()
    if utility.has_collection(COLLECTION_NAME):
        return
    fields = [
        FieldSchema(name="id", dtype=DataType.INT64, is_primary=True, auto_id=True),
        FieldSchema(name="embedding", dtype=DataType.FLOAT_VECTOR, dim=DIM),
        FieldSchema(name="text", dtype=DataType.VARCHAR, max_length=65535)
    ]
    schema = CollectionSchema(fields, description="travel policy store")
    Collection(name=COLLECTION_NAME, schema=schema)

def upsert(texts, embeddings):
    """
    texts: list[str], embeddings: list[list[float]]
    """
    connect()
    ensure_collection()
    col = Collection(COLLECTION_NAME)
    entities = [
        embeddings,
        texts
    ]
    # pymilvus expects column-wise data; using field order
    col.insert([None, embeddings, texts])  # None for auto id
    col.flush()

def search(query_embedding, top_k=4):
    connect()
    col = Collection(COLLECTION_NAME)
    search_params = {"metric_type":"L2", "params":{"nprobe":10}}
    res = col.search(
        [query_embedding],
        VECTOR_FIELD,
        search_params,
        top_k,
        output_fields=[TEXT_FIELD],
    )
    # res is list of QueryResult
    hits = []
    for hit in res[0]:
        hits.append({"id": hit.id, "text": hit.entity.get(TEXT_FIELD)})
    return hits
