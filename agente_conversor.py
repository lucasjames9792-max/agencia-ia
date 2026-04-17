import streamlit as st
import subprocess
import os
import tempfile
from pathlib import Path
from datetime import datetime
import pandas as pd
import time
from typing import List, Dict, Tuple
import zipfile
import io
import shutil
import gc

# ==================== CONFIGURAÇÃO DA PÁGINA ==================== v2
st.set_page_config(
    page_title="🎬 Agente Conversor Mass Media PRO",
    page_icon="🎬",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ==================== CSS CUSTOMIZADO ====================
st.markdown("""
    <style>
    .big-font {
        font-size:40px !important;
        font-weight: bold;
        background: linear-gradient(90deg, #FF1493, #9D50BB);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 10px;
    }
    .subtitle {
        font-size:18px;
        color: #666;
        margin-bottom: 30px;
    }
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 25px;
        border-radius: 15px;
        color: white;
        box-shadow: 0 8px 16px rgba(0,0,0,0.2);
        margin: 10px 0;
        text-align: center;
    }
    .metric-value {
        font-size: 36px;
        font-weight: bold;
        margin: 10px 0;
    }
    .metric-label {
        font-size: 14px;
        opacity: 0.9;
    }
    .success-box {
        background-color: #d4edda;
        border: 2px solid #c3e6cb;
        border-radius: 10px;
        padding: 20px;
        margin: 15px 0;
    }
    .error-box {
        background-color: #f8d7da;
        border: 2px solid #f5c6cb;
        border-radius: 10px;
        padding: 20px;
        margin: 15px 0;
    }
    .info-box {
        background-color: #d1ecf1;
        border: 2px solid #bee5eb;
        border-radius: 10px;
        padding: 20px;
        margin: 15px 0;
    }
    .profile-card {
        border: 2px solid #e0e0e0;
        border-radius: 10px;
        padding: 15px;
        margin: 10px 0;
        transition: all 0.3s;
        background: white;
    }
    .profile-card:hover {
        border-color: #FF1493;
        box-shadow: 0 4px 8px rgba(255,20,147,0.2);
    }
    .stProgress > div > div > div > div {
        background: linear-gradient(90deg, #FF1493, #9D50BB);
    }
    .video-item {
        border: 1px solid #ddd;
        border-radius: 8px;
        padding: 15px;
        margin: 10px 0;
        background: #f9f9f9;
    }
    </style>
    """, unsafe_allow_html=True)

# ==================== PERFIS DE CONVERSÃO ====================
CONVERSION_PROFILES = {
    "🌐 Redes Sociais (Recomendado)": {
        "description": "HD 1080p • 5000k • H.264 • Instagram/TikTok/Privacy",
        "video_codec": "libx264",
        "video_bitrate": "5000k",
        "audio_codec": "aac",
        "audio_bitrate": "192k",
        "resolution": "1920:1080",
        "fps": "30",
        "preset": "medium",
        "icon": "📱",
        "compression": "60-70%"
    },
    "💎 Premium (Qualidade Máxima)": {
        "description": "Original • 10000k • H.265 • OnlyFans/PPV",
        "video_codec": "libx265",
        "video_bitrate": "10000k",
        "audio_codec": "aac",
        "audio_bitrate": "256k",
        "resolution": None,
        "fps": None,
        "preset": "slow",
        "icon": "👑",
        "compression": "40-50%"
    },
    "💾 Ultra Compacto": {
        "description": "720p • 2500k • H.265 • Economia 85%",
        "video_codec": "libx265",
        "video_bitrate": "2500k",
        "audio_codec": "aac",
        "audio_bitrate": "128k",
        "resolution": "1280:720",
        "fps": "25",
        "preset": "fast",
        "icon": "🗜️",
        "compression": "80-85%"
    },
    "✈️ Telegram Friendly": {
        "description": "720p • 3000k • Máx 50MB",
        "video_codec": "libx264",
        "video_bitrate": "3000k",
        "audio_codec": "aac",
        "audio_bitrate": "128k",
        "resolution": "1280:720",
        "fps": "25",
        "preset": "fast",
        "icon": "📲",
        "compression": "70-75%"
    }
}

# ==================== INICIALIZAR SESSION STATE ====================
if 'conversion_queue' not in st.session_state:
    st.session_state.conversion_queue = []
if 'completed_conversions' not in st.session_state:
    st.session_state.completed_conversions = []
if 'failed_conversions' not in st.session_state:
    st.session_state.failed_conversions = []
if 'processing' not in st.session_state:
    st.session_state.processing = False
if 'total_processed' not in st.session_state:
    st.session_state.total_processed = 0
if 'total_saved_mb' not in st.session_state:
    st.session_state.total_saved_mb = 0

# ==================== FUNÇÕES AUXILIARES ====================

@st.cache_resource
def check_ffmpeg_installation():
    try:
        result = subprocess.run(
            ['ffmpeg', '-version'],
            capture_output=True,
            text=True,
            check=True
        )
        version = result.stdout.split('\n')[0]
        return True, version
    except:
        return False, None

def get_video_info(file_path: str) -> Dict:
    try:
        duration_cmd = [
            'ffprobe', '-v', 'error',
            '-show_entries', 'format=duration',
            '-of', 'default=noprint_wrappers=1:nokey=1',
            file_path
        ]
        duration_result = subprocess.run(duration_cmd, capture_output=True, text=True)
        duration = float(duration_result.stdout.strip()) if duration_result.stdout.strip() else 0

        resolution_cmd = [
            'ffprobe', '-v', 'error',
            '-select_streams', 'v:0',
            '-show_entries', 'stream=width,height',
            '-of', 'csv=s=x:p=0',
            file_path
        ]
        resolution_result = subprocess.run(resolution_cmd, capture_output=True, text=True)
        resolution = resolution_result.stdout.strip() if resolution_result.stdout.strip() else "Unknown"

        size_mb = os.path.getsize(file_path) / (1024 * 1024)

        return {
            'duration': duration,
            'duration_formatted': time.strftime('%H:%M:%S', time.gmtime(duration)),
            'resolution': resolution,
            'size_mb': size_mb,
            'size_formatted': f"{size_mb:.2f} MB"
        }
    except Exception as e:
        return {
            'duration': 0,
            'duration_formatted': "00:00:00",
            'resolution': "Unknown",
            'size_mb': 0,
            'size_formatted': "0 MB",
            'error': str(e)
        }

def convert_video(input_path: str, output_path: str, profile_config: Dict) -> Tuple[bool, str, Dict]:
    try:
        cmd = ['ffmpeg', '-i', input_path]
        cmd.extend(['-c:v', profile_config['video_codec']])
        cmd.extend(['-b:v', profile_config['video_bitrate']])

        if profile_config.get('resolution'):
            cmd.extend(['-vf', f"scale={profile_config['resolution']}:force_original_aspect_ratio=decrease"])

        if profile_config.get('fps'):
            cmd.extend(['-r', profile_config['fps']])

        cmd.extend(['-c:a', profile_config['audio_codec']])
        cmd.extend(['-b:a', profile_config['audio_bitrate']])
        cmd.extend(['-preset', profile_config['preset']])
        cmd.extend(['-movflags', '+faststart'])
        cmd.extend(['-map_metadata', '-1'])
        cmd.extend(['-y', output_path])

        start_time = time.time()
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            universal_newlines=True
        )
        stdout, stderr = process.communicate()
        conversion_time = time.time() - start_time

        if process.returncode == 0:
            output_info = get_video_info(output_path)
            stats = {
                'conversion_time': conversion_time,
                'conversion_time_formatted': time.strftime('%H:%M:%S', time.gmtime(conversion_time)),
                'output_size_mb': output_info['size_mb'],
                'output_duration': output_info['duration']
            }
            return True, "✅ Conversão concluída com sucesso!", stats
        else:
            return False, f"❌ Erro na conversão: {stderr[:200]}", {}

    except Exception as e:
        return False, f"❌ Erro: {str(e)}", {}

