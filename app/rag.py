import os
import torch
import getpass
from dotenv import load_dotenv
from typing import Optional

import numpy as np
from sklearn.metrics.pairwise import cosine_similarity

from langchain.chains import RetrievalQA
from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import HuggingFaceInstructEmbeddings
from langchain_groq import ChatGroq

load_dotenv()

DEVICE = "cuda:0" if torch.cuda.is_available() else "cpu"

llm: Optional[ChatGroq] = None
embeddings: Optional[HuggingFaceInstructEmbeddings] = None
qa_chain: Optional[RetrievalQA] = None
retriever = None

chat_history = []

DOMAIN_DESCRIPTION = """
Coal mining industry regulations, coal mines safety laws,
MMDR Act, Coal Mines Act, DGMS guidelines, mineral concession rules,
coal production, mine closure planning, environmental clearance,
royalty, lease, underground and opencast coal mining,
explosives, blasting, mine inspection, labor safety in mines.
"""

def init_llm():
    """Initialize LLM and embedding model"""
    global llm, embeddings

    if "GROQ_API_KEY" not in os.environ:
        os.environ["GROQ_API_KEY"] = getpass.getpass("Enter GROQ API key: ")

    llm = ChatGroq(model="llama-3.1-8b-instant")

    embeddings = HuggingFaceInstructEmbeddings(
        model_name="sentence-transformers/all-MiniLM-L6-v2"
    )

    print("LLM and embeddings initialized")


def load_faiss_index() -> bool:
    """Load FAISS index if it exists"""
    global qa_chain, retriever

    index_file = os.path.join("faiss_index", "index.faiss")
    if not os.path.exists(index_file):
        qa_chain = None
        retriever = None
        print("FAISS index files not found")
        return False

    db = FAISS.load_local(
        "faiss_index",
        embeddings,
        allow_dangerous_deserialization=True
    )

    retriever = db.as_retriever(
        search_type="mmr",
        search_kwargs={"k": 6, "lambda_mult": 0.25}
    )

    qa_chain = RetrievalQA.from_chain_type(
        llm=llm,
        chain_type="stuff",
        retriever=retriever,
        return_source_documents=False,
        input_key="question",
    )

    print("FAISS index loaded successfully")
    return True

def is_domain_question_semantic(query: str, threshold: float = 0.30) -> bool:
    """
    Semantic check: is the question related to coal/mining domain?
    """
    query_vec = embeddings.embed_query(query)
    domain_vec = embeddings.embed_query(DOMAIN_DESCRIPTION)

    similarity = cosine_similarity(
        [query_vec], [domain_vec]
    )[0][0]

    print(f"Semantic domain similarity: {similarity:.3f}")
    return similarity >= threshold


def has_relevant_retrieval(query: str, min_chars: int = 100) -> bool:
    """
    Retrieval-based fallback: if FAISS finds meaningful content,
    accept the query even if semantic gate fails (MMDR fix).
    """
    if retriever is None:
        return False

    docs = retriever.get_relevant_documents(query)
    combined_text = " ".join(d.page_content for d in docs)

    return len(combined_text.strip()) >= min_chars

def generate_summary(retrieved_text: str, user_query: str) -> str:
    """
    Strictly grounded answer generation.
    """
    prompt = f"""
You are a RESTRICTED AI legal assistant.

STRICT RULES:
- Answer ONLY using the Retrieved Information.
- Answer ONLY questions related to coal mining laws, rules, and regulations.
- DO NOT use general knowledge.
- DO NOT guess or hallucinate.
- If information is insufficient, say you cannot answer.

Retrieved Information:
{retrieved_text}

User Question:
{user_query}

Answer:
"""

    response = ""
    for chunk in llm.stream([{"role": "user", "content": prompt}]):
        response += chunk.content

    return response.strip()

def process_prompt(prompt: str) -> str:
    """
    Full guarded RAG pipeline.
    """
    global chat_history

    semantic_ok = is_domain_question_semantic(prompt)

    retrieval_ok = has_relevant_retrieval(prompt)

    if not semantic_ok and not retrieval_ok:
        return (
            "I can only answer questions related to the coal mining industry, "
            "mining regulations, safety rules, and legal frameworks."
        )

    if qa_chain is None:
        return "Knowledge base not initialized yet."

    result = qa_chain({"question": prompt, "chat_history": chat_history})
    answer = result["result"]

    if not answer or len(answer.strip()) < 30:
        return (
            "I could not find sufficient information in the provided "
            "coal mining regulations to answer this question."
        )

    summary = generate_summary(answer, prompt)
    chat_history.append((prompt, summary))

    return summary
