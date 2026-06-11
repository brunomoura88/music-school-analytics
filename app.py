import streamlit as st
import pandas as pd
import sqlite3
import plotly.express as px

# Configuração da página do Streamlit
st.set_page_config(page_title="Music School Analytics", layout="wide")

st.title("🎵 Music School Analytics — Painel de BI")
st.markdown("Bem-vindo ao painel de inteligência de negócios. Aqui analisamos a saúde financeira e a evasão de alunos.")

# 🛠️ Função para carregar os dados do SQLite
def carregar_dados():
    conn = sqlite3.connect('escola_bi_teste.db')
    
    # Pandas lê diretamente as tabelas do banco e transforma em DataFrames
    df_alunos = pd.read_sql_query("SELECT * FROM alunos", conn)
    df_mensalidades = pd.read_sql_query("SELECT * FROM mensalidades", conn)
    
    conn.close()
    return df_alunos, df_mensalidades

# Executando a função de carga
df_alunos, df_mensalidades = carregar_dados()

# --- MIGRANDO CONCEITOS DE BI: OS CARDS DE MÉTRICAS (KPIs) ---
st.header("📊 Indicadores Chave de Performance (KPIs)")

# Criando colunas no Streamlit para colocar os cards lado a lado
col1, col2, col3 = st.columns(3)

with col1:
    # 1. Total de Alunos Históricos
    total_alunos = len(df_alunos)
    st.metric(label="Alunos Cadastrados (Histórico)", value=total_alunos)

with col2:
    # 2. Alunos Ativos Atualmente
    # Aqui filtramos o DataFrame usando Pandas (equivalente ao WHERE do SQL)
    alunos_ativos = len(df_alunos[df_alunos['status'] == 'Ativo'])
    st.metric(label="Alunos Ativos Atualmente", value=alunos_ativos, delta=f"{alunos_ativos/total_alunos:.1%} do total")

with col3:
    # 3. Faturamento Total Acumulado
    faturamento_total = df_mensalidades[df_mensalidades['status_pagamento'] == 'Pago']['valor'].sum()
    st.metric(label="Receita Total Arrecadada", value=f"R$ {faturamento_total:,.2f}")

st.markdown("---")

# --- SEÇÃO 2: GRÁFICOS INTERATIVOS ---
st.header("📈 Análise de Crescimento e Saúde do Negócio")

# Criando duas colunas para colocar os gráficos lado a lado
grafico_col1, grafico_col2 = st.columns(2)

with grafico_col1:
    st.subheader("Faturamento Mensal (Receita Real)")
    
    # 1. Tratamento de Dados com Pandas: Filtrando apenas o que foi PAGO
    df_pagos = df_mensalidades[df_mensalidades['status_pagamento'] == 'Pago']
    
    # Agrupando por competência (ano-mês) e somando os valores
    faturamento_por_mes = df_pagos.groupby('competencia')['valor'].sum().reset_index()
    
    # Ordenando cronologicamente para o gráfico fazer sentido
    faturamento_por_mes = faturamento_por_mes.sort_values('competencia')
    
    # Criando o gráfico de linhas interativo com o Plotly
    fig_financeiro = px.line(
        faturamento_por_mes, 
        x='competencia', 
        y='valor',
        labels={'competencia': 'Mês/Ano', 'valor': 'Faturamento (R$)'},
        markers=True, # Adiciona pontinhos na linha
        color_discrete_sequence=['#B38F00'] # Tom dourado/ouro
    )
    
    # Renderizando o gráfico do Plotly dentro do Streamlit
    st.plotly_chart(fig_financeiro, use_container_width=True)


with grafico_col2:
    st.subheader("Volume de Cancelamentos (Churn Histórico)")
    
    # 1. Filtrando apenas alunos que cancelaram
    df_cancelados = df_alunos[df_alunos['status'] == 'Cancelado'].copy()
    
    # Convertendo a string da data para o formato de data do Pandas (datetime)
    df_cancelados['data_cancelamento'] = pd.to_datetime(df_cancelados['data_cancelamento'])
    
    # Criando uma nova coluna apenas com o Ano-Mês para podermos agrupar
    df_cancelados['mes_cancelamento'] = df_cancelados['data_cancelamento'].dt.to_period('M').astype(str)
    
    # Agrupando para contar quantos alunos saíram por mês
    churn_por_mes = df_cancelados.groupby('mes_cancelamento').size().reset_index(name='quantidade')
    churn_por_mes = churn_por_mes.sort_values('mes_cancelamento')
    
    # Criando o gráfico de barras interativo com o Plotly
    fig_churn = px.bar(
        churn_por_mes,
        x='mes_cancelamento',
        y='quantidade',
        labels={'mes_cancelamento': 'Mês/Ano', 'quantidade': 'Alunos Perdidos'},
        color_discrete_sequence=['#8B0000'] # Tom de bordô/vermelho escuro
    )
    
    st.plotly_chart(fig_churn, use_container_width=True)

st.markdown("---")

# --- SEÇÃO 3: AUDITORIA E COBRANÇA (TABELA INTERATIVA) ---
st.header("🚨 Painel de Inadimplência e Cobrança")
st.markdown("Abaixo estão listados todos os lançamentos em atraso no sistema. Use a tabela para buscar por nome ou ordenar pelos maiores valores.")

# 1. Cruzando os dados com Pandas (Equivalente ao INNER JOIN do SQL)
# Vamos juntar a tabela de mensalidades com a de alunos usando o 'aluno_id' / 'id'
df_inadimplencia = df_mensalidades[df_mensalidades['status_pagamento'] == 'Atrasado'].copy()

# O merge faz o papel do JOIN do SQL
df_relatorio_atraso = pd.merge(
    df_inadimplencia, 
    df_alunos, 
    left_on='aluno_id', 
    right_on='id', 
    how='inner'
)

# 2. Selecionando e renomeando apenas as colunas que importam para o usuário
df_relatorio_atraso = df_relatorio_atraso[['nome', 'competencia', 'valor', 'status']]
df_relatorio_atraso.columns = ['Nome do Aluno', 'Mês de Atraso', 'Valor Pendente (R$)', 'Status da Matrícula']

# 3. Exibindo métricas rápidas de inadimplência antes da tabela
total_devedores = df_relatorio_atraso['Nome do Aluno'].nunique()
valor_total_atraso = df_relatorio_atraso['Valor Pendente (R$)'].sum()

col_inf1, col_inf2 = st.columns(2)
with col_inf1:
    st.warning(f"**Total de Alunos Únicos com Pendência:** {total_devedores}")
with col_inf2:
    st.error(f"**Montante Total em Atraso:** R$ {valor_total_atraso:,.2f}")

# 4. Renderizando a tabela interativa do Streamlit (st.dataframe)
# Ela permite que o usuário ordene clicando no topo da coluna, dê dois cliques para ampliar, etc.
st.dataframe(df_relatorio_atraso, use_container_width=True, hide_index=True)

st.success("🎯 Prontinho! Painel de BI completo e atualizado em tempo real.")