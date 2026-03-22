# ⭐ avalia+
**Sistema de avaliação de comércios do Centro de Aracaju, SE**
MVP com Streamlit + LangGraph + Gemini

---

## Funcionalidades

| Feature | Status |
|--------|--------|
| Marketplace com filtros por categoria, plano e busca | ✅ |
| Perfil detalhado do comércio com avaliações reais | ✅ |
| Formulário de avaliação com geração de cupom automático | ✅ |
| Análise de sentimento e tópicos via Gemini (LangGraph) | ✅ |
| Painel do comerciante com KPIs, gráficos e insights de IA | ✅ |
| Meu painel de cupons | ✅ |
| Perfil de clientes por segmento (donut chart) | ✅ |
| Sem autenticação — pronto para demo | ✅ |
| Fallback heurístico quando a API key não está configurada | ✅ |

---

## Instalação

```bash
# 1. Crie o ambiente virtual
python -m venv venv
source venv/bin/activate      # Linux/Mac
venv\Scripts\activate         # Windows

# 2. Instale as dependências
pip install -r requirements.txt

# 3. Configure a chave do Gemini (opcional)
cp .env.example .env
# Edite .env e adicione:
# GEMINI_API_KEY=sua-chave-aqui
# Obtenha em: https://aistudio.google.com/app/apikey

# 4. Rode o app
streamlit run app.py
```

Acesse em: **http://localhost:8501**

---

## Estrutura

```
avalia_mais/
├── app.py           # Aplicação Streamlit principal (roteador + todas as páginas)
├── data.py          # Dados dos comércios do Centro de Aracaju (mock)
├── agents.py        # Agentes LangGraph com suporte a Gemini
├── requirements.txt
├── .env.example
└── README.md
```

---

## Fluxo LangGraph após avaliação

```
Usuário avalia
    ↓
[Nó 1] Analisar avaliação  → sentimento + tópicos (Gemini)
    ↓
[Nó 2] Gerar insights      → alertas/elogios/recomendações para o comerciante (Gemini)
    ↓
[Nó 3] Recomendar          → texto personalizado para o usuário (Gemini)
    ↓
Cupom gerado automaticamente + resultado exibido na tela
```

---

## Modo sem IA (fallback)

Se `GEMINI_API_KEY` não estiver configurada, o sistema usa análise heurística local:
- Sentimento baseado na nota e palavras-chave
- Insights baseados em padrões de avaliações
- Recomendações genéricas

O app funciona 100% sem a chave — a IA é um enhancement, não um requisito.

---

## Comércios disponíveis (todos no Centro de Aracaju)

| Comércio | Categoria | Plano | Nota |
|---------|-----------|-------|------|
| Churrascaria Xingó | Restaurante | Premium | 4.9 |
| Farmácia Saúde Viva | Farmácia | Premium | 4.7 |
| Mercado Bom Preço | Mercado | Freemium | 4.5 |
| Café Cotinguiba | Café | Premium | 4.8 |
| Boutique Centro Moda | Moda | Freemium | 4.3 |
| Clínica Médica São Lucas | Saúde | Premium | 4.6 |
| Pizzaria do Mercado | Restaurante | Freemium | 4.4 |
| Açaí da Praça | Café | Premium | 4.9 |
| Drogaria Central | Farmácia | Freemium | 4.2 |
| Restaurante Caju & Cia | Restaurante | Premium | 4.6 |
| Ótica Horizonte Centro | Moda | Freemium | 4.5 |
| Mercadinho São Francisco | Mercado | Freemium | 4.1 |
