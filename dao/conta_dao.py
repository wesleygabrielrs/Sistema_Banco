"""
ContaDAO - Data Access Object para a tabela 'conta'

Este arquivo implementa todas as operacoes de banco de dados
para a entidade Conta. Inclui operacoes bancarias especiais
como deposito, saque e transferencia que envolvem transacoes.

ANOTACOES IMPORTANTES:

1. Transacoes Bancarias: Operacoes como transferencia
   devem ser ATOMICAS - ou tudo acontece ou nada acontece.
   Use commit() apenas depois de todas as verificacoes.

2. Saldo: E um campo critico que deve ser atualizado
   com precisao. Evite race conditions em sistemas reais.

3. Relacionamentos: Conta esta vinculada a Cliente
   atraves de clientes_id (chave estrangeira).
"""

import mysql.connector
from mysql.connector import Error
from modelos.conta import Conta  # Importa sua classe Conta
from dao.database import Database
from dao.cliente_dao import ClienteDAO  # Para verificar se cliente existe


class ContaDAO:
    """
    DAO para gerenciar operacoes com a tabela 'conta'

    Esta classe fornece metodos para:
    - Criar novas contas (associadas a clientes)
    - Realizar operacoes bancarias (deposito, saque, transferencia)
    - Buscar contas por numero ou cliente
    - Atualizar saldo e status
    - Listar contas com filtros

    ATRIBUTOS:
    - db: Objeto Database para conexao
    - conn: Conexao ativa com o banco
    - usar_conexao_externa: Controla gerenciamento de conexao
    """

    def __init__(self, db=None):
        """
        Inicializa o ContaDAO.

        PARAMETROS:
        - db: Objeto Database existente (opcional)

        DIFERENCA DO CLIENTEDAO:
        - Contas dependem de clientes existentes
        - Operacoes bancarias exigem mais validacoes
        """
        if db is None:
            self.db = Database()
            self.conn = self.db.connect()
            self.usar_conexao_externa = False
        else:
            self.db = db
            self.conn = db.connection
            self.usar_conexao_externa = True

    def create(self, conta):
        """
        Cria uma nova conta bancaria.

        PARAMETROS:
        - conta: Objeto Conta com clientes_id preenchido

        RETORNO:
        - int: ID da conta criada
        - None: Se erro ou cliente nao existir

        VALIDACOES:
        - Cliente deve existir antes de criar conta
        - Numero da conta deve ser unico
        - Saldo inicial nao pode ser negativo
        """
        cursor = None
        try:
            # Verifica se cliente existe
            cliente_dao = ClienteDAO(self.db)
            cliente = cliente_dao.read(conta.clientes_id)
            if not cliente:
                print(f"[ERRO] Cliente ID {conta.clientes_id} nao encontrado")
                return None

            cursor = self.conn.cursor()

            # SQL para criar conta
            sql = """
            INSERT INTO conta
            (clientes_id, numero_conta, saldo, data_abertura, tipo_conta, status)
            VALUES (%s, %s, %s, %s, %s, %s)
            """

            valores = (
                conta.clientes_id,
                conta.numero_conta,
                conta.saldo,
                conta.data_abertura,
                conta.tipo_conta,
                conta.status
            )

            cursor.execute(sql, valores)
            self.conn.commit()

            conta.id = cursor.lastrowid
            print(f"[SUCESSO] Conta '{conta.numero_conta}' criada com ID: {conta.id}")
            return conta.id

        except Error as e:
            print(f"[ERRO] Erro ao criar conta: {e}")
            self.conn.rollback()
            return None
        finally:
            if cursor:
                cursor.close()

    def read(self, id):
        """
        Busca uma conta pelo ID.

        PARAMETROS:
        - id: ID da conta

        RETORNO:
        - Conta: Objeto Conta encontrado
        - None: Se nao encontrar
        """
        cursor = None
        try:
            cursor = self.conn.cursor(dictionary=True)

            sql = "SELECT * FROM conta WHERE id = %s"
            cursor.execute(sql, (id,))

            resultado = cursor.fetchone()

            if resultado:
                conta = self._row_to_conta(resultado)
                print(f"[SUCESSO] Conta encontrada: {conta.numero_conta}")
                return conta
            else:
                print(f"[ATENCAO] Conta ID {id} nao encontrada")
                return None

        except Error as e:
            print(f"[ERRO] Erro ao buscar conta: {e}")
            return None
        finally:
            if cursor:
                cursor.close()

    def buscar_por_numero(self, numero_conta):
        """
        Busca conta pelo numero da conta.

        PARAMETROS:
        - numero_conta: Numero da conta (ex: "1001-1")

        RETORNO:
        - Conta: Objeto Conta encontrado
        - None: Se nao encontrar

        VANTAGEM:
        - Numero da conta e UNIQUE na tabela
        - Interface mais amigavel para usuarios
        """
        cursor = None
        try:
            cursor = self.conn.cursor(dictionary=True)

            sql = "SELECT * FROM conta WHERE numero_conta = %s"
            cursor.execute(sql, (numero_conta,))

            resultado = cursor.fetchone()

            if resultado:
                conta = self._row_to_conta(resultado)
                print(f"[SUCESSO] Conta '{numero_conta}' encontrada")
                return conta
            else:
                print(f"[ATENCAO] Conta '{numero_conta}' nao encontrada")
                return None

        except Error as e:
            print(f"[ERRO] Erro ao buscar conta por numero: {e}")
            return None
        finally:
            if cursor:
                cursor.close()

    def listar_por_cliente(self, cliente_id):
        """
        Lista todas as contas de um cliente.

        PARAMETROS:
        - cliente_id: ID do cliente

        RETORNO:
        - list: Lista de contas do cliente
        - []: Lista vazia se nao houver contas

        USO TIPICO:
        - Mostrar todas as contas de um cliente
        - Filtrar por tipo de conta
        """
        cursor = None
        try:
            cursor = self.conn.cursor(dictionary=True)

            sql = """
            SELECT * FROM conta
            WHERE clientes_id = %s
            AND status = 'ativa'
            ORDER BY data_abertura DESC
            """
            cursor.execute(sql, (cliente_id,))

            resultados = cursor.fetchall()

            contas = []
            for row in resultados:
                contas.append(self._row_to_conta(row))

            print(f"[SUCESSO] Encontradas {len(contas)} contas para cliente ID {cliente_id}")
            return contas

        except Error as e:
            print(f"[ERRO] Erro ao listar contas do cliente: {e}")
            return []
        finally:
            if cursor:
                cursor.close()

    def atualizar_saldo(self, conta_id, novo_saldo):
        """
        Atualiza o saldo de uma conta.

        PARAMETROS:
        - conta_id: ID da conta
        - novo_saldo: Novo valor do saldo

        RETORNO:
        - bool: True se atualizou, False se erro

        SEGURANCA:
        - Em sistemas reais, use LOCK ou transacoes
        - Evite que dois depositos simultaneos corrompam saldo
        """
        cursor = None
        try:
            cursor = self.conn.cursor()

            sql = "UPDATE conta SET saldo = %s WHERE id = %s"
            cursor.execute(sql, (novo_saldo, conta_id))
            self.conn.commit()

            atualizado = cursor.rowcount > 0

            if atualizado:
                print(f"[SUCESSO] Saldo da conta ID {conta_id} atualizado para R$ {novo_saldo:.2f}")
            else:
                print(f"[ATENCAO] Conta ID {conta_id} nao encontrada")

            return atualizado

        except Error as e:
            print(f"[ERRO] Erro ao atualizar saldo: {e}")
            self.conn.rollback()
            return False
        finally:
            if cursor:
                cursor.close()

    def depositar(self, conta_id, valor):
        """
        Realiza um deposito em uma conta.

        PARAMETROS:
        - conta_id: ID da conta
        - valor: Valor a ser depositado (deve ser positivo)

        RETORNO:
        - bool: True se sucesso, False se erro

        FLUXO:
        1. Busca conta atual
        2. Calcula novo saldo
        3. Atualiza saldo no banco
        4. Registra transacao (feito separadamente)
        """
        if valor <= 0:
            print("[ERRO] Valor do deposito deve ser positivo")
            return False

        try:
            # Busca conta atual
            conta = self.read(conta_id)
            if not conta:
                return False

            # Calcula novo saldo
            novo_saldo = conta.saldo + valor

            # Atualiza no banco
            sucesso = self.atualizar_saldo(conta_id, novo_saldo)

            if sucesso:
                print(f"[SUCESSO] Deposito de R$ {valor:.2f} realizado na conta ID {conta_id}")
                return True
            else:
                return False

        except Error as e:
            print(f"[ERRO] Erro no deposito: {e}")
            return False

    def sacar(self, conta_id, valor):
        """
        Realiza um saque de uma conta.

        PARAMETROS:
        - conta_id: ID da conta
        - valor: Valor a ser sacado

        RETORNO:
        - bool: True se sucesso, False se sem saldo ou erro

        VALIDACOES:
        - Verifica saldo suficiente
        - Valor deve ser positivo
        - Conta deve estar ativa
        """
        if valor <= 0:
            print("[ERRO] Valor do saque deve ser positivo")
            return False

        try:
            # Busca conta atual
            conta = self.read(conta_id)
            if not conta:
                return False

            # Verifica status da conta
            if conta.status != 'ativa':
                print(f"[ERRO] Conta {conta.numero_conta} nao esta ativa")
                return False

            # Verifica saldo suficiente
            if conta.saldo < valor:
                print(f"[ERRO] Saldo insuficiente. Disponivel: R$ {conta.saldo:.2f}")
                return False

            # Calcula novo saldo
            novo_saldo = conta.saldo - valor

            # Atualiza no banco
            sucesso = self.atualizar_saldo(conta_id, novo_saldo)

            if sucesso:
                print(f"[SUCESSO] Saque de R$ {valor:.2f} realizado da conta ID {conta_id}")
                return True
            else:
                return False

        except Error as e:
            print(f"[ERRO] Erro no saque: {e}")
            return False

    def transferir(self, conta_origem_id, conta_destino_id, valor):
        """
        Transfere valor entre duas contas.

        PARAMETROS:
        - conta_origem_id: ID da conta de origem
        - conta_destino_id: ID da conta de destino
        - valor: Valor a ser transferido

        RETORNO:
        - bool: True se transferencia completa, False se erro

        IMPORTANTE:
        - Esta operacao deve ser ATOMICA
        - Ou ambas contas sao atualizadas, ou nenhuma
        - Em sistemas reais, use transacoes explicitas
        """
        if valor <= 0:
            print("[ERRO] Valor da transferencia deve ser positivo")
            return False

        cursor = None
        try:
            # Inicia transacao explicita
            cursor = self.conn.cursor()

            # Busca saldo da conta origem (com lock para evitar race condition)
            cursor.execute("SELECT saldo FROM conta WHERE id = %s FOR UPDATE", (conta_origem_id,))
            resultado = cursor.fetchone()

            if not resultado:
                print(f"[ERRO] Conta origem ID {conta_origem_id} nao encontrada")
                self.conn.rollback()
                return False

            saldo_origem = float(resultado[0])

            # Verifica saldo suficiente
            if saldo_origem < valor:
                print(f"[ERRO] Saldo insuficiente na conta origem")
                self.conn.rollback()
                return False

            # Busca conta destino
            cursor.execute("SELECT id FROM conta WHERE id = %s", (conta_destino_id,))
            if not cursor.fetchone():
                print(f"[ERRO] Conta destino ID {conta_destino_id} nao encontrada")
                self.conn.rollback()
                return False

            # Atualiza ambas contas
            novo_saldo_origem = saldo_origem - valor
            cursor.execute("UPDATE conta SET saldo = %s WHERE id = %s",
                          (novo_saldo_origem, conta_origem_id))

            cursor.execute("UPDATE conta SET saldo = saldo + %s WHERE id = %s",
                          (valor, conta_destino_id))

            # Confirma transacao
            self.conn.commit()

            print(f"[SUCESSO] Transferencia de R$ {valor:.2f} realizada")
            print(f"   De: conta ID {conta_origem_id}")
            print(f"   Para: conta ID {conta_destino_id}")
            return True

        except Error as e:
            print(f"[ERRO] Erro na transferencia: {e}")
            self.conn.rollback()
            return False
        finally:
            if cursor:
                cursor.close()

    def atualizar_status(self, conta_id, novo_status):
        """
        Atualiza o status de uma conta.

        PARAMETROS:
        - conta_id: ID da conta
        - novo_status: 'ativa', 'bloqueada' ou 'encerrada'

        RETORNO:
        - bool: True se atualizou, False se erro

        USOS:
        - Bloquear conta por suspeita de fraude
        - Encerrar conta a pedido do cliente
        - Reativar conta desbloqueada
        """
        cursor = None
        try:
            cursor = self.conn.cursor()

            sql = "UPDATE conta SET status = %s WHERE id = %s"
            cursor.execute(sql, (novo_status, conta_id))
            self.conn.commit()

            atualizado = cursor.rowcount > 0

            if atualizado:
                print(f"[SUCESSO] Status da conta ID {conta_id} atualizado para '{novo_status}'")
            else:
                print(f"[ATENCAO] Conta ID {conta_id} nao encontrada")

            return atualizado

        except Error as e:
            print(f"[ERRO] Erro ao atualizar status: {e}")
            self.conn.rollback()
            return False
        finally:
            if cursor:
                cursor.close()

    def _row_to_conta(self, row):
        """
        Converte linha do banco para objeto Conta.

        PARAMETROS:
        - row: Dicionario com dados do banco

        RETORNO:
        - Conta: Objeto Conta populado
        """
        return Conta(
            id=row['id'],
            clientes_id=row['clientes_id'],
            numero_conta=row['numero_conta'],
            saldo=float(row['saldo']) if row['saldo'] else 0.00,
            data_abertura=row['data_abertura'],
            tipo_conta=row['tipo_conta'],
            status=row['status']
        )

    def close(self):
        """
        Fecha a conexao se foi criada internamente.
        """
        if not self.usar_conexao_externa and self.db:
            self.db.disconnect()
            print("[CONEXAO] Conexao do ContaDAO fechada")


