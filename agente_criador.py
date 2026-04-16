import os
import streamlit as st
from dotenv import load_dotenv
from anthropic import Anthropic

# ─── CONFIGURAÇÃO ────────────────────────────────────
load_dotenv()
client = Anthropic(api_key=os.environ["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"])

SYSTEM_CRIADOR = """Você é o maior especialista do mundo em criar agentes 
de IA com Claude e em Prompt Engineering avançado.

OPERAÇÃO QUE VOCÊ CONHECE COMPLETAMENTE:
O usuário é dono de uma agência de marketing digital para 
criadoras de conteúdo adulto responsável. Ele já tem:

AGENTES JÁ CRIADOS:
1. Agente Copy — cria anúncios e copys para modelos (interface web)
2. Agente Caixinha — perguntas e respostas estratégicas para stories
3. Agente Meta Ads — analisa métricas e escala campanhas no Meta
4. Agente Telegram — posta mídias com copy e botões no canal @hvinha
5. Agente Segurança — protege chaves, monitora vazamentos
6. Agente Criador — você mesmo, cria novos agentes

INFRAESTRUTURA:
- Linguagem: Python
- Interface: Streamlit (web) ou terminal
- API: Anthropic Claude Sonnet
- Canais: Telegram (@hvinha), Meta Ads, Privacy, WhatsApp
- Objetivo: levar modelos de $20k para $60k/mês em 3 meses

SUAS 5 ESPECIALIDADES:

1. CRIAR NOVOS AGENTES
Para cada agente você entrega SEMPRE os dois:
   A) PROMPT COMPLETO — pronto para usar, explicado parte por parte
   B) CÓDIGO PYTHON COMPLETO — com interface Streamlit se web,
      ou terminal se preferir, já com a API Key configurável

2. SUGERIR AGENTES
Analise gaps na operação e sugira agentes que:
- Aumentem receita das modelos
- Economizem tempo do gestor
- Automatizem tarefas repetitivas
- Melhorem conversão e engajamento

3. ENSINAR PROMPT ENGINEERING
Técnicas que você domina e ensina com exemplos do nicho:
- Role Prompting: dar persona específica ao agente
- Chain of Thought: fazer o agente pensar passo a passo
- Few-Shot: dar exemplos de entrada e saída esperada
- Tree of Thought: explorar múltiplos caminhos
- ReAct: raciocinar e agir em loop
- Self-Consistency: gerar múltiplas respostas e combinar

4. AVALIAR E MELHORAR PROMPTS
- Nota de 0 a 10 com justificativa
- Identifica exatamente o que está fraco
- Entrega versão melhorada imediatamente
- Explica cada melhoria feita

5. ORIENTAR ARQUITETURA DE AGENTES
- Como conectar agentes entre si
- Quando usar terminal vs interface web
- Como organizar a pasta da agência
- Boas práticas de segurança

FORMATO DE RESPOSTA PADRÃO:
Quando criar um agente, SEMPRE entregue nessa ordem:
1. Nome e função do agente (2 linhas)
2. Prompt completo entre ```
3. Código Python completo entre ```python
4. Como testar o agente
5. Próximo agente sugerido com base na operação"""

# ─── INTERFACE ───────────────────────────────────────
st.set_page_config(
    page_title="Agente Criador — Fábrica de Agentes IA",
    page_icon="🏭",
    layout="wide"
)

st.title("🏭 Agente Criador de Agentes")
st.caption("Especialista em Prompt Engineering • Cria qualquer agente para sua operação")

# Inicializa histórico
if "historico" not in st.session_state:
    st.session_state.historico = []
    # Boas-vindas automáticas
    bv = client.messages.create(
        model="claude-sonnet-4-5-20251001",
        max_tokens=2000,
        system=SYSTEM_CRIADOR,
        messages=[{"role": "user", "content":
            "Dê boas-vindas mostrando que conhece minha operação completa. "
            "Liste os agentes que já tenho e sugira os 3 próximos mais "
            "importantes para escalar agora. Seja direto e empolgante."}]
    )
    st.session_state.historico.append({
        "role": "assistant",
        "content": bv.content[0].text
    })

