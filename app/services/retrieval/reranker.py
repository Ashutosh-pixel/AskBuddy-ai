from sentence_transformers import CrossEncoder

class Reranker:
    def __init__(self, model: str):
        self.model = CrossEncoder(model)

    def rerank(self, query:str, chunks:list[str]):

        pairs = [[query,chunk] for chunk in chunks]

        scores = self.model.predict(pairs)

        # results = []

        # for chunk, score in zip(chunks,scores):
        #     results.append({
        #         "text": chunk,
        #         "score": score
        #     })

        # results.sort(
        #     key=lambda x: x["score"],
        #     reverse=True
        # )

        # return results[:top_k]

        return scores