from datetime import datetime
from pydantic import BaseModel
from typing import Optional, List, Any


# ─────────────────────────────────────────────
# 📐 Pydantic model
# ─────────────────────────────────────────────
class JJBDocument(BaseModel):
    doc_type: str = "jjb"
    title: str
    date: str
    extracted_texts: List[str]
    created_at: str = datetime.now().isoformat()

# ─────────────────────────────────────────────
# 🧠 Session memory
# ─────────────────────────────────────────────
class SessionState(BaseModel):
    model_config = {"arbitrary_types_allowed": True}  # 👈 required for non-Pydantic types

    state: str = "IDLE"
    doc_type: Optional[str] = None
    date: Optional[str] = None
    title: Optional[str] = None
    query: Optional[str] = None
    rag : Optional[Any] = None
    retrieval: Optional[str] = None 
    doc_id: Optional[str] = None 
    extracted_texts: List[str] = []