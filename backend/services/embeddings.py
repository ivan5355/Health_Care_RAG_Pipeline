from services.bedrock_client import invoke_model


def generate_embedding(text: str) -> list[float]:
    result = invoke_model("amazon.titan-embed-text-v2:0", {"inputText": text})
    return result["embedding"]


def generate_embeddings_batch(texts: list[str]) -> list[list[float]]:
    return [generate_embedding(text) for text in texts]
