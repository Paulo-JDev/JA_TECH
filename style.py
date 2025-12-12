STYLE = """
* {
    font-family: 'Segoe UI', Arial;
}

/* Fundo geral azul claro */
QWidget {
    background-color: #e6f2ff;
    color: #000000;
}

/* Labels sempre pretas */
QLabel {
    color: #000000;
    font-size: 14px;
    font-weight: bold;
}

/* Campos de entrada */
QLineEdit, QSpinBox, QTimeEdit {
    background: #ffffff;
    color: #000000;
    border: 2px solid #000000;
    border-radius: 6px;
    padding: 6px;
    font-size: 13px;
}

/* Lista de Downloads */
QListWidget {
    background: #ffffff;
    color: #000000;
    border: 2px solid #000000;
    border-radius: 6px;
}

/* --- NOVO: Estilo para os Radio Buttons (Seleção Vídeo/Áudio) --- */
QRadioButton {
    color: #000000;
    font-size: 14px;
    padding: 5px;
    font-weight: bold;
}
QRadioButton::indicator {
    width: 18px;
    height: 18px;
    border-radius: 9px;
    border: 2px solid #000000;
    background-color: #ffffff;
}
QRadioButton::indicator:checked {
    background-color: #ffd000; /* Amarelo quando marcado */
    border: 2px solid #000000;
}

/* --- NOVO: Estilo para o ComboBox (Lista de qualidades) --- */
QComboBox {
    background: #ffffff;
    color: #000000;
    border: 2px solid #000000;
    border-radius: 6px;
    padding: 5px;
}
QComboBox::drop-down {
    border: 0px;
}

/* Botões de ação */
QPushButton {
    background-color: #ffd000;
    border: 1px solid #000000;
    border-radius: 8px;
    padding: 8px 14px;
    color: #000000;
    font-weight: bold;
    font-size: 13px;
}
QPushButton:hover {
    background-color: #ffdd44;
}
QPushButton:pressed {
    background-color: #e6c200;
}
QPushButton:disabled {
    background-color: #cccccc; /* Cinza quando desativado */
    color: #666666;
    border: 1px solid #999999;
}

/* Agrupamentos (Caixas em volta das seções) */
QGroupBox {
    border: 2px solid #000000;
    border-radius: 6px;
    margin-top: 20px;
    font-weight: bold;
    color: #000000;
}
QGroupBox::title {
    subcontrol-origin: margin;
    left: 10px;
    padding: 0 3px 0 3px;
}

/* Barra de rolagem (opcional, para ficar bonito) */
QScrollBar:vertical {
    background: #f0f0f0;
    width: 12px;
}
QScrollBar::handle:vertical {
    background: #cdcdcd;
    border-radius: 4px;
}
"""
