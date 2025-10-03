import sys, re, json, sqlite3
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QComboBox, QPushButton, QScrollArea, QLayout, QSizePolicy
)
from PyQt5.QtGui import QFont
from PyQt5.QtCore import Qt, QRect, QSize, QPoint
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

class FlowLayout(QLayout):
    """A QLayout that positions child widgets similar to text flow."""

    def __init__(self, parent=None, margin=0, spacing=8):
        super().__init__(parent)
        self._items = []
        self.setSpacing(spacing)
        if parent is not None:
            self.setContentsMargins(margin, margin, margin, margin)

    def __del__(self):
        item = self.takeAt(0)
        while item:
            item = self.takeAt(0)

    def addItem(self, item):
        self._items.append(item)

    def count(self):
        return len(self._items)

    def itemAt(self, index):
        if 0 <= index < len(self._items):
            return self._items[index]
        return None

    def takeAt(self, index):
        if 0 <= index < len(self._items):
            return self._items.pop(index)
        return None

    def expandingDirections(self):
        return Qt.Orientations(Qt.Orientation(0))

    def hasHeightForWidth(self):
        return True

    def heightForWidth(self, width):
        return self._do_layout(QRect(0, 0, width, 0), test_only=True)

    def setGeometry(self, rect):
        super().setGeometry(rect)
        self._do_layout(rect, test_only=False)

    def sizeHint(self):
        return self.minimumSize()

    def minimumSize(self):
        size = QSize()
        for item in self._items:
            size = size.expandedTo(item.minimumSize())
        margins = self.contentsMargins()
        size += QSize(margins.left() + margins.right(), margins.top() + margins.bottom())
        return size

    def _do_layout(self, rect, test_only):
        margins = self.contentsMargins()
        effective_rect = rect.adjusted(
            margins.left(), margins.top(), -margins.right(), -margins.bottom()
        )

        x = effective_rect.x()
        y = effective_rect.y()
        line_height = 0

        for item in self._items:
            space_x = self.spacing()
            space_y = self.spacing()
            next_x = x + item.sizeHint().width() + space_x

            if next_x - space_x > effective_rect.right() and line_height > 0:
                x = effective_rect.x()
                y = y + line_height + space_y
                next_x = x + item.sizeHint().width() + space_x
                line_height = 0

            if not test_only:
                item.setGeometry(QRect(QPoint(x, y), item.sizeHint()))

            x = next_x
            line_height = max(line_height, item.sizeHint().height())

        return y + line_height - rect.y() + margins.bottom()


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
        self.scroll_layout.setSpacing(12)
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
            verse_layout = FlowLayout()
            verse_layout.setContentsMargins(8, 4, 8, 4)

            verse_number_label = QLabel(f"{verse_num}")
            verse_number_label.setFont(QFont("Times", 12, QFont.Bold))
            verse_number_label.setTextInteractionFlags(Qt.TextSelectableByMouse)
            verse_number_label.setStyleSheet("color: #555555;")
            verse_layout.addWidget(verse_number_label)

            for word in verse_text.split():
                match = re.search(r"\{(G\d+|H\d+)\}", word)
                strongs_code = match.group(1) if match else None
                display_word = re.sub(r"\{.*?\}", "", word)

                label = QLabel(display_word)
                label.setFont(QFont("Times", 14))
                label.setTextInteractionFlags(Qt.TextSelectableByMouse)
                label.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Preferred)

                if strongs_code:
                    entry = lookup_strongs(strongs_code)
                    if entry:
                        translit = (
                            entry.get("translit")
                            or entry.get("xlit")
                            or entry.get("pron")
                            or ""
                        )
                        translit_text = f" ({translit})" if translit else ""
                        tooltip = (
                            f"{entry.get('lemma','')}{translit_text}\n"
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