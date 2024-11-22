import cx_Oracle
from flask import Flask, render_template, request, redirect, url_for, flash, g
import os

# Configuração do cliente Oracle
try:
    cx_Oracle.init_oracle_client()
    print("Oracle Client configurado corretamente!")
except cx_Oracle.DatabaseError as e:
    error, = e.args
    print(f"Erro ao configurar o Oracle Client: {error.message}")

# Configurações do Banco de Dados
DB_USER = 'RM554727'
DB_PASSWORD = '050706'
DB_HOST = 'oracle.fiap.com.br'
DB_PORT = '1521'
DB_SERVICE = 'ORCL'
dsn = cx_Oracle.makedsn(DB_HOST, DB_PORT, service_name=DB_SERVICE)

# Inicialização do Flask
app = Flask(__name__)
app.secret_key = os.urandom(24)  # Utilize uma chave secreta gerada aleatoriamente para segurança

# Gerenciador de Conexão
def conectar_bd():
    try:
        connection = cx_Oracle.connect(user=DB_USER, password=DB_PASSWORD, dsn=dsn)
        print("Conexão com o banco de dados bem-sucedida!")
        return connection
    except cx_Oracle.DatabaseError as e:
        error, = e.args
        print(f"Erro ao conectar ao banco de dados: {error.message}")
        return None

@app.before_request
def before_request():
    """Abre a conexão com o banco de dados antes de cada requisição."""
    g.db_connection = conectar_bd()

@app.teardown_request
def teardown_request(exception):
    """Fecha a conexão com o banco de dados após a requisição."""
    db_connection = getattr(g, 'db_connection', None)
    if db_connection is not None:
        db_connection.close()

# Função para executar consultas SQL
def executar_query(query, params=None, fetch=False):
    connection = g.db_connection
    if not connection:
        return None
    try:
        cursor = connection.cursor()
        cursor.execute(query, params or {})
        if fetch:
            result = cursor.fetchall()
            print(f"Resultados da query: {result}")  # Log para ver os dados
            return result
        connection.commit()
    except cx_Oracle.DatabaseError as e:
        error, = e.args
        print(f"Erro ao executar query: {error.message}")
        return None
    finally:
        cursor.close()

# Rota Principal
@app.route('/')
def index():
    return render_template("index.html")

# Consultar Eletrônicos
@app.route('/consultar_eletro', methods=['GET'])
def consultar_eletro():
    query = """
        SELECT id, marca, tipo, horas, cliente_id
        FROM eletronicos
    """
    eletrodomesticos = executar_query(query, fetch=True)
    print(f"Eletrônicos encontrados: {eletrodomesticos}")
    return render_template('consultar_eletro.html', eletrodomesticos=eletrodomesticos)


@app.route('/inserir_eletro', methods=['GET', 'POST'])
def inserir_eletro():
    if request.method == 'POST':
        cliente_id = request.form.get('cliente_id')
        nome = request.form.get('nome')
        marca = request.form.get('marca')
        hora = request.form.get('hora')
        # Verifica se todos os campos foram preenchidos
        if not (cliente_id and nome and marca and hora):
            flash("Todos os campos são obrigatórios.", "error")
            return redirect(url_for('inserir_eletro'))
        # Insere o novo eletrônico
        query_insert = """
            INSERT INTO eletronicos (cliente_id, tipo, marca, horas)
            VALUES (:1, :2, :3, :4)
        """
        success = executar_query(query_insert, (cliente_id, nome, marca, hora))
        return redirect(url_for('inserir_eletro'))
    
    # Carrega as marcas e tipos (opcionais para preencher em um formulário ou de consulta)
    return render_template("inserir_eletro.html")


# Alterar Eletrônico
@app.route('/alterar_eletro/<int:id>', methods=['GET', 'POST'])
def alterar_eletro(id):
    if request.method == 'POST':
        novo_nome = request.form.get('novo_nome')  # Novo nome (tipo do eletrônico)
        nova_marca = request.form.get('nova_marca')  # Nova marca
        novo_hora = request.form.get('novo_hora')  # Nova hora

        # Verificando se todos os campos foram preenchidos
        if not (novo_nome and nova_marca and novo_hora):
            flash("Todos os campos são obrigatórios.", "error")
            return redirect(url_for('alterar_eletro', id=id))  # Redireciona de volta caso falte campo

        # Atualizando os dados no banco de dados
        query = """
            UPDATE eletronicos
            SET tipo = :1, marca = :2, horas = :3
            WHERE id = :4
        """
        sucesso = executar_query(query, (novo_nome, nova_marca, novo_hora, id))

        if sucesso:
            flash("Eletrônico atualizado com sucesso!", "success")
        else:
            flash("Erro ao atualizar eletrônico.", "error")

        # Redireciona para a página de consulta de eletrônicos após a atualização
        return redirect(url_for('consultar_eletro'))

    # Quando a página é carregada via GET, busca os dados do eletrônico para preencher o formulário
    query = "SELECT id, tipo, marca, horas FROM eletronicos WHERE id = :1"
    eletro = executar_query(query, (id,), fetch=True)

    if eletro:
        return render_template('alterar_eletro.html', eletro=eletro[0])

    flash("Eletrônico não encontrado.", "error")
    return redirect(url_for('consultar_eletro'))

# Deletar Eletrônico
@app.route('/deletar_eletro/<int:id>', methods=['GET', 'POST'])
def deletar_eletro(id):
    # Deletando o eletrônico com o ID fornecido
    query = "DELETE FROM eletronicos WHERE id = :1"
    sucesso = executar_query(query, (id,))

    if sucesso:
        flash("Eletrônico deletado com sucesso!", "success")
    else:
        flash("Erro ao deletar eletrônico.", "error")

    # Redireciona de volta para a página de consulta de eletrônicos
    return redirect(url_for('consultar_eletro'))

# Inicialização do Flask
if __name__ == '__main__':
    app.run(debug=True)
