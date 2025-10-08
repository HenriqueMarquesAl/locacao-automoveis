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
    'database': os.environ.get('DB_NAME', 'locacao_automoveis')
}

def get_db_connection():
    return mysql.connector.connect(**db_config)

# ================== VEÍCULOS - CRUD COMPLETO ==================
@app.route('/api/veiculos', methods=['GET'])
def listar_veiculos():
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM veiculos")
        veiculos = cursor.fetchall()
        
        for veiculo in veiculos:
            if 'preco_diaria' in veiculo:
                veiculo['preco_diaria'] = float(veiculo['preco_diaria'])
        
        cursor.close()
        conn.close()
        return jsonify(veiculos)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/veiculos', methods=['POST'])
def criar_veiculo():
    try:
        data = request.json
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO veiculos (marca, modelo, ano, placa, cor, preco_diaria, disponivel)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        ''', (data['marca'], data['modelo'], data['ano'], data['placa'], data['cor'], data['preco_diaria'], True))
        
        conn.commit()
        cursor.close()
        conn.close()
        return jsonify({'message': 'Veículo cadastrado com sucesso!'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/veiculos/<int:id>', methods=['PUT'])
def atualizar_veiculo(id):
    try:
        data = request.json
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE veiculos 
            SET marca=%s, modelo=%s, ano=%s, placa=%s, cor=%s, preco_diaria=%s, disponivel=%s
            WHERE id=%s
        ''', (data['marca'], data['modelo'], data['ano'], data['placa'], data['cor'], data['preco_diaria'], data['disponivel'], id))
        
        conn.commit()
        cursor.close()
        conn.close()
        return jsonify({'message': 'Veículo atualizado com sucesso!'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/veiculos/<int:id>', methods=['DELETE'])
def deletar_veiculo(id):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("DELETE FROM veiculos WHERE id = %s", (id,))
        conn.commit()
        cursor.close()
        conn.close()
        return jsonify({'message': 'Veículo deletado com sucesso!'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ================== CLIENTES - CRUD COMPLETO ==================
@app.route('/api/clientes', methods=['GET'])
def listar_clientes():
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM clientes")
        clientes = cursor.fetchall()
        cursor.close()
        conn.close()
        return jsonify(clientes)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/clientes', methods=['POST'])
def criar_cliente():
    try:
        data = request.json
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO clientes (nome, cpf, email, telefone)
            VALUES (%s, %s, %s, %s)
        ''', (data['nome'], data['cpf'], data['email'], data['telefone']))
        
        conn.commit()
        cursor.close()
        conn.close()
        return jsonify({'message': 'Cliente cadastrado com sucesso!'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/clientes/<int:id>', methods=['PUT'])
def atualizar_cliente(id):
    try:
        data = request.json
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE clientes 
            SET nome=%s, cpf=%s, email=%s, telefone=%s
            WHERE id=%s
        ''', (data['nome'], data['cpf'], data['email'], data['telefone'], id))
        
        conn.commit()
        cursor.close()
        conn.close()
        return jsonify({'message': 'Cliente atualizado com sucesso!'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/clientes/<int:id>', methods=['DELETE'])
def deletar_cliente(id):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("DELETE FROM clientes WHERE id = %s", (id,))
        conn.commit()
        cursor.close()
        conn.close()
        return jsonify({'message': 'Cliente deletado com sucesso!'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ================== LOCAÇÕES - CRUD COMPLETO ==================
@app.route('/api/locacoes', methods=['GET'])
def listar_locacoes():
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        cursor.execute('''
            SELECT l.*, c.nome as cliente_nome, v.marca, v.modelo 
            FROM locacoes l
            JOIN clientes c ON l.cliente_id = c.id
            JOIN veiculos v ON l.veiculo_id = v.id
            ORDER BY l.created_at DESC
        ''')
        
        locacoes = cursor.fetchall()
        
        for locacao in locacoes:
            if 'valor_total' in locacao:
                locacao['valor_total'] = float(locacao['valor_total'])
        
        cursor.close()
        conn.close()
        return jsonify(locacoes)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/locacoes', methods=['POST'])
def criar_locacao():
    try:
        data = request.json
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Verificar veículo
        cursor.execute("SELECT id, preco_diaria FROM veiculos WHERE id = %s AND disponivel = TRUE", (data['veiculo_id'],))
        veiculo = cursor.fetchone()
        
        if not veiculo:
            return jsonify({'error': 'Veículo não encontrado ou indisponível'}), 400
        
        # Verificar cliente
        cursor.execute("SELECT id FROM clientes WHERE id = %s", (data['cliente_id'],))
        if not cursor.fetchone():
            return jsonify({'error': 'Cliente não encontrado'}), 400
        
        # Calcular valor
        dias = (datetime.strptime(data['data_fim'], '%Y-%m-%d') - datetime.strptime(data['data_inicio'], '%Y-%m-%d')).days
        if dias <= 0: dias = 1
        valor_total = float(veiculo[1]) * dias
        
        # Inserir locação
        cursor.execute('''
            INSERT INTO locacoes (cliente_id, veiculo_id, data_inicio, data_fim, valor_total, status)
            VALUES (%s, %s, %s, %s, %s, 'ativa')
        ''', (data['cliente_id'], data['veiculo_id'], data['data_inicio'], data['data_fim'], valor_total))
        
        # Atualizar veículo
        cursor.execute("UPDATE veiculos SET disponivel = FALSE WHERE id = %s", (data['veiculo_id'],))
        
        conn.commit()
        cursor.close()
        conn.close()
        
        return jsonify({'message': 'Locação realizada com sucesso!', 'valor_total': valor_total})
        
    except Exception as e:
        if conn:
            conn.rollback()
            cursor.close()
            conn.close()
        return jsonify({'error': str(e)}), 500

@app.route('/api/locacoes/<int:id>/finalizar', methods=['POST'])
def finalizar_locacao(id):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Obter veículo_id da locação
        cursor.execute("SELECT veiculo_id FROM locacoes WHERE id = %s", (id,))
        result = cursor.fetchone()
        
        if not result:
            return jsonify({'error': 'Locação não encontrada'}), 404
        
        veiculo_id = result[0]
        
        # Finalizar locação
        cursor.execute("UPDATE locacoes SET status = 'finalizada' WHERE id = %s", (id,))
        
        # Liberar veículo
        cursor.execute("UPDATE veiculos SET disponivel = TRUE WHERE id = %s", (veiculo_id,))
        
        conn.commit()
        cursor.close()
        conn.close()
        
        return jsonify({'message': 'Locação finalizada com sucesso!'})
        
    except Exception as e:
        if conn:
            conn.rollback()
            cursor.close()
            conn.close()
        return jsonify({'error': str(e)}), 500

# Rota principal
@app.route('/')
def index():
    return send_from_directory('.', 'index.html')

@app.route('/health')
def health():
    return jsonify({'status': 'ok', 'message': 'API CRUD funcionando!'})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)