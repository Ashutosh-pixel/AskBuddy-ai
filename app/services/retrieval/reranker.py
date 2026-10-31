from sentence_transformers import CrossEncoder

class Reranker:
    def __init__(self, model: str):
        self.model = CrossEncoder(model)

    def rerank(self, queries: list[str], chunks: list[str]):

        pairs = [
            [query, chunk]
            for query in queries
            for chunk in chunks
        ]

        scores = self.model.predict(pairs)

        # Reshape scores: queries x chunks
        scores = scores.reshape(len(queries), len(chunks))

        # Take maximum score for each chunk
        final_scores = scores.max(axis=0)

        return final_scores