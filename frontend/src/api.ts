const BASE = "http://127.0.0.1:8000";

export async function fetchBooks() {
  const r = await fetch(`${BASE}/books`);
  if (!r.ok) throw new Error("Failed to load books");
  return r.json();
}

export async function fetchChapters(bookId: number) {
  const r = await fetch(`${BASE}/chapters/${bookId}`);
  if (!r.ok) throw new Error("Failed to load chapters");
  return r.json(); // { book, chapters: number[] }
}

export async function fetchVerses(bookId: number, chapter: number) {
  const r = await fetch(`${BASE}/verses/${bookId}/${chapter}`);
  if (!r.ok) throw new Error("Failed to load verses");
  return r.json(); // { book, chapter, verses: [...] }
}
