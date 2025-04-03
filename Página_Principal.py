import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objs as go
from datetime import datetime
import google.generativeai as genai
import textwrap
import re
import gspread
from gspread_dataframe import get_as_dataframe
from oauth2client.service_account import ServiceAccountCredentials

st.set_page_config(page_title="Previsão dos Itens do Café da Manhã",page_icon="📊",layout="wide")
st.sidebar.markdown(
    """
    <h3 style='text-align: center;'>📈 Por que criei este projeto?</h3>
    <p style='text-align: justify;'>
    Com os aumentos repentinos e expressivos nos preços do <strong>café</strong> e dos <strong>ovos</strong>, comecei a me perguntar:<br>
    <em>"E os outros itens do café da manhã, como estão?"</em><br><br>
    A partir dessa curiosidade, selecionei alguns dos principais alimentos presentes na mesa do brasileiro e desenvolvi este projeto com o objetivo de:
    </p>
    <ul style='text-align: left;'>
      <li>Investigar a variação dos preços desses itens;</li>
      <li>Estimar quais produtos tendem a sofrer aumento nos próximos meses;</li>
      <li>Prever <strong>quanto esses preços podem subir nos próximos 6 meses</strong>.</li>
    </ul>
    <p style='text-align: justify;'>A proposta é fornecer uma visão clara e acessível sobre a inflação do café da manhã — combinando dados, inteligência artificial e visualizações interativas.</p>
    """,
    unsafe_allow_html=True
)




def explain_color(color_code, desc):
    st.markdown(
        f"""
        <div style='display: flex; align-items: center; margin-bottom: 10px;'>
            <div style='width: 30px; height: 30px; background-color: {color_code}; border-radius: 5px; margin-right: 10px;'></div>
            <span style='font-size: 0.8em; color: gray;'>{desc}</span>
        </div>
        """,
        unsafe_allow_html=True
    )


def return_measurament_items():
    
    return {
    "aveia":        "200g",
    "banana":       "1kg",
    "cafe":         "250g",
    "cuscuz":       "500g",
    "iogurte":      "170g",
    "leite":        "1L",
    "mamao":        "1kg",
    "manteiga":     "200g",
    "margarina":    "250g",
    "ovos":         "30 un",
    "pao frances":  "500g",
    "queijo":       "200g"
}

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

# Important Functions
@st.cache_resource
def retrieve_data():
    service_account_info = st.secrets["gspread_service_account"]

    # Escopos de acesso
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]

    # Autenticação
    creds = ServiceAccountCredentials.from_json_keyfile_dict(service_account_info, scope)
    client = gspread.authorize(creds)

    # Abrir a planilha pelo nome
    sheet = client.open("breakfast_forecast")

    # Selecionar a aba desejada (por nome ou posição)
    pages = ["breakfast_id","breakfast_timeseries","seasonality_forecast","series_forecast","supermarket_items"]
    dataset = {}

    for page in pages:
        worksheet = sheet.worksheet(page)
        df = get_as_dataframe(worksheet, evaluate_formulas=True)
        dataset[page] = df
        
    return dataset

def return_stats_df(dataset):
    supermarket_df = dataset["supermarket_items"]
    
    items = supermarket_df["item"].unique()
    
    stats = {"Item":[],"Medida":[],"Preço":[],"Preço Previsão":[],"Diferença %":[],"Diferença R$":[],"Nº Itens Estudados":[],"Inflação Média Próximos 6 Meses":[]}
    
    measures = return_measurament_items()
    
    for item in items:
        series_forecast = get_price_df(dataset,item)
        supermarket_df = dataset["supermarket_items"]
        supermarket_df = supermarket_df[supermarket_df["item"]==item]
        
        
        price_rn = get_mean_price(item,dataset,supermarket=None)
        price_future = series_forecast["price"].iloc[-1]
        mean_inflation = np.mean(series_forecast["y"].iloc[-6:].values)
        
        stats["Item"].append(return_pretty_item(item))
        stats["Medida"].append(measures[item])
        stats["Preço"].append(get_mean_price(item,dataset,supermarket=None))
        stats["Preço Previsão"].append(series_forecast["price"].iloc[-1] )
        stats["Diferença R$"].append(price_future-price_rn)
        stats["Diferença %"].append(price_future*100/price_rn -100)
        stats["Nº Itens Estudados"].append(len(supermarket_df))
        stats["Inflação Média Próximos 6 Meses"].append(mean_inflation)
        
        
    return pd.DataFrame(stats)

