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
QFrame#GridSlot {
    background: rgba(255, 255, 255, 0.025);
    border: 1px dashed #496069;
    border-radius: 8px;
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
QPushButton#ThemeToggle {
    background: #efefed;
    color: #5f5e5a;
    border: 1px solid #dfdfdc;
}
QPushButton#ThemeToggle:hover { background: #e5e5e2; color: #2f2e2b; }
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
    background: #0b0e11;
    color: #f8efe2;
    font-family: "Segoe UI Variable", "Aptos", "Segoe UI";
    font-size: 9.5pt;
}
QFrame#Table {
    background: __TABLE__;
    border: 1px solid #24343a;
    border-radius: 16px;
}
QFrame#Compartment {
    background: #171d22;
    border: 1px solid #34484f;
    border-radius: 9px;
}
QFrame#Compartment[dragging="true"] {
    border: 2px solid __ACCENT__;
}
QLabel#CompartmentTitle {
    font-size: 11.5pt;
    font-weight: 650;
    color: #f8efe2;
}
QLabel#CompartmentDescription {
    color: #8d9ba1;
    font-size: 8pt;
}
QLabel#ResizeGrip {
    color: #5c6d74;
    font-size: 7.5pt;
    font-weight: 600;
}
QLabel#WorkspaceNotice {
    color: #8d9ba1;
}
QLabel#AppName {
    color: #f8efe2;
    font-size: 16pt;
    font-weight: 700;
}
QLabel#FocusClock {
    color: __ACCENT__;
    font-size: 32pt;
    font-weight: 700;
    qproperty-alignment: AlignCenter;
}
QLineEdit, QTextEdit, QComboBox, QDateEdit, QSpinBox {
    background: #0f1418;
    color: #f8efe2;
    border: 1px solid #2d3d43;
    border-radius: 5px;
    padding: 3px 6px;
    selection-background-color: __ACCENT__;
    selection-color: #071010;
}
QPushButton {
    background: __ACCENT__;
    color: #071010;
    border: none;
    border-radius: 6px;
    padding: 5px 8px;
    font-weight: 600;
}
QPushButton:hover { background: #89e3db; }
QPushButton#Subtle {
    background: #1d2529;
    color: #f8efe2;
    border: 1px solid #2b3b42;
}
QPushButton#Danger {
    background: #a24b45;
}
QListWidget, QTableWidget {
    background: #0f1418;
    color: #f8efe2;
    border: 1px solid #2d3d43;
    border-radius: 5px;
    gridline-color: #26343a;
    alternate-background-color: #12191d;
}
QHeaderView::section {
    background: #1c252a;
    color: #f8efe2;
    border: 1px solid #2d3d43;
    padding: 3px;
    font-weight: 600;
}
QTableWidget::item {
    padding: 2px;
}
QTableWidget::item:selected, QListWidget::item:selected {
    background: __ACCENT__;
    color: #071010;
}
QToolButton {
    background: #171d22;
    color: #f8efe2;
    border: 1px solid #2b3b42;
    border-radius: 8px;
    padding: 7px 12px;
    font-weight: 600;
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

# Shared workspace theme. Keeping this central means new modules inherit the same
# spacing, typography, controls and navigation treatment without page-level CSS.
NOTION_LIGHT = """
QMainWindow, QWidget#Root {
    background: #ffffff;
    color: #37352f;
    font-family: "Segoe UI Variable", "Inter", "Segoe UI", Arial;
    font-size: 10pt;
}
QFrame#Sidebar {
    background: #f7f7f5;
    border: none;
    border-right: 1px solid #e9e9e7;
}
QLabel#AppName {
    color: #2f2e2b;
    font-size: 16pt;
    font-weight: 700;
    padding-left: 8px;
}
QLabel#SidebarCaption, QLabel#SidebarFooter {
    color: #9b9a97;
    font-size: 8.5pt;
    padding: 0 8px 8px 8px;
}
QListWidget#SidebarNav {
    background: transparent;
    border: none;
    outline: none;
    padding: 4px 0;
}
QListWidget#SidebarNav::item {
    color: #5f5e5a;
    border: none;
    border-radius: 6px;
    min-height: 31px;
    padding: 2px 10px;
    margin: 1px 0;
}
QListWidget#SidebarNav::item:hover {
    background: #ededeb;
    color: #37352f;
}
QListWidget#SidebarNav::item:selected {
    background: #e8e8e6;
    color: #242320;
    font-weight: 600;
}
QListWidget#SidebarNav::item:disabled {
    background: transparent;
    color: #aaa9a5;
    font-size: 7.5pt;
    font-weight: 700;
    padding-top: 14px;
}
QFrame#ContentArea, QStackedWidget#PageStack {
    background: #ffffff;
    border: none;
}
QTabWidget::pane { border: 1px solid #e7e7e4; border-radius: 9px; top: -1px; }
QTabBar::tab { background: #f7f7f5; color: #787774; padding: 8px 18px; margin-right: 3px; border-top-left-radius: 7px; border-top-right-radius: 7px; }
QTabBar::tab:selected { background: #ffffff; color: #2f2e2b; font-weight: 600; border-top: 3px solid __ACCENT__; }
QLabel#JournalPreviewTitle { color: #2f2e2b; font-size: 14pt; font-weight: 650; padding: 6px; }
QLabel#BoardTitle {
    color: #2f2e2b;
    font-size: 22pt;
    font-weight: 700;
}
QLabel#BoardDescription { color: #787774; font-size: 9.5pt; }
QFrame#DashboardCanvas {
    background: #f7f7f5;
    border: 1px solid #e7e7e4;
    border-radius: 14px;
}
QFrame#DashboardSlot {
    background: rgba(255, 255, 255, 0.35);
    border: 1px dashed #dededb;
    border-radius: 10px;
}
QFrame#DashboardCanvas QFrame#Compartment {
    background: #ffffff;
    border: 1px solid #e2e2df;
    border-radius: 10px;
}
QFrame#DashboardCanvas QFrame#Compartment[dragging="true"] { border: 2px solid #9b9a97; }
QFrame#DashboardCanvas QLabel#CompartmentTitle { font-size: 11pt; padding: 0; }
QFrame#DashboardCanvas QLabel#CompartmentDescription { font-size: 8pt; padding-bottom: 2px; }
QFrame#DashboardCanvas QLineEdit,
QFrame#DashboardCanvas QTextEdit,
QFrame#DashboardCanvas QComboBox { padding: 3px 5px; }
QFrame#DashboardCanvas QPushButton { padding: 4px 7px; font-size: 8.5pt; }
QFrame#DashboardCanvas QHeaderView::section { padding: 3px; font-size: 7.5pt; }
QFrame#DashboardCanvas QTableWidget::item { padding: 2px 3px; }
QFrame#Compartment {
    background: #ffffff;
    border: none;
    border-radius: 0;
}
QLabel#CompartmentTitle {
    color: #2f2e2b;
    font-size: 22pt;
    font-weight: 700;
    padding: 2px 0 4px 0;
}
QLabel#CompartmentDescription {
    color: #787774;
    font-size: 9.5pt;
    padding-bottom: 10px;
}
QLabel#ResizeGrip { color: transparent; }
QLabel#WorkspaceNotice { color: #787774; }
QLabel#TotalsLabel { color: #37352f; font-weight: 700; }
QLabel#FocusClock {
    color: #37352f;
    font-size: 34pt;
    font-weight: 650;
    qproperty-alignment: AlignCenter;
}
QLineEdit, QTextEdit, QComboBox, QDateEdit, QSpinBox {
    background: #ffffff;
    color: #37352f;
    border: 1px solid #dededb;
    border-radius: 7px;
    padding: 7px 9px;
    selection-background-color: #d9e7f5;
    selection-color: #242320;
}
QLineEdit:hover, QTextEdit:hover, QComboBox:hover, QDateEdit:hover, QSpinBox:hover {
    border-color: #c7c7c3;
}
QLineEdit:focus, QTextEdit:focus, QComboBox:focus, QDateEdit:focus, QSpinBox:focus {
    border: 1px solid #9b9a97;
}
QComboBox::drop-down { border: none; width: 24px; }
QPushButton {
    background: #37352f;
    color: #ffffff;
    border: 1px solid #37352f;
    border-radius: 7px;
    padding: 7px 12px;
    font-weight: 600;
}
QPushButton:hover { background: #242320; border-color: #242320; }
QPushButton:pressed { background: #11110f; }
QPushButton#Subtle {
    background: #f7f7f5;
    color: #5f5e5a;
    border: 1px solid #e4e4e1;
}
QPushButton#Subtle:hover { background: #ededeb; color: #2f2e2b; }
QPushButton#Danger {
    background: transparent;
    color: #787774;
    border: 1px solid #e4e4e1;
}
QPushButton#Danger:hover { background: #fbeaea; color: #9b3b3b; border-color: #efcaca; }
QListWidget, QTableWidget {
    background: #ffffff;
    color: #37352f;
    border: 1px solid #e7e7e4;
    border-radius: 9px;
    gridline-color: transparent;
    alternate-background-color: #fafaf9;
    outline: none;
}
QListWidget::item {
    border-bottom: 1px solid #efefed;
    padding: 10px 12px;
    min-height: 28px;
}
QListWidget::item:hover, QTableWidget::item:hover { background: #f7f7f5; }
QListWidget::item:selected, QTableWidget::item:selected {
    background: #efefed;
    color: #2f2e2b;
}
QHeaderView::section {
    background: #fafaf9;
    color: #787774;
    border: none;
    border-bottom: 1px solid #e7e7e4;
    padding: 9px 8px;
    font-size: 8.5pt;
    font-weight: 600;
}
QTableWidget::item {
    border: none;
    border-bottom: 1px solid #f0f0ee;
    /* Keep enough vertical room for Qt's temporary QLineEdit cell editor.
       Large item padding is subtracted from the editor geometry and clipped
       typed text in compact spreadsheet rows. */
    padding: 2px 8px;
}
QTableWidget QLineEdit {
    background: #ffffff;
    color: #242320;
    selection-background-color: #d9e7f5;
    selection-color: #242320;
    border: 1px solid #9b9a97;
    border-radius: 0;
    padding: 2px 4px;
}
QCheckBox { color: #5f5e5a; spacing: 8px; }
QCheckBox::indicator { width: 16px; height: 16px; border: 1px solid #b8b8b4; border-radius: 4px; background: white; }
QCheckBox::indicator:hover { border-color: #787774; background: #fafaf9; }
QCheckBox::indicator:checked { background: __ACCENT__; border-color: __ACCENT__; }
QMenu {
    background: #ffffff;
    color: #37352f;
    border: 1px solid #dededb;
    border-radius: 7px;
    padding: 5px;
}
QMenu::item { border-radius: 5px; padding: 7px 20px; }
QMenu::item:selected { background: #efefed; }
QToolTip { background: #37352f; color: white; border: none; padding: 5px; }
QScrollBar:vertical { background: transparent; width: 10px; margin: 2px; }
QScrollBar::handle:vertical { background: #d4d4d1; border-radius: 4px; min-height: 30px; }
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }
"""

# Dark mode keeps the same hierarchy and spacing; only the neutral palette changes.
# Appending overrides avoids duplicating the full component system above.
NOTION_DARK = NOTION_LIGHT + """
QMainWindow, QWidget#Root { background: #191919; color: #e6e6e3; }
QFrame#Sidebar { background: #202020; border-right-color: #333333; }
QLabel#AppName, QLabel#CompartmentTitle, QLabel#BoardTitle { color: #f1f1ef; }
QLabel#SidebarCaption, QLabel#SidebarFooter, QLabel#CompartmentDescription,
QLabel#BoardDescription, QLabel#WorkspaceNotice, QLabel#InlineNotice { color: #9b9b97; }
QListWidget#SidebarNav::item { color: #b7b7b3; }
QListWidget#SidebarNav::item:hover { background: #2c2c2c; color: #f1f1ef; }
QListWidget#SidebarNav::item:selected { background: #333333; color: #ffffff; }
QListWidget#SidebarNav::item:disabled { background: transparent; color: #777773; }
QFrame#ContentArea, QStackedWidget#PageStack, QFrame#Compartment { background: #191919; }
QTabWidget::pane { border-color: #3c3c3c; }
QTabBar::tab { background: #252525; color: #aaa9a5; }
QTabBar::tab:selected { background: #191919; color: #ffffff; }
QLabel#JournalPreviewTitle { color: #f1f1ef; }
QFrame#DashboardCanvas { background: #202020; border-color: #393939; }
QFrame#DashboardSlot { background: rgba(255,255,255,0.015); border-color: #3b3b3b; }
QFrame#DashboardCanvas QFrame#Compartment { background: #252525; border-color: #3d3d3d; }
QLineEdit, QTextEdit, QComboBox, QDateEdit, QSpinBox {
    background: #242424; color: #e6e6e3; border-color: #414141;
    selection-background-color: #40566c; selection-color: #ffffff;
}
QLineEdit:hover, QTextEdit:hover, QComboBox:hover, QDateEdit:hover, QSpinBox:hover { border-color: #565656; }
QLineEdit:focus, QTextEdit:focus, QComboBox:focus, QDateEdit:focus, QSpinBox:focus { border-color: #777773; }
QPushButton { background: #e6e6e3; color: #222222; border-color: #e6e6e3; }
QPushButton:hover { background: #ffffff; border-color: #ffffff; }
QPushButton#Subtle, QPushButton#ThemeToggle { background: #292929; color: #d5d5d2; border-color: #414141; }
QPushButton#Subtle:hover, QPushButton#ThemeToggle:hover { background: #353535; color: #ffffff; }
QPushButton#Danger { background: transparent; color: #9b9b97; border-color: #414141; }
QPushButton#Danger:hover { background: #422727; color: #efb8b8; border-color: #704040; }
QListWidget, QTableWidget { background: #222222; color: #e6e6e3; border-color: #3c3c3c; alternate-background-color: #262626; }
QListWidget::item, QTableWidget::item { border-bottom-color: #353535; }
QListWidget::item:hover, QTableWidget::item:hover { background: #2c2c2c; }
QListWidget::item:selected, QTableWidget::item:selected { background: #3a3a3a; color: #ffffff; }
QTableWidget QLineEdit {
    background: #242424; color: #ffffff; border-color: #777773;
    selection-background-color: #40566c; selection-color: #ffffff;
}
QHeaderView::section { background: #252525; color: #aaa9a5; border-bottom-color: #404040; }
QCheckBox { color: #c7c7c3; }
QCheckBox::indicator { background: #242424; border-color: #666662; }
QMenu { background: #252525; color: #e6e6e3; border-color: #444444; }
QMenu::item:selected { background: #383838; }
QScrollBar::handle:vertical { background: #555551; }
"""
