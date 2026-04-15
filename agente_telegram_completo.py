import os
import streamlit as st
import requests
import json
import threading
from dotenv import load_dotenv
from anthropic import Anthropic
from datetime import datetime, timedelta

# ─── CONFIGURAÇÕES ───────────────────────────────────
load_dotenv()
client     = Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
BOT_TOKEN  = os.environ["TELEGRAM_BOT_TOKEN"]
CHANNEL_ID = "@hvinha"
TG_URL     = f"https://api.telegram.org/bot{BOT_TOKEN}"

# ─── BOTÕES PADRÃO — UM ABAIXO DO OUTRO ─────────────
BOTOES_PADRAO = {
    "inline_keyboard": [
        [{"text": "🎁 Abre Meu Presente",
          "url":  "https://privacy.com.br/profile/hivia24"}],
        [{"text": "🔥 Não Quero Ficar De Fora",
          "url":  "http://t.me/Hiviasilva_bot?start=start"}]
    ]
}

# ─── BOTÕES ANIVERSÁRIO — UM ABAIXO DO OUTRO ────────
def botoes_aniversario(preco):
    return {
        "inline_keyboard": [
            [{"text": f"🎂 OFERTA ESPECIAL R${preco} — Pegar Agora!",
              "url":  "https://privacy.com.br/profile/hivia24"}],
            [{"text": "🔥 Não Quero Ficar De Fora",
              "url":  "http://t.me/Hiviasilva_bot?start=start"}]
        ]
    }

# ─── SYSTEM PROMPTS ──────────────────────────────────
SYSTEM_PADRAO = """Você é especialista em copywriting para Telegram de 
criadora de conteúdo adulto responsável chamada Hivia.

Crie legendas curtas e impactantes que:
- Param o scroll nos primeiros 2 segundos
- Usam no máximo 5 emojis estratégicos
- Criam FOMO e curiosidade sem ser explícito
- Direcionam para os botões abaixo do post
- Têm no máximo 200 caracteres

ESTRUTURA:
Linha 1: GANCHO com emoji
Linha 2: CORPO curto e misterioso
Linha 3: CTA para os botões

Gere 3 opções numeradas. Considere qualquer instrução extra do usuário."""

SYSTEM_ANIVERSARIO = """Você é especialista em copywriting para Telegram de 
criadora de conteúdo adulto responsável chamada Hivia.

É SEMANA DE ANIVERSÁRIO com promoção especial!
Crie legendas que:
- Destacam a promoção de aniversário com urgência
- Usam o preço promocional como gancho principal
- Criam FOMO (oferta por tempo limitado)
- São curtas e impactantes (máximo 200 caracteres)
- Usam emojis de festa e fogo 🎂🎉🔥

ESTRUTURA:
Linha 1: GANCHO de aniversário + preço
Linha 2: Urgência (só essa semana!)
Linha 3: CTA para o botão

Gere 3 opções numeradas. Considere qualquer instrução extra do usuário."""

# ─── GERAR COPY ──────────────────────────────────────
def gerar_copy(contexto, modo_aniversario=False, preco=None):
    system = SYSTEM_ANIVERSARIO if modo_aniversario else SYSTEM_PADRAO
    prompt = contexto
    if modo_aniversario and preco:
        prompt = f"Preço promocional: R${preco}. {contexto}"
    r = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=800,
        system=system,
        messages=[{"role": "user", "content": prompt}]
    )
    return r.content[0].text

# ─── POSTAR MÍDIA ────────────────────────────────────
def postar_midia(arquivo_bytes, nome, legenda, botoes):
    ext = nome.split(".")[-1].lower()
    if ext in ["jpg", "jpeg", "png"]:
        r = requests.post(
            f"{TG_URL}/sendPhoto",
            data={"chat_id": CHANNEL_ID, "caption": legenda,
                  "parse_mode": "HTML", "reply_markup": json.dumps(botoes)},
            files={"photo": (nome, arquivo_bytes)}
        )
    else:
        r = requests.post(
            f"{TG_URL}/sendVideo",
            data={"chat_id": CHANNEL_ID, "caption": legenda,
                  "parse_mode": "HTML", "reply_markup": json.dumps(botoes),
                  "supports_streaming": True},
            files={"video": (nome, arquivo_bytes)}
        )
    return r.json()