def comprimir_antes_converter(input_path: str, temp_dir: str) -> str:
    """Comprime o vídeo se for maior que 200MB antes de converter"""
    tamanho_mb = os.path.getsize(input_path) / (1024 * 1024)

    if tamanho_mb <= 200:
        return input_path  # Não precisa comprimir

    # Definir perfil de compressão baseado no tamanho
    if tamanho_mb > 1000:
        crf = "28"
        resolucao = "1280:720"
    elif tamanho_mb > 500:
        crf = "26"
        resolucao = "1280:720"
    else:
        crf = "24"
        resolucao = "1280:720"

    output_path = os.path.join(temp_dir, "pre_comprimido_" + os.path.basename(input_path) + ".mp4")

    cmd = [
        'ffmpeg', '-i', input_path,
        '-vf', f'scale={resolucao}:force_original_aspect_ratio=decrease',
        '-c:v', 'libx264',
        '-crf', crf,
        '-preset', 'fast',
        '-c:a', 'aac',
        '-b:a', '128k',
        '-y', output_path
    ]

    try:
        subprocess.run(cmd, check=True, capture_output=True)
        return output_path
    except:
        return input_path  # Se falhar, usa o original

def create_zip_from_files(file_paths: List[str]) -> bytes:
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
        for file_path in file_paths:
            if os.path.exists(file_path):
                zip_file.write(file_path, os.path.basename(file_path))
    return zip_buffer.getvalue()

