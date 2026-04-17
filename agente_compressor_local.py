import streamlit as st
import subprocess
import os
import tempfile
from pathlib import Path
from datetime import datetime
from PIL import Image
import pandas as pd
import time

# ==================== CONFIGURAÇÃO DA PÁGINA ====================
st.set_page_config(
    page_title="🖥️ Agente Compressor LOCAL",
    page_icon="🖥️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ==================== CSS CUSTOMIZADO ====================
st.markdown("""
    <style>
    .big-font {
        font-size: 36px !important;
        font-weight: bold;
        background: linear-gradient(90deg, #FF1493, #9D50BB);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 6px;
    }
    .subtitle {
        font-size: 16px;
        color: #aaa;
        margin-bottom: 25px;
    }
    .metric-card {
        background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
        border: 1px solid #FF1493;
        padding: 20px;
        border-radius: 14px;
        color: white;
        text-align: center;
        margin: 8px 0;
    }
    .metric-value {
        font-size: 32px;
        font-weight: bold;
        color: #FF1493;
        margin: 8px 0;
    }
    .metric-label {
        font-size: 13px;
        color: #ccc;
    }
    .stProgress > div > div > div > div {
        background: linear-gradient(90deg, #FF1493, #9D50BB);
    }
    .path-box {
        background: #1a1a2e;
        border: 1px solid #9D50BB;
        border-radius: 8px;
        padding: 12px;
        color: white;
        font-family: monospace;
    }
    </style>
""", unsafe_allow_html=True)

# ==================== VERIFICAR FFMPEG ====================
def check_ffmpeg():
    try:
        result = subprocess.run(['ffmpeg', '-version'], capture_output=True, text=True, check=True)
        return True, result.stdout.split('\n')[0]
    except FileNotFoundError:
        return False, None
    except Exception:
        return False, None

ffmpeg_ok, ffmpeg_version = check_ffmpeg()

# ==================== FUNÇÕES ====================

def formata_tamanho(size_bytes):
    mb = size_bytes / (1024 * 1024)
    if mb >= 1024:
        return f"{mb/1024:.2f} GB"
    return f"{mb:.2f} MB"

def define_perfil_video(size_bytes):
    mb = size_bytes / (1024 * 1024)
    if mb > 1000:
        return {"resolucao": "1280:720", "crf": "28", "target_mb": 150, "label": ">1GB → máx 150MB (720p)"}
    elif mb > 500:
        return {"resolucao": "1280:720", "crf": "26", "target_mb": 100, "label": "500MB-1GB → máx 100MB (720p)"}
    elif mb > 200:
        return {"resolucao": "1280:720", "crf": "24", "target_mb": 80,  "label": "200-500MB → máx 80MB (720p)"}
    else:
        return {"resolucao": "640:480",  "crf": "23", "target_mb": 50,  "label": "<200MB → máx 50MB (480p)"}

def comprimir_video(input_path, output_path, perfil, progress_placeholder):
    cmd = [
        'ffmpeg', '-i', input_path,
        '-vf', f"scale={perfil['resolucao']}:force_original_aspect_ratio=decrease",
        '-c:v', 'libx264',
        '-crf', perfil['crf'],
        '-preset', 'medium',
        '-c:a', 'aac',
        '-b:a', '128k',
        '-movflags', '+faststart',
        '-map_metadata', '-1',
        '-y', output_path
    ]

    start = time.time()
    progress_placeholder.info("🔄 Comprimindo vídeo... aguarde")

    process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    stdout, stderr = process.communicate()
    elapsed = time.time() - start

    if process.returncode == 0:
        out_size = os.path.getsize(output_path)
        # Segunda passagem se ainda maior que o target
        out_mb = out_size / (1024 * 1024)
        if out_mb > perfil['target_mb']:
            try:
                dur_cmd = ['ffprobe', '-v', 'error', '-show_entries', 'format=duration',
                           '-of', 'default=noprint_wrappers=1:nokey=1', input_path]
                dur = float(subprocess.run(dur_cmd, capture_output=True, text=True).stdout.strip())
                target_kbps = max(300, int((perfil['target_mb'] * 8 * 1024) / dur) - 128)
                cmd2 = [
                    'ffmpeg', '-i', input_path,
                    '-vf', f"scale={perfil['resolucao']}:force_original_aspect_ratio=decrease",
                    '-c:v', 'libx264', '-b:v', f'{target_kbps}k',
                    '-preset', 'medium',
                    '-c:a', 'aac', '-b:a', '128k',
                    '-movflags', '+faststart', '-map_metadata', '-1',
                    '-y', output_path
                ]
                process2 = subprocess.Popen(cmd2, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                process2.communicate()
                out_size = os.path.getsize(output_path)
            except:
                pass
        return True, out_size, elapsed
    else:
        return False, 0, elapsed

def comprimir_imagem(input_path, output_path):
    try:
        img = Image.open(input_path)
        if img.mode in ('RGBA', 'P', 'LA'):
            img = img.convert('RGB')
        img.save(output_path, 'WEBP', quality=85, method=6)
        return True, os.path.getsize(output_path)
    except Exception as e:
        return False, 0

def listar_videos_pasta(pasta):
    exts = ['.mp4', '.mov', '.avi', '.mkv']
    arquivos = []
    try:
        for f in Path(pasta).iterdir():
            if f.is_file() and f.suffix.lower() in exts:
                arquivos.append(str(f))
    except Exception as e:
        st.error(f"Erro ao ler pasta: {e}")
    return sorted(arquivos)

# ==================== SESSION STATE ====================
if 'resultados' not in st.session_state:
    st.session_state.resultados = []
if 'total_antes' not in st.session_state:
    st.session_state.total_antes = 0
if 'total_depois' not in st.session_state:
    st.session_state.total_depois = 0

# ==================== HEADER ====================
st.markdown('<p class="big-font">🖥️ AGENTE COMPRESSOR LOCAL — SEM LIMITE DE TAMANHO</p>', unsafe_allow_html=True)
st.markdown('<p class="subtitle">Comprime diretamente do seu PC • FFmpeg local • Sem upload • Sem limite</p>', unsafe_allow_html=True)

# ==================== AVISO FFMPEG ====================
if not ffmpeg_ok:
    st.error("❌ **FFmpeg não encontrado no sistema!**")
    st.markdown("""
    ### Como instalar o FFmpeg no Windows:
    1. Acesse: https://www.gyan.dev/ffmpeg/builds/
    2. Baixe **ffmpeg-release-essentials.zip**
    3. Extraia para `C:\\ffmpeg`
    4. Adicione `C:\\ffmpeg\\bin` nas **Variáveis de Ambiente** do Windows (PATH)
    5. Reinicie o terminal e rode novamente: `streamlit run agente_compressor_local.py`
    """)
    st.stop()

st.sidebar.success(f"✅ FFmpeg instalado\n\n`{ffmpeg_version[:60]}`")

# ==================== SIDEBAR ====================
with st.sidebar:
    st.header("⚙️ Configurações")

    tipo = st.radio("Tipo de arquivo:", ["🎬 Vídeos", "🖼️ Imagens"])

    st.divider()
    st.markdown("#### 🎬 Perfis de Vídeo (automático)")
    st.markdown("""
    - **>1GB** → máx 150MB (720p, crf 28)
    - **500MB-1GB** → máx 100MB (720p, crf 26)
    - **200-500MB** → máx 80MB (720p, crf 24)
    - **<200MB** → máx 50MB (480p, crf 23)
    """)
    st.divider()
    st.markdown("#### 🖼️ Imagens")
    st.markdown("- Formato: **WEBP** | Qualidade: **85%**")
    st.markdown("- Salvo na mesma pasta com `_comprimido`")

    st.divider()
    if st.button("🗑️ Limpar resultados", use_container_width=True):
        st.session_state.resultados = []
        st.session_state.total_antes = 0
        st.session_state.total_depois = 0
        st.rerun()

# ==================== MÉTRICAS ====================
economia_total = st.session_state.total_antes - st.session_state.total_depois
perc = (economia_total / st.session_state.total_antes * 100) if st.session_state.total_antes > 0 else 0

col1, col2, col3, col4 = st.columns(4)
with col1:
    st.markdown(f"""<div class="metric-card">
        <div class="metric-label">ARQUIVOS COMPRIMIDOS</div>
        <div class="metric-value">{len(st.session_state.resultados)}</div>
    </div>""", unsafe_allow_html=True)
with col2:
    st.markdown(f"""<div class="metric-card">
        <div class="metric-label">TAMANHO ORIGINAL</div>
        <div class="metric-value">{formata_tamanho(st.session_state.total_antes)}</div>
    </div>""", unsafe_allow_html=True)
with col3:
    st.markdown(f"""<div class="metric-card">
        <div class="metric-label">APÓS COMPRESSÃO</div>
        <div class="metric-value">{formata_tamanho(st.session_state.total_depois)}</div>
    </div>""", unsafe_allow_html=True)
with col4:
    st.markdown(f"""<div class="metric-card">
        <div class="metric-label">ESPAÇO ECONOMIZADO</div>
        <div class="metric-value">{perc:.1f}%</div>
    </div>""", unsafe_allow_html=True)

st.markdown("---")

# ==================== ENTRADA DE ARQUIVOS ====================
st.header("📂 Selecionar Arquivos")

tab1, tab2 = st.tabs(["📝 Colar caminhos", "📁 Processar pasta inteira"])

caminhos_para_processar = []

with tab1:
    st.markdown("Cole um ou mais caminhos completos, **um por linha**:")
    caminhos_texto = st.text_area(
        "Caminhos dos arquivos:",
        placeholder="C:\\Users\\Core i5\\Videos\\meu_video.mov\nC:\\Users\\Core i5\\Videos\\outro.mp4\nC:\\Users\\Core i5\\Fotos\\foto.jpg",
        height=150,
        label_visibility="collapsed"
    )
    if caminhos_texto.strip():
        linhas = [l.strip().strip('"').strip("'") for l in caminhos_texto.strip().splitlines() if l.strip()]
        for caminho in linhas:
            if os.path.isfile(caminho):
                caminhos_para_processar.append(caminho)
            else:
                st.warning(f"⚠️ Arquivo não encontrado: `{caminho}`")

with tab2:
    caminho_pasta = st.text_input(
        "Caminho da pasta:",
        placeholder="C:\\Users\\Core i5\\Videos\\minha_pasta"
    )
    if caminho_pasta.strip():
        caminho_pasta = caminho_pasta.strip().strip('"').strip("'")
        if os.path.isdir(caminho_pasta):
            videos_pasta = listar_videos_pasta(caminho_pasta)
            if videos_pasta:
                st.success(f"✅ {len(videos_pasta)} vídeo(s) encontrado(s) na pasta")
                for v in videos_pasta:
                    st.markdown(f"- `{v}`")
                caminhos_para_processar = videos_pasta
            else:
                st.warning("Nenhum vídeo encontrado na pasta (.mp4, .mov, .avi, .mkv)")
        else:
            st.error("Pasta não encontrada!")

# ==================== PROCESSAMENTO ====================
if caminhos_para_processar:
    st.markdown("---")
    st.subheader(f"📋 {len(caminhos_para_processar)} arquivo(s) prontos para comprimir")

    # Preview
    preview = []
    for c in caminhos_para_processar:
        size = os.path.getsize(c)
        ext = Path(c).suffix.lower()
        tipo_arq = "🎬 Vídeo" if ext in ['.mp4', '.mov', '.avi', '.mkv'] else "🖼️ Imagem"
        preview.append({'Arquivo': Path(c).name, 'Caminho': c, 'Tipo': tipo_arq, 'Tamanho': formata_tamanho(size)})
    st.dataframe(pd.DataFrame(preview)[['Arquivo', 'Tipo', 'Tamanho']], use_container_width=True)

    if st.button("🚀 COMPRIMIR TODOS AGORA", type="primary", use_container_width=True):
        progresso_geral = st.progress(0)
        status_geral = st.empty()

        for idx, caminho in enumerate(caminhos_para_processar):
            nome = Path(caminho).name
            status_geral.markdown(f"**Processando:** `{nome}` ({idx+1}/{len(caminhos_para_processar)})")
            ext = Path(caminho).suffix.lower()
            size_antes = os.path.getsize(caminho)
            pasta_saida = str(Path(caminho).parent)
            stem = Path(caminho).stem

            progress_ph = st.empty()

            with st.expander(f"📄 {nome}", expanded=True):
                col_a, col_b, col_c = st.columns(3)
                with col_a:
                    st.metric("Tamanho original", formata_tamanho(size_antes))

                sucesso = False
                size_depois = 0

                if ext in ['.mp4', '.mov', '.avi', '.mkv']:
                    perfil = define_perfil_video(size_antes)
                    st.info(f"🎯 Perfil: {perfil['label']}")
                    output_path = os.path.join(pasta_saida, f"{stem}_comprimido.mp4")
                    sucesso, size_depois, elapsed = comprimir_video(caminho, output_path, perfil, progress_ph)

                elif ext in ['.jpg', '.jpeg', '.png', '.webp']:
                    output_path = os.path.join(pasta_saida, f"{stem}_comprimido.webp")
                    sucesso, size_depois = comprimir_imagem(caminho, output_path)
                    elapsed = 0

                if sucesso and size_depois > 0:
                    reducao = ((size_antes - size_depois) / size_antes) * 100
                    with col_b:
                        st.metric("Após compressão", formata_tamanho(size_depois), f"-{(size_antes-size_depois)/(1024*1024):.1f} MB")
                    with col_c:
                        st.metric("Economia", f"{reducao:.1f}%")

                    progress_ph.success(f"✅ Salvo em: `{output_path}`")

                    st.session_state.resultados.append({
                        'nome': nome,
                        'saida': output_path,
                        'antes': size_antes,
                        'depois': size_depois,
                        'reducao': reducao
                    })
                    st.session_state.total_antes += size_antes
                    st.session_state.total_depois += size_depois
                else:
                    progress_ph.error(f"❌ Falha ao comprimir `{nome}`")

            progresso_geral.progress((idx + 1) / len(caminhos_para_processar))

        status_geral.success("✅ **Todos os arquivos processados!**")
        st.balloons()
        st.rerun()

# ==================== RESULTADOS ====================
if st.session_state.resultados:
    st.markdown("---")
    st.header("📊 Arquivos Comprimidos")
    df = pd.DataFrame([{
        'Arquivo': r['nome'],
        'Antes': formata_tamanho(r['antes']),
        'Depois': formata_tamanho(r['depois']),
        'Economia': f"{r['reducao']:.1f}%",
        'Salvo em': r['saida']
    } for r in st.session_state.resultados])
    st.dataframe(df, use_container_width=True)
    st.info("💾 Os arquivos foram salvos diretamente na mesma pasta dos originais com o sufixo `_comprimido`.")

# ==================== FOOTER ====================
st.divider()
st.markdown("""
**💡 Dicas:**
- Cole o caminho completo do arquivo (ex: `C:\\Users\\Videos\\video.mp4`)
- Use aspas se o caminho tiver espaços — ou cole sem elas, funciona dos dois jeitos
- Os arquivos comprimidos são salvos na **mesma pasta** do original
- Para vídeos muito grandes (>2GB), o processo pode levar alguns minutos
""")
