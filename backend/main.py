import re, json, sqlite3
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

# Allow the React dev server to talk to FastAPI
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Load resources ---
conn = sqlite3.connect("backend/kjv_strongs.sqlite", check_same_thread=False)
cur = conn.cursor()

with open("backend/greek.json", "r", encoding="utf-8") as f:
    greek_dict = json.load(f)
with open("backend/hebrew.json", "r", encoding="utf-8") as f:
    hebrew_dict = json.load(f)

BOOKS = {
    1: "Genesis",
    2: "Exodus",
    3: "Leviticus",
    4: "Numbers",
    5: "Deuteronomy",
    43: "John",
    66: "Revelation",
}

def lookup_strongs(code):
    if code is None:
        return None
    if code.startswith("G"):
        return greek_dict.get(code)
    elif code.startswith("H"):
        return hebrew_dict.get(code)
    return None

@app.get("/")
def root():
    return {"message": "Bible backend is running!"}

@app.get("/books")
def get_books():
    return [{"id": b, "name": n} for b, n in BOOKS.items()]

@app.get("/chapters/{book_id}")
def get_chapters(book_id: int):
    cur.execute("SELECT MAX(chapter) FROM verses WHERE book=?", (book_id,))
    max_chapter = cur.fetchone()[0]
    if not max_chapter:
        raise HTTPException(status_code=404, detail="Book not found")
    return {"book": book_id, "chapters": list(range(1, max_chapter + 1))}

@app.get("/verses/{book_id}/{chapter}")
def get_verses(book_id: int, chapter: int):
    cur.execute(
        "SELECT verse, text FROM verses WHERE book=? AND chapter=? ORDER BY verse",
        (book_id, chapter),
    )
    rows = cur.fetchall()
    if not rows:
        raise HTTPException(status_code=404, detail="No verses found")
    result = []
    for verse_num, text in rows:
        words = []
        for word in text.split():
            match = re.search(r"\{(G\d+|H\d+)\}", word)
            code = match.group(1) if match else None
            display_word = re.sub(r"\{.*?\}", "", word)
            entry = lookup_strongs(code)
            words.append({
                "text": display_word,
                "strongs": code,
                "lemma": entry.get("lemma") if entry else None,
                "translit": entry.get("translit") if entry else None,
                "def": entry.get("strongs_def") if entry else None,
                "kjv_def": entry.get("kjv_def") if entry else None
            })
        result.append({"verse": verse_num, "words": words})
    return {"book": book_id, "chapter": chapter, "verses": result}
