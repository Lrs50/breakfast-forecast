import streamlit as st

st.set_page_config(page_title="Previsão dos Itens do Café da Manhã", page_icon="📊", layout="wide")

col = st.columns([3, 2])

with col[0]:
    text = """
    ### Tecnologias e Arquitetura do Projeto

    Este projeto tem como objetivo construir uma solução completa para a **coleta**, **processamento**, **análise**, **previsão** e **disponibilização de dados** relacionados ao consumo de itens do café da manhã. A seguir, explico os principais componentes e como eles se integram na arquitetura geral do sistema.

    O **Data Warehouse**, implementado em **MySQL**, é o repositório central onde todos os dados processados são armazenados. Ele é alimentado por pipelines de **ETL** orquestradas com **Apache Airflow**, que rodam em contêineres **Docker**, garantindo escalabilidade e reprodutibilidade ao sistema.

    As ETLs integram dados de duas principais fontes:
    - A **API SIDRA do IBGE**, que fornece séries históricas de preços de alimentos.
    - Plataformas de supermercados e delivery, como a **UberEats**, através de **web scraping** com **Selenium** e **BeautifulSoup**.
    """
    st.markdown(text)

with col[1]:    
    st.write(" ")
    st.write(" ")
    st.image("imgs/diagrama_dados_breakfast.png", caption="Diagrama do Projeto")

text =  """ 
Após a coleta, os dados são transformados e tratados com as bibliotecas **Pandas** e **NumPy**, e posteriormente armazenados no MySQL. Para facilitar o acesso externo e modularizar a solução, foi desenvolvida uma **API com FastAPI** que permite consultas seguras e rápidas aos dados.

Na etapa de modelagem, o sistema utiliza **Facebook Prophet** para previsão de séries temporais, complementado por **algoritmos genéticos** que otimizam os parâmetros dos modelos. A avaliação dos resultados é feita com métricas do **Scikit-learn**, e as previsões geradas também são armazenadas no Data Warehouse.

A fase inicial de desenvolvimento contou com ampla **prototipagem em Jupyter Notebooks**, acelerando a experimentação e validação de hipóteses.

A camada de **visualização e interação** com o usuário foi construída utilizando **Streamlit**, que atua tanto como front-end quanto back-end da aplicação. A interface permite a exploração interativa dos dados, incluindo gráficos de preços, análises de sazonalidade e previsões.

Para enriquecer a experiência do usuário, a aplicação também se conecta à **API do Google Gemini**, responsável por **gerar sugestões automáticas de receitas** com base nos ingredientes com tendência de queda nos preços — uma funcionalidade útil e criativa.

Além disso, os dados utilizados nos modelos e visualizações também são armazenados em um **Data Lake na Google Cloud Platform**, que serve como repositório intermediário para datasets brutos e processados.

Durante o desenvolvimento, foram utilizadas as seguintes **linguagens de programação**:
- **Python**, principal linguagem para scripts, modelagem preditiva, automações e APIs.
- **SQL**, para manipulação e consulta de dados no Data Warehouse.
- **HTML e CSS**, aplicados na personalização visual da interface Streamlit.

---

Se você gostou do projeto, tem sugestões ou quer trocar ideias sobre dados, entre em contato por **lucaspook12@gmail.com** ou [LinkedIn](https://www.linkedin.com/in/lucas-dos-reis-lrs).
"""

st.markdown(text)
