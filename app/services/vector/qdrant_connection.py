from qdrant_client import AsyncQdrantClient
from qdrant_client.models import Distance,VectorParams
import os

client = AsyncQdrantClient(
    host=os.getenv("QDRANT_HOST"),
    port=int(os.getenv("QDRANT_PORT"))
)

collection_name = os.getenv("COLLECTION_NAME")
size = int(os.getenv("VECTOR_SIZE"))
distance = Distance.COSINE

async def connect_qdrant():
    response = await client.get_collections()
    existing_collections = response.collections

    print(existing_collections)
    collection_found=False

    for i in range(len(existing_collections)):
        if(existing_collections[i].name == collection_name):
            collection_found=True
            break

    if collection_found == False:
        await client.create_collection(
            collection_name=collection_name,
            vectors_config=VectorParams(
                size=size,
                distance=distance
            )
        )

        print(f"{collection_name} created")

    else:
        print(f"{collection_name} already exists")


async def stop_qdrant():
    await client.close()