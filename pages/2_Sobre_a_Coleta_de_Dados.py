import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="Previsão dos Itens do Café da Manhã",page_icon="📊",layout="wide")


text = """
### 📦 Sobre a Coleta de Dados

#### 📊 Inflação

Os dados relacionados à **inflação** foram obtidos diretamente do **IBGE**, por meio da sua API oficial, a **SIDRA API**. A tabela utilizada foi:

**Tabela 7060 — IPCA:**  
Variação mensal, acumulada no ano, acumulada em 12 meses e peso mensal, abrangendo o índice geral, grupos, subgrupos, itens e subitens de produtos e serviços *(a partir de janeiro/2020)*.

🔗 [Acesse a Tabela 7060](https://sidra.ibge.gov.br/Tabela/7060)

Essa tabela foi essencial para obter uma visão detalhada dos principais itens consumidos no café da manhã e suas respectivas variações inflacionárias ao longo do tempo.

#### 🛒 Estimativa dos Preços Médios

Para estimar os **preços médios** dos itens do café da manhã, foi realizada uma etapa de **mineração de dados** via **web scraping** na plataforma **UberEats**. O objetivo foi obter valores aproximados para cada item, considerando estabelecimentos localizados na cidade de **Recife**.

Os dados foram coletados nos seguintes supermercados:

- Carrefour Hiper  
- Atacadão  
- Assaí  
- Pão de Açúcar  
- Barateiro  
- Big by Carrefour Hiper  
- Sam's Club  

Como os **catálogos variam entre supermercados e entre os próprios itens**, a **quantidade e qualidade dos dados** apresenta certa **variabilidade**. Ainda assim, foi possível construir uma estimativa robusta com base nos valores mais frequentes e representativos de cada produto.
"""

st.markdown(text)

@st.cache_resource
def return_pretty_item(item,inverse=False):
    
    map_dict = {
        "aveia":        "🌾 Aveia",
        "banana":       "🍌 Banana",
        "cafe":         "☕ Café",
        "cuscuz":       "🍚 Cuscuz",
        "iogurte":      "🥛 Iogurte",
        "leite":        "🍼 Leite",
        "mamao":        "🍈 Mamão",
        "manteiga":     "🧈 Manteiga",
        "margarina":    "🧈 Margarina",
        "ovos":         "🥚 Ovos",
        "pao frances":  "🥖 Pão Francês",
        "queijo":       "🧀 Queijo"
        }
    
    if inverse:
        display_to_key = {v: k for k, v in map_dict.items()}
        
        return display_to_key.get(item,None)
    
    return map_dict.get(item,None)

# Access the data from session_state
if "dataset" in st.session_state:
    dataset = st.session_state["dataset"]
    
    supermarket_df = dataset["supermarket_items"].copy()
    supermarket_df["item"] = supermarket_df["item"].apply(return_pretty_item)
    col = st.columns(2)
    
    with col[0]:
        fig = px.pie(supermarket_df.rename(columns={"supermarket":"Supermercado"}),
                     names="Supermercado",title="Distribuição por Supermercado")
        st.plotly_chart(fig, use_container_width=True)
        
    with col[1]:
        
        fig = px.pie(supermarket_df.rename(columns={"item":"Produto"}),
                     names="Produto",title="Distribuição por Produto")
        st.plotly_chart(fig, use_container_width=True,key="item_pie")
        
    
else:
    st.warning("Os dados ainda não foram carregados na página principal.")


footer = """
<hr style="margin-top: 3rem; margin-bottom: 1rem;">

<div style="text-align: center; font-size: 0.9rem; color: #666;">
    <p>Se você gostou do projeto, tem alguma sugestão ou quer trocar uma ideia, entre em contato:</p>
    <p>
        📧 <a href="mailto:lucaspook12@gmail.com" style="text-decoration: none; color: #2980b9;">lucaspook12@gmail.com</a> |
        💼 <a href="https://www.linkedin.com/in/lucas-dos-reis-lrs" target="_blank" style="text-decoration: none; color: #2980b9;">LinkedIn</a>
    </p>
    <p style="font-size: 0.8rem; color: #aaa;">© 2025 Lucas Reis. Todos os direitos reservados.</p>
</div>
"""

st.markdown(footer, unsafe_allow_html=True)