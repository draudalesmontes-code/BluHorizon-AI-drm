import tiktoken
from sentence_transformers import SentenceTransformer 

_model = SentenceTransformer("all-MiniLM-L6-v2")

_tokenizer = tiktoken.get_encoding("cl100k_base")

def embed_text(text:str)-> list[float]:
   return _model.encode(text).tolist

def embed_batch(texts: list[str]) -> list[list[float]]:
   return _model.encode(texts).tolist()

def chunk_text(text:str, max_tokens:int = 300, overlap:int = 50) -> list[str]:
   token_ids = _tokenizer.encode(text)
   chunks = []
   start = 0
   while start < len(token_ids):
    end = start + max_tokens
    chunk_ids = token_ids[start:end]
    chunk_text = _tokenizer.decode(chunk_ids).strip()
    chunks.append(chunk_text)
    start += max_tokens - overlap

   return [c for c in chunks if c]
      


