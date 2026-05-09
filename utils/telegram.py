
from models import SessionState, JJBDocument
import os
import requests
from datetime import datetime
from dotenv import load_dotenv
import re

from utils.ocr import run_ocr_on_url
from utils.save_doc import save_document, save_doc_db
from utils.rag import RAG

load_dotenv()

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_API = f"https://api.telegram.org/bot{BOT_TOKEN}"

sessions: dict = {}

def get_session(user_id: str) -> SessionState:
    if user_id not in sessions:
        sessions[user_id] = SessionState()
    return sessions[user_id]
# ─────────────────────────────────────────────
# 📤 Send message back to Telegram
# ─────────────────────────────────────────────
def send_message(chat_id: str, text: str):
    requests.post(f"{TELEGRAM_API}/sendMessage", json={
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "Markdown"
    })

# ─────────────────────────────────────────────
# 📥 Get image URL from Telegram file_id
# ─────────────────────────────────────────────
def get_file_url(file_id: str) -> str:
    res = requests.get(f"{TELEGRAM_API}/getFile?file_id={file_id}")
    file_path = res.json()["result"]["file_path"]
    return f"https://api.telegram.org/file/bot{BOT_TOKEN}/{file_path}"

# ─────────────────────────────────────────────
# 🤖 State machine handler
# ─────────────────────────────────────────────
def handle_message(user_id: str, text: str = None, image_url: str = None) -> str:
    session = get_session(user_id)
    text = (text or "").strip()

    # Reset anytime
    if text.upper() == "/RESET":
        sessions[user_id] = SessionState()
        return "🔄 Session reset. Send *GO* to start."

    # IDLE — waiting for GO
    if session.state == "IDLE":
        if text.upper() == "GO":
            session.state = "WAITING_TASK"
            return "👋 What kind of task would you like to perform? OCR or RAG?"
        return "Send *GO* to start the OCR process."

    # Waiting for OCR type
    elif session.state == "WAITING_TASK":
        if text.lower() == "ocr":
            session.doc_type = "ocr"
            session.state = "WAITING_DATE"
            return "📅 What is the date of the document? (e.g. 12/03/2026)"
        elif text.lower() == "rag":
            session.doc_type = "rag"
            session.state = "WAITING_QUERY"
            return("What is your question?")
        return f"❓ Unknown type *{text}*. Currently supported: *ocr* or *rag*."


    #### OCR ####

    # Waiting for date
    elif session.state == "WAITING_DATE":
        session.date = text
        session.state = "WAITING_TITLE"
        return "📝 What is the title of the document?"

    # Waiting for title
    elif session.state == "WAITING_TITLE":
        session.title = text
        session.state = "WAITING_IMAGES"
        return "📸 Got it! Send your pictures one by one. Type *DONE* when finished."

    # Waiting for images or DONE
    elif session.state == "WAITING_IMAGES":
        if image_url:
            extracted = run_ocr_on_url(image_url)
            session.extracted_texts = session.extracted_texts + [extracted]
            return (
                f"✅ Image {len(session.extracted_texts)} processed!\n\n"
                f"`{extracted[:300]}`\n\n"
                f"Send more images or type *DONE*."
            )

        if text.upper() == "DONE":
            if not session.extracted_texts:
                return "⚠️ No images received yet. Please send at least one picture."

            doc = JJBDocument(
                title=session.title,
                date=session.date,
                extracted_texts=session.extracted_texts
            )
            filepath_json, filepath_txt = save_document(doc)

            print(f"\n{'#'*20}\n filepath_txt = {filepath_txt} \n{'#'*20}\n")

            save_doc_bool = save_doc_db(filepath_txt + ".txt") # Save doc in db 
            
            sessions[user_id] = SessionState()  # reset session

            if save_doc_bool: 
                return (
                f"🎉 Done! Documents saved:\n"
                f"📄 `{filepath_json}.json`\n"
                f"📝 `{filepath_txt}.txt`\n\n"
                f"*{doc.title}* — {doc.date}\n"
                f"🖼️ {len(doc.extracted_texts)} image(s) processed\n\n"
                f"💾 Added to the jjb database.\n\n"
                f"Send *GO* to start a new task."
                )

            else : 
                return (
                    f"🎉 Done! Documents saved:\n"
                    f"📄 `{filepath_json}.json`\n"
                    f"📝 `{filepath_txt}.txt`\n\n"
                    f"*{doc.title}* — {doc.date}\n"
                    f"🖼️ {len(doc.extracted_texts)} image(s) processed\n\n"
                    f"Send *GO* to start a new task."
                    )

        return "📸 Send a picture, or type *DONE* when finished."


    #### RAG ####

    elif session.state == "WAITING_QUERY":
        session.query = text
        try:
            print("⏳ Processing your query, please wait...") # change the print such that it appears for the user.
            rag = RAG(session.query)
            session.rag = rag  
            session.retrieval = rag.retrieval()
            session.state = "WAITING_DOC_NB"
            
            #sessions[user_id] = SessionState()  # reset session
            return ( # 4096 tokens max for telegram
                f"🎉 Here are the most relevant documents regarding your query.\n"
                f"{session.retrieval}\n"
                f"Send *RANK NUMBER* if you want to see a particular document.\nSend *QUERY* if you want to ask something else.\nSend *GO* otherwise."
            )
            
        except Exception as e:
            print(f"RAG error: {e}")
            return f"❌ Error during RAG: {str(e)}"
        
    elif session.state == "WAITING_DOC_NB":
        print(f"in")
        session.doc_id = text
        if text.upper() == "GO":
            sessions[user_id] = SessionState()  # reset session
        elif text.upper() == "QUERY":
            session.state == "WAITING_QUERY"
        else:
            doc_id = re.findall(r'\d+', session.doc_id)
            if doc_id == []:
                session.state == "WAITING_DOC_NB"
                return("⚠️ Invalid number. Please try again.")
        
            try : 
                #rag = RAG(session.query)
                #session.retrieval = rag.retrieval()
                answer = session.rag.export_document_2(rank=int(doc_id[0]))
                session.state == "WAITING_DOC_NB"
                return(f"Here is your document:\n{answer}\n\nSend *RANK NUMBER* if you want to see a particular document.\nSend *QUERY* if you want to ask something else.\nSend *GO* otherwise.")
                #filepath = session.rag.export_document(rank=int(doc_id[0]))
                #send_document(chat_id, filepath, caption=f"📄 Document n°{int(doc_id[0])}")
                #return "📨 Document sent! Send another rank number or *GO* to continue."
            
            except: 
                session.state == "WAITING_DOC_NB"
                return("Error occured.")

    
        
        
    return "Something went wrong. Type */reset* to restart."