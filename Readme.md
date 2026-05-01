# 🥋 BJJ Notes RAG — Telegram-based retrieval agent for handwritten grappling notes

A personal RAG (Retrieval-Augmented Generation) system built around a real problem: after years of taking handwritten notes during Brazilian Jiu-Jitsu (nogi) sessions, finding a specific technique buried in a stack of notebooks became impossible. This project solves that by turning every handwritten page into a searchable, queryable knowledge base — all accessible from Telegram.

---

## How it works

1. **Upload** a photo of your handwritten notes directly in Telegram.
2. **OCR** — Claude Vision transcribes the image, with domain awareness of BJJ/nogi terminology (French + English mixed), positions, submissions, and concepts.
3. **Storage** — the transcribed note is saved in both `.txt` and `.json` format.
4. **Embedding** — each document is embedded using [`microsoft/harrier-oss-v1-270m`](https://huggingface.co/microsoft/harrier-oss-v1-270m).
5. **Query** — send a text query via Telegram (e.g. *"heel hook from outside sankaku"*) and the agent retrieves the 3 most relevant notes using vector similarity search.

```
Phone camera → Telegram → FastAPI webhook → Claude OCR → Embedding → Vector store
                                                                            ↑
                                         Query via Telegram ────────────────┘
```

---

## Stack

| Component | Technology |
|---|---|
| Interface | Telegram Bot API |
| Backend | FastAPI + uvicorn |
| OCR | Claude Vision (`claude-sonnet-4-20250514`) |
| Embedding model | `microsoft/harrier-oss-v1-270m` |
| Notes format | `.txt` + `.json` |

---

## Project structure

```
.
├── app.py                  # FastAPI webhook entrypoint
├── utils/
│   ├── telegram.py         # Telegram helpers (send_message, get_file_url, handle_message)
│   ├── ocr.py              # Claude Vision OCR function
│   └── retrieval.py        # Embedding + vector search logic
├── data/                   # Stored notes (auto-created)
├── .env                    # Environment variables (not committed)
└── requirements.txt
```

---

## Setup

### 1. Clone the repo

```bash
git clone https://github.com/yourusername/bjj-notes-rag.git
cd bjj-notes-rag
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure environment variables

Create a `.env` file at the root:

```env
ANTHROPIC_API_KEY=your_anthropic_api_key
TELEGRAM_BOT_TOKEN=your_telegram_bot_token
TELEGRAM_WEBHOOK_URL=https://your-public-url.com
```

### 4. Run the server

```bash
uvicorn app:app --host 0.0.0.0 --port 8000
```

On startup, the app automatically registers the webhook with Telegram.

---

## Usage

| Action | How |
|---|---|
| Add a note | Send a photo of your handwritten page to the bot |
| Query your notes | Send a text message describing the technique |
| Result | Bot replies with the 3 most relevant notes |

---

## Motivation

As a nogi practitioner, I take detailed handwritten notes after each session — positions, transitions, submissions, counters. Over time, finding a specific note became a problem. This project makes the entire notebook searchable from my phone, with no friction: photo in, answer out.

---

## Notes on OCR

The OCR prompt is specifically tuned for BJJ notes written in French with English grappling terminology. It handles:
- Mixed French/English vocabulary
- Position names (`garde`, `demi-garde`, `turtle`, `x-guard`...)
- Submission names (`étranglement`, `heel hook`, `kimura`...)
- Abbreviations and shorthand common in training notes