import sys
import os
import subprocess
import json
import webbrowser
from pathlib import Path
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QLabel, QTimeEdit, QLineEdit, QFrame, QRadioButton, QComboBox,
                             QSpinBox, QPushButton, QListWidget, QApplication, QStackedWidget, QProgressBar,
                             QListWidgetItem, QFileDialog, QMessageBox, QHBoxLayout, QGroupBox, QButtonGroup)
from PyQt6.QtCore import QTimer, QTime, Qt, QSize, QUrl, QThread, pyqtSignal
from PyQt6.QtGui import QIcon
from PyQt6.QtMultimedia import QMediaPlayer, QAudioOutput
from PyQt6.QtMultimediaWidgets import QVideoWidget
import yt_dlp
from style import STYLE

# --- Versão ---
APP_VERSION = "1.0.1"

# --- Configurações Globais ---
DATA_FILE = "configuracoes.json"
ROOT_DIR = Path(sys.executable).parent if getattr(sys, 'frozen', False) else Path(__file__).parent
# Define onde está a pasta build
BUILDE_DIR = ROOT_DIR / "builde"
# Garante que a pasta downloads fique na raiz do projeto
DOWNLOAD_DIR = ROOT_DIR / "downloads"
DOWNLOAD_DIR.mkdir(exist_ok=True) # Cria a pasta se não existir

# Verificação visual no terminal
print(f"Raiz do Projeto: {ROOT_DIR}")
print(f"Pasta de Ferramentas (Builde): {BUILDE_DIR}")

# --- Funções de JSON ---
def carregar_config():
    if not os.path.exists(DATA_FILE):
        return {"eventos": [], "downloads": []}
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"Erro ao carregar JSON: {e}")
        return {"eventos": [], "downloads": []}

def salvar_config(cfg):
    try:
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(cfg, f, indent=4, ensure_ascii=False)
    except Exception as e:
        print(f"Erro ao salvar JSON: {e}")

class DownloadWorker(QThread):
    progress = pyqtSignal(int)
    finished = pyqtSignal(str)
    error = pyqtSignal(str)
    status_msg = pyqtSignal(str)

    def __init__(self, url, is_audio, quality_id):
        super().__init__()
        self.url = url
        self.is_audio = is_audio
        self.quality_id = quality_id
        # Garante que seja string para o yt-dlp
        self.ffmpeg_dir = str(BUILDE_DIR)

    def run(self):
        # --- 1. Verificação de Segurança do FFmpeg ---
        # Verifica se os arquivos realmente existem antes de tentar baixar
        ffmpeg_path = BUILDE_DIR / "ffmpeg.exe"
        ffprobe_path = BUILDE_DIR / "ffprobe.exe"

        if not ffmpeg_path.exists():
            self.error.emit(f"CRÍTICO: ffmpeg.exe não encontrado em:\n{ffmpeg_path}")
            return
        
        if not ffprobe_path.exists():
            self.error.emit(f"CRÍTICO: ffprobe.exe não encontrado em:\n{ffprobe_path}")
            return

        # --- 2. Hook de Progresso Matemático (Sem ler texto) ---
        def progress_hook(d):
            if d['status'] == 'downloading':
                try:
                    # Pega os bytes totais e baixados
                    total = d.get('total_bytes') or d.get('total_bytes_estimate')
                    baixado = d.get('downloaded_bytes', 0)
                    
                    if total:
                        # Calcula a porcentagem matematicamente (infalível)
                        porcentagem = (baixado / total) * 100
                        self.progress.emit(int(porcentagem))
                    
                    # Atualiza o texto de status
                    velocidade = d.get('_speed_str', '...')
                    percent_str = d.get('_percent_str', '0%')
                    self.status_msg.emit(f"Baixando: {percent_str} | Vel: {velocidade}")
                    
                except Exception as e:
                    print(f"Erro cálculo progresso: {e}")
            
            elif d['status'] == 'finished':
                self.progress.emit(100)
                self.status_msg.emit("Download finalizado. Convertendo áudio/vídeo (aguarde)...")

        # --- 3. Configurações yt-dlp ---
        ydl_opts = {
            'outtmpl': str(DOWNLOAD_DIR / '%(title)s.%(ext)s'),
            'ffmpeg_location': self.ffmpeg_dir, # Passa a pasta 'build'
            'quiet': True,
            'noprogress': True, # Desliga a barra do terminal para evitar lixo no log
            'progress_hooks': [progress_hook],
        }

        if self.is_audio:
            ydl_opts.update({
                'format': 'bestaudio/best',
                'postprocessors': [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                    'preferredquality': '192',
                }],
            })
        else:
            # Baixa vídeo + melhor áudio disponível
            ydl_opts.update({
                'format': f'{self.quality_id}+bestaudio/best'
            })

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(self.url, download=True)
                titulo = info.get('title', 'Arquivo')
                self.finished.emit(f"Sucesso! Salvo em downloads.\nTítulo: {titulo}")
        except Exception as e:
            self.error.emit(f"Erro no Download: {str(e)}")

