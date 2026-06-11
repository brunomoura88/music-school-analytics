import sqlite3
import random
from datetime import datetime, timedelta
from faker import Faker

fake = Faker('pt_BR')  # Gerador de dados em português
conn = sqlite3.connect('escola_bi_teste.db')
cursor = conn.cursor()

# 1. Criar tabelas de teste
cursor.execute('''
CREATE TABLE IF NOT EXISTS alunos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nome TEXT,
    data_matricula TEXT,
    status TEXT, -- 'Ativo' ou 'Cancelado'
    data_cancelamento TEXT
)''')

cursor.execute('''
CREATE TABLE IF NOT EXISTS mensalidades (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    aluno_id INTEGER,
    competencia TEXT, -- Ex: '2026-01'
    valor REAL,
    status_pagamento TEXT, -- 'Pago' ou 'Atrasado'
    FOREIGN KEY(aluno_id) REFERENCES alunos(id)
)''')

# 2. Gerar dados simulados (Histórico de 2025 até meados de 2026)
status_opcoes = ['Ativo', 'Cancelado']
pagamento_opcoes = ['Pago', 'Atrasado']

print("Gerando dados fictícios para o BI...")

for _ in range(150):  # Simulando 150 alunos históricos
    # Data de matrícula aleatória em 2025
    dias_atras = random.randint(180, 500)
    data_mat = datetime.now() - timedelta(days=dias_atras)
    data_mat_str = data_mat.strftime('%Y-%m-%d')
    
    # Define se o aluno continua ativo ou se cancelou
    status = random.choices(status_opcoes, weights=[75, 25])[0] # 25% de taxa de cancelamento histórica
    data_canc_str = None
    
    if status == 'Cancelado':
        # Cancelou em algum momento após a matrícula
        dias_ate_cancelar = random.randint(30, 150)
        data_canc = data_mat + timedelta(days=dias_ate_cancelar)
        data_canc_str = data_canc.strftime('%Y-%m-%d')
        
    # Inserir Aluno
    cursor.execute("INSERT INTO alunos (nome, data_matricula, status, data_cancelamento) VALUES (?, ?, ?, ?)",
                   (fake.name(), data_mat_str, status, data_canc_str))
    aluno_id = cursor.lastrowid
    
    # Gerar mensalidades para esse aluno do início da matrícula até hoje (ou até o cancelamento)
    data_corrente = data_mat
    fim_periodo = data_canc if status == 'Cancelado' else datetime.now()
    
    while data_corrente <= fim_periodo:
        competencia = data_corrente.strftime('%Y-%m')
        # Alunos ativos pagam mais em dia, cancelados costumam ter deixado pendências
        pesos_pagam = [90, 10] if status == 'Ativo' else [40, 60]
        status_pag = random.choices(pagamento_opcoes, weights=pesos_pagam)[0]
        
        cursor.execute("INSERT INTO mensalidades (aluno_id, competencia, valor, status_pagamento) VALUES (?, ?, ?, ?)",
                       (aluno_id, competencia, 180.00, status_pag))
        
        # Avança para o próximo mês
        data_corrente += timedelta(days=30)

conn.commit()
conn.close()
print("Banco de dados 'escola_bi_teste.db' gerado com sucesso!")