# ==================== VERIFICAÇÃO DE FFMPEG ====================
ffmpeg_installed, ffmpeg_version = check_ffmpeg_installation()

if not ffmpeg_installed:
    st.error("⚠️ **FFmpeg não está instalado!**")
    st.stop()

# ==================== HEADER ====================
st.markdown('<p class="big-font">🎬 AGENTE CONVERSOR MASS MEDIA PRO</p>', unsafe_allow_html=True)
st.markdown('<p class="subtitle">Processamento industrial de vídeos • Compressão automática para arquivos grandes</p>', unsafe_allow_html=True)

# ==================== SIDEBAR ====================
st.sidebar.header("⚙️ Configurações")
st.sidebar.subheader("📋 Perfil de Conversão")

selected_profile = st.sidebar.selectbox(
    "Escolha o perfil:",
    list(CONVERSION_PROFILES.keys()),
    index=0
)

profile_config = CONVERSION_PROFILES[selected_profile]

with st.sidebar.expander("ℹ️ Detalhes do Perfil", expanded=False):
    st.markdown(f"""
    **{profile_config['icon']} {selected_profile}**
    {profile_config['description']}
    - 🎥 Codec: {profile_config['video_codec']}
    - 📊 Bitrate: {profile_config['video_bitrate']}
    - 🔊 Áudio: {profile_config['audio_codec']} {profile_config['audio_bitrate']}
    - 📐 Resolução: {profile_config['resolution'] or 'Original'}
    - 🎬 FPS: {profile_config['fps'] or 'Original'}
    - 💾 Economia: ~{profile_config['compression']}
    """)

st.sidebar.markdown("---")
st.sidebar.subheader("🎯 Opções Avançadas")

rename_pattern = st.sidebar.text_input(
    "Padrão de renomeação:",
    "video_{numero}",
    help="Use {numero} para sequência automática."
)

remove_originals = st.sidebar.checkbox(
    "🗑️ Remover originais após conversão",
    value=False
)

st.sidebar.markdown("---")
st.sidebar.markdown(f"**FFmpeg:** ✅ Instalado")
st.sidebar.markdown(f"**Versão:** {ffmpeg_version[:50]}...")

# ==================== ESTATÍSTICAS ====================
col1, col2, col3 = st.columns(3)

with col1:
    st.markdown(f"""<div class="metric-card">
        <div class="metric-label">VÍDEOS PROCESSADOS</div>
        <div class="metric-value">{st.session_state.total_processed}</div>
    </div>""", unsafe_allow_html=True)

with col2:
    st.markdown(f"""<div class="metric-card">
        <div class="metric-label">ESPAÇO ECONOMIZADO</div>
        <div class="metric-value">{st.session_state.total_saved_mb:.1f} MB</div>
    </div>""", unsafe_allow_html=True)

