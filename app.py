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

# ================== VEÍCULOS - CRUD ==================
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
        return jsonify({'message': 'Veículo cadastrado!'})
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
        return jsonify({'message': 'Veículo deletado!'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ================== CLIENTES - CRUD ==================
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
        return jsonify({'message': 'Cliente cadastrado!'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ================== LOCAÇÕES ==================
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
        
        cursor.execute("SELECT preco_diaria FROM veiculos WHERE id = %s AND disponivel = TRUE", (data['veiculo_id'],))
        veiculo = cursor.fetchone()
        
        if not veiculo:
            return jsonify({'error': 'Veículo não disponível'}), 400
        
        dias = (datetime.strptime(data['data_fim'], '%Y-%m-%d') - datetime.strptime(data['data_inicio'], '%Y-%m-%d')).days
        if dias <= 0: dias = 1
        valor_total = float(veiculo[1]) * dias
        
        cursor.execute('''
            INSERT INTO locacoes (cliente_id, veiculo_id, data_inicio, data_fim, valor_total, status)
            VALUES (%s, %s, %s, %s, %s, 'ativa')
        ''', (data['cliente_id'], data['veiculo_id'], data['data_inicio'], data['data_fim'], valor_total))
        
        cursor.execute("UPDATE veiculos SET disponivel = FALSE WHERE id = %s", (data['veiculo_id'],))
        
        conn.commit()
        cursor.close()
        conn.close()
        return jsonify({'message': 'Locação realizada!', 'valor_total': valor_total})
        
    except Exception as e:
        if conn:
            conn.rollback()
            cursor.close()
            conn.close()
        return jsonify({'error': str(e)}), 500

# ================== ROTAS PRINCIPAIS ==================
@app.route('/')
def index():
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Locadora - Sistema CRUD</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 40px; background: #f5f5f5; }
            .container { max-width: 1200px; margin: 0 auto; background: white; padding: 20px; border-radius: 10px; }
            .nav { background: #2c3e50; padding: 15px; border-radius: 5px; margin-bottom: 20px; }
            .nav button { background: #3498db; color: white; border: none; padding: 10px 20px; margin: 0 5px; cursor: pointer; border-radius: 5px; }
            .section { display: none; padding: 20px; border: 1px solid #ddd; border-radius: 5px; margin-bottom: 20px; }
            .active { display: block; }
            table { width: 100%; border-collapse: collapse; margin: 10px 0; }
            th, td { padding: 10px; border: 1px solid #ddd; text-align: left; }
            th { background: #f8f9fa; }
            form { display: grid; gap: 10px; max-width: 400px; margin: 10px 0; }
            input, button { padding: 8px; border: 1px solid #ddd; border-radius: 4px; }
            button { background: #27ae60; color: white; border: none; cursor: pointer; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🚗 Sistema de Locação - CRUD Completo</h1>
            
            <div class="nav">
                <button onclick="showSection('veiculos')">Veículos</button>
                <button onclick="showSection('clientes')">Clientes</button>
                <button onclick="showSection('locacoes')">Locações</button>
                <button onclick="showSection('nova-locacao')">Nova Locação</button>
            </div>

            <!-- Veículos -->
            <div id="veiculos" class="section active">
                <h2>Veículos</h2>
                <button onclick="carregarVeiculos()">Carregar Veículos</button>
                <div id="lista-veiculos"></div>
                
                <h3>Cadastrar Veículo</h3>
                <form onsubmit="criarVeiculo(event)">
                    <input type="text" id="marca" placeholder="Marca" required>
                    <input type="text" id="modelo" placeholder="Modelo" required>
                    <input type="number" id="ano" placeholder="Ano" required>
                    <input type="text" id="placa" placeholder="Placa" required>
                    <input type="text" id="cor" placeholder="Cor" required>
                    <input type="number" id="preco_diaria" placeholder="Preço Diária" step="0.01" required>
                    <button type="submit">Cadastrar Veículo</button>
                </form>
            </div>

            <!-- Clientes -->
            <div id="clientes" class="section">
                <h2>Clientes</h2>
                <button onclick="carregarClientes()">Carregar Clientes</button>
                <div id="lista-clientes"></div>
                
                <h3>Cadastrar Cliente</h3>
                <form onsubmit="criarCliente(event)">
                    <input type="text" id="nome" placeholder="Nome" required>
                    <input type="text" id="cpf" placeholder="CPF" required>
                    <input type="email" id="email" placeholder="Email" required>
                    <input type="text" id="telefone" placeholder="Telefone" required>
                    <button type="submit">Cadastrar Cliente</button>
                </form>
            </div>

            <!-- Locações -->
            <div id="locacoes" class="section">
                <h2>Locações</h2>
                <button onclick="carregarLocacoes()">Carregar Locações</button>
                <div id="lista-locacoes"></div>
            </div>

            <!-- Nova Locação -->
            <div id="nova-locacao" class="section">
                <h2>Nova Locação</h2>
                <form onsubmit="fazerLocacao(event)">
                    <select id="cliente_id" required>
                        <option value="">Selecione o cliente</option>
                    </select>
                    <select id="veiculo_id" required>
                        <option value="">Selecione o veículo</option>
                    </select>
                    <input type="date" id="data_inicio" required>
                    <input type="date" id="data_fim" required>
                    <button type="submit">Realizar Locação</button>
                </form>
            </div>
        </div>

        <script>
            function showSection(sectionId) {
                document.querySelectorAll('.section').forEach(s => s.classList.remove('active'));
                document.getElementById(sectionId).classList.add('active');
            }

            async function carregarVeiculos() {
                const response = await fetch('/api/veiculos');
                const veiculos = await response.json();
                document.getElementById('lista-veiculos').innerHTML = `
                    <table>
                        <tr><th>ID</th><th>Marca</th><th>Modelo</th><th>Ano</th><th>Placa</th><th>Cor</th><th>Preço</th><th>Ação</th></tr>
                        ${veiculos.map(v => `
                            <tr>
                                <td>${v.id}</td><td>${v.marca}</td><td>${v.modelo}</td><td>${v.ano}</td>
                                <td>${v.placa}</td><td>${v.cor}</td><td>R$ ${v.preco_diaria}</td>
                                <td><button onclick="deletarVeiculo(${v.id})">Deletar</button></td>
                            </tr>
                        `).join('')}
                    </table>
                `;
            }

            async function criarVeiculo(event) {
                event.preventDefault();
                const data = {
                    marca: document.getElementById('marca').value,
                    modelo: document.getElementById('modelo').value,
                    ano: document.getElementById('ano').value,
                    placa: document.getElementById('placa').value,
                    cor: document.getElementById('cor').value,
                    preco_diaria: document.getElementById('preco_diaria').value
                };
                
                await fetch('/api/veiculos', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify(data)
                });
                
                event.target.reset();
                carregarVeiculos();
                alert('Veículo cadastrado!');
            }

            async function deletarVeiculo(id) {
                await fetch(`/api/veiculos/${id}`, {method: 'DELETE'});
                carregarVeiculos();
                alert('Veículo deletado!');
            }

            async function carregarClientes() {
                const response = await fetch('/api/clientes');
                const clientes = await response.json();
                document.getElementById('lista-clientes').innerHTML = `
                    <table>
                        <tr><th>ID</th><th>Nome</th><th>CPF</th><th>Email</th><th>Telefone</th></tr>
                        ${clientes.map(c => `<tr><td>${c.id}</td><td>${c.nome}</td><td>${c.cpf}</td><td>${c.email}</td><td>${c.telefone}</td></tr>`).join('')}
                    </table>
                `;
            }

            async function criarCliente(event) {
                event.preventDefault();
                const data = {
                    nome: document.getElementById('nome').value,
                    cpf: document.getElementById('cpf').value,
                    email: document.getElementById('email').value,
                    telefone: document.getElementById('telefone').value
                };
                
                await fetch('/api/clientes', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify(data)
                });
                
                event.target.reset();
                carregarClientes();
                alert('Cliente cadastrado!');
            }

            async function carregarLocacoes() {
                const response = await fetch('/api/locacoes');
                const locacoes = await response.json();
                document.getElementById('lista-locacoes').innerHTML = `
                    <table>
                        <tr><th>ID</th><th>Cliente</th><th>Veículo</th><th>Início</th><th>Fim</th><th>Valor</th><th>Status</th></tr>
                        ${locacoes.map(l => `
                            <tr>
                                <td>${l.id}</td><td>${l.cliente_nome}</td><td>${l.marca} ${l.modelo}</td>
                                <td>${l.data_inicio}</td><td>${l.data_fim}</td><td>R$ ${l.valor_total}</td><td>${l.status}</td>
                            </tr>
                        `).join('')}
                    </table>
                `;
            }

            async function fazerLocacao(event) {
                event.preventDefault();
                const data = {
                    cliente_id: document.getElementById('cliente_id').value,
                    veiculo_id: document.getElementById('veiculo_id').value,
                    data_inicio: document.getElementById('data_inicio').value,
                    data_fim: document.getElementById('data_fim').value
                };
                
                const response = await fetch('/api/locacoes', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify(data)
                });
                
                const result = await response.json();
                alert(result.message || result.error);
                event.target.reset();
            }

            // Carregar dados iniciais
            carregarVeiculos();
        </script>
    </body>
    </html>
    """

@app.route('/health')
def health():
    return jsonify({'status': 'ok', 'message': 'Sistema CRUD funcionando!'})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)