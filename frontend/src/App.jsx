import { useEffect, useState } from "react";
import { fetchBooks, fetchChapters, fetchVerses } from "./api";

export default function App() {
  const [books, setBooks] = useState([]);
  const [book, setBook] = useState(43);   // John by default
  const [chapters, setChapters] = useState([]);
  const [chapter, setChapter] = useState(1);
  const [verses, setVerses] = useState([]);

  useEffect(() => {
    fetchBooks().then(setBooks).catch(console.error);
  }, []);

  useEffect(() => {
    if (book) fetchChapters(book).then(d => setChapters(d.chapters)).catch(console.error);
  }, [book]);

  useEffect(() => {
    if (book && chapter) fetchVerses(book, chapter).then(d => setVerses(d.verses)).catch(console.error);
  }, [book, chapter]);

  return (
    <div style={{ padding: 16, fontFamily: "Inter, system-ui" }}>
      <h2 style={{ marginBottom: 12 }}>Bible Study (React + FastAPI)</h2>

      <div style={{ display: "flex", gap: 8, marginBottom: 12 }}>
        <select value={book} onChange={e => setBook(Number(e.target.value))}>
          {books.map(b => (
            <option key={b.id} value={b.id}>{b.name}</option>
          ))}
        </select>

        <select value={chapter} onChange={e => setChapter(Number(e.target.value))}>
          {chapters.map(c => (
            <option key={c} value={c}>{c}</option>
          ))}
        </select>
      </div>

      <div style={{ display: "grid", gap: 8 }}>
        {verses.map(v => (
          <div key={v.verse} style={{ lineHeight: 1.9 }}>
            <span style={{ opacity: 0.6, marginRight: 8 }}>{v.verse}</span>
            {v.words.map((w, i) => (
              <span
                key={i}
                title={w.strongs ? `${w.lemma ?? ""} (${w.translit ?? ""})\n${w.def ?? ""}\n${w.kjv_def ?? ""}\n${w.strongs}` : ""}
                style={{
                  marginRight: 6,
                  textDecoration: w.strongs ? "underline" : "none",
                  color: w.strongs ? "#1a0dab" : "inherit",
                  cursor: w.strongs ? "help" : "default"
                }}
              >
                {w.text}
              </span>
            ))}
          </div>
        ))}
      </div>
    </div>
  );
}
