STYLE = '''
QMainWindow, QWidget { background: #101113; color: #ECEDEF; font-family: "Segoe UI"; }
QWidget#Sidebar { background: #151619; border-right: 1px solid #27292D; }
QLabel#Brand { font-size: 19px; font-weight: 700; color: #FFFFFF; }
QLabel#Muted { color: #858990; }
QLabel#PageTitle { font-size: 25px; font-weight: 700; color: #F4F4F5; }
QLabel#SectionTitle { font-size: 14px; font-weight: 650; color: #E7E8EA; }
QPushButton { background: #24262A; color: #EDEEF0; border: 1px solid #34363B; border-radius: 8px; padding: 9px 14px; }
QPushButton:hover { background: #303238; border-color: #50535A; }
QPushButton:pressed { background: #1D1F22; }
QPushButton#Primary { background: #FF6A22; color: #151515; border: 0; font-weight: 700; }
QPushButton#Primary:hover { background: #FF8245; }
QPushButton#Nav { text-align: left; background: transparent; border: 0; color: #AEB1B7; padding: 12px 14px; }
QPushButton#Nav:checked { background: #29231F; color: #FF874B; }
QLineEdit, QComboBox { background: #191B1F; border: 1px solid #303238; border-radius: 8px; padding: 11px; color: #F1F1F2; selection-background-color: #FF6A22; }
QLineEdit:focus, QComboBox:focus { border: 1px solid #FF6A22; }
QTableWidget { background: #141619; alternate-background-color: #181A1E; border: 1px solid #292B30; border-radius: 10px; gridline-color: transparent; }
QHeaderView::section { background: #191B1F; color: #92969E; padding: 11px; border: 0; font-weight: 600; }
QTableWidget::item { padding: 7px; border-bottom: 1px solid #25272B; }
QTableWidget::item:selected { background: #34251E; color: #FFFFFF; }
QProgressBar { background: #292B30; border: 0; border-radius: 4px; height: 7px; text-align: center; }
QProgressBar::chunk { background: #FF6A22; border-radius: 4px; }
QCheckBox { spacing: 8px; }
QCheckBox::indicator { width: 16px; height: 16px; }
QScrollBar:vertical { background: #101113; width: 9px; }
QScrollBar::handle:vertical { background: #393C42; border-radius: 4px; min-height: 24px; }
'''
