LIGHT = """
QMainWindow, QWidget#Root {
    background: #111417;
    color: #2f2923;
    font-family: "Segoe UI";
    font-size: 10.5pt;
}
QFrame#Table {
    background: __TABLE__;
    border: 1px solid #33454a;
    border-radius: 18px;
}
QFrame#Compartment {
    background: #181d21;
    border: 1px solid #33454a;
    border-radius: 8px;
}
QFrame#Compartment[dragging="true"] {
    border: 2px solid __ACCENT__;
}
QLabel#CompartmentTitle {
    font-size: 13pt;
    font-weight: 700;
    color: #f8efe2;
}
QLabel#CompartmentDescription {
    color: #aebbc0;
    font-size: 9.5pt;
}
QLabel#DragGrip {
    color: __ACCENT__;
    font-weight: 800;
}
QLineEdit, QTextEdit, QComboBox, QDateEdit, QSpinBox {
    background: #101417;
    color: #f8efe2;
    border: 1px solid #33454a;
    border-radius: 6px;
    padding: 6px;
}
QPushButton {
    background: __ACCENT__;
    color: white;
    border: none;
    border-radius: 6px;
    padding: 7px 10px;
    font-weight: 600;
}
QPushButton:hover { background: #89e3db; }
QPushButton#Subtle {
    background: #242d31;
    color: #f8efe2;
}
QPushButton#Danger {
    background: #a24b45;
}
QListWidget, QTableWidget {
    background: #101417;
    color: #f8efe2;
    border: 1px solid #33454a;
    border-radius: 6px;
}
"""

DARK = """
QMainWindow, QWidget#Root {
    background: #0d1013;
    color: #f8efe2;
    font-family: "Segoe UI Variable", "Aptos", "Segoe UI";
    font-size: 10pt;
}
QFrame#Table {
    background: __TABLE__;
    border: 1px solid #3b5057;
    border-radius: 22px;
}
QFrame#Compartment {
    background: #171d22;
    border: 1px solid #34484f;
    border-radius: 10px;
}
QFrame#Compartment[dragging="true"] {
    border: 2px solid __ACCENT__;
}
QLabel#CompartmentTitle {
    font-size: 12.5pt;
    font-weight: 650;
    color: #f8efe2;
}
QLabel#CompartmentDescription {
    color: #a9b7bd;
    font-size: 9pt;
}
QLabel#DragGrip {
    color: __ACCENT__;
    font-weight: 800;
}
QLabel#ResizeGrip {
    color: #6f858d;
    font-size: 8pt;
    font-weight: 700;
}
QLineEdit, QTextEdit, QComboBox, QDateEdit, QSpinBox {
    background: #0f1418;
    color: #f8efe2;
    border: 1px solid #2d3d43;
    border-radius: 6px;
    padding: 6px 8px;
    selection-background-color: __ACCENT__;
    selection-color: #071010;
}
QPushButton {
    background: __ACCENT__;
    color: #071010;
    border: none;
    border-radius: 8px;
    padding: 7px 12px;
    font-weight: 650;
}
QPushButton:hover { background: #89e3db; }
QPushButton#Subtle {
    background: #222c31;
    color: #f8efe2;
    border: 1px solid #33484f;
}
QPushButton#Danger {
    background: #a24b45;
}
QListWidget, QTableWidget {
    background: #0f1418;
    color: #f8efe2;
    border: 1px solid #2d3d43;
    border-radius: 6px;
    gridline-color: #26343a;
    alternate-background-color: #12191d;
}
QHeaderView::section {
    background: #1c252a;
    color: #f8efe2;
    border: 1px solid #2d3d43;
    padding: 6px;
    font-weight: 650;
}
QTableWidget::item:selected, QListWidget::item:selected {
    background: __ACCENT__;
    color: #071010;
}
QToolButton {
    background: #171d22;
    color: #f8efe2;
    border: 1px solid #2f4147;
    border-radius: 10px;
    padding: 8px 14px;
    font-weight: 650;
}
QToolButton:hover {
    border-color: __ACCENT__;
}
QMenu {
    background: #11171b;
    color: #f8efe2;
    border: 1px solid #2f4147;
}
QLabel#TotalsLabel {
    color: __ACCENT__;
    font-weight: 700;
}
"""