with col3:
    success_rate = (st.session_state.total_processed / max(1, st.session_state.total_processed + len(st.session_state.failed_conversions))) * 100
    st.markdown(f"""<div class="metric-card">
        <div class="metric-label">TAXA DE SUCESSO</div>
        <div class="metric-value">{success_rate:.1f}%</div>
    </div>""", unsafe_allow_html=True)

st.markdown("---")

# ==================== UPLOAD ====================
st.header("📁 Enviar Vídeos")

st.warning("⚠️ **Limite de upload direto: ~100MB** (limitação do proxy do Railway)\n\n"
           "👇 Para vídeos maiores use a **aba de URL** (Google Drive, Dropbox, link direto)")

tab_upload, tab_url = st.tabs(["📤 Upload direto (até 100MB)", "🔗 URL / Google Drive (sem limite)"])

video_analysis = []

# ---------- ABA 1: Upload direto ----------
with tab_upload:
    uploaded_files = st.file_uploader(
        "Arraste vídeos aqui (máx ~100MB por arquivo neste servidor)",
        type=['mov', 'avi', 'mkv', 'wmv', 'flv', 'webm', 'm4v', 'mpg', 'mpeg', '3gp', 'mp4'],
        accept_multiple_files=True
    )

    if uploaded_files:
        st.success(f"✅ **{len(uploaded_files)} arquivo(s) carregado(s)**")
        for uploaded_file in uploaded_files:
            with tempfile.NamedTemporaryFile(delete=False, suffix=Path(uploaded_file.name).suffix) as tmp_file:
                uploaded_file.seek(0)
                shutil.copyfileobj(uploaded_file, tmp_file, length=1024 * 1024)
                tmp_path = tmp_file.name
            gc.collect()

            info = get_video_info(tmp_path)
            video_analysis.append({
                'Nome': uploaded_file.name,
                'Tamanho': info['size_formatted'],
                'Duração': info['duration_formatted'],
                'Resolução': info['resolution'],
                'temp_path': tmp_path
            })

# ---------- ABA 2: URL ----------
with tab_url:
    st.markdown("""
    **Como usar com Google Drive:**
    1. Faça upload do vídeo no Google Drive
    2. Clique com botão direito → **Compartilhar** → **Qualquer pessoa com o link**
    3. Copie o link e cole abaixo

    **Funciona também com:** Dropbox, WeTransfer, links diretos de vídeo (.mp4, .mov...)
    """)

    urls_texto = st.text_area(
        "Cole as URLs (uma por linha):",
        placeholder="https://drive.google.com/file/d/SEU_ID/view\nhttps://www.dropbox.com/s/xxx/video.mp4",
        height=120
    )

    def baixar_url(url: str, output_path: str) -> bool:
        """Baixa vídeo de URL, com suporte a Google Drive."""
        try:
            import urllib.request
            import urllib.parse

            # Converter Google Drive share link para download direto
            if "drive.google.com" in url:
                if "/file/d/" in url:
                    file_id = url.split("/file/d/")[1].split("/")[0]
                    url = f"https://drive.google.com/uc?export=download&id={file_id}&confirm=t"
                elif "id=" in url:
                    file_id = url.split("id=")[1].split("&")[0]
                    url = f"https://drive.google.com/uc?export=download&id={file_id}&confirm=t"

            # Dropbox: mudar ?dl=0 para ?dl=1
            if "dropbox.com" in url:
                url = url.replace("?dl=0", "?dl=1").replace("?dl=0", "?dl=1")
                if "?dl=" not in url:
                    url += "?dl=1"

            headers = {'User-Agent': 'Mozilla/5.0'}
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req, timeout=300) as response:
                with open(output_path, 'wb') as f:
                    shutil.copyfileobj(response, f, length=1024 * 1024)
            return True
        except Exception as e:
            st.error(f"❌ Erro ao baixar URL: {e}")
            return False

    if urls_texto.strip():
        urls = [u.strip() for u in urls_texto.strip().splitlines() if u.strip()]
        if st.button("⬇️ Baixar vídeos das URLs", use_container_width=True):
            for i, url in enumerate(urls):
                nome = f"video_url_{i+1}.mp4"
                tmp_path = os.path.join(tempfile.gettempdir(), nome)
                with st.spinner(f"Baixando {url[:60]}..."):
                    if baixar_url(url, tmp_path):
                        info = get_video_info(tmp_path)
                        video_analysis.append({
                            'Nome': nome,
                            'Tamanho': info['size_formatted'],
                            'Duração': info['duration_formatted'],
                            'Resolução': info['resolution'],
                            'temp_path': tmp_path
                        })
                        st.success(f"✅ Baixado: {info['size_formatted']}")

