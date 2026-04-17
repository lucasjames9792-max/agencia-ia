import streamlit as st
from PIL import Image
import io
from pathlib import Path
import zipfile
from datetime import datetime
import subprocess
import tempfile
import os

st.set_page_config(page_title="Compressor de Mídia", page_icon="🗜️", layout="wide")

# Inicializa session_state para armazenar arquivos comprimidos
if 'compressed_files' not in st.session_state:
    st.session_state.compressed_files = {}

st.title("🗜️ Agente Compressor de Mídia")
st.markdown("**Comprima imagens e vídeos mantendo qualidade para suas modelos**")

# Sidebar com configurações
st.sidebar.header("⚙️ Configurações")
tipo_arquivo = st.sidebar.radio("Tipo de arquivo:", ["📸 Imagens", "🎥 Vídeos"])

if tipo_arquivo == "📸 Imagens":
    qualidade = st.sidebar.select_slider(
        "Qualidade:",
        options=["Baixa (50%)", "Média (70%)", "Alta (90%)"],
        value="Alta (90%)"
    )
    qualidade_num = int(qualidade.split("(")[1].split("%")[0])

    formato_saida = st.sidebar.selectbox(
        "Formato de saída:",
        ["WEBP (menor)", "JPEG", "PNG (sem perda)"]
    )

else:  # Vídeos
    resolucao = st.sidebar.selectbox(
        "Resolução máxima:",
        ["1080p (Full HD)", "720p (HD)", "480p (SD)"]
    )
    resolucao_num = resolucao.split("p")[0]

# Upload de arquivos
st.subheader("📤 Upload de Arquivos")

if tipo_arquivo == "📸 Imagens":
    uploaded_files = st.file_uploader(
        "Arraste imagens aqui (JPG, PNG, WEBP)",
        type=["jpg", "jpeg", "png", "webp"],
        accept_multiple_files=True
    )
else:
    uploaded_files = st.file_uploader(
        "Arraste vídeos aqui (MP4, MOV, AVI)",
        type=["mp4", "mov", "avi"],
        accept_multiple_files=True
    )

