# MetaBeeAI GUI
#
# Execute with:
#   python metabeeai_llm/beegui.py
#
# m.mieskolainen@imperial.ac.uk, 2025

import json
import math
import os
import sys
from datetime import datetime

import fitz  # PyMuPDF
from PyQt5.QtCore import QEvent, QPoint, QRect, Qt, pyqtSignal
from PyQt5.QtGui import QColor, QFont, QGuiApplication, QImage, QPainter, QPen, QPixmap
from PyQt5.QtWidgets import (
    QAction,
    QApplication,
    QFileDialog,
    QFrame,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QMainWindow,
    QMenu,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QSlider,
    QSplitter,
    QTextEdit,
    QToolButton,
    QVBoxLayout,
    QWidget,
)


class AutoActivateListWidget(QListWidget):
    def keyPressEvent(self, event):
        super().keyPressEvent(event)
        if event.key() in (Qt.Key_Up, Qt.Key_Down):
            current = self.currentItem()
            if current:
                self.itemActivated.emit(current)


class PDFViewer(QLabel):
    resized = pyqtSignal()  # emitted on resize
    hoverChanged = pyqtSignal(list)  # new signal emitting hovered annotations

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMouseTracking(True)
        self.annotations = []  # list of dicts: {"rect": QRect, "cid": str}
        self.rendered_pixmap = None
        self.displayed_rect = QRect()
        self.hovered_annotations = []

    def setRenderedPixmap(self, pixmap, displayed_rect):
        self.rendered_pixmap = pixmap
        self.displayed_rect = displayed_rect
        self.update()

    def setAnnotations(self, annotations):
        self.annotations = annotations
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        if self.rendered_pixmap:
            painter.drawPixmap(self.displayed_rect, self.rendered_pixmap)
        pen = QPen(QColor(0, 0, 255))
        pen.setWidth(3)
        painter.setPen(pen)
        for ann in self.annotations:
            painter.drawRect(ann["rect"])
        # Uncomment below to highlight hovered annotations
        # for ann in self.hovered_annotations:
        #    brush = QColor(255, 255, 0, 100)  # semi-transparent yellow
        #    painter.fillRect(ann["rect"], brush)
        painter.end()

    def mouseMoveEvent(self, event):
        pos = event.pos()
        self.hovered_annotations = []
        for ann in self.annotations:
            if ann["rect"].contains(pos):
                self.hovered_annotations.append(ann)
        # Emit the hovered annotations so MainWindow can update the tooltip.
        self.hoverChanged.emit(self.hovered_annotations)
        super().mouseMoveEvent(event)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.resized.emit()


# Define a custom ZoomSlider class.
class ZoomSlider(QSlider):
    def mouseDoubleClickEvent(self, event):
        # Only reset if the current value is not already near 100
        if abs(self.value() - 100) > 1:
            self.setValue(100)
        event.accept()


# -------------------- PDF Scroll Area --------------------
class PDFScrollArea(QScrollArea):
    # Allows panning (by dragging) and zooming via Ctrl+wheel.
    def __init__(self, parent=None):
        super().__init__(parent)

        self.setFrameShape(QFrame.NoFrame)  # Remove the QScrollArea frame

        # Disable automatic resizing so that the PDFViewer can have its own size.
        self.setWidgetResizable(False)  # Changed from True
        self.setAlignment(Qt.AlignCenter)  # Center the widget when it is smaller than the viewport
        self.pdf_viewer = PDFViewer()
        self.setWidget(self.pdf_viewer)
        # Install event filter on PDFViewer to capture mouse events.
        self.pdf_viewer.installEventFilter(self)
        self._dragging = False
        self._drag_start = QPoint()
        self._h_scroll_start = 0
        self._v_scroll_start = 0
        self.onWheelZoom = None  # callback for wheel zoom

    def eventFilter(self, obj, event):
        # Only filter events from the PDFViewer.
        if obj == self.pdf_viewer:
            if event.type() == QEvent.MouseButtonPress:
                if event.button() == Qt.LeftButton:
                    self._dragging = True
                    self._drag_start = event.pos()
                    self._h_scroll_start = self.horizontalScrollBar().value()
                    self._v_scroll_start = self.verticalScrollBar().value()
            elif event.type() == QEvent.MouseMove:
                if self._dragging:
                    delta = event.pos() - self._drag_start
                    self.horizontalScrollBar().setValue(self._h_scroll_start - delta.x())
                    self.verticalScrollBar().setValue(self._v_scroll_start - delta.y())
            elif event.type() == QEvent.MouseButtonRelease:
                if event.button() == Qt.LeftButton:
                    self._dragging = False
        # Pass the event on so the PDFViewer can process hover etc.
        return super().eventFilter(obj, event)

    def wheelEvent(self, event):
        # If Ctrl is held, use wheel for zooming.
        if event.modifiers() & Qt.ControlModifier:
            if self.onWheelZoom:
                self.onWheelZoom(event.angleDelta().y())
            event.accept()
        else:
            super().wheelEvent(event)


# -------------------- Star Rating Widget --------------------
class StarRatingWidget(QWidget):
    def __init__(self, max_stars=10, parent=None):
        super().__init__(parent)
        self.max_stars = max_stars
        self.current_rating = 0  # default rating is 0 (no active stars)
        self.star_buttons = []
        self.layout = QHBoxLayout()
        self.layout.setSpacing(2)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(self.layout)
        for i in range(1, max_stars + 1):
            btn = QToolButton()
            btn.setText("☆")
            btn.setFont(QFont("Arial", 20))
            btn.setAutoRaise(True)
            btn.setCheckable(True)
            btn.clicked.connect(self.make_star_handler(i))
            self.star_buttons.append(btn)
            self.layout.addWidget(btn)
        self.update_stars()

    def make_star_handler(self, star_value):
        def handler():
            # If the clicked star is already active, clear the rating.
            if self.current_rating == star_value:
                self.current_rating = 0
            else:
                self.current_rating = star_value
            self.update_stars()
            self.ratingChanged()

        return handler

    def update_stars(self):
        for i, btn in enumerate(self.star_buttons, start=1):
            if i <= self.current_rating:
                btn.setText("★")
                btn.setChecked(True)
            else:
                btn.setText("☆")
                btn.setChecked(False)

    def ratingChanged(self):
        if hasattr(self, "onRatingChanged"):
            self.onRatingChanged(self.current_rating)

    def getRating(self):
        return self.current_rating

    def setRating(self, rating):
        self.current_rating = rating
        self.update_stars()