# ---------- ANÁLISE PRÉVIA ----------
if video_analysis:
    with st.expander("📊 Análise Prévia dos Vídeos", expanded=True):
        total_size = sum(get_video_info(v['temp_path'])['size_mb'] for v in video_analysis)
        total_duration = sum(get_video_info(v['temp_path'])['duration'] for v in video_analysis)

        df_analysis = pd.DataFrame(video_analysis)
        st.dataframe(df_analysis[['Nome', 'Tamanho', 'Duração', 'Resolução']], use_container_width=True)

        col_a, col_b, col_c, col_d = st.columns(4)
        with col_a:
            st.metric("📦 Tamanho Total", f"{total_size:.1f} MB")
        with col_b:
            st.metric("⏱️ Duração Total", time.strftime('%H:%M:%S', time.gmtime(total_duration)))
        with col_c:
            compression = profile_config['compression'].split('-')[0]
            estimated_saving = total_size * (int(compression) / 100)
            st.metric("💾 Economia Estimada", f"{estimated_saving:.1f} MB")
        with col_d:
            estimated_time = (total_size / 100) * 60
            st.metric("⏳ Tempo Estimado", f"{estimated_time:.0f} min")

    st.markdown("---")
    col_b1, col_b2, col_b3 = st.columns([2, 1, 1])

    with col_b1:
        if st.button("🚀 CONVERTER TODOS OS VÍDEOS", type="primary", disabled=st.session_state.processing, use_container_width=True):
            st.session_state.processing = True
            st.session_state.conversion_queue = video_analysis.copy()
            st.rerun()

    with col_b2:
        if st.button("🗑️ Limpar Lista", use_container_width=True):
            for video in video_analysis:
                if os.path.exists(video['temp_path']):
                    os.unlink(video['temp_path'])
            st.rerun()

    with col_b3:
        if st.button("🔄 Reset", use_container_width=True):
            st.session_state.completed_conversions = []
            st.session_state.failed_conversions = []
            st.session_state.processing = False
            st.rerun()

