from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS
import mysql.connector
import os
from datetime import datetime

app = Flask(__name__)
CORS(app)

# Configuração do MySQL
db_config = {
    'host': os.environ.get('DB_HOST', 'server-bd-cn1.mysql.database.azure.com'),
    'user': os.environ.get('DB_USER', 'useradmin'),
    'password': os.environ.get('DB_PASSWORD', 'admin@123'),
    'database': os.environ.get('DB_NAME', 'locacao_automoveis'),
    'ssl_ca': 'DigiCertGlobalRootCA.crt.pem'
}

def get_db_connection():
    return mysql.connector.connect(**db_config)

# Criar tabelas
def criar_tabelas():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS veiculos (
            id INT AUTO_INCREMENT PRIMARY KEY,
            marca VARCHAR(50) NOT NULL,
            modelo VARCHAR(50) NOT NULL,
            ano INT NOT NULL,
            placa VARCHAR(10) UNIQUE NOT NULL,
            cor VARCHAR(30) NOT NULL,
            preco_diaria DECIMAL(10,2) NOT NULL,
            disponivel BOOLEAN DEFAULT TRUE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS clientes (
            id INT AUTO_INCREMENT PRIMARY KEY,
            nome VARCHAR(100) NOT NULL,
            cpf VARCHAR(14) UNIQUE NOT NULL,
            email VARCHAR(100) UNIQUE NOT NULL,
            telefone VARCHAR(15) NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS locacoes (
            id INT AUTO_INCREMENT PRIMARY KEY,
            cliente_id INT,
            veiculo_id INT,
            data_inicio DATETIME NOT NULL,
            data_fim DATETIME NOT NULL,
            valor_total DECIMAL(10,2) NOT NULL,
            status VARCHAR(20) DEFAULT 'ativa',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (cliente_id) REFERENCES clientes(id),
            FOREIGN KEY (veiculo_id) REFERENCES veiculos(id)
        )
    ''')
    
    # Inserir dados de exemplo
    cursor.execute("SELECT COUNT(*) FROM veiculos")
    if cursor.fetchone()[0] == 0:
        veiculos = [
            ('Toyota', 'Corolla', 2022, 'ABC-1234', 'Branco', 120.00),
            ('Honda', 'Civic', 2023, 'DEF-5678', 'Prata', 130.00),
            ('Volkswagen', 'Golf', 2021, 'GHI-9012', 'Preto', 110.00),
            ('Ford', 'Fiesta', 2022, 'JKL-3456', 'Azul', 90.00)
        ]
        cursor.executemany('''
            INSERT INTO veiculos (marca, modelo, ano, placa, cor, preco_diaria)
            VALUES (%s, %s, %s, %s, %s, %s)
        ''', veiculos)
    
    conn.commit()
    cursor.close()
    conn.close()

# Rotas da API
@app.route('/api/veiculos', methods=['GET'])
def listar_veiculos():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    cursor.execute("SELECT * FROM veiculos WHERE disponivel = TRUE")
    veiculos = cursor.fetchall()
    
    cursor.close()
    conn.close()
    return jsonify(veiculos)

@app.route('/api/veiculos', methods=['POST'])
def criar_veiculo():
    data = request.json
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute('''
            INSERT INTO veiculos (marca, modelo, ano, placa, cor, preco_diaria)
            VALUES (%s, %s, %s, %s, %s, %s)
        ''', (data['marca'], data['modelo'], data['ano'], data['placa'], data['cor'], data['preco_diaria']))
        
        conn.commit()
        return jsonify({'message': 'Veículo cadastrado com sucesso!'})
    except mysql.connector.Error as err:
        return jsonify({'error': str(err)}), 400
    finally:
        cursor.close()
        conn.close()

@app.route('/api/clientes', methods=['GET'])
def listar_clientes():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    cursor.execute("SELECT * FROM clientes")
    clientes = cursor.fetchall()
    
    cursor.close()
    conn.close()
    return jsonify(clientes)

@app.route('/api/clientes', methods=['POST'])
def criar_cliente():
    data = request.json
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute('''
            INSERT INTO clientes (nome, cpf, email, telefone)
            VALUES (%s, %s, %s, %s)
        ''', (data['nome'], data['cpf'], data['email'], data['telefone']))
        
        conn.commit()
        return jsonify({'message': 'Cliente cadastrado com sucesso!'})
    except mysql.connector.Error as err:
        return jsonify({'error': str(err)}), 400
    finally:
        cursor.close()
        conn.close()

@app.route('/api/locacoes', methods=['POST'])
def criar_locacao():
    data = request.json
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Calcular valor total
        cursor.execute("SELECT preco_diaria FROM veiculos WHERE id = %s", (data['veiculo_id'],))
        preco_diaria = cursor.fetchone()[0]
        
        data_inicio = datetime.strptime(data['data_inicio'], '%Y-%m-%d')
        data_fim = datetime.strptime(data['data_fim'], '%Y-%m-%d')
        dias = (data_fim - data_inicio).days
        valor_total = preco_diaria * dias
        
        # Criar locação
        cursor.execute('''
            INSERT INTO locacoes (cliente_id, veiculo_id, data_inicio, data_fim, valor_total)
            VALUES (%s, %s, %s, %s, %s)
        ''', (data['cliente_id'], data['veiculo_id'], data['data_inicio'], data['data_fim'], valor_total))
        
        # Marcar veículo como indisponível
        cursor.execute("UPDATE veiculos SET disponivel = FALSE WHERE id = %s", (data['veiculo_id'],))
        
        conn.commit()
        return jsonify({'message': 'Locação realizada com sucesso!'})
    except mysql.connector.Error as err:
        conn.rollback()
        return jsonify({'error': str(err)}), 400
    finally:
        cursor.close()
        conn.close()

# Servir arquivos estáticos
@app.route('/')
def index():
    return send_from_directory('.', 'index.html')

@app.route('/<path:path>')
def static_files(path):
    return send_from_directory('.', path)

if __name__ == '__main__':
    criar_tabelas()
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)