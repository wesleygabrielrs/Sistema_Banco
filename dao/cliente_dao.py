"""
ClienteDAO - Data Access Object para a tabela 'clientes'

Este arquivo implementa todas as operacoes de banco de dados
para a entidade Cliente. Cada metodo corresponde a uma operacao
CRUD (Create, Read, Update, Delete) no banco MySQL.

ANOTACOES IMPORTANTES:

1. DAO (Data Access Object): Padrao de projeto que separa
   a logica de negocio (classes Python) da logica de
   persistencia (banco de dados).

2. Seguranca: Sempre use PARAMETROS (%s) nas queries SQL
   para prevenir SQL Injection.

3. Transacoes: Use commit() para confirmar alteracoes e
   rollback() para desfazer em caso de erro.

4. Recursos: Sempre feche cursor e conexao no finally.
"""

import mysql.connector
from mysql.connector import Error
from modelos.cliente import Cliente  # Importa sua classe Cliente
from dao.database import Database    # Importa sua classe de conexao


class ClienteDAO:

    def __init__(self, db=None):
        """
        Inicializa o ClienteDAO com uma conexao ao banco.

        PARAMETROS:
        - db: Objeto Database (opcional)
              Se None, cria nova conexao.
              Se fornecido, usa conexao existente.

        POR QUE ISSO E IMPORTANTE:
        - Permite reutilizar conexoes entre DAOs
        - Evita multiplas conexoes desnecessarias
        - Melhora performance em operacoes em lote
        """
        if db is None:
            # Cria uma nova conexao especifica para este DAO
            self.db = Database()
            self.conn = self.db.connect()
            self.usar_conexao_externa = False
        else:
            # Reutiliza conexao existente (de outro DAO)
            self.db = db
            self.conn = db.connection
            self.usar_conexao_externa = True

    def create(self, cliente):
        """""
        EXEMPLO DE USO:
        >>> cliente = Cliente("Joao", "123.456.789-00", "1990-01-01")
        >>> dao = ClienteDAO()
        >>> id_gerado = dao.create(cliente)
        >>> print(f"Cliente criado com ID: {id_gerado}")
        """
        cursor = None
        try:
            # Cria um cursor para executar comandos SQL
            cursor = self.conn.cursor()

            # SQL para inserir cliente - NOTE os placeholders %s
            # NUNCA use concatenacao de strings direta (f"SQL {variavel}")
            sql = """
            INSERT INTO clientes
            (nome, cpf, data_nascimento, email, telefone, endereco)
            VALUES (%s, %s, %s, %s, %s, %s)
            """

            # Valores para substituir os placeholders %s
            # A ordem DEVE corresponder a ordem das colunas no SQL
            valores = (
                cliente.nome,
                cliente.cpf,
                cliente.data_nascimento,
                cliente.email,
                cliente.telefone,
                cliente.endereco
            )

            # Executa a query com os valores
            cursor.execute(sql, valores)

            # Confirma a transacao - sem commit(), nada e salvo
            self.conn.commit()

            # Pega o ID gerado automaticamente pelo AUTO_INCREMENT
            cliente.id = cursor.lastrowid

            print(f"[SUCESSO] Cliente '{cliente.nome}' criado com ID: {cliente.id}")
            return cliente.id

        except Error as e:
            # Em caso de erro, desfaz qualquer alteracao
            print(f"[ERRO] Erro ao criar cliente: {e}")
            self.conn.rollback()  # Desfaz a transacao
            return None
        finally:
            # SEMPRE feche o cursor, mesmo em caso de erro
            if cursor:
                cursor.close()

    def read(self, id):
        
        cursor = None
        try:
            # cursor(dictionary=True) faz cada linha vir como dicionario
            # Exemplo: {'id': 1, 'nome': 'Joao', 'cpf': '123...'}
            cursor = self.conn.cursor(dictionary=True)

            sql = "SELECT * FROM clientes WHERE id = %s"
            cursor.execute(sql, (id,))  # Tupla com um elemento precisa da virgula

            resultado = cursor.fetchone()

            if resultado:
                # Converte o dicionario do banco para objeto Cliente
                cliente = self._row_to_cliente(resultado)
                print(f"[SUCESSO] Cliente encontrado: {cliente.nome} (ID: {cliente.id})")
                return cliente
            else:
                print(f"[ATENCAO] Cliente com ID {id} nao encontrado")
                return None

        except Error as e:
            print(f"[ERRO] Erro ao buscar cliente: {e}")
            return None
        finally:
            if cursor:
                cursor.close()

    def update(self, cliente):
       
        cursor = None
        try:
            if cliente.id is None:
                print("[ERRO] Nao e possivel atualizar cliente sem ID")
                return False

            cursor = self.conn.cursor()

            sql = """
            UPDATE clientes
            SET nome = %s, cpf = %s, data_nascimento = %s,
                email = %s, telefone = %s, endereco = %s
            WHERE id = %s
            """

            valores = (
                cliente.nome,
                cliente.cpf,
                cliente.data_nascimento,
                cliente.email,
                cliente.telefone,
                cliente.endereco,
                cliente.id  # WHERE id = %s
            )

            cursor.execute(sql, valores)
            self.conn.commit()

            # rowcount diz quantas linhas foram afetadas
            atualizado = cursor.rowcount > 0

            if atualizado:
                print(f"[SUCESSO] Cliente ID {cliente.id} atualizado com sucesso")
            else:
                print(f"[ATENCAO] Nenhum cliente encontrado com ID {cliente.id}")

            return atualizado

        except Error as e:
            print(f"[ERRO] Erro ao atualizar cliente: {e}")
            self.conn.rollback()
            return False
        finally:
            if cursor:
                cursor.close()

    def delete(self, id):
        
        cursor = None
        try:
            cursor = self.conn.cursor()

            sql = "DELETE FROM clientes WHERE id = %s"
            cursor.execute(sql, (id,))
            self.conn.commit()

            removido = cursor.rowcount > 0

            if removido:
                print(f"[SUCESSO] Cliente ID {id} removido com sucesso")
            else:
                print(f"[ATENCAO] Nenhum cliente encontrado com ID {id}")

            return removido

        except Error as e:
            print(f"[ERRO] Erro ao deletar cliente: {e}")
            self.conn.rollback()
            return False
        finally:
            if cursor:
                cursor.close()

    def buscar_por_cpf(self, cpf):

        cursor = None
        try:
            cursor = self.conn.cursor(dictionary=True)

            sql = "SELECT * FROM clientes WHERE cpf = %s"
            cursor.execute(sql, (cpf,))

            resultado = cursor.fetchone()

            if resultado:
                cliente = self._row_to_cliente(resultado)
                print(f"[SUCESSO] Cliente encontrado por CPF: {cliente.nome}")
                return cliente
            else:
                print(f"[ATENCAO] Cliente com CPF {cpf} nao encontrado")
                return None

        except Error as e:
            print(f"[ERRO] Erro ao buscar por CPF: {e}")
            return None
        finally:
            if cursor:
                cursor.close()

    def listar_todos(self):
        """
        Retorna lista de todos os clientes cadastrados.

        RETORNO:
        - list: Lista de objetos Cliente
        - []: Lista vazia se nao houver clientes ou erro

        PERFORMANCE:
        - Use LIMIT em bancos grandes para nao trazer todos de uma vez
        - ORDER BY garante ordem consistente
        """
        cursor = None
        try:
            cursor = self.conn.cursor(dictionary=True)

            sql = "SELECT * FROM clientes ORDER BY nome"
            cursor.execute(sql)

            resultados = cursor.fetchall()

            # Converte cada linha para objeto Cliente
            clientes = []
            for row in resultados:
                clientes.append(self._row_to_cliente(row))

            print(f"[SUCESSO] Listados {len(clientes)} clientes")
            return clientes

        except Error as e:
            print(f"[ERRO] Erro ao listar clientes: {e}")
            return []
        finally:
            if cursor:
                cursor.close()

    def _row_to_cliente(self, row):
        """
        Converte uma linha do banco (dicionario) para objeto Cliente.

        PARAMETROS:
        - row: Dicionario com dados do banco

        RETORNO:
        - Cliente: Objeto Cliente populado

        NOTA:
        - Metodo privado (comeca com _) - usado apenas internamente
        - Isola logica de conversao em um unico lugar
        - Facilita manutencao se estrutura da tabela mudar
        """
        return Cliente(
            id=row['id'],
            nome=row['nome'],
            cpf=row['cpf'],
            data_nascimento=row['data_nascimento'],
            email=row['email'],
            telefone=row['telefone'],
            endereco=row['endereco'],
            data_cadastro=row['data_cadastro']
        )

    def close(self):
        """
        Fecha a conexao com o banco de dados.

        IMPORTANTE:
        - So fecha se a conexao foi criada internamente
        - Se recebeu conexao externa, nao fecha (outro DAO cuida)
        """
        if not self.usar_conexao_externa and self.db:
            self.db.disconnect()
            print("[CONEXAO] Conexao do ClienteDAO fechada")