class TelaDownload(QWidget):
    def __init__(self, cfg):
        super().__init__()
        self.cfg = cfg
        self.formatos_encontrados = [] 
        layout = QVBoxLayout()

        # --- Seção YouTube ---
        group_yt = QGroupBox("Download do YouTube")
        layout_yt = QVBoxLayout()

        lbl_url = QLabel("Cole o Link do Vídeo:")
        self.youtube_input = QLineEdit()
        self.youtube_input.setPlaceholderText("Ex: https://www.youtube.com/watch?v=...")
        
        self.btn_analisar = QPushButton("🔍 1. Analisar Link")
        self.btn_analisar.clicked.connect(self.analisar_link)

        # Escolha Vídeo/Áudio
        frame_escolha = QFrame()
        layout_radio = QHBoxLayout(frame_escolha)
        self.radio_video = QRadioButton("Vídeo (MP4)")
        self.radio_audio = QRadioButton("Áudio (MP3)")
        self.radio_video.setChecked(True)
        self.radio_video.toggled.connect(self.limpar_combo)
        layout_radio.addWidget(self.radio_video)
        layout_radio.addWidget(self.radio_audio)
        
        self.combo_qualidade = QComboBox()
        self.combo_qualidade.addItem("Analise o link primeiro...")
        self.combo_qualidade.setEnabled(False)

        # Barra de Progresso (NOVO)
        self.progress_bar = QProgressBar()
        self.progress_bar.setValue(0)
        self.progress_bar.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.progress_bar.setTextVisible(True)

        self.youtube_btn = QPushButton("⬇️ 2. Baixar Selecionado")
        self.youtube_btn.setEnabled(False)
        self.youtube_btn.clicked.connect(self.iniciar_download)

        layout_yt.addWidget(lbl_url)
        layout_yt.addWidget(self.youtube_input)
        layout_yt.addWidget(self.btn_analisar)
        layout_yt.addSpacing(5)
        layout_yt.addWidget(frame_escolha)
        layout_yt.addWidget(self.combo_qualidade)
        layout_yt.addSpacing(10)
        layout_yt.addWidget(QLabel("Progresso:"))
        layout_yt.addWidget(self.progress_bar) # Adiciona barra
        layout_yt.addWidget(self.youtube_btn)
        
        group_yt.setLayout(layout_yt)
        layout.addWidget(group_yt)

        # Status
        self.status = QLabel("Aguardando ação...")
        self.status.setWordWrap(True)
        self.status.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status.setStyleSheet("border: 1px dashed #000; padding: 5px; background: #fff;") 
        layout.addWidget(self.status)
        
        layout.addStretch()
        self.setLayout(layout)

    def limpar_combo(self):
        self.combo_qualidade.clear()
        self.combo_qualidade.addItem("Analise o link novamente...")
        self.combo_qualidade.setEnabled(False)
        self.youtube_btn.setEnabled(False)

    def analisar_link(self):
        url = self.youtube_input.text().strip()
        if not url: return

        self.status.setText("Analisando vídeo... (Aguarde)")
        self.btn_analisar.setEnabled(False)
        self.combo_qualidade.clear()
        QApplication.processEvents()

        try:
            ydl_opts = {'quiet': True}
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
                self.formatos_encontrados = info.get('formats', [])
                titulo = info.get('title', 'Vídeo')
                
                if self.radio_audio.isChecked():
                    self.status.setText(f"Encontrado: {titulo}. (Áudio)")
                    self.combo_qualidade.addItem(f"Melhor Qualidade (MP3)", "best_audio")
                else:
                    self.status.setText(f"Encontrado: {titulo}. (Vídeo)")
                    seen_res = set()
                    formatos_video = sorted(
                        [f for f in self.formatos_encontrados if f.get('height') and f.get('vcodec') != 'none'],
                        key=lambda x: x.get('height', 0), reverse=True
                    )

                    for f in formatos_video:
                        height = f.get('height')
                        if height not in seen_res:
                            self.combo_qualidade.addItem(f"{height}p ({f['ext']})", f['format_id'])
                            seen_res.add(height)
                
                if self.combo_qualidade.count() > 0:
                    self.combo_qualidade.setEnabled(True)
                    self.youtube_btn.setEnabled(True)

        except Exception as e:
            self.status.setText(f"Erro ao analisar: {str(e)}")
        finally:
            self.btn_analisar.setEnabled(True)

    def iniciar_download(self):
        url = self.youtube_input.text().strip()
        data_escolhida = self.combo_qualidade.currentData()
        is_audio = self.radio_audio.isChecked()
        
        # Reseta a interface
        self.progress_bar.setValue(0)
        self.youtube_btn.setEnabled(False)
        self.btn_analisar.setEnabled(False)
        self.status.setText("Iniciando download...")

        # Não precisamos mais passar ffmpeg_local, o Worker já pega o global
        self.worker = DownloadWorker(url, is_audio, data_escolhida)
        self.worker.progress.connect(self.atualizar_barra)
        self.worker.status_msg.connect(self.atualizar_status)
        self.worker.finished.connect(self.download_concluido)
        self.worker.error.connect(self.download_erro)
        self.worker.start()

    def atualizar_barra(self, val):
        self.progress_bar.setValue(val)

    def atualizar_status(self, msg):
        self.status.setText(msg)

    def download_concluido(self, msg):
        self.status.setText(msg)
        self.youtube_btn.setEnabled(True)
        self.btn_analisar.setEnabled(True)
        self.progress_bar.setValue(100)
        if self.cfg:
             self.cfg["downloads"].append({"tipo": "youtube", "data": QTime.currentTime().toString("HH:mm")})

    def download_erro(self, erro_msg):
        self.status.setText(f"Erro: {erro_msg}")
        self.youtube_btn.setEnabled(True)
        self.btn_analisar.setEnabled(True)
        if "ffmpeg" in erro_msg.lower() or "ffprobe" in erro_msg.lower():
             QMessageBox.critical(self, "Erro FFmpeg", "Certifique-se que ffmpeg.exe E ffprobe.exe estão na pasta.")