def plot_seasonality(season_forecast,item,title=""):
    fig = go.Figure([
    go.Scatter(
        name=f'Tendencia {return_pretty_item(item)}',
        x=season_forecast['ds'],
        y=season_forecast['season'],
        mode='lines',
        line=dict(color='rgb(31, 119, 180)'))
    ])
    
    all_series_min = season_forecast["season"].min()
    all_series_max = season_forecast["season"].max()*1.1
    
    # Find the overall date range
    min_date = season_forecast["ds"].min()
    max_date = season_forecast["ds"].max()
    
    # Add shaded area for past data
    fig.add_shape(
        type="rect", 
        x0=min_date, 
        x1=max_date,  # Today's date as the cutoff
        y0=all_series_min, 
        y1=all_series_max,
        fillcolor="rgba(52, 73, 94, 0.25)",
        line=dict(color="rgba(255, 255, 255, 0)")
    )
    fig.update_xaxes(tickformat="%b-%d") 
    fig.update_layout(
        title=title, 
        #title_x=0.5,  # Center the title,
        title_font=dict(size=24),  # Increase title font size
        autosize=True,  # Make the plot responsive
        margin=dict(l=10, r=10, t=40, b=20),  # Adjust margins for a tighter layout
        legend_title_text='Items',
        width=800,  # Set a fixed width or leave it responsive
        height=300,  # Set a fixed height to avoid it being too tall
        hovermode="x",
        
    )

    return fig

def get_mean_price(item,dataset,supermarket=None):
    
    supermarket_df = dataset["supermarket_items"]

    dates = supermarket_df["ETL"].unique()
    date = dates.max()

    item_df = supermarket_df[(supermarket_df["item"]==item) & (supermarket_df["ETL"]==date)]
    if supermarket:
        try:
            item_df = item_df[item_df["supermarket"]==supermarket]
        except Exception as e:
            print("Error {e}")
    
    
    return item_df["price"].mean()

def get_price_df(dataset,item):
    
    id_data = dataset["breakfast_id"]

    id = id_data[id_data["item"]==item]["id"].values[0]

    series_forecast = dataset["series_forecast"]
    series_forecast = series_forecast[series_forecast["id"]==id].copy()
    series_forecast["ds"] = pd.to_datetime(series_forecast["ds"])
    
    supermarket_df = dataset["supermarket_items"]

    dates = supermarket_df["ETL"].unique()
    date = dates.max()

    past_data = series_forecast[series_forecast["ds"]<date].reset_index(drop=True)
    future_data = series_forecast[series_forecast["ds"]>=date].reset_index(drop=True)

    past_data.loc[past_data.index[-1], 'price'] = get_mean_price(item,dataset)

    present_index = len(past_data)

    for i in range(len(past_data) - 2, -1, -1):
        past_data.loc[i, 'price'] = past_data.loc[i + 1, 'price'] / (1 + past_data.loc[i + 1, 'y']/100)

    past_data = pd.concat([past_data,future_data]).reset_index(drop=True)

    for i in range(present_index,len(past_data)):
        past_data.loc[i,"price"] = past_data.loc[i - 1, 'price'] * (1 + past_data.loc[i - 1, 'y']/100)

    past_data.loc[past_data.index[present_index-1], 'price_lower'] = get_mean_price(item,dataset)
    past_data.loc[past_data.index[present_index-1], 'price_upper'] = get_mean_price(item,dataset)

    for i in range(present_index,len(past_data)):
        past_data.loc[i,"price_lower"] = past_data.loc[i - 1, 'price_lower'] * (1 + past_data.loc[i - 1, 'y_lower']/100)
        past_data.loc[i,"price_upper"] = past_data.loc[i - 1, 'price_upper'] * (1 + past_data.loc[i - 1, 'y_upper']/100)
    
    return past_data
 