def get_questions_for_chunk(chunk_id, questions_data):
    """
    Recursively traverse questions_data (a dict) and return a list of question keys (as strings)
    for which the 'chunk_ids' list (if present) contains chunk_id.
    """
    results = []

    def traverse(data, prefix=""):
        if isinstance(data, dict):
            # If this dictionary has chunk_ids, check them.
            if "chunk_ids" in data:
                # If the chunk is found, add the prefix as a question key.
                if any(str(cid).strip() == chunk_id for cid in data["chunk_ids"]):
                    results.append(prefix if prefix else "Unnamed")
            # Otherwise, traverse further.
            for key, value in data.items():
                new_prefix = f"{prefix}.{key}" if prefix else key
                traverse(value, new_prefix)

    traverse(questions_data)
    return results


# -------------------- Main Window --------------------
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("MetaBeeAI")

        screen = QGuiApplication.primaryScreen()
        if screen:
            available_geometry = screen.availableGeometry()
            self.resize(int(available_geometry.width() * 1.0), int(available_geometry.height() * 1.0))
        else:
            self.resize(1400, 900)

        self.current_pdf_doc = None
        self.current_json_data = None
        self.current_answers_data = {}
        self.answers_extended_data = {}
        self.chunk_dict = {}
        self.questions_map = {}
        self.current_question_id = None
        self.current_paper_folder = None
        self.base_papers_dir = None
        self.current_page_num = 0
        self.current_zoom = 100
        self.annotation_mode = "individual"
        self.current_annotation = None
        self.current_question_chunk_ids = []
        self.loading_question = False
        self.fontSize = 12
        self.updateFontSize()

        # ---------------- Left Pane: Paper Navigation and Page Controls ----------------
        self.paper_list = AutoActivateListWidget()
        self.paper_list.setFocusPolicy(Qt.StrongFocus)
        self.paper_list.itemActivated.connect(self.on_paper_selected)
        self.paper_list.setMinimumWidth(150)
        self.paper_list.itemClicked.connect(self.on_paper_selected)
        self.prev_paper_btn = QPushButton("Prev Paper")
        self.prev_paper_btn.clicked.connect(self.on_prev_paper)
        self.next_paper_btn = QPushButton("Next Paper")
        self.next_paper_btn.clicked.connect(self.on_next_paper)
        paper_nav_layout = QVBoxLayout()
        paper_nav_layout.addWidget(self.prev_paper_btn)
        paper_nav_layout.addWidget(self.next_paper_btn)
        paper_nav_layout.addWidget(self.paper_list)

        # Page navigation controls for PDF pages
        self.prev_page_btn = QPushButton("Prev Page")
        self.prev_page_btn.clicked.connect(self.on_prev_page)
        self.next_page_btn = QPushButton("Next Page")
        self.next_page_btn.clicked.connect(self.on_next_page)
        self.page_label = QLabel("")
        page_nav_layout = QHBoxLayout()
        page_nav_layout.addWidget(self.prev_page_btn)
        page_nav_layout.addStretch()
        page_nav_layout.addWidget(self.page_label, alignment=Qt.AlignCenter)
        page_nav_layout.addStretch()
        page_nav_layout.addWidget(self.next_page_btn)
        page_nav_widget = QWidget()
        page_nav_widget.setLayout(page_nav_layout)
        paper_nav_layout.addWidget(page_nav_widget)

        # Zoom slider controls
        self.zoom_slider = ZoomSlider(Qt.Horizontal)
        self.zoom_slider.setMinimum(10)
        self.zoom_slider.setMaximum(400)
        self.zoom_slider.setValue(self.current_zoom)
        self.zoom_slider.valueChanged.connect(self.on_zoom_changed)
        self.zoom_label = QLabel(f"{self.current_zoom}%")
        zoom_layout = QHBoxLayout()
        zoom_layout.addWidget(self.zoom_label)
        zoom_layout.addWidget(self.zoom_slider)
        zoom_widget = QWidget()
        zoom_widget.setLayout(zoom_layout)
        paper_nav_layout.addWidget(zoom_widget)

        # Modified label
        self.modified_label = QLabel("")
        paper_nav_layout.addWidget(self.modified_label)

        paper_nav_widget = QWidget()
        paper_nav_widget.setLayout(paper_nav_layout)

        # ---------------- Center Pane: PDF Display ----------------
        self.pdf_scroll_area = PDFScrollArea()
        self.pdf_scroll_area.onWheelZoom = self.handle_wheel_zoom
        self.pdf_viewer = self.pdf_scroll_area.pdf_viewer
        self.pdf_viewer.resized.connect(self.render_current_page)
        self.pdf_viewer.hoverChanged.connect(self.handle_hover_annotations)
        pdf_layout = QVBoxLayout()
        pdf_layout.addWidget(self.pdf_scroll_area)
        pdf_widget = QWidget()
        pdf_widget.setLayout(pdf_layout)

        # ---------------- Right Pane: Question Panel, Mode Keys, and Chunk IDs ----------------
        self.question_panel = self.create_question_panel()

        # Create mode buttons container.
        self.individual_btn = QPushButton("Individual")
        self.individual_btn.setCheckable(True)
        self.individual_btn.setChecked(True)
        self.individual_btn.clicked.connect(lambda: self.set_annotation_mode("individual"))
        self.all_btn = QPushButton("All")
        self.all_btn.setCheckable(True)
        self.all_btn.clicked.connect(lambda: self.set_annotation_mode("all"))
        mode_layout = QHBoxLayout()
        mode_layout.addWidget(self.individual_btn)
        mode_layout.addWidget(self.all_btn)
        self.mode_widget = QWidget()
        self.mode_widget.setLayout(mode_layout)
        self.mode_widget.hide()  # hide mode keys initially

        self.chunk_list = AutoActivateListWidget()
        self.chunk_list.itemClicked.connect(self.on_chunk_selected)
        self.chunk_list.itemActivated.connect(self.on_chunk_selected)
        self.chunk_list.hide()  # hide chunk IDs until a question is selected

        right_layout = QVBoxLayout()
        right_layout.addWidget(self.question_panel)
        # right_layout.addWidget(QLabel("")) # Chunk IDs
        right_layout.addWidget(self.chunk_list)
        right_layout.addWidget(self.mode_widget)
        right_widget = QWidget()
        right_widget.setLayout(right_layout)

        # ---------------- Main Layout ----------------
        main_splitter = QSplitter(Qt.Horizontal)
        main_splitter.addWidget(paper_nav_widget)
        main_splitter.addWidget(pdf_widget)
        main_splitter.addWidget(right_widget)
        main_splitter.setStretchFactor(1, 1)
        container = QWidget()
        container_layout = QHBoxLayout()
        container_layout.addWidget(main_splitter)
        container.setLayout(container_layout)
        self.setCentralWidget(container)

        # ---------------- Menu ----------------
        openFolderAction = QAction("Open Folder", self)
        openFolderAction.triggered.connect(lambda: self.open_folder(initial=False))
        file_menu = self.menuBar().addMenu("File")
        file_menu.addAction(openFolderAction)

        # ---------------- Option Menu: Theme and Font ----------------

        options_menu = self.menuBar().addMenu("Options")

        # Theme Actions.
        self.darkThemeAction = QAction("Dark Mode", self, checkable=True)
        self.lightThemeAction = QAction("Light Mode", self, checkable=True)

        # Default to dark mode.
        self.darkThemeAction.setChecked(True)
        self.darkThemeAction.triggered.connect(lambda: self.setTheme("dark"))
        self.lightThemeAction.triggered.connect(lambda: self.setTheme("light"))
        options_menu.addAction(self.darkThemeAction)
        options_menu.addAction(self.lightThemeAction)

        # Font Size Widget: one option with buttons and current font size.
        fontSizeMenu = QMenu("Font Size", self)
        fontSizeWidget = QWidget(self)
        fontSizeLayout = QHBoxLayout()
        fontSizeLayout.setContentsMargins(5, 5, 5, 5)

        # Create buttons and label.
        decreaseButton = QPushButton("-")
        self.fontSizeLabel = QLabel(f"{self.fontSize}")
        increaseButton = QPushButton("+")

        # Connect button clicks.
        decreaseButton.clicked.connect(self.decreaseFontSize)
        increaseButton.clicked.connect(self.increaseFontSize)

        # Add them to the layout.
        fontSizeLayout.addWidget(decreaseButton)
        fontSizeLayout.addWidget(self.fontSizeLabel)
        fontSizeLayout.addWidget(increaseButton)
        fontSizeWidget.setLayout(fontSizeLayout)

        # Embed the widget into the menu using QWidgetAction.
        from PyQt5.QtWidgets import QWidgetAction  # ensure this import is present at the top if not already

        fontSizeAction = QWidgetAction(self)
        fontSizeAction.setDefaultWidget(fontSizeWidget)
        fontSizeMenu.addAction(fontSizeAction)
        options_menu.addMenu(fontSizeMenu)

        # (Optionally, call updateFontSize() again here to update the menu text immediately.)
        self.updateFontSize()

        ## Help menu
        help_menu = self.menuBar().addMenu("Help")
        about_action = QAction("About", self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)

        # ---------------- Full-Screen Toggle ----------------
        # Add an action with the F11 shortcut to toggle full screen mode.
        self.fullScreenAction = QAction("Toggle Full Screen", self)
        self.fullScreenAction.setShortcut(Qt.Key_F11)
        self.fullScreenAction.triggered.connect(self.toggleFullScreen)
        self.addAction(self.fullScreenAction)

        # Set default theme to dark.
        self.setTheme("dark")

        # Try to load default folder "data/papers" automatically.
        self.open_folder(initial=True)

    def show_about(self):
        QMessageBox.about(self, "About", "MetaBeeAI (2025)")

    def toggleFullScreen(self):
        if self.isFullScreen():
            self.menuBar().setVisible(True)
            self.showNormal()
        else:
            self.menuBar().setVisible(False)
            self.showFullScreen()

    def handle_hover_annotations(self, annotations):
        if not annotations:
            self.pdf_viewer.setToolTip("")
            return

        tooltip_lines = []
        for ann in annotations:
            cid = ann.get("cid", "")
            if self.current_question_id is None:
                # No question is selected: search the entire questions data for all matching questions.
                related_questions = get_questions_for_chunk(cid, self.current_answers_data.get("QUESTIONS", {}))
                if related_questions:
                    tooltip_lines.append(f"<b>{cid}</b>")
                    for q in related_questions:
                        tooltip_lines.append(q)
                    tooltip_lines.append("")
                else:
                    tooltip_lines.append(f"<b>{cid}</b>")
            else:
                # When a question is selected, show just the chunk id.
                tooltip_lines.append(f"<b>{cid}</b>")
        self.pdf_viewer.setToolTip("\n".join(tooltip_lines))

    def setTheme(self, theme):
        if theme == "dark":
            dark_style = """
                QMainWindow {
                    background-color: #1e1e1e;
                    color: #d4d4d4;
                }
                QLabel {
                    background-color: #1e1e1e;
                    color: #f5eaa2;
                }
                QListWidget, QTextEdit {
                    background-color: #252526;
                    color: #d4d4d4;
                }
                QPushButton, QToolButton, QSlider {
                    background-color: #3c3c3c;
                    color: #d4d4d4;
                }
                QMenuBar, QMenu, QMenu::item {
                    background-color: #1e1e1e;
                    color: #d4d4d4;
                }
                QListWidget::item:selected {
                    background-color: #1e1e1e;
                    color: #007acc;
                }
                QListWidget::item:disabled {
                    background-color: #1e1e1e;
                    color: #888888;
                }
                QListWidget:disabled {
                    background-color: #1e1e1e;
                    color: #888888;
                }
                QScrollArea {
                    background-color: #1e1e1e;
                }
                QScrollBar:vertical {
                    background: #1e1e1e;
                    width: 15px;
                    margin: 0px;
                }
                QScrollBar::handle:vertical {
                    background: #007acc;
                    min-height: 20px;
                    border-radius: 0px;
                }
                QScrollBar::add-line:vertical,
                QScrollBar::sub-line:vertical {
                    background: none;
                }
                QScrollBar:horizontal {
                    background: #1e1e1e;
                    height: 15px;
                    margin: 0px;
                }
                QScrollBar::handle:horizontal {
                    background: #007acc;
                    min-width: 20px;
                    border-radius: 0px;
                }
                QScrollBar::add-line:horizontal,
                QScrollBar::sub-line:horizontal {
                    background: none;
                }
            """
            self.setStyleSheet(dark_style)
            self.darkThemeAction.setChecked(True)
            self.lightThemeAction.setChecked(False)
        else:
            light_style = """
                QMainWindow {
                    background-color: #f3f3f3;
                    color: #333333;
                }
                QLabel {
                    background-color: #f3f3f3;
                    color: #007bff;
                }
                QListWidget, QTextEdit {
                    background-color: #ffffff;
                    color: #333333;
                }
                QListWidget::item:disabled {
                    background-color: #ffffff;
                    color: #888888;
                }
                QListWidget:disabled {
                    background-color: #ffffff;
                    color: #888888;
                }
                QListWidget::item {
                    background-color: #ffffff;
                    color: #333333;
                }
                QListWidget::item:selected {
                    background-color: #cce6ff;
                    color: #333333;
                }
                QListWidget::item:!selected:!active {
                    background-color: #ffffff;
                }
                QPushButton, QToolButton, QSlider {
                    background-color: #e7e7e7;
                    color: #333333;
                }
                QMenuBar, QMenu, QMenu::item {
                    background-color: #f3f3f3;
                    color: #333333;
                }
                QScrollArea {
                    background-color: #f3f3f3;
                }
                QScrollBar:vertical {
                    background: #f3f3f3;
                    width: 15px;
                    margin: 0px;
                }
                QScrollBar::handle:vertical {
                    background: #007acc;
                    min-height: 20px;
                    border-radius: 0px;
                }
                QScrollBar::add-line:vertical,
                QScrollBar::sub-line:vertical {
                    background: none;
                }
                QScrollBar:horizontal {
                    background: #f3f3f3;
                    height: 15px;
                    margin: 0px;
                }
                QScrollBar::handle:horizontal {
                    background: #007acc;
                    min-width: 20px;
                    border-radius: 0px;
                }
                QScrollBar::add-line:horizontal,
                QScrollBar::sub-line:horizontal {
                    background: none;
                }
            """
            self.setStyleSheet(light_style)
            self.darkThemeAction.setChecked(False)
            self.lightThemeAction.setChecked(True)

        # Reapply the global font after switching themes.
        self.updateFontSize()

    def updateFontSize(self):
        new_font = QFont("Helvetica", self.fontSize)

        # Update the global application font.
        QApplication.setFont(new_font)
        # Also update the main window's font.
        self.setFont(new_font)
        # Refresh all child widgets to immediately reflect the new font size.
        for widget in self.findChildren(QWidget):
            widget.setFont(new_font)
            widget.updateGeometry()
            widget.repaint()
        # Force the main window to repaint.
        self.repaint()

        # Update the font size label (if it exists).
        if hasattr(self, "fontSizeLabel"):
            self.fontSizeLabel.setText(str(self.fontSize))

    def increaseFontSize(self):
        self.fontSize += 1
        self.updateFontSize()

    def decreaseFontSize(self):
        if self.fontSize > 1:
            self.fontSize -= 1
            self.updateFontSize()

    def resizeEvent(self, event):
        # When at 100% (fit-to-window), re-render the page on window resize.
        if self.zoom_slider.value() == 100:
            self.render_current_page()
        super().resizeEvent(event)

    # Enable left/right key navigation for PDF pages.
    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Left:
            self.on_prev_page()
            event.accept()
        elif event.key() == Qt.Key_Right:
            self.on_next_page()
            event.accept()
        else:
            super().keyPressEvent(event)

    def handle_wheel_zoom(self, delta):
        if delta > 0:
            new_zoom = min(self.current_zoom + 10, 400)
        else:
            new_zoom = max(self.current_zoom - 10, 10)
        self.zoom_slider.setValue(new_zoom)

    def create_question_panel(self):
        panel = QGroupBox("")
        layout = QVBoxLayout()

        # Always visible: the question list.
        self.question_list = AutoActivateListWidget()
        self.question_list.itemClicked.connect(self.on_question_selected)
        self.question_list.itemActivated.connect(self.on_question_selected)  # allow Enter key activation
        layout.addWidget(QLabel("<b><center><h3>Questions</h3></center></b>"))
        layout.addWidget(self.question_list)

        # Container for controls to be hidden until a question is selected.
        self.question_controls = QWidget()
        qc_layout = QVBoxLayout()

        self.answer_field = QTextEdit()
        self.answer_field.setReadOnly(True)
        self.reason_field = QTextEdit()
        self.reason_field.setReadOnly(True)
        qc_layout.addWidget(QLabel("AI Answer"))
        qc_layout.addWidget(self.answer_field)
        qc_layout.addWidget(QLabel("AI Reason"))
        qc_layout.addWidget(self.reason_field)

        ## Star rating
        self.star_rating = StarRatingWidget(10)
        self.star_rating.onRatingChanged = self.on_star_rating_changed
        self.rating_number_label = QLabel("0")  # default is 0
        star_layout = QHBoxLayout()
        star_layout.addWidget(self.star_rating)
        star_layout.addWidget(self.rating_number_label)
        qc_layout.addWidget(QLabel())
        qc_layout.addLayout(star_layout)

        ## User answers
        self.answer_positive_field = QTextEdit()
        self.answer_negative_field = QTextEdit()
        self.reason_positive_field = QTextEdit()
        self.reason_negative_field = QTextEdit()
        # Connect textChanged signals to auto_save.
        self.answer_positive_field.textChanged.connect(self.auto_save)
        self.answer_negative_field.textChanged.connect(self.auto_save)
        self.reason_positive_field.textChanged.connect(self.auto_save)
        self.reason_negative_field.textChanged.connect(self.auto_save)

        qc_layout.addWidget(QLabel('<font color="green">Answer (✓)</font>'))
        qc_layout.addWidget(self.answer_positive_field)
        qc_layout.addWidget(QLabel('<font color="green">Reason (✓)</font>'))
        qc_layout.addWidget(self.reason_positive_field)
        qc_layout.addWidget(QLabel('<font color="red">Answer (✗)</font>'))
        qc_layout.addWidget(self.answer_negative_field)
        qc_layout.addWidget(QLabel('<font color="red">Reason (✗)</font>'))
        qc_layout.addWidget(self.reason_negative_field)

        self.question_controls.setLayout(qc_layout)
        self.question_controls.hide()  # hide controls until a question is selected

        layout.addWidget(self.question_controls)
        panel.setLayout(layout)
        return panel

    def log_field_change(self, field_name, new_value):
        """
        Append a log line to beegui.log under the current paper folder.
        Format: [timestamp] field_name changed to: new_value
        """
        if not self.current_paper_folder:
            return
        log_path = os.path.join(self.current_paper_folder, "beegui.log")
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_line = f"[{timestamp}] {field_name} changed to: {new_value}\n"
        try:
            with open(log_path, "a", encoding="utf-8") as f:
                f.write(log_line)
        except Exception as e:
            print(f"Error writing to log file: {e}")

    def on_star_rating_changed(self, rating):
        self.rating_number_label.setText(str(rating))
        # Log the star rating change.
        self.log_field_change("user_rating", str(rating))
        if not self.loading_question:
            self.auto_save()

    def open_folder(self, initial=False):
        # Import centralized configuration for default folder
        import sys

        script_dir = os.path.dirname(os.path.abspath(__file__))
        parent_dir = os.path.dirname(script_dir)
        if parent_dir not in sys.path:
            sys.path.insert(0, parent_dir)
        from config import get_papers_dir

        default_folder = get_papers_dir()

        if initial:
            if os.path.isdir(default_folder):
                folder = default_folder
            else:
                folder = QFileDialog.getExistingDirectory(self, "Select Folder Containing 'papers'", os.getcwd())
                if not folder:
                    return
        else:
            initial_dir = self.base_papers_dir if self.base_papers_dir else os.getcwd()
            folder = QFileDialog.getExistingDirectory(self, "Select Folder Containing 'papers'", initial_dir)
            if not folder:
                return

        papers_subfolder = os.path.join(folder, "papers")
        if folder != default_folder and os.path.isdir(papers_subfolder):
            self.base_papers_dir = papers_subfolder
        else:
            self.base_papers_dir = folder

        self.paper_list.clear()
        for foldername in sorted(os.listdir(self.base_papers_dir)):
            path = os.path.join(self.base_papers_dir, foldername)
            # Accept folders that are alphanumeric (paper IDs) and not hidden (starting with .)
            if os.path.isdir(path) and not foldername.startswith(".") and foldername.isalnum():
                # Add the paper number only; progress will be added on selection.
                self.paper_list.addItem(f"{foldername}")

    def on_prev_paper(self):
        current_row = self.paper_list.currentRow()
        if current_row > 0:
            self.paper_list.setCurrentRow(current_row - 1)
            self.on_paper_selected(self.paper_list.currentItem())

    def on_next_paper(self):
        current_row = self.paper_list.currentRow()
        if current_row < self.paper_list.count() - 1:
            self.paper_list.setCurrentRow(current_row + 1)
            self.on_paper_selected(self.paper_list.currentItem())

    def on_paper_selected(self, item):
        # Suppress auto_save during programmatic updates.
        self.suppress_auto_save = True

        # Extract paper_id (in case the item text already has a percentage appended).
        paper_id = item.text().split()[0]
        self.current_paper_folder = os.path.join(self.base_papers_dir, paper_id)
        pdf_path = os.path.join(self.current_paper_folder, f"{paper_id}_main.pdf")
        json_path = os.path.join(self.current_paper_folder, "pages", "merged_v2.json")
        answers_path = os.path.join(self.current_paper_folder, "answers.json")
        answers_extended_path = os.path.join(self.current_paper_folder, "answers_extended.json")
        if not os.path.isfile(pdf_path):
            self.pdf_scroll_area.pdf_viewer.setText(f"Missing PDF: {pdf_path}")
            self.suppress_auto_save = False
            return
        if not os.path.isfile(json_path):
            self.pdf_scroll_area.pdf_viewer.setText(f"Missing JSON: {json_path}")
            self.suppress_auto_save = False
            return

        self.current_pdf_doc = fitz.open(pdf_path)
        with open(json_path, "r", encoding="utf-8") as f:
            self.current_json_data = json.load(f)
        self.chunk_dict = {}
        for chunk in self.current_json_data.get("data", {}).get("chunks", []):
            cid = chunk.get("chunk_id")
            if cid:
                cid = str(cid).strip()
                self.chunk_dict[cid] = chunk
        if os.path.isfile(answers_path):
            with open(answers_path, "r", encoding="utf-8") as f:
                self.current_answers_data = json.load(f)
        else:
            self.current_answers_data = {"QUESTIONS": {}}
        if os.path.isfile(answers_extended_path):
            with open(answers_extended_path, "r", encoding="utf-8") as f:
                self.answers_extended_data = json.load(f)
        else:
            self.answers_extended_data = {"QUESTIONS": {}}

        self.populate_questions()
        self.pdf_scroll_area.pdf_viewer.setText("Select a chunk or navigate pages.")

        # Clear all UI fields without triggering auto_save.
        self.chunk_list.clear()
        self.reason_field.clear()
        self.answer_field.clear()
        self.answer_positive_field.clear()
        self.answer_negative_field.clear()
        self.reason_positive_field.clear()
        self.reason_negative_field.clear()
        self.star_rating.setRating(0)  # Reset to default (no active stars)
        self.rating_number_label.setText("0")
        self.current_page_num = 0
        self.current_annotation = None
        self.current_question_chunk_ids = []

        # Clear current question selection and hide question-related UI elements.
        self.current_question_id = None
        self.question_controls.hide()
        self.mode_widget.hide()
        self.chunk_list.hide()

        # Collect all chunk IDs from all questions.
        all_chunk_ids = set()
        for q_val in self.current_answers_data.get("QUESTIONS", {}).values():
            if isinstance(q_val, dict) and "chunk_ids" in q_val:
                for cid in q_val["chunk_ids"]:
                    all_chunk_ids.add(str(cid).strip())
        # Set the list of chunk IDs to be used for drawing annotations.
        self.current_question_chunk_ids = list(all_chunk_ids)
        # Force annotation mode to "all" so that render_current_page() draws bounding boxes for all.
        self.annotation_mode = "all"

        self.render_current_page()
        self.update_modification_label()

        # Compute progress using in-memory data.
        progress = self.compute_progress_for_current_paper()
        # Update the current item's text with the progress percentage.
        item.setText(f"{paper_id} ({progress}%)")

        # Re-enable auto_save after programmatic updates.
        self.suppress_auto_save = False

    def compute_progress_for_current_paper(self):
        """
        Compute the progress percentage for the current paper using in‑memory data.
        Checks five fields per question:
        - user_answer_positive
        - user_answer_negative
        - user_reason_positive
        - user_reason_negative
        - user_rating (non‑zero)
        Uses the union of question keys from both the system answers and the extended (user) answers.
        """
        # Get keys from both the system answers and extended answers.
        questions_keys = set(self.current_answers_data.get("QUESTIONS", {}).keys())
        extended_keys = set(self.answers_extended_data.get("QUESTIONS", {}).keys())
        all_keys = questions_keys.union(extended_keys)

        total_questions = len(all_keys)
        total_fields = total_questions * 5
        if total_fields == 0:
            return 0

        filled_fields = 0
        for key in all_keys:
            entry = self.answers_extended_data.get("QUESTIONS", {}).get(key, {})
            if entry.get("user_answer_positive", "").strip() != "":
                filled_fields += 1
            if entry.get("user_answer_negative", "").strip() != "":
                filled_fields += 1
            if entry.get("user_reason_positive", "").strip() != "":
                filled_fields += 1
            if entry.get("user_reason_negative", "").strip() != "":
                filled_fields += 1
            try:
                rating = int(entry.get("user_rating", 0))
            except:
                rating = 0
            if rating != 0:
                filled_fields += 1

        # Use floor, if we are near maximum (e.g. missing one)
        percentage = math.floor((filled_fields / total_fields) * 100)
        return percentage

    def populate_questions(self):
        self.questions_map = {}
        self.question_list.clear()
        questions = self.current_answers_data.get("QUESTIONS", {})
        for q_key, q_val in questions.items():
            if isinstance(q_val, dict) and "reason" in q_val and "answer" in q_val:
                key = q_key
                self.questions_map[key] = q_val
                self.question_list.addItem(key)
            elif isinstance(q_val, dict):
                for sub_key, sub_val in q_val.items():
                    if isinstance(sub_val, dict) and "reason" in sub_val and "answer" in sub_val:
                        key = f"{q_key}.{sub_key}"
                        self.questions_map[key] = sub_val
                        self.question_list.addItem(key)

    def on_question_selected(self, item):
        qid = item.text()
        if self.current_question_id == qid:
            return
        self.loading_question = True
        # Clear previous annotation state
        self.current_annotation = None
        self.current_question_chunk_ids = []
        self.pdf_scroll_area.pdf_viewer.setAnnotations([])  # clear drawn boxes

        self.set_annotation_mode("all")
        self.current_question_id = qid
        question_obj = self.questions_map.get(qid, {})
        self.answer_field.setPlainText(question_obj.get("answer", ""))
        self.reason_field.setPlainText(question_obj.get("reason", ""))
        edited = self.answers_extended_data.get("QUESTIONS", {}).get(qid, {})
        self.answer_positive_field.setPlainText(edited.get("user_answer_positive", ""))
        self.answer_negative_field.setPlainText(edited.get("user_answer_negative", ""))
        self.reason_positive_field.setPlainText(edited.get("user_reason_positive", ""))
        self.reason_negative_field.setPlainText(edited.get("user_reason_negative", ""))
        try:
            rating = int(edited.get("user_rating", 0))
        except:
            rating = 0
        self.star_rating.setRating(rating)
        self.rating_number_label.setText(str(rating))

        # Update chunk list: this may change the list of chunk IDs to annotate.
        self.chunk_list.clear()
        self.current_question_chunk_ids = question_obj.get("chunk_ids", [])
        for cid in self.current_question_chunk_ids:
            cid = str(cid).strip()
            if cid in self.chunk_dict:
                item = QListWidgetItem(cid)
                self.chunk_list.addItem(item)
        if self.annotation_mode == "all":
            self.chunk_list.setDisabled(True)
            self.chunk_list.selectAll()
        else:
            self.chunk_list.setDisabled(False)

        # Show question controls, mode keys, and chunk list.
        self.question_controls.show()
        self.mode_widget.show()
        self.chunk_list.show()

        # Optionally, set the current page based on a grounding found.
        page_set = False
        for cid in self.current_question_chunk_ids:
            cid = str(cid).strip()
            if cid in self.chunk_dict:
                chunk = self.chunk_dict[cid]
                if "grounding" in chunk and len(chunk["grounding"]) > 0:
                    for grounding in chunk["grounding"]:
                        if grounding.get("page") is not None:
                            self.current_page_num = grounding.get("page", 0)
                            page_set = True
                            break
                if page_set:
                    break
        if not page_set:
            self.current_page_num = 0

        # Redraw the page from scratch.
        self.render_current_page()
        self.updateAnnotations()
        self.loading_question = False

    def auto_save(self):
        # If auto-save is suppressed or we are loading a question, do nothing.
        if not self.current_question_id or self.loading_question or getattr(self, "suppress_auto_save", False):
            return

        # Log which field triggered the auto_save if available.
        sender = self.sender()
        if sender is not None:
            if sender == self.answer_positive_field:
                self.log_field_change("user_answer_positive", self.answer_positive_field.toPlainText().strip())
            elif sender == self.answer_negative_field:
                self.log_field_change("user_answer_negative", self.answer_negative_field.toPlainText().strip())
            elif sender == self.reason_positive_field:
                self.log_field_change("user_reason_positive", self.reason_positive_field.toPlainText().strip())
            elif sender == self.reason_negative_field:
                self.log_field_change("user_reason_negative", self.reason_negative_field.toPlainText().strip())

        qid = self.current_question_id
        new_data = {
            "user_answer_positive": self.answer_positive_field.toPlainText().strip(),
            "user_answer_negative": self.answer_negative_field.toPlainText().strip(),
            "user_reason_positive": self.reason_positive_field.toPlainText().strip(),
            "user_reason_negative": self.reason_negative_field.toPlainText().strip(),
            "user_rating": self.star_rating.getRating(),
        }
        default_data = {
            "user_answer_positive": "",
            "user_answer_negative": "",
            "user_reason_positive": "",
            "user_reason_negative": "",
            "user_rating": 0,  # default rating is 0
        }
        answers_extended_path = os.path.join(self.current_paper_folder, "answers_extended.json")
        if new_data == default_data:
            if "QUESTIONS" in self.answers_extended_data and qid in self.answers_extended_data["QUESTIONS"]:
                del self.answers_extended_data["QUESTIONS"][qid]
                if not self.answers_extended_data["QUESTIONS"]:
                    if os.path.isfile(answers_extended_path):
                        os.remove(answers_extended_path)
                    self.modified_label.setText("Modified: Not saved")
                else:
                    try:
                        with open(answers_extended_path, "w", encoding="utf-8") as f:
                            json.dump(self.answers_extended_data, f, indent=2)
                        mod_time = os.path.getmtime(answers_extended_path)
                        mod_dt = datetime.fromtimestamp(mod_time).strftime("%Y-%m-%d %H:%M:%S")
                        self.modified_label.setText(f"Modified: {mod_dt}")
                    except Exception as e:
                        print(f"Error saving answers_extended.json: {e}")
            # Update progress display even when cleared.
            self.update_progress_display()
            return

        if "QUESTIONS" not in self.answers_extended_data:
            self.answers_extended_data["QUESTIONS"] = {}
        if self.answers_extended_data["QUESTIONS"].get(qid) == new_data:
            return

        self.answers_extended_data["QUESTIONS"][qid] = new_data
        try:
            with open(answers_extended_path, "w", encoding="utf-8") as f:
                json.dump(self.answers_extended_data, f, indent=2)
            mod_time = os.path.getmtime(answers_extended_path)
            mod_dt = datetime.fromtimestamp(mod_time).strftime("%Y-%m-%d %H:%M:%S")
            self.modified_label.setText(f"Modified: {mod_dt}")
        except Exception as e:
            print(f"Error saving answers_extended.json: {e}")

        # Update the current paper's progress percentage in real time.
        self.update_progress_display()

    def set_annotation_mode(self, mode):
        self.annotation_mode = mode
        self.individual_btn.setChecked(mode == "individual")
        self.all_btn.setChecked(mode == "all")
        if mode == "all":
            self.chunk_list.setDisabled(True)
            self.chunk_list.clearSelection()  # Ensure no selection/highlighting.
            # In "all" mode you might set a specific color:
            for index in range(self.chunk_list.count()):
                item = self.chunk_list.item(index)
                item.setBackground(QColor())
        else:
            self.chunk_list.setDisabled(False)
            # Remove any manual background color so it uses the default stylesheet.
            for index in range(self.chunk_list.count()):
                item = self.chunk_list.item(index)
                item.setBackground(QColor())  # Reset to default.
            if self.chunk_list.count() > 0:
                self.chunk_list.setCurrentRow(0)
                self.on_chunk_selected(self.chunk_list.item(0))
        self.updateAnnotations()

    def on_chunk_selected(self, item):
        if self.annotation_mode == "all":
            return
        cid = str(item.text()).strip()
        if not self.current_pdf_doc or cid not in self.chunk_dict:
            return
        chunk = self.chunk_dict[cid]
        if "grounding" in chunk and len(chunk["grounding"]) > 0:
            grounding = chunk["grounding"][0]
        else:
            return
        self.current_annotation = {"cid": cid, "box": grounding.get("box"), "page": grounding.get("page")}
        self.current_page_num = grounding.get("page", 0)

        self.render_current_page()

    def on_prev_page(self):
        if self.current_pdf_doc and self.current_page_num > 0:
            self.current_page_num -= 1
            self.render_current_page()

    def on_next_page(self):
        if self.current_pdf_doc and self.current_page_num < len(self.current_pdf_doc) - 1:
            self.current_page_num += 1
            self.render_current_page()

    def on_zoom_changed(self, value):
        self.current_zoom = value
        self.zoom_label.setText(f"{value}%")
        self.render_current_page()

    def render_current_page(self):
        if not self.current_pdf_doc:
            return
        page = self.current_pdf_doc[self.current_page_num]
        orig_rect = page.rect
        orig_width, orig_height = orig_rect.width, orig_rect.height
        viewer_size = self.pdf_scroll_area.viewport().size()
        viewer_width, viewer_height = viewer_size.width(), viewer_size.height()
        base_scale = min(viewer_width / orig_width, viewer_height / orig_height)
        effective_scale = base_scale * (self.current_zoom / 100.0)

        resolution_factor = 1.0
        matrix = fitz.Matrix(effective_scale * resolution_factor, effective_scale * resolution_factor)

        pix = page.get_pixmap(matrix=matrix)
        rendered_width, rendered_height = pix.width, pix.height

        # Instead of centering via offsets, resize the PDFViewer to match the rendered page.
        displayed_rect = QRect(0, 0, rendered_width, rendered_height)
        self.pdf_scroll_area.pdf_viewer.resize(rendered_width, rendered_height)

        image = QImage(
            pix.samples, pix.width, pix.height, pix.stride, QImage.Format_RGBA8888 if pix.alpha else QImage.Format_RGB888
        ).copy()
        rendered_pixmap = QPixmap.fromImage(image)

        # Prepare annotations (adjust x_offset and y_offset to 0 now)
        annotations = []
        if self.annotation_mode == "individual" and self.current_annotation is not None:
            # Get the chunk corresponding to the current annotation.
            cid = self.current_annotation.get("cid", "")
            if cid in self.chunk_dict:
                chunk = self.chunk_dict[cid]
                if "grounding" in chunk:
                    # Loop over all groundings in the chunk.
                    for grounding in chunk["grounding"]:
                        if grounding.get("page") == self.current_page_num:
                            ann = self.computeAnnotation(
                                {"cid": cid, "box": grounding.get("box")}, rendered_width, rendered_height, 0, 0
                            )
                            if ann:
                                annotations.append(ann)
        elif self.annotation_mode == "all" and self.current_question_chunk_ids:
            for cid in self.current_question_chunk_ids:
                cid = str(cid).strip()
                if cid in self.chunk_dict:
                    chunk = self.chunk_dict[cid]
                    if "grounding" in chunk:
                        for grounding in chunk["grounding"]:
                            if grounding.get("page") == self.current_page_num:
                                ann = self.computeAnnotation(
                                    {"cid": cid, "box": grounding.get("box")}, rendered_width, rendered_height, 0, 0
                                )
                                if ann:
                                    annotations.append(ann)
        self.pdf_scroll_area.pdf_viewer.setAnnotations(annotations)
        self.pdf_scroll_area.pdf_viewer.setRenderedPixmap(rendered_pixmap, displayed_rect)
        total_pages = len(self.current_pdf_doc)
        self.page_label.setText(f"{self.current_page_num+1}/{total_pages}")

    def computeAnnotation(self, ann_data, img_width, img_height, x_offset, y_offset, padding=2):
        rel_box = ann_data.get("box")
        if not rel_box:
            return None
        l = int(rel_box.get("l", 0) * img_width) + x_offset
        t = int(rel_box.get("t", 0) * img_height) + y_offset
        r = int(rel_box.get("r", 0) * img_width) + x_offset
        b = int(rel_box.get("b", 0) * img_height) + y_offset

        l -= padding
        t -= padding
        r += padding
        b += padding
        rect = QRect(l, t, r - l, b - t)
        return {"rect": rect, "cid": ann_data.get("cid", "")}

    def updateAnnotations(self):
        self.render_current_page()

    def update_progress_display(self):
        """
        Refresh the paper list item's text for the current paper,
        showing the updated progress percentage.
        """
        current_item = self.paper_list.currentItem()
        if current_item:
            # Extract the paper id (first token before any spaces)
            paper_id = current_item.text().split()[0]
            progress = self.compute_progress_for_current_paper()
            current_item.setText(f"{paper_id} ({progress}%)")

    def update_modification_label(self):
        answers_extended_path = os.path.join(self.current_paper_folder, "answers_extended.json")
        if os.path.isfile(answers_extended_path):
            mod_time = os.path.getmtime(answers_extended_path)
            mod_dt = datetime.fromtimestamp(mod_time).strftime("%Y-%m-%d %H:%M:%S")
            self.modified_label.setText(f"Modified: {mod_dt}")
        else:
            self.modified_label.setText("Modified: Never")


def main():
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
