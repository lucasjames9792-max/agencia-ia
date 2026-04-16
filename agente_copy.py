import os
import streamlit as st
from dotenv import load_dotenv
from anthropic import Anthropic

# ─── CONFIGURAÇÃO ────────────────────────────────────
load_dotenv()
client = Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])

SYSTEM_COPY = """Você é um especialista em copywriting de alta conversão
para marketing de criadores de conteúdo adulto responsável.

Seu objetivo é criar copys que:
- Despertem curiosidade intensa sem ser explícito
- Gerem FOMO (medo de ficar de fora)
- Usem gatilhos de escassez, prova social e autoridade
- Sejam adequadas para Instagram, TikTok e Twitter/X
- Convertam seguidores em assinantes pagantes

ESTRUTURA DE COPY QUE VOCÊ SEMPRE SEGUE:
1. GANCHO (1 linha que para o scroll)
2. PROBLEMA/DOR (identifica o que o lead quer)
3. SOLUÇÃO/PROMESSA (o que a modelo oferece)
4. PROVA SOCIAL (números, resultados, depoimentos)
5. CTA (chamada para ação urgente)

FORMATOS QUE VOCÊ DOMINA:
- Story (até 3 frases, urgência máxima)
- Post feed (5-8 linhas, storytelling)
- Anúncio pago (headline + descrição + CTA)
- Bio otimizada (150 caracteres que vendem)
- DM de abordagem (mensagem que converte)

REGRAS:
- Nunca use palavras explícitas
- Sempre adapte ao tom da modelo (sensual, misteriosa, divertida, premium)
- Gere sempre 3 variações de cada copy
- Indique qual plataforma cada copy é ideal

Quando o usuário pedir uma copy, pergunte:
1. Tom da modelo (ex: misteriosa, divertida, premium)
2. Objetivo (novos assinantes, reengajar, upsell)
3. Plataforma alvo"""

# ─── INTERFACE ───────────────────────────────────────
st.set_page_config(
    page_title="Agente Copy — Anúncios de Alto Impacto",
    page_icon="✍️",
    layout="wide"
)

st.title("✍️ Agente Copy — Anúncios de Alto Impacto")
st.caption("Crie copys de alta conversão para Instagram, TikTok e Twitter/X")

# Inicializa histórico
if "historico" not in st.session_state:
    st.session_state.historico = []
    bv = client.messages.create(
        model="claude-sonnet-4-5",
        max_tokens=1000,
        system=SYSTEM_COPY,
        messages=[{"role": "user", "content":
            "Dê as boas-vindas, explique rapidamente o que você faz "
            "e peça informações sobre a modelo para começar a criar copys."}]
    )
    st.session_state.historico.append({
        "role": "assistant",
        "content": bv.content[0].text
    })

# ─── SIDEBAR — AÇÕES RÁPIDAS ─────────────────────────
with st.sidebar:
    st.header("⚡ Ações Rápidas")

    if st.button("📸 Copy para Story"):
        st.session_state.acao_rapida = (
            "Crie 3 opções de copy para Story do Instagram. "
            "Tom: misterioso. Objetivo: novos assinantes. "
            "Máximo 3 frases, urgência máxima."
        )

    if st.button("📰 Copy para Post Feed"):
        st.session_state.acao_rapida = (
            "Crie 3 opções de copy para Post Feed. "
            "5 a 8 linhas com storytelling. "
            "Tom: premium e sofisticado."
        )

    if st.button("💰 Anúncio Pago"):
        st.session_state.acao_rapida = (
            "Crie 3 variações de anúncio pago completo: "
            "headline + descrição + CTA. "
            "Plataforma: Meta Ads."
        )

    if st.button("👤 Bio Otimizada"):
        st.session_state.acao_rapida = (
            "Crie 3 opções de bio otimizada para Instagram. "
            "Máximo 150 caracteres que vendam e convertam."
        )

    if st.button("💌 DM de Abordagem"):
        st.session_state.acao_rapida = (
            "Crie 3 opções de DM de abordagem para enviar "
            "para novos seguidores e converter em assinantes."
        )

    st.divider()
    st.subheader("🎯 Configurações")

    tom = st.selectbox("Tom da modelo:", [
        "Misteriosa e sedutora 🌙",
        "Divertida e provocante 😈",
        "Premium e sofisticada 💎",
        "Urgente e escassa ⏰",
        "Íntima e pessoal 🌹"
    ])
    st.session_state.tom = tom

    plataforma = st.selectbox("Plataforma alvo:", [
        "Instagram",
        "TikTok",
        "Twitter/X",
        "Meta Ads",
        "Todas as plataformas"
    ])
    st.session_state.plataforma = plataforma

    objetivo = st.selectbox("Objetivo:", [
        "Novos assinantes 💰",
        "Reengajar fãs antigos 🔁",
        "Upsell conteúdo premium 🔥",
        "Gerar curiosidade 👀",
        "Aumentar engajamento 📈"
    ])
    st.session_state.objetivo = objetivo

    st.divider()
    if st.button("🗑️ Limpar conversa"):
        st.session_state.historico = []
        st.rerun()

# ─── ÁREA DE CHAT ────────────────────────────────────
for msg in st.session_state.historico:
    if msg["role"] == "user":
        with st.chat_message("user"):
            st.write(msg["content"])
    else:
        with st.chat_message("assistant", avatar="✍️"):
            st.markdown(msg["content"])

# ─── AÇÃO RÁPIDA ─────────────────────────────────────
if "acao_rapida" in st.session_state and st.session_state.acao_rapida:
    prompt = st.session_state.acao_rapida
    st.session_state.acao_rapida = ""

    contexto = (
        f"{prompt}\n\nTom: {st.session_state.get('tom', 'Misteriosa')}. "
        f"Plataforma: {st.session_state.get('plataforma', 'Instagram')}. "
        f"Objetivo: {st.session_state.get('objetivo', 'Novos assinantes')}."
    )

    st.session_state.historico.append({"role": "user", "content": contexto})
    with st.chat_message("user"):
        st.write(prompt)

    with st.chat_message("assistant", avatar="✍️"):
        with st.spinner("Gerando copy..."):
            r = client.messages.create(
                model="claude-sonnet-4-5",
                max_tokens=2048,
                system=SYSTEM_COPY,
                messages=st.session_state.historico
            )
            texto = r.content[0].text
            st.markdown(texto)

    st.session_state.historico.append({"role": "assistant", "content": texto})
    st.rerun()

# ─── INPUT DO USUÁRIO ────────────────────────────────
if prompt := st.chat_input("Descreva a copy que precisa ou use as ações rápidas na lateral..."):
    contexto = (
        f"{prompt}\n\nTom: {st.session_state.get('tom', 'Misteriosa')}. "
        f"Plataforma: {st.session_state.get('plataforma', 'Instagram')}. "
        f"Objetivo: {st.session_state.get('objetivo', 'Novos assinantes')}."
    )

    st.session_state.historico.append({"role": "user", "content": contexto})
    with st.chat_message("user"):
        st.write(prompt)

    with st.chat_message("assistant", avatar="✍️"):
        with st.spinner("Gerando copy..."):
            r = client.messages.create(
                model="claude-sonnet-4-5",
                max_tokens=2048,
                system=SYSTEM_COPY,
                messages=st.session_state.historico
            )
            texto = r.content[0].text
            st.markdown(texto)

    st.session_state.historico.append({"role": "assistant", "content": texto})
