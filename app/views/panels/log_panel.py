"""
Módulo com o painel de visualização de logs
"""
import sys
import re
from io import StringIO
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QTextEdit, QPushButton, QHBoxLayout, 
                           QLabel, QCheckBox, QFileDialog)
from PyQt5.QtCore import Qt, pyqtSlot, QObject, pyqtSignal
from PyQt5.QtGui import QColor, QTextCharFormat
from app.utils import log

class LogStream(QObject):
    """Stream para redirecionar saída do console para um widget"""
    
    # Sinal emitido quando novos dados são recebidos
    newText = pyqtSignal(str)
    
    def __init__(self, original_stream=None):
        """
        Inicializa o stream de logs
        
        Args:
            original_stream: Stream original para replicar a saída
        """
        super().__init__()
        self.buffer = StringIO()
        self.original_stream = original_stream
    
    def write(self, text):
        """
        Escreve texto no stream e emite sinal
        
        Args:
            text: Texto a ser escrito
        """
        if text:  # Inclui espaços em branco para preservar formatação
            self.newText.emit(text)
            self.buffer.write(text)
            
            # Também enviar para o stream original, se existir
            if self.original_stream is not None:
                self.original_stream.write(text)
                self.original_stream.flush()
            
    def flush(self):
        """Limpa o buffer"""
        if self.original_stream is not None:
            self.original_stream.flush()
        
    def getvalue(self):
        """Retorna o conteúdo do buffer"""
        return self.buffer.getvalue()

