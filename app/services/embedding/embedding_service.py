class Embedding:
    def __init__(self, model):
        self.model=model

    def embed_chunks(self,chunks):
        embeddings = []
        for chunk in chunks:
            embed = self.model.encode(chunk)
            embeddings.append(embed)
            print(f"embedding = {embed}")

        # print(f"embeddings = {embeddings}")            
        return embeddings