if uploaded_files:
    st.success(f"✅ {len(uploaded_files)} arquivo(s) carregado(s)")

    col1, col2 = st.columns(2)

    with col1:
        comprimir_individual = st.button("🗜️ Comprimir Arquivos", use_container_width=True)

    with col2:
        comprimir_zip = st.button("📦 Comprimir e Baixar ZIP", use_container_width=True)

    # COMPRESSÃO INDIVIDUAL
    if comprimir_individual:
        st.subheader("📊 Resultados da Compressão")

        # Limpa arquivos anteriores
        st.session_state.compressed_files = {}

        with tempfile.TemporaryDirectory() as temp_dir:
            for idx, uploaded_file in enumerate(uploaded_files):
                col_antes, col_depois, col_economia = st.columns(3)

                tamanho_antes = len(uploaded_file.getvalue()) / 1024 / 1024  # MB

                with col_antes:
                    st.metric("📁 Arquivo", uploaded_file.name)
                    st.metric("Antes", f"{tamanho_antes:.2f} MB")

                # PROCESSAMENTO DE IMAGENS
                if tipo_arquivo == "📸 Imagens":
                    img = Image.open(uploaded_file)

                    # Converte RGBA para RGB se necessário
                    if img.mode == 'RGBA' and formato_saida.startswith("JPEG"):
                        img = img.convert('RGB')

                    # Comprime
                    buffer = io.BytesIO()

                    if formato_saida.startswith("WEBP"):
                        img.save(buffer, format='WEBP', quality=qualidade_num, method=6)
                        extensao = "webp"
                    elif formato_saida.startswith("JPEG"):
                        img.save(buffer, format='JPEG', quality=qualidade_num, optimize=True)
                        extensao = "jpg"
                    else:  # PNG
                        img.save(buffer, format='PNG', optimize=True)
                        extensao = "png"

                    buffer.seek(0)
                    arquivo_comprimido = buffer.getvalue()

                # PROCESSAMENTO DE VÍDEOS
                else:
                    input_path = os.path.join(temp_dir, f"input_{idx}.mp4")
                    output_path = os.path.join(temp_dir, f"output_{idx}.mp4")

                    # Salva arquivo temporário
                    with open(input_path, "wb") as f:
                        f.write(uploaded_file.getvalue())

                    # Comando FFmpeg
                    comando = [
                        "ffmpeg", "-i", input_path,
                        "-vf", f"scale=-2:{resolucao_num}",
                        "-c:v", "libx264",
                        "-crf", "23",
                        "-preset", "medium",
                        "-c:a", "aac",
                        "-b:a", "128k",
                        "-y",
                        output_path
                    ]

                    try:
                        subprocess.run(comando, check=True, capture_output=True)

                        # Lê arquivo comprimido
                        with open(output_path, "rb") as f:
                            arquivo_comprimido = f.read()

                        extensao = "mp4"

                    except subprocess.CalledProcessError:
                        st.error(f"❌ Erro ao comprimir {uploaded_file.name}")
                        continue
                    except FileNotFoundError:
                        st.error("❌ FFmpeg não instalado. Instale com: `sudo apt install ffmpeg`")
                        continue

                # Calcula tamanho depois
                tamanho_depois = len(arquivo_comprimido) / 1024 / 1024  # MB
                economia = ((tamanho_antes - tamanho_depois) / tamanho_antes) * 100

                with col_depois:
                    st.metric("Depois", f"{tamanho_depois:.2f} MB")

                with col_economia:
                    st.metric("💰 Economia", f"{economia:.1f}%")

                # SALVA NO SESSION_STATE (fora do tempfile)
                nome_comprimido = f"{Path(uploaded_file.name).stem}_comprimido.{extensao}"
                st.session_state.compressed_files[nome_comprimido] = arquivo_comprimido

        # BOTÕES DE DOWNLOAD (FORA DO TEMPFILE)
        st.divider()
        st.subheader("⬇️ Downloads Disponíveis")

        for nome_arquivo, conteudo_bytes in st.session_state.compressed_files.items():
            st.download_button(
                label=f"📥 Baixar {nome_arquivo}",
                data=conteudo_bytes,
                file_name=nome_arquivo,
                mime="application/octet-stream",
                use_container_width=True
            )

    # COMPRESSÃO EM ZIP
    if comprimir_zip:
        st.subheader("📦 Criando arquivo ZIP...")

        with tempfile.TemporaryDirectory() as temp_dir:
            zip_buffer = io.BytesIO()

            with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
                for idx, uploaded_file in enumerate(uploaded_files):
                    # PROCESSAMENTO DE IMAGENS
                    if tipo_arquivo == "📸 Imagens":
                        img = Image.open(uploaded_file)

                        if img.mode == 'RGBA' and formato_saida.startswith("JPEG"):
                            img = img.convert('RGB')

                        buffer = io.BytesIO()

                        if formato_saida.startswith("WEBP"):
                            img.save(buffer, format='WEBP', quality=qualidade_num, method=6)
                            extensao = "webp"
                        elif formato_saida.startswith("JPEG"):
                            img.save(buffer, format='JPEG', quality=qualidade_num, optimize=True)
                            extensao = "jpg"
                        else:
                            img.save(buffer, format='PNG', optimize=True)
                            extensao = "png"

                        buffer.seek(0)
                        nome_arquivo = f"{Path(uploaded_file.name).stem}_comprimido.{extensao}"
                        zip_file.writestr(nome_arquivo, buffer.getvalue())

                    # PROCESSAMENTO DE VÍDEOS
                    else:
                        input_path = os.path.join(temp_dir, f"input_{idx}.mp4")
                        output_path = os.path.join(temp_dir, f"output_{idx}.mp4")

                        with open(input_path, "wb") as f:
                            f.write(uploaded_file.getvalue())

                        comando = [
                            "ffmpeg", "-i", input_path,
                            "-vf", f"scale=-2:{resolucao_num}",
                            "-c:v", "libx264",
                            "-crf", "23",
                            "-preset", "medium",
                            "-c:a", "aac",
                            "-b:a", "128k",
                            "-y",
                            output_path
                        ]

                        try:
                            subprocess.run(comando, check=True, capture_output=True)
                            nome_arquivo = f"{Path(uploaded_file.name).stem}_comprimido.mp4"
                            zip_file.write(output_path, nome_arquivo)
                        except:
                            st.warning(f"⚠️ Pulando {uploaded_file.name} (erro na compressão)")

            zip_buffer.seek(0)
            zip_bytes = zip_buffer.getvalue()

            # SALVA ZIP NO SESSION_STATE
            st.session_state.compressed_files['zip'] = zip_bytes

        # BOTÃO DE DOWNLOAD DO ZIP (FORA DO TEMPFILE)
        st.success("✅ ZIP criado com sucesso!")

        nome_zip = f"comprimidos_{datetime.now().strftime('%Y%m%d_%H%M%S')}.zip"

        st.download_button(
            label="📥 Baixar ZIP com Todos os Arquivos",
            data=st.session_state.compressed_files['zip'],
            file_name=nome_zip,
            mime="application/zip",
            use_container_width=True
        )

# Footer
st.divider()
st.markdown("""
**💡 Dicas:**
- WEBP oferece melhor compressão que JPEG
- Qualidade Alta (90%) é ideal para vendas
- Vídeos em 720p são ótimos para stories
- Sempre teste a qualidade antes de enviar para cliente
""")