# Exemplo de uso (remova em producao):
if __name__ == "__main__":
    """
    Teste basico do ClienteDAO.
    Execute: python dao/cliente_dao.py
    """
    print(" TESTE DO CLIENTEDAO")
    print("=" * 50)

    try:
        dao = ClienteDAO()

        # Teste 1: Criar cliente
        print("\n1. Criando cliente de teste...")
        cliente_teste = Cliente(
            nome="Joao Silva",
            cpf="123.456.789-00",
            data_nascimento="1990-05-15",
            email="joao@email.com",
            telefone="(11) 99999-8888",
            endereco="Rua das Flores, 123"
        )

        id_gerado = dao.create(cliente_teste)

        # Teste 2: Buscar por ID
        if id_gerado:
            print("\n2. Buscando cliente criado...")
            cliente_buscado = dao.read(id_gerado)
            if cliente_buscado:
                print(f"   Nome: {cliente_buscado.nome}")
                print(f"   Email: {cliente_buscado.email}")

        # Teste 3: Buscar por CPF
        print("\n3. Buscando por CPF...")
        cliente_cpf = dao.buscar_por_cpf("123.456.789-00")
        if cliente_cpf:
            print(f"   Encontrado: {cliente_cpf.nome}")

        # Teste 4: Listar todos
        print("\n4. Listando todos os clientes...")
        todos = dao.listar_todos()
        for c in todos:
            print(f"    {c.id}: {c.nome} ({c.cpf})")

        # Teste 5: Atualizar
        print("\n5. Atualizando cliente...")
        if cliente_buscado:
            cliente_buscado.email = "joao.novo@email.com"
            sucesso = dao.update(cliente_buscado)
            print(f"   Atualizacao: {'Sucesso' if sucesso else 'Falha'}")

        # Teste 6: Deletar (opcional - comente se quiser manter dados)
        # print("\n6. Deletando cliente...")
        # if id_gerado:
        #     sucesso = dao.delete(id_gerado)
        #     print(f"   Delecao: {'Sucesso' if sucesso else 'Falha'}")

    finally:
        # Garante que conexao sera fechada
        dao.close()

    print("\n" + "=" * 50)
    print("[SUCESSO] Teste concluido!")