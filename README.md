# Auto-JA – Ferramenta de Automação Multimídia

Uma aplicação Desktop desenvolvida em Python (PyQt6) para gerenciar downloads do YouTube, converter mídia e agendar reprodução automática de vídeos ou links em monitores específicos (Suporte a Multi-telas).

## 🚀 Funcionalidades

* **Downloader YouTube:** Baixa Vídeos (MP4) ou converte para Áudio (MP3) com alta qualidade usando `yt-dlp`.
* **Agendador de Tarefas:** Programa horários para abrir vídeos locais ou links (YouTube/Web) automaticamente.
* **Suporte Multi-Monitor:** Escolha em qual tela (Monitor 1, Monitor 2, etc.) o conteúdo deve abrir em tela cheia.
* **Conversor Automático:** Barra de progresso real e conversão automática de formatos.

---

## 📂 Estrutura do Projeto

Para que o projeto funcione, a estrutura de pastas deve ser respeitada:

```text
Auto-JA/
├── builde/                 <-- PASTA CRÍTICA (Veja instruções abaixo)
│   ├── ffmpeg.exe
│   └── ffprobe.exe
├── downloads/             <-- Onde os arquivos são salvos
├── icons/                 <-- Seus ícones (.png)
├── venv/                  <-- Ambiente virtual Python
├── configuracoes.json     <-- Banco de dados local
├── JA_TECH.py             <-- Código Principal
├── style.py               <-- Estilização CSS
├── requirements.txt       <-- Dependências
└── README.md

## Estrutura para clonar o repositório

# Clone este repositório
git clone [https://github.com/SEU-USUARIO/Auto-JA.git](https://github.com/SEU-USUARIO/Auto-JA.git)

# Entre na pasta
cd Auto-JA

# Crie um ambiente virtual
python -m venv venv

# Ative o ambiente virtual
# No Windows:
.\venv\Scripts\activate
# No Linux/Mac:
source venv/bin/activate

# Instale as dependências
pip install -r requirements.txt