def create_forecast_plot(series_forecasts, items, metric,title=""):  
    """
    Create a plot for multiple forecast series.
    
    Parameters:
    - series_forecasts: List of forecast DataFrames
    - items: List of item names corresponding to the forecast series
    - metric: The column name to plot from the forecast DataFrames
    
    Returns:
    - Plotly Figure with multiple traces
    """
    # Ensure datetime conversion for all series
    for series in series_forecasts:
        series['ds'] = pd.to_datetime(series['ds'])
    
    # Create the plot
    today_date = datetime.today()
    
    fig = go.Figure()
    
    # Color palette for multiple traces
    colors = ['#3182bd','#e41a1c','#4daf4a','#984ea3','#ff7f00','#a65628','#f781bf','#999999','#e6194B','#3cb44b','#ffe119',
              '#4363d8','#f58231','#911eb4','#42d4f4','#469990','#9A6324','#800000','#808000','#008080','#000075','#a9a9a9',
              '#00ff00','#ff00ff','#00ffff']

    # Plot traces for each forecast series
    for i, (series, item) in enumerate(zip(series_forecasts, items)):
        # Alternate color if more items than default colors
        color = colors[i % len(colors)]
        
        # Add main prediction trace
        fig.add_trace(go.Scatter(
            x=series["ds"], 
            y=series[metric], 
            mode='lines', 
            name=f'{item}',
            line=dict(color=color)
        ))
    
    # Determine global min and max for consistent shading
    all_series_min = min(series[metric].min() for series in series_forecasts)
    all_series_max = max(series[metric].max() for series in series_forecasts)*1.1
    
    # Find the overall date range
    min_date = min(series["ds"].min() for series in series_forecasts)
    max_date = max(series["ds"].max() for series in series_forecasts)
    
    # Add shaded area for past data
    fig.add_shape(
        type="rect", 
        x0=min_date, 
        x1=today_date,  # Today's date as the cutoff
        y0=all_series_min, 
        y1=all_series_max,
        fillcolor="rgba(52, 73, 94, 0.25)",
        line=dict(color="rgba(255, 255, 255, 0)")
    )
    
    # Add shaded area for future data
    fig.add_shape(
        type="rect", 
        x0=today_date,  # Today's date as the start for future
        x1=max_date, 
        y0=all_series_min, 
        y1=all_series_max,
        fillcolor="rgba(243, 156, 18, 0.25)",  # Light blue shading
        line=dict(color="rgba(255, 255, 255, 0)")
    )
    
    space_legend = -0.3 -0.1*(len(items)//4)
    
    
    fig.update_layout(
    title=title,
    #title_x=0.5,  # Center the title
    title_font=dict(size=24),  # Increase title font size
    autosize=True,  # Make the plot responsive
    margin=dict(l=10, r=10, t=40, b=20),  # Adjust margins for a tighter layout
    legend=dict(
        orientation="h",  # Horizontal legend
        yanchor="bottom",  # Anchor the legend at the bottom
        y=space_legend,  # Move the legend below the plot
        xanchor="center",  # Center the legend horizontally
        x=0.5,  # Center the legend horizontally
    ),
    width=800,  # Set a fixed width or leave it responsive
    height=300,  # Set a fixed height to avoid it being too tall
    hovermode="x",
    )
    
    fig.update_xaxes(nticks=10)  # Set the desired number of ticks on x-axis
    fig.update_yaxes(nticks=10)  # Set the desired number of ticks on y-axis
    
    return fig

def create_forecast_plot_solo(serie_forecast, item, metric,title="",tendency = False):
    """
    Create a plot for multiple forecast series.
    
    Parameters:
    - series_forecasts: List of forecast DataFrames
    - items: List of item names corresponding to the forecast series
    - metric: The column name to plot from the forecast DataFrames
    
    Returns:
    - Plotly Figure with multiple traces
    """
    df_true = serie_forecast[serie_forecast["model"] == 0]
    df_error = serie_forecast[serie_forecast["model"] == 1]

    last_row = df_true.iloc[[-1]] 
    df_error = pd.concat([last_row, df_error], ignore_index=True)
    # Create the plot
    today_date = pd.to_datetime(df_error["ds"].iloc[1])
    
    fig = go.Figure()

    # Add main prediction trace
    
    if tendency:
        fig.add_trace(go.Scatter(
        x=serie_forecast["ds"], 
        y=serie_forecast["trend"], 
        mode='lines', 
        name=f'{"tendência"}',
        line=dict(color="#DC143C")
    )) 
    
    fig.add_trace(go.Scatter(
        x=serie_forecast["ds"], 
        y=serie_forecast[metric], 
        mode='lines', 
        name=f'{item}',
        line=dict(color="#3182bd")
    ))
    
    fig.add_trace(go.Scatter(
            name='Limite Superior',
            x=df_error['ds'],
            y=df_error[f"{metric}_upper"],
            mode='lines',
            marker=dict(color="#444"),
            line=dict(width=0),
            showlegend=False
        ))
    
    fig.add_trace(go.Scatter(
            name='Limite inferior',
            x=df_error['ds'],
            y=df_error[f'{metric}_lower'],
            marker=dict(color="#444"),
            line=dict(width=0),
            mode='lines',
            fillcolor='rgba(68, 68, 68, 0.3)',
            fill='tonexty',
            showlegend=False
        ))
    
    # Determine global min and max for consistent shading
    all_series_min = min(serie_forecast[metric].min(), df_error[f'{metric}_lower'].min(),serie_forecast["trend"].min())
    all_series_max = max(serie_forecast[metric].max(), df_error[f'{metric}_upper'].max(),serie_forecast["trend"].min())
    all_series_max = all_series_max * 1.05 if all_series_max > 0 else all_series_max * 0.95
    all_series_min = all_series_min * 1.05 if all_series_min < 0 else all_series_min * 0.95
    
    
    # Find the overall date range
    min_date = serie_forecast["ds"].min()
    max_date = serie_forecast["ds"].max()
    
    # Add shaded area for past data
    fig.add_shape(
        type="rect", 
        x0=min_date, 
        x1=today_date,  # Today's date as the cutoff
        y0=all_series_min, 
        y1=all_series_max,
        fillcolor="rgba(52, 73, 94, 0.25)",
        line=dict(color="rgba(255, 255, 255, 0)")
    )
    
    # Add shaded area for future data
    fig.add_shape(
        type="rect", 
        x0=today_date,  # Today's date as the start for future
        x1=max_date, 
        y0=all_series_min, 
        y1=all_series_max,
        fillcolor="rgba(243, 156, 18, 0.25)",  # Light blue shading
        line=dict(color="rgba(255, 255, 255, 0)")
    )
    
    fig.update_layout(
        title=title, 
        #title_x=0.5,  # Center the title
        title_font=dict(size=24),  # Increase title font size
        autosize=True,  # Make the plot responsive
        margin=dict(l=10, r=10, t=40, b=20),  # Adjust margins for a tighter layout
        showlegend=False,
        hovermode="x",
        #legend_title_text='Items',
        width=800,  # Set a fixed width or leave it responsive
        height=300,  # Set a fixed height to avoid it being too tall
    )
    
    return fig
@st.cache_resource
def call_gemini(prompt):
    genai.configure(api_key=st.secrets["api_keys"]["genimi_api"])
    model = genai.GenerativeModel('gemini-2.0-flash')

    response = model.generate_content(prompt)
    return format_output_llm(response.text)

def format_output_llm(text):
  text = text.replace('•', '  *')
  return textwrap.indent(text, '> ', predicate=lambda _: True)
# Body of the Page
st.title("☕ Quanto Custa o Café da Manhã?")

#bases = ["breakfast_id","breakfast_timeseries","seasonality_forecast","series_forecast","supermarket_items"]

def get_dataset():
    if "dataset" not in st.session_state:
        st.session_state["dataset"] = retrieve_data()
    return st.session_state["dataset"]

dataset = get_dataset()

#@st.fragment()
def info_time_series_general():
        
    items_df = dataset["breakfast_id"]
    breakfast_items = [return_pretty_item(item) for item in items_df["item"].values]
    
    placeholder="Escolha os itens para a análise"
    
    forecasts = []
    measuraments = return_measurament_items()
    with st.container(border=True):
        item_choice = st.multiselect(placeholder, breakfast_items,default=[return_pretty_item(item) for item in['aveia', 'banana','cafe','ovos','leite']] )
        info_data = pd.DataFrame()
        
        item_choice =  [return_pretty_item(item,inverse=True) for item in item_choice]
        
        column_names_dict = [{"ds":"Data"},{"ds":"Data"}]
        
        porcoes = ""
        for item in item_choice:
        
            id = items_df[items_df["item"]==item]["id"].values[0]
            
            series_forecast = get_price_df(dataset,item)
            season_forecast = dataset["seasonality_forecast"]
            season_forecast = season_forecast[season_forecast["id"]==id]
            
            series_forecast["ds"] = series_forecast["ds"].dt.strftime('%Y-%m')
            series_forecast["y"] = series_forecast["y"].round(2)
            series_forecast["price"] = series_forecast["price"].round(2)
            
            if "ds" not in info_data.columns:
                info_data["ds"] = series_forecast["ds"]
            
            info_data[f"{item}_inflation"] = series_forecast["y"]
            info_data[f"{item}_price"]     = series_forecast["price"]
            column_names_dict[0][f"{item}_inflation"] = return_pretty_item(item)
            column_names_dict[1][f"{item}_price"]     = return_pretty_item(item)
            
            porcoes += f" {return_pretty_item(item)} {measuraments[item]},"
            forecasts.append(series_forecast)
            
        if len(item_choice)>0:
            porcoes = porcoes[::-1].replace(',', '.', 1)[::-1]
            st.caption(f"Foram considerados as seguintes porções:{porcoes}")
            #"rgba(52, 73, 94, 0.25)
            #rgba(243, 156, 18, 0.25)
            # explain_color("rgba(52, 73, 94, 0.25)","Representa os dados do passado.")
            # explain_color("rgba(243, 156, 18, 0.25)","Representa a previsão do futuro.")
            col = st.columns(2)
            with col[0]:
                explain_color("rgba(52, 73, 94, 0.25)","Representa os dados do passado.")
                graph,data = st.tabs(["Gráfico","Dados"])
                with graph:
                    fig = create_forecast_plot(forecasts,item_choice,"y","Inflação %")
                    st.plotly_chart(fig,use_container_width=True)
                with data:
                    st.markdown(f"<h4 style='text-align: center;'>Inflação %</h4>", unsafe_allow_html=True)
                    
                    st.dataframe(info_data[["ds"]+[col for col in info_data.columns if "inflation" in col]].rename(columns=column_names_dict[0]),hide_index=True)
            with col[1]:
                explain_color("rgba(243, 156, 18, 0.25)","Representa a previsão do futuro.")
                graph,data = st.tabs(["Gráfico","Dados"])
                with graph:
                    fig = create_forecast_plot(forecasts,item_choice,"price","Preço R$")
                    st.plotly_chart(fig,use_container_width=True)
                with data:
                    st.markdown(f"<h4 style='text-align: center;'>Preço R$</h4>", unsafe_allow_html=True)
                    st.dataframe(info_data[["ds"]+[col for col in info_data.columns if "price" in col]].rename(columns=column_names_dict[1]),hide_index=True)

def info_time_series_solo():
        
    items_df = dataset["breakfast_id"]
    breakfast_items = items_df["item"].values
    
    placeholder="Escolha o item para a análise"
    
    with st.container(border=True):
        breakfast_items = [return_pretty_item(item) for item in breakfast_items]
        item = st.selectbox(placeholder, breakfast_items)
        
        item = return_pretty_item(item,inverse=True)
        
        id = items_df[items_df["item"]==item]["id"].values[0]
        
        st.markdown(f"<h3 style='text-align: center;'>Informações Detalhadas sobre {return_pretty_item(item)}</h3>", unsafe_allow_html=True)
        
        series_forecast = get_price_df(dataset,item)
        series_forecast["ds"] = pd.to_datetime(series_forecast["ds"])
        series_forecast["ds"] = series_forecast["ds"].dt.strftime('%Y-%m')
        series_forecast[["y", "y_lower", "y_upper"]] = series_forecast[["y", "y_lower", "y_upper"]].round(2)
        series_forecast[["price", "price_lower", "price_upper"]] = series_forecast[["price", "price_lower", "price_upper"]].round(2)
        series_forecast[["trend", "trend_lower", "trend_upper"]] = series_forecast[["trend", "trend_lower", "trend_upper"]].round(2)
        
        series_forecast.iloc[:-7, series_forecast.columns.get_indexer(['y_lower', 'y_upper'])] = np.nan
        series_forecast.iloc[:-7, series_forecast.columns.get_indexer(['trend_lower', 'trend_upper'])] = np.nan
        
        season_forecast = dataset["seasonality_forecast"]
        season_forecast = season_forecast.reset_index()
        season_forecast = season_forecast[season_forecast["id"]==id].copy()
        season_forecast["ds"] = pd.to_datetime(season_forecast["ds"])
        season_forecast["season"] = season_forecast["season"].round(2)
        
        supermarket_df = dataset["supermarket_items"]
        supermarket_df = supermarket_df[supermarket_df["item"]==item]
        
        dates = supermarket_df["ETL"].unique()
        date = dates.max()
        
        col = st.columns(2)
        with col[0]:
            explain_color("rgba(52, 73, 94, 0.25)","Representa os dados do passado.")
            graph,data = st.tabs(["Gráfico","Dados"])
            with graph:
                fig = create_forecast_plot_solo(series_forecast.copy(),item,"y","Inflação %",True)
                st.plotly_chart(fig,use_container_width=True)
            with data:
                st.dataframe(series_forecast[["ds", "y","y_lower","y_upper","trend"]]
                             .rename(columns={"ds": "Data", "y": "Inflação %",
                                              "y_lower":"Limite Inferior",
                                              "y_upper":"Limite Superior",
                                              "trend":"Tendência"}),hide_index=True)
            
                
        with col[1]:
            explain_color("rgba(243, 156, 18, 0.25)","Representa a previsão do futuro.")
            graph,data = st.tabs(["Gráfico","Dados"])
            with graph:
                fig = create_forecast_plot_solo(series_forecast.copy(),item,"price","Preço R$")
                st.plotly_chart(fig,use_container_width=True)
            with data:
                st.dataframe(series_forecast[["ds", "price","price_lower","price_upper"]]
                             .rename(columns={"ds": "Data", "price": "Preço R$",
                                              "price_lower":"Limite Inferior",
                                              "price_upper":"Limite Superior"}),hide_index=True)
        col = st.columns(2)
        
        # with col[0]:
        #     graph,data = st.tabs(["Gráfico","Dados"])
        #     #st.markdown(f"<h6 style='text-align: center;'>Tendência</h6>", unsafe_allow_html=True)
        #     with graph:
        #         fig = create_forecast_plot_solo(series_forecast.copy(),item,"trend","Tendência %")
        #         st.plotly_chart(fig,use_container_width=True)
        #     with data:
        #         st.dataframe(series_forecast[["ds", "trend","trend_lower","trend_upper"]]
        #                      .rename(columns={"ds": "Data", "trend": "Tendência",
        #                                       "trend_lower":"Limite Inferior",
        #                                       "trend_upper":"Limite Superior"}))
        with col[0]:
            #st.markdown(f"<h6 style='text-align: center;'>Sazonalidade</h6>", unsafe_allow_html=True)
            
            graph,data = st.tabs(["Gráfico","Dados"])
            with graph:
                fig = plot_seasonality(season_forecast,item,"Sazonalidade % (Inflação)")
                st.plotly_chart(fig,use_container_width=True)
            with data:
                season_forecast["ds"] = season_forecast["ds"].dt.strftime('%m-%d')
                st.dataframe(season_forecast[["ds", "season"]]
                             .rename(columns={"ds": "Data", "season": "Sazonalidade %"}),hide_index=True)
        with col[1]:
            #st.markdown(f"<h6 style='text-align: center;'>informações Sobre Precificação</h6>", unsafe_allow_html=True)
            graph,data = st.tabs(["Resumo","Dados"])
            with graph:
                measuraments = return_measurament_items()
                st.caption(f"Foram considerados {measuraments[item]} do item {return_pretty_item(item)} para a análise.")
                col = st.columns(2)    
                price_rn = get_mean_price(item,dataset)
                future_price = series_forecast["price"].iloc[-1] 
            
                with col[0]:
                    st.metric(label='Preço Médio (Atual)', value=f"R$ {round(price_rn, 2):,.2f}")
                    st.metric(label='Variação Próximos 6 meses (Estimativa)', value=f"R$ {round(future_price - price_rn, 2):,.2f}")    

                    change = future_price*100/price_rn -100
                    st.metric(label='Mudança Percentual (Estimativa)', value=f"{round(change, 2):,.2f}%") 
                    
                    st.metric(label = "Cidades Consideradas",value="Recife")
                with col[1]:
                    st.metric(label='Preço Futuro (Estimativa)', value=f"R$ {round(future_price, 2):,.2f}")
                    st.metric(label='Data de Coleta', value=date) 

                    n_items = len(supermarket_df)
                    n_supermarkets = len(supermarket_df["supermarket"].unique())
                    
                    st.metric(label='Nº Items Analisados', value=n_items) 
                    st.metric(label='Nº Supermecados Considerados', value=n_supermarkets) 
                    
            with data:
                st.dataframe(supermarket_df[["price","name","supermarket"]]
                             .rename(columns={"price": "Preço", "name": "Nome","supermarket":"Supermercado"}),hide_index=True)

def general_info_all():
    
    
    stats_df = return_stats_df(dataset)
    round_list = ["Preço","Preço Previsão","Diferença %","Diferença R$","Inflação Média Próximos 6 Meses"]
    stats_df[round_list] = stats_df[round_list].round(2)
    
    df_up = stats_df[stats_df["Diferença R$"]>=0]
    df_down = stats_df[stats_df["Diferença R$"]<0]
    
    with st.container(border=True):
        st.markdown(f"<h3 style='text-align: center;'>📊 Estatísticas</h3>", unsafe_allow_html=True)
        tab = st.tabs(["Resumo","Dados"])
        with tab[0]:
            col = st.columns(2)
            
            with col[0]:
                with st.container(border=True):
                    st.markdown(f"<h5 style='text-align: center;'>Itens em Baixa 📉</h5>", unsafe_allow_html=True)
                    st.dataframe(
                                df_down[["Item", "Preço","Preço Previsão","Diferença R$"]]
                                .rename(columns={"Diferença R$": "Diminuição"})
                                .sort_values('Diminuição', ascending=True),
                                hide_index=True
                                )
            with col[1]:
                with st.container(border=True):
                    st.markdown(f"<h5 style='text-align: center;'>Itens em Alta 📈</h5>", unsafe_allow_html=True)
                    st.dataframe(
                                df_up[["Item", "Preço","Preço Previsão", "Diferença R$"]]
                                .rename(columns={"Diferença R$": "Aumento"})
                                .sort_values('Aumento', ascending=False),
                                hide_index=True
                                )
                
        with tab[1]:
            st.dataframe(stats_df,hide_index=True)
    
    
    with st.container(border=True):
        st.markdown(f"<h3 style='text-align: center;'>🍽️ Sugestão de Receitas</h3>", unsafe_allow_html=True)
        
        prompt = f"""
        Você é um chef especializado em café da manhã saudável. Sua missão é criar cinco receitas nutritivas utilizando os seguintes ingredientes como foco: {df_down['Item'].values}.

        Diretrizes:
        - Faça receitas deliciosas, que além de nutritivas sejam palatáveis, por exemplo combinações estranhas como cuscuz e mamão misturados devem ser evitadas.
        - Não faça combinações esquisitas de ingredientes, foque em receitas que já existem.
        - Seja claro em suas instruções, evite deixar passos vagos
        - Não se apresente, apenas forneça as receitas.
        - Cada receita deve conter:
        1. Um título, precedido pela marcação "<RECETA>" para facilitar a separação.
        2. Uma breve explicação sobre por que essa refeição é uma boa escolha, foque nos possiveis beneficios a saude, a explicação deve ter o formato *texto*.
        3. A lista de ingredientes com quantidades.
        4. O modo de preparo com instruções claras e objetivas.
        5. A descrição dos macronutrientes aproximados, incluindo calorias, proteínas, carboidratos, gorduras e fibras.
        6. O titulo da receita deve ter o seguinte formato **Titulo**
        Seja detalhado e direto, garantindo que as receitas sejam fáceis de entender e seguir.
        """
        response_text = call_gemini(prompt)
        response_text = response_text.split("<RECETA>")
        
        for index,recipe in enumerate(response_text[1:]):
            match = re.search(r"\*\*(.*?)\*\*", recipe)
            with st.expander(f"{index+1}. {match.group(1)}"):
                st.markdown(recipe)
        
      
general, solo = st.tabs(["Análise Geral","Análise Detalhada Idividual"])

with general:    
    info_time_series_general()
with solo:
    info_time_series_solo()

general_info_all()


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