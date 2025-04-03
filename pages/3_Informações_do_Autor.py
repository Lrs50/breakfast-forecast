import streamlit as st

st.set_page_config(page_title="Previsão dos Itens do Café da Manhã",page_icon="📊",layout="wide")

col = st.columns([4,1])

with col[0]:
    text = """
    ### Sobre mim

    Meu nome é **Lucas dos Reis Silva**, nascido no interior da Bahia, em uma cidadezinha chamada **Nova Soure**. Aos 18 anos, me mudei para **Recife** com o objetivo de estudar **Engenharia da Computação** na **Universidade Federal de Pernambuco (UFPE)**.

    Sou apaixonado por **tecnologia, esportes e animais**. No meu tempo livre, gosto de programar, praticar atividades físicas e, claro, ouvir uma boa música enquanto faço tudo isso.

    Durante a graduação, participei de uma pesquisa em **redes 5G** no projeto **CIN/Motorola** e realizei uma **PIBIC** na área de **redes neurais quânticas**. Atualmente, meu foco está em **MLOps**, com ênfase no desenvolvimento completo de projetos de dados.

    Como engenheiro, sinto-me confortável em atuar em todas as etapas do ciclo de vida de um projeto — da concepção aos retoques finais. Gosto de explorar as diferentes formas de pensar, as ferramentas e metodologias necessárias em cada fase de um projeto.
    
    Tenho planos de cursar **mestrado na área de Ciência da Computação**, com foco em **predição de séries temporais**, um campo que considero extremamente relevante e no qual acredito poder contribuir de forma significativa.
    """
    st.markdown(text)

with col[1]:    
    st.write(" ")
    st.write(" ")
    # 233 - 293
    st.image("imgs/logo_lucas.jpg", caption="Momento da apresentação do projeto de pesquisa (PIBIC)")
    
    
text =  """ 
---

Se você gostou do projeto, tem alguma crítica ou simplesmente quer trocar uma ideia, pode me encontrar pelo e-mail **lucaspook12@gmail.com** ou pelo [LinkedIn](https://www.linkedin.com/in/lucas-dos-reis-lrs).
"""

st.markdown(text)