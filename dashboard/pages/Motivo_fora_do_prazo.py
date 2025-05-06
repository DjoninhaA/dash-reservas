import streamlit as st
import pandas as pd
from datetime import datetime
import re

# Configuração da página
st.set_page_config(page_title="Motivo Fora do Prazo", layout="wide")

# Título do aplicativo
st.title("📅 Análise de Reservas Fora do Prazo")

def extract_days(situacao):
    # Extrai o número entre parênteses da situação
    match = re.search(r'\((\d+)\)', situacao)
    if match:
        return int(match.group(1))
    return 0

def check_time_limit(row):
    # Extrai o número entre parênteses da situação
    dias_limite = extract_days(row['situacao'])
    
    if dias_limite == 0:
        return False
        
    # Pega a data da última alteração
    data_ultima_alteracao = pd.to_datetime(row['data_ultima_alteracao_situacao'])
    
    # Calcula a diferença entre agora e a última alteração em dias
    dias_decorridos = (datetime.now() - data_ultima_alteracao).days
    
    # Verifica se o tempo desde a última alteração excede o limite
    return dias_decorridos >= dias_limite

# Carregando os dados
@st.cache_data
def load_data():
    reservas_df = pd.read_csv('reservas_abril.csv')
    
    # Converter colunas de data
    reservas_df['data_cad'] = pd.to_datetime(reservas_df['data_cad'])
    reservas_df['data_ultima_alteracao_situacao'] = pd.to_datetime(reservas_df['data_ultima_alteracao_situacao'])
    
    return reservas_df

reservas_df = load_data()

# Sidebar para filtros
st.sidebar.header("Filtros")

# Filtro de empreendimento
empreendimentos = sorted(reservas_df['empreendimento'].unique())
empreendimento_selecionado = st.sidebar.selectbox("Empreendimento", ["Todos"] + list(empreendimentos))

# Filtro de situação
situacoes = sorted(reservas_df['situacao'].unique())
situacao_selecionada = st.sidebar.selectbox("Situação", ["Todas"] + list(situacoes))

# Aplicar filtros
df_filtrado = reservas_df.copy()
if empreendimento_selecionado != "Todos":
    df_filtrado = df_filtrado[df_filtrado['empreendimento'] == empreendimento_selecionado]
if situacao_selecionada != "Todas":
    df_filtrado = df_filtrado[df_filtrado['situacao'] == situacao_selecionada]

# Remover reservas canceladas e vendidas
df_sem_canceladas_vendidas = df_filtrado[~df_filtrado['situacao'].isin(['Cancelada', 'Vendida'])]

# Verificar reservas fora do prazo
df_sem_canceladas_vendidas['fora_do_prazo'] = df_sem_canceladas_vendidas.apply(check_time_limit, axis=1)
df_sem_canceladas_vendidas['dias_na_situacao'] = (datetime.now() - df_sem_canceladas_vendidas['data_ultima_alteracao_situacao']).dt.days

# Métricas principais
col1, col2, col3 = st.columns(3)
with col1:
    total_fora_prazo = df_sem_canceladas_vendidas['fora_do_prazo'].sum()
    st.metric(label="Total Fora do Prazo", value=int(total_fora_prazo))
with col2:
    percentual_fora_prazo = (total_fora_prazo / len(df_sem_canceladas_vendidas)) * 100
    st.metric(label="Percentual Fora do Prazo", value=f"{percentual_fora_prazo:.1f}%")
with col3:
    valor_total_fora_prazo = df_sem_canceladas_vendidas[df_sem_canceladas_vendidas['fora_do_prazo']]['valor_contrato'].sum()
    st.metric(label="Valor Total Fora do Prazo", value=f"R$ {valor_total_fora_prazo:,.2f}")

# Análise por situação
st.subheader("Análise por Situação")
analise_situacao = df_sem_canceladas_vendidas[df_sem_canceladas_vendidas['fora_do_prazo']].groupby('situacao').agg({
    'idreserva': 'count',
    'dias_na_situacao': 'mean',
    'valor_contrato': 'sum'
}).reset_index()

analise_situacao.columns = ['Situação', 'Quantidade', 'Média de Dias', 'Valor Total']
analise_situacao['Média de Dias'] = analise_situacao['Média de Dias'].round(1)
analise_situacao['Valor Total'] = analise_situacao['Valor Total'].map('R$ {:,.2f}'.format)

st.table(analise_situacao)

# Lista detalhada de reservas fora do prazo
st.subheader("Lista de Reservas Fora do Prazo")
df_fora_prazo = df_sem_canceladas_vendidas[df_sem_canceladas_vendidas['fora_do_prazo']]
colunas_exibir = ['idreserva', 'cliente', 'empreendimento', 'situacao', 
                  'dias_na_situacao', 'valor_contrato', 'imobiliaria']

st.dataframe(df_fora_prazo[colunas_exibir], use_container_width=True)

# Gráfico de distribuição
st.subheader("Distribuição por Dias na Situação")
fig_data = df_fora_prazo.groupby('situacao')['dias_na_situacao'].mean().reset_index()
st.bar_chart(data=fig_data, x='situacao', y='dias_na_situacao')