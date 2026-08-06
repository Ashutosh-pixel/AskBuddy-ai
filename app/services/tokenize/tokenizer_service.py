class Chunker:
    def __init__(self, tokenizer, chunkSize:int=200, overlap:int=10):
        self.tokenizer = tokenizer
        self.chunk_Size = chunkSize
        self.overlap = overlap


    def countToken(self, text:str):
        count = len(self.tokenizer(text)["input_ids"])
        return count


    def recursive_split(self, text: str, separator_index: int, separators, chunkSize: int):
        if separator_index == len(separators) - 1:
            str = ""
            result = []
            for item in text:
                if self.countToken(item+str) > chunkSize:
                    result.append(str)
                    str = ""

                str += item

            result.append(str)
            return result

        elif separator_index >= len(separators):
            return []

        elif self.countToken(text) <= chunkSize:
            result = [text]
            return result

        chunks = []
        parts = text.split(separators[separator_index])

        for i in range(len(parts)):
            if self.countToken(parts[i] + separators[separator_index]) > chunkSize:
                chunks.extend(
                    self.recursive_split(
                        parts[i] + separators[separator_index],
                        separator_index + 1,
                        separators,
                        chunkSize,
                    )
                )
            else:
                chunk = parts[i] + separators[separator_index]
                if chunk.strip():
                    chunks.append(chunk)

        return chunks


    def merge_chunks(self, result, chunkSize: int):
        current_chunk = ""
        chunks = []
        for i in range(len(result)):
            if result[i].strip() == "":
                continue

            elif self.countToken(current_chunk + result[i]) <= chunkSize:
                current_chunk += result[i]

            else:
                chunks.append(current_chunk)
                current_chunk = ""
                current_chunk += result[i]

        if self.countToken(current_chunk) > 0:
            chunks.append(current_chunk)

        return chunks

    def overlap_chunks(self, chunks, overlap_words=20):
        final = [chunks[0]]

        for i in range(1, len(chunks)):
            words = chunks[i-1].split()

            overlap = " ".join(words[-overlap_words:])

            final.append(overlap + " " + chunks[i])

        return final


    def chunk(self, text: str=""):

        separators = ["\n\n", "\n", ". ", " ", ""]
        separator_index = 0
        chunks = self.merge_chunks(self.recursive_split(text, separator_index, separators, self.chunk_Size), self.chunk_Size)

        final_chunks = self.overlap_chunks(chunks, self.overlap);

        totalsize = 0
        for i in range(len(final_chunks)):
            print(f"{self.countToken(final_chunks[i])} {final_chunks[i]}")
            # totalsize += self.countToken(final_chunks[i])

        # print(totalsize)

        return final_chunks