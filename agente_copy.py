import os
from dotenv import load_dotenv
from anthropic import Anthropic

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

historico_copy = []

def agente_copy(mensagem):
    historico_copy.append({"role": "user", "content": mensagem})
    resposta = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=2048,
        system=SYSTEM_COPY,
        messages=historico_copy
    )
    texto = resposta.content[0].text
    historico_copy.append({"role": "assistant", "content": texto})
    return texto

def main():
    print("=" * 55)
    print("  AGENTE COPY — ANÚNCIOS DE ALTO IMPACTO")
    print("=" * 55)
    print("Digite 'sair' para encerrar | 'limpar' para reiniciar\n")

    inicio = agente_copy(
        "Dê as boas-vindas, explique rapidamente o que você faz "
        "e peça informações sobre a modelo para começar a criar copys."
    )
    print(f"Agente: {inicio}\n")

    while True:
        entrada = input("Você: ").strip()
        if not entrada:
            continue
        if entrada.lower() == "sair":
            break
        if entrada.lower() == "limpar":
            historico_copy.clear()
            print("Reiniciado!\n")
            continue
        print(f"\nAgente: {agente_copy(entrada)}\n")
        print("-" * 55)

if __name__ == "__main__":
    main()