class TelaAgendador(QWidget):
    def __init__(self, cfg):
        super().__init__()
        self.cfg = cfg
        self.timer = QTimer()
        self.timer.timeout.connect(self.verificar_eventos)
        self.timer.start(1000)

        layout = QVBoxLayout()

        # --- Área de Configuração ---
        group_config = QGroupBox("Configurar Novo Evento")
        layout_config = QVBoxLayout()

        # Escolha: Arquivo vs Link
        self.radio_group = QButtonGroup()
        self.radio_arquivo = QRadioButton("Arquivo Local")
        self.radio_link = QRadioButton("Link (URL/YouTube)")
        self.radio_arquivo.setChecked(True)
        self.radio_group.addButton(self.radio_arquivo)
        self.radio_group.addButton(self.radio_link)
        
        layout_radios = QHBoxLayout()
        layout_radios.addWidget(self.radio_arquivo)
        layout_radios.addWidget(self.radio_link)
        
        # Conecta mudança de estado
        self.radio_arquivo.toggled.connect(self.alternar_modo)

        # Inputs
        self.arquivo_btn = QPushButton("📂 Selecionar arquivo de Mídia")
        self.arquivo_btn.clicked.connect(self.selecionar_arquivo)
        
        self.input_link = QLineEdit()
        self.input_link.setPlaceholderText("Cole o link aqui (ex: https://youtube.com/...)")
        self.input_link.setVisible(False) 

        self.lbl_conteudo = QLabel("Nenhum conteúdo selecionado.")
        self.lbl_conteudo.setStyleSheet("color: #555; font-style: italic;")

        self.hora_execucao = QTimeEdit()
        self.hora_execucao.setDisplayFormat("HH:mm")
        self.hora_execucao.setTime(QTime.currentTime())

        # Seleção de Monitor (NOVO)
        lbl_monitor = QLabel("Abrir em qual Monitor?")
        self.spin_monitor = QSpinBox()
        self.spin_monitor.setRange(0, 5)
        self.spin_monitor.setPrefix("Monitor ID: ")
        self.spin_monitor.setValue(0) # 0 é a tela principal
        self.spin_monitor.setToolTip("0 = Principal, 1 = Secundária, etc.")

        # Tempo e Conversor
        lbl_tempo = QLabel("Tempo que ficará aberto (em segundos):")
        self.tempo_execucao = QSpinBox()
        self.tempo_execucao.setRange(1, 28800) # Até 8 horas
        self.tempo_execucao.setValue(10)
        self.tempo_execucao.setSuffix(" seg")

        layout_conv = QHBoxLayout()
        lbl_min = QLabel("Ou converta minutos:")
        self.spin_minutos = QSpinBox()
        self.spin_minutos.setRange(0, 480)
        self.spin_minutos.setSuffix(" min")
        self.spin_minutos.valueChanged.connect(self.converter_minutos)
        layout_conv.addWidget(lbl_min)
        layout_conv.addWidget(self.spin_minutos)

        self.add_event_btn = QPushButton("➕ Adicionar Evento")
        self.add_event_btn.setStyleSheet("background-color: #4CAF50; color: white; font-weight: bold;")
        self.add_event_btn.clicked.connect(self.adicionar_evento)

        layout_config.addLayout(layout_radios)
        layout_config.addWidget(self.arquivo_btn)
        layout_config.addWidget(self.input_link)
        layout_config.addWidget(self.lbl_conteudo)
        layout_config.addWidget(QLabel("Horário de início:"))
        layout_config.addWidget(self.hora_execucao)
        layout_config.addWidget(lbl_monitor) # Add Monitor
        layout_config.addWidget(self.spin_monitor) # Add Monitor
        layout_config.addWidget(lbl_tempo)
        layout_config.addWidget(self.tempo_execucao)
        layout_config.addLayout(layout_conv)
        layout_config.addWidget(self.add_event_btn)
        group_config.setLayout(layout_config)

        # --- Lista de Eventos ---
        self.lista_label = QLabel("Eventos Agendados (Marque a caixa para excluir):")
        self.lista_eventos = QListWidget()
        
        self.del_event_btn = QPushButton("❌ Excluir Eventos Marcados")
        self.del_event_btn.setStyleSheet("background-color: #ff4444; color: white; font-weight: bold;")
        self.del_event_btn.clicked.connect(self.excluir_eventos_marcados)

        layout.addWidget(group_config)
        layout.addSpacing(10)
        layout.addWidget(self.lista_label)
        layout.addWidget(self.lista_eventos)
        layout.addWidget(self.del_event_btn)
        
        self.setLayout(layout)

        self.conteudo_selecionado = None 
        self.eventos_disparados = []
        self.recarregar_eventos()

    def alternar_modo(self):
        is_file = self.radio_arquivo.isChecked()
        self.arquivo_btn.setVisible(is_file)
        self.input_link.setVisible(not is_file)
        self.lbl_conteudo.setText("Insira o conteúdo acima.")
        self.conteudo_selecionado = None

    def converter_minutos(self, valor):
        segundos = valor * 60
        if segundos > 0:
            self.tempo_execucao.setValue(segundos)

    def selecionar_arquivo(self):
        arquivo, _ = QFileDialog.getOpenFileName(self, "Selecionar arquivo")
        if arquivo:
            path_arquivo = Path(arquivo)
            self.conteudo_selecionado = str(path_arquivo)
            self.lbl_conteudo.setText(path_arquivo.name)
            self.lbl_conteudo.setToolTip(str(path_arquivo))

    def adicionar_evento(self):
        hora = self.hora_execucao.time().toString("HH:mm")
        tempo = self.tempo_execucao.value()
        monitor = self.spin_monitor.value() # Pega o ID do monitor
        tipo = "arquivo" if self.radio_arquivo.isChecked() else "url"
        
        if tipo == "url":
            link = self.input_link.text().strip()
            if not link:
                QMessageBox.warning(self, "Aviso", "Cole um link válido.")
                return
            self.conteudo_selecionado = link
        elif tipo == "arquivo":
            if not self.conteudo_selecionado:
                QMessageBox.warning(self, "Aviso", "Selecione um arquivo.")
                return

        # Adiciona ao JSON com a info do monitor
        self.cfg["eventos"].append({
            "tipo": tipo,
            "arquivo": self.conteudo_selecionado, 
            "hora": hora,
            "duracao": tempo,
            "monitor": monitor # Salva o monitor escolhido
        })
        
        salvar_config(self.cfg) 
        
        self.recarregar_eventos()
        self.lbl_conteudo.setText("Evento adicionado!")
        self.conteudo_selecionado = None
        self.input_link.clear()
        self.spin_minutos.setValue(0)

    def recarregar_eventos(self):
        self.lista_eventos.clear()
        for ev in self.cfg.get("eventos", []):
            conteudo = ev.get('arquivo', '?')
            nome_exibicao = os.path.basename(conteudo) if ev.get('tipo') == 'arquivo' else conteudo
            tipo_icon = "📄" if ev.get('tipo', 'arquivo') == 'arquivo' else "🌐"
            monitor_id = ev.get('monitor', 0)
            
            texto = f"⏰ {ev['hora']} | 📺 Tela {monitor_id} | ⏳ {ev['duracao']}s | {tipo_icon} {nome_exibicao}"
            
            item = QListWidgetItem(texto)
            item.setFlags(item.flags() | Qt.ItemFlag.ItemIsUserCheckable)
            item.setCheckState(Qt.CheckState.Unchecked)
            self.lista_eventos.addItem(item)

    def excluir_eventos_marcados(self):
        itens_para_remover = []
        for i in range(self.lista_eventos.count()):
            item = self.lista_eventos.item(i)
            if item.checkState() == Qt.CheckState.Checked:
                itens_para_remover.append(i)
        
        if not itens_para_remover:
            QMessageBox.warning(self, "Aviso", "Marque os itens para excluir.")
            return

        for i in sorted(itens_para_remover, reverse=True):
            del self.cfg["eventos"][i]
            self.lista_eventos.takeItem(i)
            
        salvar_config(self.cfg) 
        QMessageBox.information(self, "Sucesso", "Eventos removidos.")

    def verificar_eventos(self):
        agora = QTime.currentTime().toString("HH:mm")
        
        if self.eventos_disparados and self.eventos_disparados[0]['hora'] != agora:
            self.eventos_disparados.clear()

        for ev in self.cfg.get("eventos", []):
            chave_evento = f"{ev['hora']}_{ev['arquivo']}"
            ja_disparado = any(f"{e['hora']}_{e['arquivo']}" == chave_evento for e in self.eventos_disparados)

            if ev["hora"] == agora and not ja_disparado:
                print(f"Disparando: {ev['arquivo']}")
                
                try:
                    tipo = ev.get("tipo", "arquivo")
                    conteudo = ev["arquivo"]
                    monitor_idx = ev.get("monitor", 0)

                    # --- Lógica de Posicionamento (Geometria da Tela) ---
                    app = QApplication.instance()
                    screens = app.screens()
                    pos_x = 0
                    pos_y = 0
                    
                    if monitor_idx < len(screens):
                        rect = screens[monitor_idx].geometry()
                        pos_x = rect.x()
                        pos_y = rect.y()
                    else:
                        print(f"Aviso: Monitor {monitor_idx} não existe. Usando principal.")

                    if tipo == "url":
                        # Abre link no navegador com coordenadas
                        chrome_path = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
                        edge_path = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
                        browser = chrome_path if os.path.exists(chrome_path) else edge_path

                        if os.path.exists(browser):
                            # Modo Kiosk ou Fullscreen forçado na coordenada X,Y
                            cmd = [
                                browser,
                                "--new-window",
                                f"--window-position={pos_x},{pos_y}",
                                "--start-fullscreen",
                                conteudo
                            ]
                            subprocess.Popen(cmd)
                        else:
                            webbrowser.open(conteudo)

                    else:
                        # Abre arquivo local
                        # Tenta usar VLC para garantir que abra na tela certa
                        vlc_path = r"C:\Program Files\VideoLAN\VLC\vlc.exe"
                        
                        if os.path.exists(vlc_path):
                            cmd = [
                                vlc_path,
                                conteudo,
                                "--no-embedded-video",
                                "--fullscreen",
                                f"--video-x={pos_x}",
                                f"--video-y={pos_y}"
                            ]
                            subprocess.Popen(cmd)
                        else:
                            # Se não tiver VLC, usa o padrão (não garante tela certa)
                            if sys.platform == "win32":
                                os.startfile(conteudo)
                            else:
                                subprocess.Popen(["xdg-open", conteudo])
                    
                    self.eventos_disparados.append(ev)
                    QTimer.singleShot(ev["duracao"] * 1000, lambda c=conteudo: self.fechar_midia(c))

                except Exception as e:
                    print(f"Erro ao disparar evento: {e}")

    def fechar_midia(self, conteudo):
        print(f"Tentando fechar: {conteudo}")
        
        # Se for link, tenta fechar navegadores
        if "http" in str(conteudo):
            if sys.platform == "win32":
                subprocess.run('taskkill /F /IM "chrome.exe"', shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                subprocess.run('taskkill /F /IM "msedge.exe"', shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            return

        path = Path(conteudo)
        nome_arquivo = path.name
        nome_sem_extensao = path.stem

        if sys.platform == "win32":
            try:
                lista_players = ["Microsoft.Media.Player.exe", "Video.UI.exe", "wmplayer.exe", "vlc.exe", "mpc-hc64.exe", "PotPlayerMini64.exe", "mpv.exe"]
                for player in lista_players:
                    subprocess.run(f'taskkill /F /IM "{player}"', shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

                cmd_title = f'taskkill /FI "WINDOWTITLE eq *{nome_sem_extensao}*" /F'
                subprocess.run(cmd_title, shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            except Exception:
                pass

class JanelaPrincipal(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("JA TECH – Ferramenta Multimídia")
        self.setWindowIcon(QIcon("icons/ja_logo.png")) 
        self.setStyleSheet(STYLE)

        self.cfg = carregar_config()

        self.stacked = QStackedWidget()
        self.stacked.addWidget(TelaDownload(self.cfg))
        self.stacked.addWidget(TelaAgendador(self.cfg))
        # TelaMultiTela REMOVIDA DAQUI

        layout_principal = QHBoxLayout()
        menu = QVBoxLayout()

        # Botões do Menu
        btn1 = QPushButton()
        btn1.setObjectName("MenuButton")
        #btn1.setText("Download") 
        if os.path.exists("icons/download.png"): 
            btn1.setIcon(QIcon("icons/download.png"))
            btn1.setIconSize(QSize(48, 48))
        btn1.clicked.connect(lambda: self.stacked.setCurrentIndex(0))

        btn2 = QPushButton()
        btn2.setObjectName("MenuButton")
        #btn2.setText("Agendador")
        if os.path.exists("icons/auto.png"): 
            btn2.setIcon(QIcon("icons/auto.png"))
            btn2.setIconSize(QSize(48, 48))
        btn2.clicked.connect(lambda: self.stacked.setCurrentIndex(1))

        # Botão Multi-Tela REMOVIDO DAQUI

        menu.addWidget(btn1)
        menu.addWidget(btn2)
        menu.addStretch()

        layout_principal.addLayout(menu)
        layout_principal.addWidget(self.stacked)
        self.setLayout(layout_principal)

class App(QApplication):
    def __init__(self, args):
        super().__init__(args)
        self.win = JanelaPrincipal()
        self.win.resize(900, 600)
        self.win.show()

if __name__ == "__main__":
    print("JA TECH – Ferramenta Multimídia")
    # versão do app
    print(f"Versão: {APP_VERSION}")
    app = App(sys.argv)
    sys.exit(app.exec())
