import pandas as pd
import streamlit as st
from langchain_core.tools import Tool
from datetime import datetime

# Funções auxiliares

def extract_final_response(text: str) -> str:
    """Extrai apenas a Resposta Final do output do agente."""
    with st.spinner("Pensando..."):
        if "Resposta Final:" in text:
            return text.split("Resposta Final:")[1].strip()
    return text

@st.cache_data
def load_data(file_path: str) -> pd.DataFrame:
    """Carrega o dataset de imóveis."""
    return pd.read_csv(file_path)


# Tools
def search_properties(
    valor: float, quartos: int, vagas: int, bairro: str
) -> str:
    """
    Pesquisa imóveis com base nos critérios fornecidos.

    Args:
        infos (dict): Dicionário com as informações de busca
            - valor (int): Valor máximo do imóvel
            - quartos (int): Número mínimo de quartos
            - vagas (int): Número mínimo de vagas
            - bairro (str): Nome do bairro desejado

    Returns:
        str: String com os imóveis encontrados formatados
    """
    # Carrega o dataset de imóveis
    data = load_data(r'C:\Users\diham\langchain\vendas_ap\dados_wgs.csv')

    # Configura opções de exibição do DataFrame
    pd.set_option('display.max_columns', None)
    pd.set_option('display.max_rows', None)
    pd.set_option('display.width', None)
    
    filtered_data = data[
        (data['valor_total'] <= valor) &
        (data['quartos'] >= quartos) &
        (data['vagas'] >= vagas) &
        (data['bairro'].str.contains(bairro, case=False))
    ]
    
    return filtered_data

def schedule_visit(address: str, date: str, hour: str, nome):
    """
    Agenda uma visita adicionando o endereço, data e hora ao arquivo de visitas.

    Args:
        address: O endereço do imóvel a ser visitado.
        date: A data da visita no formato 'YYYY-MM-DD'.
        hour: A hora da visita no formato 'HH:MM'.
    """
    
    # Carrega os dados existentes de visitas
    file_path = r'C:\Users\diham\langchain\vendas_ap\visitas.csv'
    try:
        data = load_data(file_path)
    except FileNotFoundError:
        # Cria um DataFrame vazio com as colunas se o arquivo não existir
        data = pd.DataFrame(columns=["endereco", "data", "hora", "Nome"])

    # Adiciona a nova visita como uma nova linha
    new_visit = pd.DataFrame([[nome, address, date, hour]], 
                             columns=["endereco", "data", "hora", "Nome"])
    data = pd.concat([data, new_visit], ignore_index=True)

    # Salva o DataFrame atualizado no arquivo CSV
    data.to_csv(file_path, index=False)

search_tool = Tool(
    name="search_properties",
    func=search_properties,
    description="Use para pesquisar imóveis com base nos critérios fornecidos."
)

schedule_visit_tool = Tool(
    name="schedule_visit",
    func=schedule_visit,
    description="Use para agendar uma visita ao imóvel."
)

tools = [search_tool, schedule_visit_tool]