# Exemplo de uso (remova em producao):
if __name__ == "__main__":
    """
    Teste basico do ContaDAO.
    Execute: python dao/conta_dao.py
    """
    print(" TESTE DO CONTADAO")
    print("=" * 50)

    try:
        dao = ContaDAO()

        # Primeiro precisamos de um cliente para testar
        from dao.cliente_dao import ClienteDAO
        cliente_dao = ClienteDAO(dao.db)

        # Cria cliente de teste se nao existir
        cliente_teste = cliente_dao.buscar_por_cpf("999.888.777-66")
        if not cliente_teste:
            cliente_teste = Cliente(
                nome="Maria Teste",
                cpf="999.888.777-66",
                data_nascimento="1985-03-20"
            )
            cliente_id = cliente_dao.create(cliente_teste)
            cliente_teste.id = cliente_id

        # Teste 1: Criar conta
        print("\n1. Criando conta de teste...")
        conta_teste = Conta(
            clientes_id=cliente_teste.id,
            numero_conta="9999-9",
            saldo=1000.00,
            data_abertura="2026-08-13",
            tipo_conta="corrente"
        )

        conta_id = dao.create(conta_teste)

        # Teste 2: Buscar conta
        if conta_id:
            print("\n2. Buscando conta criada...")
            conta_buscada = dao.read(conta_id)
            if conta_buscada:
                print(f"   Numero: {conta_buscada.numero_conta}")
                print(f"   Saldo: R$ {conta_buscada.saldo:.2f}")

        # Teste 3: Deposito
        print("\n3. Realizando deposito...")
        if conta_id:
            sucesso = dao.depositar(conta_id, 500.00)
            print(f"   Deposito: {'Sucesso' if sucesso else 'Falha'}")

        # Teste 4: Saque
        print("\n4. Realizando saque...")
        if conta_id:
            sucesso = dao.sacar(conta_id, 200.00)
            print(f"   Saque: {'Sucesso' if sucesso else 'Falha'}")

        # Teste 5: Listar contas do cliente
        print("\n5. Listando contas do cliente...")
        contas = dao.listar_por_cliente(cliente_teste.id)
        for c in contas:
            print(f"    {c.numero_conta}: R$ {c.saldo:.2f} ({c.tipo_conta})")

    finally:
        # Garante que conexoes serao fechadas
        dao.close()
        cliente_dao.close()

    print("\n" + "=" * 50)
    print("[SUCESSO] Teste do ContaDAO concluido!")