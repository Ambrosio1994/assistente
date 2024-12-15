import streamlit as st
import pandas as pd
from langchain_core.prompts import ChatPromptTemplate
from langchain_anthropic import ChatAnthropic
from langchain_core.output_parsers import StrOutputParser
from langchain_core.tools import tool
from langchain.agents import create_react_agent

# Configurações iniciais do Streamlit
st.set_page_config(page_title="Moveis SP", 
                   page_icon="🏠",
                   layout="centered")

# Interface do usuário
st.title("🏠 IA - Assistente Imobiliário")

# Funções auxiliares
@st.cache_data
def load_data(file_path: str) -> pd.DataFrame:
    """Carrega o dataset de imóveis."""
    return pd.read_csv(file_path)

@tool
def search_properties(valor: int, quartos: int, vagas: int, bairro: str) -> str:
    """
    Pesquisa imóveis com base nos critérios fornecidos.
    
    Args:
        valor: Valor máximo do imóvel
        quartos: Número mínimo de quartos
        vagas: Número mínimo de vagas
        bairro: Nome do bairro desejado
    
    Returns:
        String com os imóveis encontrados formatados
    """
    data = load_data(r'C:\Users\diham\langchain\vendas_ap\dados_wgs.csv')
    
    filtered_data = data[
        (data['valor_total'] <= valor) &
        (data['quartos'] >= quartos) &
        (data['vagas'] >= vagas) &
        (data['bairro'].str.contains(bairro, case=False))
    ]
    
    pd.set_option('display.max_columns', None)
    pd.set_option('display.max_rows', None)
    pd.set_option('display.width', None)
    
    return filtered_data.to_string(index=False)

def extract_final_response(text: str) -> str:
    """Extrai apenas a Resposta Final do output do agente."""
    if "Resposta Final:" in text:
        return text.split("Resposta Final:")[1].strip()
    return text

# Sidebar com preferências
with st.sidebar:
    st.header("Suas Preferências")
    quartos = st.slider("Quantos quartos você precisa?", 1, 5, 2, key='quartos')
    vagas = st.slider("Quantas vagas de garagem você precisa?", 1, 5, 1, key='vagas')
    valor = st.slider("Qual valor você está disposto a pagar?", 100000, 1000000, 200000, key='valor')
    bairro = st.text_input("Qual bairro você prefere?", "", key='bairro')

# Verifica se o bairro foi informado
if not bairro:
    st.info("👈 Por favor, escolha suas preferências no menu lateral")
    st.stop()

# Inicialização do estado da sessão
if 'chat_history' not in st.session_state:
    st.session_state.chat_history = []

if 'agent' not in st.session_state:
    llm = ChatAnthropic(
        model="claude-3-5-sonnet-20240620",
        temperature=0,
        max_tokens=4000
    )
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", """
        Você é um corretor imobiliário em São Paulo, SP.
        Use a ferramenta search_properties para encontrar imóveis que atendam às preferências do cliente.
        
        Preferências atuais do cliente:
        - Quartos: {quartos}
        - Vagas de carro: {vagas} 
        - Valor máximo: R$ {valor}
        - Bairro: {bairro}

        Instruções importantes:
        1. Para cada imóvel encontrado, apresente as informações nesta ordem:
           📍 Endereço completo
           - Quartos: [número]
           - Vagas: [número]
           - Área: [valor] m²
           💰 Valores:
           - Valor total: R$ [valor]
           - Condomínio: R$ [valor] (se disponível)
           - 🚇 Metrô mais próximo: [nome da estação] - [linha] ([distância] metros)
         
        2. Apresente primeiro os imóveis que melhor atendam TODOS os critérios
        3. Ordene por valor, do menor para o maior
        4. Não invente informações - use apenas os dados disponíveis
        5. Se alguma informação não estiver disponível, não a inclua na resposta

        FERRAMENTAS DISPONÍVEIS:
        {tools}
        
        NOME DA FERRAMENTA: 
        {tool_names}

        Você DEVE seguir EXATAMENTE este formato para cada resposta:

        Pensamento: preciso buscar imóveis que atendam aos critérios
        Ação: search_properties
        Entrada da Ação: {{"valor": {valor}, "quartos": {quartos}, "vagas": {vagas}, "bairro": "{bairro}"}}
        Observação: (resultado da pesquisa)
        Pensamento: vou analisar os resultados e apresentar de forma organizada
        Resposta Final: (apresentação formatada dos imóveis)

        {agent_scratchpad}
        
        Histórico da conversa:
        {chat_history}
        """),
        ("human", "{input}")
    ])

    # Configuração do agente    
    st.session_state.agent = create_react_agent(
        llm=llm,
        tools=[search_properties],
        prompt=prompt,
        output_parser=StrOutputParser()
    )

# Chat inicial
if not st.session_state.chat_history:
    initial_response = st.session_state.agent.invoke({
        "input": "Por favor, mostre as opções de imóveis disponíveis.",
        "quartos": quartos,
        "vagas": vagas,
        "valor": valor,
        "bairro": bairro,
        "chat_history": [],
        "intermediate_steps": []
    })
    
    # Extrai apenas a resposta final
    if isinstance(initial_response, dict) and "output" in initial_response:
        final_response = extract_final_response(initial_response["output"])
        st.session_state.chat_history.append({"role": "assistant", "content": final_response})
    else:
        final_response = extract_final_response(initial_response)
        st.session_state.chat_history.append({"role": "assistant", "content": final_response})

# Exibe histórico do chat
for message in st.session_state.chat_history:
    with st.chat_message(message["role"], avatar="🤖" if message["role"] == "assistant" else "🤷"):
        st.write(message["content"])

# Input do usuário
user_query = st.chat_input("Tire suas dúvidas...")
if user_query:
    # Adiciona mensagem do usuário ao histórico
    st.session_state.chat_history.append({"role": "human", "content": user_query})
    
    # Exibe mensagem do usuário
    with st.chat_message("human", avatar="🤷"):
        st.write(user_query)
    
    # Obtém e exibe resposta do bot
    with st.chat_message("assistant", avatar="🤖"):
        with st.spinner("Buscando imóveis..."):
            response = st.session_state.agent.invoke({
                "input": user_query,
                "quartos": quartos,
                "vagas": vagas,
                "valor": valor,
                "bairro": bairro,
                "chat_history": st.session_state.chat_history,
                "intermediate_steps": []
            })
            
            # Extrai apenas a resposta final
            if isinstance(response, dict) and "output" in response:
                final_response = extract_final_response(response["output"])
                st.write(final_response)
            else:
                final_response = extract_final_response(response)
                st.write(final_response)
            
            # Adiciona resposta do bot ao histórico
            st.session_state.chat_history.append({"role": "assistant", "content": final_response})