# ==================== PROCESSAMENTO ====================
if st.session_state.processing and st.session_state.conversion_queue:
    st.markdown("---")
    st.header("⚙️ Processamento em Andamento")

    global_progress = st.progress(0)
    status_text = st.empty()
    total_videos = len(st.session_state.conversion_queue)

    for idx, video_data in enumerate(st.session_state.conversion_queue):
        status_text.markdown(f"**Processando:** {video_data['Nome']} ({idx + 1}/{total_videos})")

        with st.expander(f"🎬 {video_data['Nome']}", expanded=True):
            col1, col2 = st.columns([3, 1])
            with col1:
                st.info(f"📊 Tamanho: {video_data['Tamanho']} | ⏱️ Duração: {video_data['Duração']}")
            with col2:
                individual_progress = st.progress(0)

            output_filename = rename_pattern.replace('{numero}', f"{idx + 1:03d}") + ".mp4"
            output_path = os.path.join(tempfile.gettempdir(), output_filename)

            individual_progress.progress(25)
            st.write("🔄 Iniciando conversão...")

            # Comprimir automaticamente se arquivo for grande
            tamanho_original = os.path.getsize(video_data['temp_path']) / (1024 * 1024)
            if tamanho_original > 200:
                st.info(f"⚡ Arquivo grande ({tamanho_original:.0f}MB) — comprimindo antes de converter...")
                video_path_para_converter = comprimir_antes_converter(video_data['temp_path'], tempfile.gettempdir())
            else:
                video_path_para_converter = video_data['temp_path']

            success, message, stats = convert_video(
                video_path_para_converter,
                output_path,
                profile_config
            )

            individual_progress.progress(100)

            if success:
                original_size = get_video_info(video_data['temp_path'])['size_mb']
                converted_size = stats['output_size_mb']
                saved_mb = original_size - converted_size
                saved_percent = (saved_mb / original_size) * 100 if original_size > 0 else 0

                st.success(f"✅ {message}")

                m1, m2, m3 = st.columns(3)
                with m1:
                    st.metric("Antes", f"{original_size:.1f} MB")
                with m2:
                    st.metric("Depois", f"{converted_size:.1f} MB", f"-{saved_mb:.1f} MB")
                with m3:
                    st.metric("Economia", f"{saved_percent:.1f}%", f"⏱️ {stats['conversion_time_formatted']}")

                st.session_state.completed_conversions.append({
                    'original_name': video_data['Nome'],
                    'output_name': output_filename,
                    'output_path': output_path,
                    'original_size_mb': original_size,
                    'converted_size_mb': converted_size,
                    'saved_mb': saved_mb,
                    'saved_percent': saved_percent,
                    'conversion_time': stats['conversion_time_formatted'],
                    'profile': selected_profile
                })

                st.session_state.total_processed += 1
                st.session_state.total_saved_mb += saved_mb

                if remove_originals and os.path.exists(video_data['temp_path']):
                    os.unlink(video_data['temp_path'])
            else:
                st.error(message)
                st.session_state.failed_conversions.append({
                    'name': video_data['Nome'],
                    'error': message
                })

        global_progress.progress((idx + 1) / total_videos)

    status_text.markdown("✅ **Processamento concluído!**")
    st.session_state.processing = False
    st.session_state.conversion_queue = []
    st.balloons()
    time.sleep(1)
    st.rerun()

# ==================== DOWNLOADS ====================
if st.session_state.completed_conversions:
    st.markdown("---")
    st.header("📥 Downloads Disponíveis")

    df_completed = pd.DataFrame(st.session_state.completed_conversions)
    st.dataframe(
        df_completed[['original_name', 'output_name', 'original_size_mb', 'converted_size_mb', 'saved_percent', 'conversion_time']].rename(columns={
            'original_name': 'Original',
            'output_name': 'Convertido',
            'original_size_mb': 'Antes (MB)',
            'converted_size_mb': 'Depois (MB)',
            'saved_percent': 'Economia (%)',
            'conversion_time': 'Tempo'
        }),
        use_container_width=True
    )

    st.subheader("💾 Download Individual")
    cols = st.columns(3)
    for idx, conversion in enumerate(st.session_state.completed_conversions):
        col_idx = idx % 3
        with cols[col_idx]:
            if os.path.exists(conversion['output_path']):
                with open(conversion['output_path'], 'rb') as f:
                    st.download_button(
                        label=f"⬇️ {conversion['output_name']}",
                        data=f,
                        file_name=conversion['output_name'],
                        mime="video/mp4",
                        use_container_width=True
                    )

    st.markdown("---")

    if len(st.session_state.completed_conversions) > 1:
        st.subheader("📦 Download em Lote (ZIP)")
        output_paths = [c['output_path'] for c in st.session_state.completed_conversions if os.path.exists(c['output_path'])]
        zip_data = create_zip_from_files(output_paths)

        total_size_converted = sum([c['converted_size_mb'] for c in st.session_state.completed_conversions])
        st.info(f"📦 Tamanho total: {total_size_converted:.1f} MB")

        st.download_button(
            label=f"📦 BAIXAR TODOS EM ZIP ({len(output_paths)} arquivos)",
            data=zip_data,
            file_name=f"conversoes_{datetime.now().strftime('%Y%m%d_%H%M%S')}.zip",
            mime="application/zip",
            type="primary",
            use_container_width=True
        )