# ─── AGENDADOR ───────────────────────────────────────
def executar_post_agendado(post):
    postar_midia(post["bytes"], post["nome"], post["copy"], post["botoes"])

def iniciar_agendador(fila):
    def rodar():
        for post in fila:
            horario_obj = post["horario_obj"]
            agora = datetime.now()
            if horario_obj > agora:
                delay = (horario_obj - agora).total_seconds()
                t = threading.Timer(delay, executar_post_agendado, args=[post])
                t.daemon = True
                t.start()
    thread = threading.Thread(target=rodar, daemon=True)
    thread.start()

# ─── INTERFACE ───────────────────────────────────────
st.set_page_config(
    page_title="Agente Telegram — Hivia",
    page_icon="📲",
    layout="wide"
)

st.title("📲 Agente Postador — @hvinha")
st.caption("Upload em massa • Copy automática • Agendamento • Recorrência 24h")

if "fila_posts" not in st.session_state:
    st.session_state.fila_posts = []

# ─── SIDEBAR ─────────────────────────────────────────
with st.sidebar:
    st.header("⚙️ Configurações")

    st.subheader("🎂 Promoção de Aniversário")
    modo_aniversario = st.toggle("Ativar semana de aniversário")
    preco_aniversario = None
    if modo_aniversario:
        preco_aniversario = st.selectbox(
            "Preço promocional:",
            ["20", "30", "50"],
            format_func=lambda x: f"R$ {x}"
        )
        st.success(f"🎉 Modo aniversário ativo — R${preco_aniversario}")

    st.divider()

    st.subheader("✍️ Estilo das Copys")
    tom = st.selectbox("Tom:", [
        "Misteriosa e sedutora 🌙",
        "Divertida e provocante 😈",
        "Premium e sofisticada 💎",
        "Urgente e escassa ⏰",
        "Íntima e pessoal 🌹"
    ])
    objetivo = st.selectbox("Objetivo:", [
        "Converter em assinantes 💰",
        "Reengajar fãs antigos 🔁",
        "Gerar curiosidade 👀",
        "Vender conteúdo premium 🔥",
        "Aumentar engajamento 📈"
    ])

    st.subheader("💬 Como quer as copys agora?")
    instrucao_global = st.text_area(
        "Instrução extra para todas:",
        placeholder="Ex: tema de praia, seja mais ousada, mencione exclusividade...",
        height=100
    )

    st.divider()
    st.subheader("🎁 Preview dos Botões")
    if modo_aniversario and preco_aniversario:
        st.button(f"🎂 OFERTA R${preco_aniversario} — Pegar Agora!", disabled=True)
    else:
        st.button("🎁 Abre Meu Presente", disabled=True)
    st.button("🔥 Não Quero Ficar De Fora", disabled=True)
    st.caption("Ficam um abaixo do outro no Telegram ✅")

# ─── UPLOAD EM MASSA ─────────────────────────────────
st.subheader("1️⃣ Upload em massa de mídias")
midias = st.file_uploader(
    "Arraste todas as fotos e vídeos de uma vez",
    type=["jpg", "jpeg", "png", "mp4", "mov"],
    accept_multiple_files=True
)

