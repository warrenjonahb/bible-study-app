import sys, re, json, sqlite3
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QComboBox, QPushButton, QScrollArea
)
from PyQt5.QtGui import QFont
from PyQt5.QtCore import Qt
from books_dict import BOOKS

# --- Load Greek & Hebrew lexicons ---
with open("greek.json", "r", encoding="utf-8") as f:
    greek_dict = json.load(f)
with open("hebrew.json", "r", encoding="utf-8") as f:
    hebrew_dict = json.load(f)

def lookup_strongs(code):
    """Lookup a Strong's number in Greek/Hebrew dicts"""
    if code.startswith("G"):
        return greek_dict.get(code, None)
    elif code.startswith("H"):
        return hebrew_dict.get(code, None)
    return None

# --- Connect to Bible database ---
conn = sqlite3.connect("kjv_strongs.sqlite")
cur = conn.cursor()

def get_chapter(book_number, chapter):
    cur.execute("SELECT verse, text FROM verses WHERE book=? AND chapter=?", (book_number, chapter))
    rows = cur.fetchall()
    print(f"DEBUG: Found {len(rows)} verses for book={book_number}, chapter={chapter}")
    return rows

# --- PyQt5 App ---

class BibleApp(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Bible Study App")
        self.setGeometry(200, 200, 1000, 600)

        main_layout = QVBoxLayout()

        # --- Controls row ---
        control_layout = QHBoxLayout()

        # Book selector
        self.book_dropdown = QComboBox()
        for num, name in BOOKS.items():
            self.book_dropdown.addItem(name, num)
        control_layout.addWidget(self.book_dropdown)

        # Chapter selector
        self.chapter_dropdown = QComboBox()
        control_layout.addWidget(self.chapter_dropdown)

        # Load button
        load_btn = QPushButton("Load")
        load_btn.clicked.connect(self.load_chapter)
        control_layout.addWidget(load_btn)

        main_layout.addLayout(control_layout)

        # --- Scroll area for verses ---
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll_content = QWidget()
        self.scroll_layout = QVBoxLayout(self.scroll_content)
        self.scroll.setWidget(self.scroll_content)
        main_layout.addWidget(self.scroll)

        self.setLayout(main_layout)

        # Populate chapters for first book
        self.book_dropdown.currentIndexChanged.connect(self.populate_chapters)
        self.populate_chapters()

    def populate_chapters(self):
        """Fill chapter dropdown based on selected book"""
        book_num = self.book_dropdown.currentData()
        cur.execute("SELECT MAX(chapter) FROM verses WHERE book=?", (book_num,))
        max_chapter = cur.fetchone()[0] or 1

        self.chapter_dropdown.clear()
        for c in range(1, max_chapter + 1):
            self.chapter_dropdown.addItem(str(c), c)

    def load_chapter(self):
        """Load verses for selected book + chapter"""
        book_num = self.book_dropdown.currentData()
        chapter = self.chapter_dropdown.currentData()

        # Clear old verses
        for i in reversed(range(self.scroll_layout.count())):
            widget = self.scroll_layout.itemAt(i).widget()
            if widget:
                widget.deleteLater()

        verses = get_chapter(book_num, chapter)
        for verse_num, verse_text in verses:
            verse_layout = QHBoxLayout()

            for word in verse_text.split():
                match = re.search(r"\{(G\d+|H\d+)\}", word)
                strongs_code = match.group(1) if match else None
                display_word = re.sub(r"\{.*?\}", "", word)

                label = QLabel(display_word)
                label.setFont(QFont("Times", 14))
                label.setTextInteractionFlags(Qt.TextSelectableByMouse)

                if strongs_code:
                    entry = lookup_strongs(strongs_code)
                    if entry:
                        tooltip = (
                            f"{entry.get('lemma','')} ({entry.get('translit','')})\n"
                            f"Definition: {entry.get('strongs_def','')}\n"
                            f"KJV: {entry.get('kjv_def','')}\n"
                            f"Strong's: {strongs_code}"
                        )
                        label.setToolTip(tooltip)
                        label.setStyleSheet("color: blue; text-decoration: underline;")

                verse_layout.addWidget(label)

            verse_widget = QWidget()
            verse_widget.setLayout(verse_layout)
            self.scroll_layout.addWidget(verse_widget)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = BibleApp()
    window.show()
    sys.exit(app.exec_())