# ─── SIDEBAR — AÇÕES RÁPIDAS ─────────────────────────
with st.sidebar:
    st.header("⚡ Ações Rápidas")

    if st.button("🤖 Sugerir próximo agente"):
        st.session_state.acao_rapida = (
            "Analise minha operação atual e me diga qual é o próximo "
            "agente mais importante para criar agora. Entregue o prompt "
            "completo e o código Python pronto."
        )

    if st.button("📚 Ensinar uma técnica"):
        st.session_state.acao_rapida = (
            "Me ensine a técnica de prompt engineering mais poderosa "
            "para iniciantes com exemplos práticos do meu nicho de "
            "agência de criadores de conteúdo."
        )

    if st.button("🔍 Avaliar meu prompt"):
        st.session_state.acao_rapida = (
            "Vou te mostrar um prompt meu para você avaliar de 0 a 10 "
            "e entregar a versão melhorada:"
        )

    if st.button("📋 Listar agentes que tenho"):
        st.session_state.acao_rapida = (
            "Liste todos os agentes que já tenho na minha operação, "
            "o que cada um faz e como eles se conectam entre si."
        )

    if st.button("💡 Ideia de agente novo"):
        st.session_state.acao_rapida = (
            "Me dê 5 ideias criativas de agentes que eu ainda não tenho "
            "e que poderiam aumentar muito minha receita ou produtividade."
        )

    st.divider()
    st.subheader("📦 Preferência de entrega")
    preferencia = st.radio(
        "Quando criar um agente, entregar:",
        ["Prompt + Código Python (os dois)",
         "Só o prompt e a ideia",
         "Só o código Python"]
    )
    st.session_state.preferencia = preferencia

    st.divider()
    st.subheader("🖥️ Interface preferida")
    interface = st.radio(
        "Novo agente com interface:",
        ["Web (Streamlit)", "Terminal (Python puro)"]
    )
    st.session_state.interface = interface

    if st.button("🗑️ Limpar conversa"):
        st.session_state.historico = []
        st.rerun()

# ─── ÁREA DE CHAT ────────────────────────────────────
for msg in st.session_state.historico:
    if msg["role"] == "user":
        with st.chat_message("user"):
            st.write(msg["content"])
    else:
        with st.chat_message("assistant", avatar="🏭"):
            st.markdown(msg["content"])

# ─── AÇÃO RÁPIDA ─────────────────────────────────────
if "acao_rapida" in st.session_state and st.session_state.acao_rapida:
    prompt = st.session_state.acao_rapida
    st.session_state.acao_rapida = ""

    st.session_state.historico.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.write(prompt)

    with st.chat_message("assistant", avatar="🏭"):
        with st.spinner("Criando..."):
            contexto = (
                f"{prompt}\n\nPreferência de entrega: "
                f"{st.session_state.get('preferencia', 'os dois')}. "
                f"Interface: {st.session_state.get('interface', 'Web')}."
            )
            r = client.messages.create(
                model="claude-sonnet-4-5-20251001",
                max_tokens=4000,
                system=SYSTEM_CRIADOR,
                messages=st.session_state.historico
            )
            texto = r.content[0].text
            st.markdown(texto)

    st.session_state.historico.append({
        "role": "assistant", "content": texto
    })
    st.rerun()

# ─── INPUT DO USUÁRIO ────────────────────────────────
if prompt := st.chat_input(
    "Descreva o agente que quer criar, peça uma técnica ou cole seu prompt para avaliar..."
):
    st.session_state.historico.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.write(prompt)

    with st.chat_message("assistant", avatar="🏭"):
        with st.spinner("Criando seu agente..."):
            contexto = (
                f"{prompt}\n\nPreferência de entrega: "
                f"{st.session_state.get('preferencia', 'os dois')}. "
                f"Interface: {st.session_state.get('interface', 'Web')}."
            )
            mensagens = st.session_state.historico[:-1] + [
                {"role": "user", "content": contexto}
            ]
            r = client.messages.create(
                model="claude-sonnet-4-5-20251001",
                max_tokens=4000,
                system=SYSTEM_CRIADOR,
                messages=mensagens
            )
            texto = r.content[0].text
            st.markdown(texto)

    st.session_state.historico.append({
        "role": "assistant", "content": texto
    })
