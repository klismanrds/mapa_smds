import streamlit as st
import pandas as pd
import folium
from folium.plugins import Fullscreen
from streamlit_folium import st_folium
import numpy as np # Adicionado por segurança, embora pandas já o importe

# ----------------------------------------------------
# 1. Configuração e Variáveis
# ----------------------------------------------------

st.set_page_config(
    page_title="Mapa Unidades SMDS - Uberlândia-MG", 
    layout="wide"
)

# Definir cores por tipo (incluindo "Outro")
TIPO_CORES = {
    "Casa da Mulher": "pink",
    "Casa Dia": "lightgreen",
    "CEAI": "purple",
    "Centro Prof.": "blue",
    "Complexo": "black",
    "Condomínio do Idoso": "darkblue",
    "Conselhos Municipais": "darkred",
    "Conselhos Tutelares": "cadetblue",
    "CRAS": "red",
    "CREAS": "lightblue",
    "NAICA": "green",
    "SINE": "orange",
    "Centro de Referência Especializado em População de Rua / Migrantes": "lightgray",
    "Outro": "gray" # Adicionado para garantir cor, caso o mapeamento falhe
}

# ----------------------------------------------------
# 2. Funções de Processamento (Cache)
# ----------------------------------------------------

# Mapear tipo baseado no nome da Unidade
def mapear_tipo(unidade):
    for tipo in TIPO_CORES.keys():
        if tipo.upper() in unidade.upper():
            return tipo
    return "Outro"

# Função para carregar e limpar dados (Usando CACHE para velocidade)
@st.cache_data
def load_and_process_data(filepath="dados.csv"):
    """Carrega dados, trata coordenadas e mapeia tipos."""
    try:
        df = pd.read_csv(filepath)
    except FileNotFoundError:
        st.error(f"Erro: O arquivo '{filepath}' não foi encontrado. Certifique-se de que ele está no diretório.")
        return pd.DataFrame() # Retorna um DataFrame vazio em caso de erro

    # Separar latitude e longitude
    if 'Coordenadas' in df.columns:
        df[['latitude', 'longitude']] = df['Coordenadas'].str.split(',', expand=True)
        df['latitude'] = pd.to_numeric(df['latitude'], errors='coerce')
        df['longitude'] = pd.to_numeric(df['longitude'], errors='coerce')
        
        # Remover linhas com coordenadas inválidas
        df = df.dropna(subset=['latitude', 'longitude'])
    else:
        st.error("Coluna 'Coordenadas' não encontrada no CSV.")
        return pd.DataFrame()

    # Mapear tipo
    df['Tipo'] = df['Unidade'].apply(mapear_tipo)
    return df

# Carrega os dados processados uma única vez
df = load_and_process_data()

# ----------------------------------------------------
# 3. Layout e Sidebar (Filtros)
# ----------------------------------------------------

# Layout para a aplicação - SEM CSS FIXO!
st.title("Unidades SMDS de Uberlândia - MG")
st.markdown("---") # Linha divisória simples

if df.empty:
    st.stop() # Para a execução se o DataFrame estiver vazio

# Sidebar de filtros
with st.sidebar:
    st.header("Filtros")

    tipos = ["Todos"] + sorted(df["Tipo"].unique())
    regioes = ["Todas"] + sorted(df["Região"].unique())

    tipo_selecionado = st.selectbox("Filtrar por equipamento", tipos)
    regiao_selecionada = st.selectbox("Filtrar por Região", regioes)

    # Legenda
    st.markdown("### Legenda das Unidades")
    legend_html = ""
    # Itera sobre o dicionário TIPO_CORES (já inclui "Outro")
    for tipo, cor in TIPO_CORES.items():
        # HTML mais simples e compatível com Streamlit
        legend_html += f"""
        <div style='display:flex; align-items:center; margin-bottom:6px;'>
            <div style='width:15px; height:15px; background:{cor}; border-radius:50%; margin-right:8px;'></div>
            <span>{tipo}</span>
        </div>
        """
    st.markdown(legend_html, unsafe_allow_html=True)
    st.markdown("---")
    st.info(f"Total de Unidades: {len(df)}")


# ----------------------------------------------------
# 4. Filtrar e Criar Mapa
# ----------------------------------------------------

# Filtrar pontos
df_filtrado = df.copy()
if tipo_selecionado != "Todos":
    df_filtrado = df_filtrado[df_filtrado["Tipo"] == tipo_selecionado]
if regiao_selecionada != "Todas":
    df_filtrado = df_filtrado[df_filtrado["Região"] == regiao_selecionada]

st.subheader(f"Total de unidades filtradas: **{len(df_filtrado)}**")

# Criar mapa
mapa = folium.Map(
    location=[-18.9186, -48.2766], # Centro em Uberlândia
    zoom_start=12,
    control_scale=True,
    prefer_canvas=True
)

# Adiciona Fullscreen (do Folium)
Fullscreen(
    position="topleft",
    title="Expandir mapa",
    title_cancel="Sair do fullscreen",
    force_separate_button=True
).add_to(mapa)

# Adicionar marcadores com cores por tipo
for _, row in df_filtrado.iterrows():
    # Conteúdo do Popup
    popup_content = f"""
        <div style="font-family: Arial; font-size: 14px; line-height:1.4;">
            <b style="font-size:16px;">{row['Unidade']}</b><br>
            <b>Tipo:</b> {row['Tipo']}<br>
            <b>Região:</b> {row['Região']}<br>
            📍 <b>Endereço:</b> {row['Endereço']}<br>
            ☎️ <b>Telefone:</b> {row['Telefone']}<br>
            🔗 <a href="https://www.uberlandia.mg.gov.br" target="_blank">Mais informações</a>
        </div>
    """
    popup = folium.Popup(popup_content, max_width=300)
    
    # Pega a cor do dicionário TIPO_CORES. O get é seguro.
    cor = TIPO_CORES.get(row['Tipo'], 'gray')

    folium.Marker(
        location=[row['latitude'], row['longitude']],
        popup=popup,
        icon=folium.Icon(color=cor)
    ).add_to(mapa)

# === Exibir mapa com altura ajustada ===
st_folium(mapa, use_container_width=True, height=700)