class LogPanel(QWidget):
    """Painel para visualização de logs da aplicação"""
    
    def __init__(self, parent=None):
        """
        Inicializa o painel de logs
        
        Args:
            parent: Widget pai
        """
        super().__init__(parent)
        self.setup_ui()
        self.setup_stream()

        # Mapeamento de cores ANSI para QColor
        self.ansi_colors = {
            '30': QColor(0, 0, 0),        # Preto
            '31': QColor(170, 0, 0),      # Vermelho
            '32': QColor(0, 130, 0),      # Verde  
            '33': QColor(170, 85, 0),     # Amarelo
            '34': QColor(0, 0, 170),      # Azul
            '35': QColor(170, 0, 170),    # Magenta
            '36': QColor(0, 0, 170),    # Ciano QColor(0, 170, 170)
            '37': QColor(170, 170, 170),  # Branco
        }
        
    def setup_ui(self):
        """Configura a interface do painel"""
        # Layout principal
        layout = QVBoxLayout(self)
        
        # Opções de visualização
        options_layout = QHBoxLayout()
        
        # Auto-rolagem
        self.auto_scroll = QCheckBox("Auto-rolagem")
        self.auto_scroll.setChecked(True)
        
        # Word wrap
        self.word_wrap = QCheckBox("Quebra de linha")
        self.word_wrap.setChecked(False)
        self.word_wrap.stateChanged.connect(self.toggle_word_wrap)
        
        # Montagem layout de opções
        options_layout.addWidget(self.auto_scroll)
        options_layout.addWidget(self.word_wrap)
        options_layout.addStretch(1)
        
        layout.addLayout(options_layout)
        
        # Área de texto para logs
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setLineWrapMode(QTextEdit.NoWrap)
        self.log_text.setStyleSheet("""
            QTextEdit {
                font-family: 'Consolas', 'Courier New', monospace;
                font-size: 10pt;
                background-color: #f5f5f5;
                color: #333333;
                border: 1px solid #cccccc;
            }
        """)
        layout.addWidget(self.log_text)
        
        # Botões para controle de logs
        button_layout = QHBoxLayout()
        
        self.clear_button = QPushButton("Limpar Logs")
        self.clear_button.clicked.connect(self.clear_logs)
        
        self.copy_button = QPushButton("Copiar para Área de Transferência")
        self.copy_button.clicked.connect(self.copy_logs)
        
        self.save_button = QPushButton("Salvar Logs")
        self.save_button.clicked.connect(self.save_logs)
        
        button_layout.addWidget(self.clear_button)
        button_layout.addWidget(self.copy_button)
        button_layout.addWidget(self.save_button)
        button_layout.addStretch(1)
        
        layout.addLayout(button_layout)
    
    def setup_stream(self):
        """Configura o stream de redirecionamento"""
        # Guardar os streams originais
        self.original_stdout = sys.stdout
        self.original_stderr = sys.stderr
        
        # Criar e conectar o stream de logs
        self.log_stream = LogStream(self.original_stdout)
        self.error_stream = LogStream(self.original_stderr)
        self.log_stream.newText.connect(self.append_log)
        self.error_stream.newText.connect(self.append_error_log)
        
        # Redirecionar saídas, mas mantendo a saída para o terminal original
        sys.stdout = self.log_stream
        sys.stderr = self.error_stream
        
        # Adicionar mensagem inicial
        self.append_log("=== Log de eventos do OAS-GUI ===\n")
        self.append_log("Sistema iniciado. Logs serão registrados aqui.\n")
        
    def toggle_word_wrap(self, state):
        """Alterna a quebra de linha no widget de texto"""
        if state == Qt.Checked:
            self.log_text.setLineWrapMode(QTextEdit.WidgetWidth)
        else:
            self.log_text.setLineWrapMode(QTextEdit.NoWrap)
        
    @pyqtSlot(str)
    def append_log(self, text):
        """
        Adiciona texto ao widget de logs com suporte a cores ANSI
        
        Args:
            text: Texto a adicionar (pode conter códigos ANSI)
        """
        # Regex para encontrar códigos ANSI
        ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
        
        cursor = self.log_text.textCursor()
        cursor.movePosition(cursor.End)
        
        # Dividir o texto em partes com e sem códigos ANSI
        parts = ansi_escape.split(text)
        codes = ansi_escape.findall(text)
        
        current_format = QTextCharFormat()
        current_format.setForeground(QColor(51, 51, 51))  # Cor padrão (#333333)
        
        for i, part in enumerate(parts):
            if part:  # Se há texto para adicionar
                cursor.setCharFormat(current_format)
                cursor.insertText(part)
            
            # Se há um código ANSI correspondente a esta parte
            if i < len(codes):
                code = codes[i]
                # Extrair o número do código (ex: \033[32m -> 32)
                color_match = re.search(r'\[(\d+)m', code)
                if color_match:
                    color_code = color_match.group(1)
                    if color_code == '0':  # Reset
                        current_format = QTextCharFormat()
                        current_format.setForeground(QColor(51, 51, 51))
                    elif color_code in self.ansi_colors:
                        current_format.setForeground(self.ansi_colors[color_code])
        
        # Auto-rolagem se ativada
        if self.auto_scroll.isChecked():
            self.log_text.setTextCursor(cursor)
            self.log_text.ensureCursorVisible()

    @pyqtSlot(str)
    def append_error_log(self, text):
        """
        Adiciona texto de erro ao widget de logs com formatação especial
        
        Args:
            text: Texto de erro a adicionar
        """
        # You can add special formatting for errors here if needed
        self.append_log(text)
            
    def clear_logs(self):
        """Limpa o conteúdo dos logs"""
        from app.utils import log
        
        self.log_text.clear()
        
        # Adicionar mensagem inicial
        self.append_log("=== Log limpo ===\n")
        log.info("Log limpo pelo usuário")
        
    def copy_logs(self):
        """Copia logs para a área de transferência"""
        self.log_text.selectAll()
        self.log_text.copy()
        # Desselecionar após copiar
        cursor = self.log_text.textCursor()
        cursor.clearSelection()
        self.log_text.setTextCursor(cursor)
        
    def save_logs(self):
        """Salva logs em um arquivo"""
        from datetime import datetime
        
        # Gerar nome padrão com data e hora
        default_name = f"logs_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        
        # Abrir diálogo para salvar
        filename, _ = QFileDialog.getSaveFileName(
            self, "Salvar Logs", default_name, "Arquivos de Texto (*.txt)"
        )
        
        if filename:
            try:
                with open(filename, 'w', encoding='utf-8') as f:
                    f.write(self.log_text.toPlainText())
                log.info(f"Logs salvos em: {filename}")
            except Exception as e:
                log.error(f"Erro ao salvar logs: {str(e)}")
                
    def closeEvent(self, event):
        """Restaura saída original ao fechar"""
        # Verificar se os streams foram modificados
        if hasattr(self, 'original_stdout') and hasattr(self, 'original_stderr'):
            # Restaurar os streams originais
            sys.stdout = self.original_stdout
            sys.stderr = self.original_stderr
        
        # Continuar com o evento de fechamento
        super().closeEvent(event) 