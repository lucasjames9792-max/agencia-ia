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
- Sempre adapte ao tom da modelo
- Gere sempre 3 variações de cada copy
- Indique qual plataforma cada copy é ideal"""

# ─── INTERFACE ───────────────────────────────────────
st.set_page_config(
    page_title="Agente Copy — Agência IA",
    page_icon="✍️",
    layout="centered"
)

st.title("✍️ Agente Copy")
st.caption("Crie anúncios e copys de alto impacto para suas modelos")

# Inicializa histórico na sessão
if "historico" not in st.session_state:
    st.session_state.historico = []
    # Mensagem de boas vindas automática
    bv = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=1000,
        system=SYSTEM_COPY,
        messages=[{"role": "user", "content":
            "Dê boas-vindas e pergunte sobre o perfil da modelo."}]
    )
    st.session_state.historico.append({
        "role": "assistant",
        "content": bv.content[0].text
    })

# Mostra histórico de mensagens
for msg in st.session_state.historico:
    if msg["role"] == "user":
        with st.chat_message("user"):
            st.write(msg["content"])
    else:
        with st.chat_message("assistant", avatar="✍️"):
            st.write(msg["content"])

# Campo de input
if prompt := st.chat_input("Digite sua mensagem..."):
    # Adiciona mensagem do usuário
    st.session_state.historico.append({
        "role": "user",
        "content": prompt
    })
    with st.chat_message("user"):
        st.write(prompt)

    # Chama o Claude
    with st.chat_message("assistant", avatar="✍️"):
        with st.spinner("Gerando copy..."):
            resposta = client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=2000,
                system=SYSTEM_COPY,
                messages=st.session_state.historico
            )
            texto = resposta.content[0].text
            st.write(texto)

    # Salva resposta no histórico
    st.session_state.historico.append({
        "role": "assistant",
        "content": texto
    })

# Botão para limpar conversa
if st.button("🗑️ Limpar conversa"):
    st.session_state.historico = []
    st.rerun()