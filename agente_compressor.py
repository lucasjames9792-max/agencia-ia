import streamlit as st
import subprocess
import os
import tempfile
import zipfile
import io
import time
from pathlib import Path
from PIL import Image
import pandas as pd
from datetime import datetime

# ==================== CONFIGURAÇÃO DA PÁGINA ====================
st.set_page_config(
    page_title="🗜️ Agente Compressor de Mídia",
    page_icon="🗜️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ==================== CSS CUSTOMIZADO ====================
st.markdown("""
    <style>
    body { background-color: #0e0e1a; }
    .big-font {
        font-size: 38px !important;
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
    .file-card {
        background: #1a1a2e;
        border: 1px solid #333;
        border-radius: 10px;
        padding: 16px;
        margin: 10px 0;
        color: white;
    }
    .success-tag {
        background: #1a3a1a;
        border: 1px solid #28a745;
        border-radius: 6px;
        padding: 4px 10px;
        color: #28a745;
        font-size: 13px;
        font-weight: bold;
    }
    .stProgress > div > div > div > div {
        background: linear-gradient(90deg, #FF1493, #9D50BB);
    }
    </style>
""", unsafe_allow_html=True)

# ==================== FUNÇÕES AUXILIARES ====================

def formata_mb(size_bytes):
    mb = size_bytes / (1024 * 1024)
    return f"{mb:.2f} MB"

def get_video_resolution(path):
    try:
        cmd = [
            'ffprobe', '-v', 'error',
            '-select_streams', 'v:0',
            '-show_entries', 'stream=width,height',
            '-of', 'csv=s=x:p=0', path
        ]
        result = subprocess.run(cmd, capture_output=True, text=True)
        parts = result.stdout.strip().split('x')
        if len(parts) == 2:
            return int(parts[0]), int(parts[1])
    except:
        pass
    return None, None

def define_target_size_mb(size_bytes):
    mb = size_bytes / (1024 * 1024)
    if mb > 500:
        return 150
    elif mb > 200:
        return 80
    else:
        return 50

def comprimir_video(input_path, output_path, original_size_bytes):
    width, height = get_video_resolution(input_path)

    vf_filter = None
    if height and height > 1080:
        vf_filter = "scale=-2:1080"

    target_mb = define_target_size_mb(original_size_bytes)

    cmd = ['ffmpeg', '-y', '-i', input_path]

    if vf_filter:
        cmd += ['-vf', vf_filter]

    cmd += [
        '-c:v', 'libx264',
        '-preset', 'medium',
        '-crf', '28',
        '-c:a', 'aac',
        '-b:a', '128k',
        '-movflags', '+faststart',
        '-map_metadata', '-1',
        output_path
    ]

    process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    stdout, stderr = process.communicate()

    if process.returncode == 0:
        out_size = os.path.getsize(output_path)
        # Se ainda ficou maior que o target, recomprime com bitrate controlado
        out_mb = out_size / (1024 * 1024)
        if out_mb > target_mb:
            duration_cmd = [
                'ffprobe', '-v', 'error',
                '-show_entries', 'format=duration',
                '-of', 'default=noprint_wrappers=1:nokey=1',
                input_path
            ]
            dur_result = subprocess.run(duration_cmd, capture_output=True, text=True)
            try:
                duration = float(dur_result.stdout.strip())
                target_kbps = int((target_mb * 8 * 1024) / duration)
                video_kbps = max(300, target_kbps - 128)

                cmd2 = ['ffmpeg', '-y', '-i', input_path]
                if vf_filter:
                    cmd2 += ['-vf', vf_filter]
                cmd2 += [
                    '-c:v', 'libx264',
                    '-preset', 'medium',
                    '-b:v', f'{video_kbps}k',
                    '-c:a', 'aac',
                    '-b:a', '128k',
                    '-movflags', '+faststart',
                    '-map_metadata', '-1',
                    output_path
                ]
                process2 = subprocess.Popen(cmd2, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                process2.communicate()
            except:
                pass

        return True, os.path.getsize(output_path)
    else:
        return False, 0

def comprimir_imagem(input_path, output_path, original_size_bytes):
    try:
        img = Image.open(input_path)

        # Converter RGBA para RGB se necessário
        if img.mode in ('RGBA', 'P'):
            img = img.convert('RGB')

        ext = Path(input_path).suffix.lower()
        size_mb = original_size_bytes / (1024 * 1024)

        # PNG > 2MB → converte para JPG
        if ext == '.png' and size_mb > 2:
            output_path = str(Path(output_path).with_suffix('.jpg'))
            img.save(output_path, 'JPEG', quality=75, optimize=True)
        elif ext in ['.jpg', '.jpeg']:
            img.save(output_path, 'JPEG', quality=75, optimize=True)
        elif ext == '.webp':
            img.save(output_path, 'WEBP', quality=75)
        else:
            img.save(output_path, quality=75, optimize=True)

        return True, os.path.getsize(output_path), output_path
    except Exception as e:
        return False, 0, output_path

def criar_zip(arquivos):
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, 'w', zipfile.ZIP_DEFLATED) as zf:
        for path, nome in arquivos:
            if os.path.exists(path):
                zf.write(path, nome)
    return buf.getvalue()

# ==================== VERIFICAR FFMPEG ====================
def check_ffmpeg():
    try:
        subprocess.run(['ffmpeg', '-version'], capture_output=True, check=True)
        return True
    except:
        return False

ffmpeg_ok = check_ffmpeg()

# ==================== SESSION STATE ====================
if 'resultados' not in st.session_state:
    st.session_state.resultados = []
if 'total_original' not in st.session_state:
    st.session_state.total_original = 0
if 'total_comprimido' not in st.session_state:
    st.session_state.total_comprimido = 0

# ==================== HEADER ====================
st.markdown('<p class="big-font">🗜️ AGENTE COMPRESSOR DE MÍDIA</p>', unsafe_allow_html=True)
st.markdown('<p class="subtitle">Comprime vídeos e imagens sem perda visual perceptível</p>', unsafe_allow_html=True)

# ==================== SIDEBAR ====================
with st.sidebar:
    st.header("⚙️ Configurações")

    st.markdown("#### 🎬 Vídeos")
    st.info("**Perfil automático por tamanho:**\n\n"
            "- Acima de 500MB → máx **150MB**\n"
            "- 200MB a 500MB → máx **80MB**\n"
            "- Abaixo de 200MB → máx **50MB**")
    st.markdown("- Codec: `libx264` | CRF: `28`")
    st.markdown("- Áudio: `aac 128k`")
    st.markdown("- 4K → reduz para **1080p**")

    st.divider()

    st.markdown("#### 🖼️ Imagens")
    st.markdown("- Qualidade: **75%**")
    st.markdown("- PNG > 2MB → converte para **JPG**")
    st.markdown("- Proporção original mantida")

    st.divider()

    st.markdown(f"**FFmpeg:** {'✅ Instalado' if ffmpeg_ok else '❌ Não encontrado'}")

    st.divider()
    if st.button("🗑️ Limpar resultados", use_container_width=True):
        st.session_state.resultados = []
        st.session_state.total_original = 0
        st.session_state.total_comprimido = 0
        st.rerun()

# ==================== MÉTRICAS ====================
col1, col2, col3, col4 = st.columns(4)

total_economizado = st.session_state.total_original - st.session_state.total_comprimido
perc = (total_economizado / st.session_state.total_original * 100) if st.session_state.total_original > 0 else 0

with col1:
    st.markdown(f"""<div class="metric-card">
        <div class="metric-label">ARQUIVOS COMPRIMIDOS</div>
        <div class="metric-value">{len(st.session_state.resultados)}</div>
    </div>""", unsafe_allow_html=True)
with col2:
    st.markdown(f"""<div class="metric-card">
        <div class="metric-label">TAMANHO ORIGINAL</div>
        <div class="metric-value">{formata_mb(st.session_state.total_original)}</div>
    </div>""", unsafe_allow_html=True)
with col3:
    st.markdown(f"""<div class="metric-card">
        <div class="metric-label">APÓS COMPRESSÃO</div>
        <div class="metric-value">{formata_mb(st.session_state.total_comprimido)}</div>
    </div>""", unsafe_allow_html=True)
with col4:
    st.markdown(f"""<div class="metric-card">
        <div class="metric-label">ESPAÇO ECONOMIZADO</div>
        <div class="metric-value">{perc:.1f}%</div>
    </div>""", unsafe_allow_html=True)

st.markdown("---")

# ==================== UPLOAD ====================
st.header("📁 Enviar Arquivos")

arquivos = st.file_uploader(
    "Arraste vídeos e imagens aqui ou clique para selecionar",
    type=['mp4', 'mov', 'avi', 'mkv', 'jpg', 'jpeg', 'png', 'webp'],
    accept_multiple_files=True
)

if arquivos:
    st.success(f"✅ **{len(arquivos)} arquivo(s) selecionado(s)**")

    # Preview tabela
    preview = []
    for f in arquivos:
        size_mb = len(f.getvalue()) / (1024 * 1024)
        ext = Path(f.name).suffix.lower()
        tipo = "🎬 Vídeo" if ext in ['.mp4', '.mov', '.avi', '.mkv'] else "🖼️ Imagem"
        if tipo == "🎬 Vídeo":
            target = define_target_size_mb(len(f.getvalue()))
            meta = f"Máx {target}MB"
        else:
            meta = "Qualidade 75%"
        preview.append({
            'Arquivo': f.name,
            'Tipo': tipo,
            'Tamanho': f"{size_mb:.2f} MB",
            'Meta': meta
        })

    st.dataframe(pd.DataFrame(preview), use_container_width=True)

    st.markdown("---")

    if st.button("🚀 COMPRIMIR TODOS", type="primary", use_container_width=True):
        progresso = st.progress(0)
        status = st.empty()
        novos_resultados = []

        for idx, arquivo in enumerate(arquivos):
            status.markdown(f"**Comprimindo:** `{arquivo.name}` ({idx+1}/{len(arquivos)})")
            ext = Path(arquivo.name).suffix.lower()
            dados = arquivo.getvalue()
            original_size = len(dados)

            with tempfile.NamedTemporaryFile(delete=False, suffix=ext) as tmp_in:
                tmp_in.write(dados)
                tmp_in_path = tmp_in.name

            out_name = Path(arquivo.name).stem + "_comprimido" + ext
            tmp_out_path = os.path.join(tempfile.gettempdir(), out_name)

            sucesso = False
            out_size = 0
            final_out_path = tmp_out_path
            final_out_name = out_name

            if ext in ['.mp4', '.mov', '.avi', '.mkv']:
                if ffmpeg_ok:
                    sucesso, out_size = comprimir_video(tmp_in_path, tmp_out_path, original_size)
                else:
                    st.error("FFmpeg não encontrado!")
            elif ext in ['.jpg', '.jpeg', '.png', '.webp']:
                sucesso, out_size, final_out_path = comprimir_imagem(tmp_in_path, tmp_out_path, original_size)
                final_out_name = Path(final_out_path).name

            if sucesso and out_size > 0:
                reducao = ((original_size - out_size) / original_size) * 100
                novos_resultados.append({
                    'nome_original': arquivo.name,
                    'nome_saida': final_out_name,
                    'path': final_out_path,
                    'original_bytes': original_size,
                    'comprimido_bytes': out_size,
                    'reducao': reducao
                })
                st.session_state.total_original += original_size
                st.session_state.total_comprimido += out_size
            else:
                st.warning(f"⚠️ Não foi possível comprimir: `{arquivo.name}`")

            os.unlink(tmp_in_path)
            progresso.progress((idx + 1) / len(arquivos))

        st.session_state.resultados.extend(novos_resultados)
        status.markdown("✅ **Compressão concluída!**")
        st.balloons()
        st.rerun()

# ==================== RESULTADOS E DOWNLOADS ====================
if st.session_state.resultados:
    st.markdown("---")
    st.header("📥 Downloads")

    for r in st.session_state.resultados:
        orig_mb = r['original_bytes'] / (1024 * 1024)
        comp_mb = r['comprimido_bytes'] / (1024 * 1024)
        reducao = r['reducao']

        col_a, col_b, col_c, col_d, col_e = st.columns([3, 1.5, 1.5, 1.5, 2])
        with col_a:
            st.markdown(f"**{r['nome_original']}**")
        with col_b:
            st.metric("Antes", f"{orig_mb:.1f} MB")
        with col_c:
            st.metric("Depois", f"{comp_mb:.1f} MB")
        with col_d:
            st.metric("Redução", f"{reducao:.1f}%")
        with col_e:
            if os.path.exists(r['path']):
                with open(r['path'], 'rb') as f:
                    st.download_button(
                        label=f"⬇️ Baixar",
                        data=f,
                        file_name=r['nome_saida'],
                        mime="video/mp4" if r['nome_saida'].endswith('.mp4') else "image/jpeg",
                        use_container_width=True,
                        key=f"dl_{r['nome_original']}_{idx if 'idx' in dir() else r['nome_original']}"
                    )
        st.divider()

    # Download ZIP
    if len(st.session_state.resultados) > 1:
        st.subheader("📦 Baixar Todos em ZIP")
        arquivos_zip = [(r['path'], r['nome_saida']) for r in st.session_state.resultados if os.path.exists(r['path'])]
        zip_data = criar_zip(arquivos_zip)
        total_comp = sum(r['comprimido_bytes'] for r in st.session_state.resultados) / (1024 * 1024)
        st.info(f"📦 Total comprimido: **{total_comp:.1f} MB**")
        st.download_button(
            label=f"📦 BAIXAR TODOS EM ZIP ({len(arquivos_zip)} arquivos)",
            data=zip_data,
            file_name=f"comprimidos_{datetime.now().strftime('%Y%m%d_%H%M%S')}.zip",
            mime="application/zip",
            type="primary",
            use_container_width=True
        )
