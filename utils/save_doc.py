import json
from datetime import datetime
import os
from os import listdir
from os.path import isfile, join
from dotenv import load_dotenv
from models import JJBDocument

load_dotenv()

# ─────────────────────────────────────────────
# 💾 Save document
# ─────────────────────────────────────────────
def save_document(doc: JJBDocument) -> str:
    """Saves the structured document as JSON and TXT in /data with format yyyy_mm_dd_title."""
    
    # Convert date from dd/mm/yyyy to yyyy_mm_dd
    try:
        parsed_date = datetime.strptime(doc.date, "%d/%m/%Y")
        formatted_date = parsed_date.strftime("%Y_%m_%d")
    except ValueError:
        formatted_date = doc.date.replace("/", "_")

    clean_title = doc.title.replace(" ", "_")
    core_title = f"{formatted_date}_{clean_title}"
    base_path_json = "data/json/"+core_title
    base_path_txt = "data/txt/"+core_title

    # Save JSON
    with open(f"{base_path_json}.json", "w", encoding="utf-8") as f:
        json.dump(doc.model_dump(), f, indent=2, ensure_ascii=False)

    # Save TXT (clean readable version)
    with open(f"{base_path_txt}.txt", "w", encoding="utf-8") as f:
        f.write(f"Title: {doc.title}\n")
        f.write(f"Date: {doc.date}\n")
        f.write(f"Type: {doc.doc_type}\n")
        f.write(f"Created: {doc.created_at}\n")
        f.write("\n" + "─" * 40 + "\n\n")
        for i, text in enumerate(doc.extracted_texts, 1):
            f.write(f"[ Page {i} ]\n{text}\n\n")

    return base_path_json, base_path_txt


def save_doc_db(note_path : str,path_txt = "data/txt" ) : 
    
    from langchain.chat_models import init_chat_model
    from langchain_huggingface import HuggingFaceEmbeddings
    from langchain_chroma import Chroma
    from langchain_core.documents import Document

    os.environ["ANTHROPIC_API_KEY"] = os.getenv("ANTHROPIC_API_KEY") 
    os.environ["HUGGINGFACEHUB_API_TOKEN"] = os.getenv("HF_TOKEN")

    #model = init_chat_model("claude-sonnet-4-6")
    embeddings = HuggingFaceEmbeddings(model_name="microsoft/harrier-oss-v1-270m")

    vector_store = Chroma(
        collection_name="jjb_notes",
        embedding_function=embeddings,
        persist_directory="data/chroma_langchain_db",
    )

    nb_docs = vector_store._collection.count()
    note_txt = open(path_txt+'/'+note_path, 'r', encoding='utf-8')
    content = note_txt.read()
    date = note_path[:10]
    date = date[-2:] + '/' + date[-5:-3] + '/' + date[:4]
    theme = note_path[11:-4].replace('_', ' ')
    doc = Document(id=str(nb_docs+1), page_content=content, metadata={"title": theme, 'date': date})

    vector_store.add_documents([doc])

    return(True)