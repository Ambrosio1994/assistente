import streamlit as st
from prompt_agent import PROMPT
from langchain_anthropic import ChatAnthropic
from langchain.chains import LLMChain
from tools_agent import search_properties

# Configurações iniciais do Streamlit
st.set_page_config(page_title="Assistente Imobiliário", page_icon="🏠")

# Inicialização do estado da sessão
if 'chat_history' not in st.session_state:
    st.session_state.chat_history = []
    
if 'chain' not in st.session_state:
    llm = ChatAnthropic(
        model="claude-3-5-sonnet-20240620",
        temperature=0,
        max_tokens=4000
    )
    
    st.session_state.chain = LLMChain(
        llm=llm,
        prompt=PROMPT,
        verbose=False
    )

# Funções auxiliares
def get_bot_response(user_input, database, preferences):
    """Obtém resposta do chatbot"""
    st.session_state.chat_history.append({"role": "human", "content": user_input})
    if not st.session_state.chat_history:
        return st.session_state.chain.run(
            database=database.to_string(index=False),
            **preferences,
            input=user_input,
            chat_history=[]
        )
    else:
        return st.session_state.chain.run(
            database=database.to_string(index=False),
            **preferences,
            input=user_input,
            chat_history=st.session_state.chat_history
        )

# Interface do usuário
st.title("🏠 Assistente Imobiliário")

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

# Carrega e filtra os dados
database = search_properties(valor, quartos, vagas, bairro)

# Preferências do usuário em um dicionário
preferences = {
    "quartos": quartos,
    "vagas": vagas,
    "valor": valor,
    "bairro": bairro
}

# Chat inicial
if not st.session_state.chat_history:
    initial_response = get_bot_response(
        "Por favor, mostre as opções de imóveis disponíveis com base nas minhas preferências.",
        database,
        preferences,
    )
    st.session_state.chat_history.append({"role": "assistant", "content": initial_response})

# Exibe histórico do chat
for message in st.session_state.chat_history:
    with st.chat_message(message["role"], avatar="🤖" if message["role"] == "assistant" else "🤷"):
        st.write(message["content"])

# Input do usuário
user_query = st.chat_input("Digite sua mensagem...")
if user_query:
    # Adiciona mensagem do usuário ao histórico
    st.session_state.chat_history.append({"role": "human", "content": user_query})
    
    # Exibe mensagem do usuário
    with st.chat_message("human", avatar="🤷"):
        st.write(user_query)
    
    # Obtém e exibe resposta do bot
    with st.chat_message("assistant", avatar="🤖"):      
        bot_response = get_bot_response(user_query, database, preferences)
        st.write(bot_response)
            
    # Adiciona resposta do bot ao histórico
    st.session_state.chat_history.append({"role": "assistant", "content": bot_response})