if midias:
    st.success(f"✅ {len(midias)} mídia(s) carregada(s)!")

    st.subheader("2️⃣ Gerar copys automáticas")
    if st.button("✨ Gerar Copy para Todas as Mídias", type="primary"):
        if "copys_geradas" not in st.session_state:
            st.session_state.copys_geradas = {}
        barra = st.progress(0)
        for i, midia in enumerate(midias):
            with st.spinner(f"Gerando copy para {midia.name}..."):
                contexto = (
                    f"Mídia: {midia.name}. Tom: {tom}. "
                    f"Objetivo: {objetivo}. "
                    f"Instrução extra: {instrucao_global or 'nenhuma'}."
                )
                copy = gerar_copy(contexto, modo_aniversario, preco_aniversario)
                st.session_state.copys_geradas[midia.name] = copy
            barra.progress((i + 1) / len(midias))
        st.success("✅ Copys geradas para todas as mídias!")

    if "copys_geradas" in st.session_state and st.session_state.copys_geradas:
        st.subheader("3️⃣ Configure cada post")
        posts_configurados = []

        for i, midia in enumerate(midias):
            with st.expander(f"📸 Post {i+1} — {midia.name}", expanded=(i == 0)):
                col1, col2 = st.columns([1, 1])

                with col1:
                    if "image" in midia.type:
                        st.image(midia, use_column_width=True)
                    else:
                        st.video(midia)

                with col2:
                    copy_opcoes = st.session_state.copys_geradas.get(midia.name, "")
                    st.text_area("Opções geradas:", value=copy_opcoes,
                                 height=150, disabled=True, key=f"op_{i}")

                    copy_final = st.text_area(
                        "Cole a copy escolhida:",
                        placeholder="Cole aqui...",
                        height=80, key=f"copy_{i}"
                    )

                    instrucao_extra = st.text_input(
                        "💬 Instrução específica para este post:",
                        placeholder="Ex: mencione que é foto exclusiva...",
                        key=f"inst_{i}"
                    )

                    if instrucao_extra and st.button("🔄 Regerar", key=f"regen_{i}"):
                        with st.spinner("Regerando..."):
                            novo_ctx = (
                                f"Mídia: {midia.name}. Tom: {tom}. "
                                f"Objetivo: {objetivo}. "
                                f"Instrução extra: {instrucao_extra}."
                            )
                            nova = gerar_copy(novo_ctx, modo_aniversario, preco_aniversario)
                            st.session_state.copys_geradas[midia.name] = nova
                            st.rerun()

                    horario = st.time_input(
                        "🕐 Horário:",
                        value=datetime.now().replace(
                            hour=(datetime.now().hour + i + 1) % 24,
                            minute=0, second=0
                        ),
                        key=f"hora_{i}"
                    )

                    botoes = (
                        botoes_aniversario(preco_aniversario)
                        if modo_aniversario else BOTOES_PADRAO
                    )

                    if copy_final:
                        horario_obj = datetime.combine(datetime.now().date(), horario)
                        if horario_obj < datetime.now():
                            horario_obj += timedelta(days=1)
                        midia.seek(0)
                        posts_configurados.append({
                            "id":          i,
                            "nome":        midia.name,
                            "bytes":       midia.read(),
                            "copy":        copy_final,
                            "horario":     horario.strftime("%H:%M"),
                            "horario_obj": horario_obj,
                            "botoes":      botoes,
                            "status":      "⏳ Aguardando"
                        })

        st.subheader("4️⃣ Agendar todos os posts")
        st.info(f"📅 {len(posts_configurados)} post(s) configurado(s) • Recorrência 24h")

        if posts_configurados:
            if st.button(f"🚀 AGENDAR {len(posts_configurados)} POSTS", type="primary"):
                st.session_state.fila_posts = posts_configurados
                iniciar_agendador(posts_configurados)
                st.success(f"✅ {len(posts_configurados)} posts agendados!")
                st.balloons()

if st.session_state.fila_posts:
    st.divider()
    st.subheader("📋 Fila de Posts Agendados")
    for post in st.session_state.fila_posts:
        col1, col2, col3 = st.columns([2, 2, 1])
        with col1:
            st.write(f"📸 **{post['nome']}**")
        with col2:
            st.write(f"🕐 {post['horario']} — recorre a cada 24h")
        with col3:
            st.write(post.get("status", "⏳ Aguardando"))
    if st.button("🗑️ Limpar fila"):
        st.session_state.fila_posts = []
        st.rerun()