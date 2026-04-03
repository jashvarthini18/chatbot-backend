import fitz 
from langchain.docstore.document import Document
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS


def process_document(pdf_path: str, embeddings):
    doc = fitz.open(pdf_path)
    full_text = ""

    for page in doc:
        full_text += page.get_text("text") + "\n"

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=3000,
        chunk_overlap=200
    )

    chunks = splitter.split_text(full_text)
    documents = [Document(page_content=chunk) for chunk in chunks]

    db = FAISS.from_documents(documents, embeddings)
    db.save_local("./faiss_index")
