import os
from os import listdir
from os.path import isfile, join
from langchain.chat_models import init_chat_model
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma
from langchain_core.documents import Document
import tqdm

os.environ["ANTHROPIC_API_KEY"] = os.getenv("ANTHROPIC_API_KEY")
os.environ["HUGGINGFACEHUB_API_TOKEN"] = os.getenv("HF_TOKEN")
model = init_chat_model("claude-sonnet-4-6")
embeddings = HuggingFaceEmbeddings(model_name="microsoft/harrier-oss-v1-270m")
# Load database
vector_store = Chroma(
    collection_name="jjb_notes",
    embedding_function=embeddings,
    persist_directory="data/chroma_langchain_db",  # Where to save data locally, remove if not necessary
    )


class RAG:

    def __init__(self, query):
        self.query = query
        self.model = model
        self.embeddings = embeddings
        self.vector_store = vector_store
        self.k = 3
        self._results = []  

    def retrieval(self):
        """Retrieve the k most relevant documents and return only title + score."""
        results = self.vector_store.similarity_search_with_score(query=self.query, k=self.k)

        # Store results for potential export (most relevant first)
        self._results = sorted(results, key=lambda x: x[1])
        self._results = self._results[::-1]  # Go from the most relevant to the least

        answer = "📋 *Top matching documents:*\n\n"
        for rank, (doc, score) in enumerate(self._results, start=1):
            title = (
                doc.metadata.get("title")
                or "Untitled"
            )
            date = (
                doc.metadata.get("date")
                or ""
            )

            if "/" in str(title):
                title = str(title).split("/")[-1]
            if date != "":
                answer += f"{rank}. 📄 *{title} - {date}*\n   Score: `{score:.4f}`\n\n"
            else: 
                answer += f"{rank}. 📄 *{title}*\n   Score: `{score:.4f}`\n\n"

        return answer

    def export_document(self, rank=1, output_dir="exports"):
        """
        Export the full content of a retrieved document as a .txt file.

        Args:
            rank (int): Which result to export (1 = most relevant).
            output_dir (str): Directory where the .txt file will be saved.

        Returns:
            str: Path to the exported file, or an error message.
        """
        if not self._results:
            return "⚠️ No results available. Run retrieval() first."

        if rank < 1 or rank > len(self._results):
            return f"⚠️ Invalid rank. Choose between 1 and {len(self._results)}."

        doc, score = self._results[rank - 1]

        title = (
            doc.metadata.get("title")
            or doc.metadata.get("source")
            or doc.metadata.get("file_name")
            or f"document_{rank}"
        )
        if "/" in str(title):
            title = str(title).split("/")[-1]

        # Sanitize filename
        safe_title = "".join(c if c.isalnum() or c in " _-." else "_" for c in title)
        filename = f"{safe_title}.txt" if not safe_title.endswith(".txt") else safe_title

        os.makedirs(output_dir, exist_ok=True)
        filepath = os.path.join(output_dir, filename)

        with open(filepath, "w", encoding="utf-8") as f:
            f.write(f"Title: {title}\n")
            f.write(f"Similarity Score: {score:.4f}\n")
            f.write(f"Metadata: {doc.metadata}\n")
            f.write(f"{'='*50}\n\n")
            f.write(doc.page_content)

        return filepath
    
    def export_document_2(self, rank):
        """The goal of this function is to retrieve the k most relevant documents based on the user query."""
        # Compute similarity between the user query and db
        if not self._results:
            return "⚠️ No results available. Run retrieval() first."
        if rank < 1 or rank > len(self._results):
            return f"⚠️ Invalid rank. Choose between 1 and {len(self._results)}."
        
        doc, score = self._results[rank-1]
        title = doc.metadata.get("title", "Untitled")
        header = f"📄 *{title}*\nScore: `{score:.4f}`\n\n"
        max_content = 4096 - len(header) - 160

        if len(doc.page_content) > max_content:
            content = doc.page_content[:max_content] + "\n..."
        else:
            content = doc.page_content
        return header + content
    
    def generate_answer(self): 

        """Based on user query and k documents retrieved, generate answer."""

        # RUn retrieval

        k_doc_retrieved = self.retrieval(self.query)

        prompt = f"""You are a black belt in Brazilian Jiu-Jitsu (BJJ), with a specialty in nogi (no-gi) grappling.
                    Given the user query and handwritten notes in french, respond to his/her question based on the context you receive. 
                    The notes may contain French words mixed with English BJJ/grappling terminology
                    At the end of your message, mention the titles of the document you based your analyze on and their dates.
                    User query: {self.query}
                    Notes: {k_doc_retrieved}.
                    """
         # Run model using langchain.


