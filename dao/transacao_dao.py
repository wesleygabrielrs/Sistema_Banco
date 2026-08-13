"""
TransacaoDAO - Data Access Object para a tabela 'transacao'

Este arquivo implementa operacoes para registrar e consultar
transacoes bancarias. As transacoes sao o historico completo
de todas as operacoes financeiras do sistema.

ANOTACOES IMPORTANTES:

1. Historico Completo: Toda operacao financeira (deposito,
   saque, transferencia) deve gerar uma transacao registrada.

2. Auditoria: Transacoes nao podem ser alteradas ou deletadas
   apos criadas - isso garante rastreabilidade e auditoria.

3. Relacionamentos: Transacao referencia conta (origem) e
   opcionalmente conta_destino (para transferencias).
"""

import mysql.connector
from mysql.connector import Error
from modelos.transacao import Transacao  # Importa sua classe Transacao
from dao.database import Database
from datetime import datetime


class TransacaoDAO:
    """
    DAO para gerenciar operacoes com a tabela 'transacao'

    Esta classe fornece metodos para:
    - Registrar novas transacoes (historico financeiro)
    - Consultar extrato de uma conta
    - Buscar transacoes por periodo ou tipo
    - Gerar relatorios de movimentacao

    ATRIBUTOS:
    - db: Objeto Database para conexao
    - conn: Conexao ativa com o banco
    - usar_conexao_externa: Controla gerenciamento de conexao
    """

    def __init__(self, db=None):
        """
        Inicializa o TransacaoDAO.

        PARAMETROS:
        - db: Objeto Database existente (opcional)

        CARACTERISTICAS UNICAS:
        - Transacoes sao somente-leitura apos criacao
        - Nao ha metodos update() ou delete()
        - Foco em consultas e relatorios
        """
        if db is None:
            self.db = Database()
            self.conn = self.db.connect()
            self.usar_conexao_externa = False
        else:
            self.db = db
            self.conn = db.connection
            self.usar_conexao_externa = True

    def create(self, transacao):
        """
        Registra uma nova transacao no historico.

        PARAMETROS:
        - transacao: Objeto Transacao com dados da operacao

        RETORNO:
        - int: ID da transacao criada
        - None: Se erro

        TIPOS DE TRANSACAO:
        - 'deposito': Apenas conta_id (conta que recebe)
        - 'saque': Apenas conta_id (conta que retira)
        - 'transferencia': conta_id (origem) e conta_destino_id
        - 'pagamento': Similar a transferencia com finalidade especifica

        IMPORTANTE:
        - Transacoes sao IMUTAVEIS apos criacao
        - Nao ha rollback de transacao registrada
        """
        cursor = None
        try:
            cursor = self.conn.cursor()

            # SQL para inserir transacao
            sql = """
            INSERT INTO transacao
            (tipo, valor, descricao, conta_destino_id, conta_id)
            VALUES (%s, %s, %s, %s, %s)
            """

            valores = (
                transacao.tipo,
                transacao.valor,
                transacao.descricao,
                transacao.conta_destino_id,
                transacao.conta_id
            )

            cursor.execute(sql, valores)
            self.conn.commit()

            transacao.id = cursor.lastrowid
            print(f"[SUCESSO] Transacao {transacao.tipo} registrada com ID: {transacao.id}")
            return transacao.id

        except Error as e:
            print(f"[ERRO] Erro ao registrar transacao: {e}")
            self.conn.rollback()
            return None
        finally:
            if cursor:
                cursor.close()

    def read(self, id):
        """
        Busca uma transacao pelo ID.

        PARAMETROS:
        - id: ID da transacao

        RETORNO:
        - Transacao: Objeto Transacao encontrado
        - None: Se nao encontrar

        USO:
        - Para auditoria ou consulta especifica
        - Verificacao de transacoes duvidosas
        """
        cursor = None
        try:
            cursor = self.conn.cursor(dictionary=True)

            sql = "SELECT * FROM transacao WHERE id = %s"
            cursor.execute(sql, (id,))

            resultado = cursor.fetchone()

            if resultado:
                transacao = self._row_to_transacao(resultado)
                print(f"[SUCESSO] Transacao ID {id} encontrada")
                return transacao
            else:
                print(f"[ATENCAO] Transacao ID {id} nao encontrada")
                return None

        except Error as e:
            print(f"[ERRO] Erro ao buscar transacao: {e}")
            return None
        finally:
            if cursor:
                cursor.close()

    def extrato(self, conta_id, limite=50):
        """
        Retorna o extrato (historico) de uma conta.

        PARAMETROS:
        - conta_id: ID da conta
        - limite: Numero maximo de transacoes (padrao: 50)

        RETORNO:
        - list: Lista de transacoes ordenada por data (mais recente primeiro)
        - []: Lista vazia se nao houver transacoes

        OBSERVACAO:
        - Mostra transacoes ONDE a conta e origem (conta_id)
        - Para transferencias recebidas, use extrato_recebidas()
        """
        cursor = None
        try:
            cursor = self.conn.cursor(dictionary=True)

            sql = """
            SELECT * FROM transacao
            WHERE conta_id = %s
            ORDER BY data_hora DESC
            LIMIT %s
            """

            cursor.execute(sql, (conta_id, limite))

            resultados = cursor.fetchall()

            transacoes = []
            for row in resultados:
                transacoes.append(self._row_to_transacao(row))

            print(f"[SUCESSO] Extrato: {len(transacoes)} transacoes para conta ID {conta_id}")
            return transacoes

        except Error as e:
            print(f"[ERRO] Erro ao buscar extrato: {e}")
            return []
        finally:
            if cursor:
                cursor.close()

    def extrato_completo(self, conta_id, limite=50):
        """
        Retorna extrato completo incluindo transferencias recebidas.

        PARAMETROS:
        - conta_id: ID da conta
        - limite: Numero maximo de transacoes

        RETORNO:
        - list: Todas transacoes onde a conta e origem OU destino

        DIFERENCA DO extrato():
        - Inclui transferencias recebidas (conta_destino_id)
        - Visao completa de todas movimentacoes
        """
        cursor = None
        try:
            cursor = self.conn.cursor(dictionary=True)

            sql = """
            SELECT * FROM transacao
            WHERE conta_id = %s OR conta_destino_id = %s
            ORDER BY data_hora DESC
            LIMIT %s
            """

            cursor.execute(sql, (conta_id, conta_id, limite))

            resultados = cursor.fetchall()

            transacoes = []
            for row in resultados:
                transacoes.append(self._row_to_transacao(row))

            print(f"[SUCESSO] Extrato completo: {len(transacoes)} transacoes")
            return transacoes

        except Error as e:
            print(f"[ERRO] Erro ao buscar extrato completo: {e}")
            return []
        finally:
            if cursor:
                cursor.close()

    def extrato_periodo(self, conta_id, data_inicio, data_fim):
        """
        Retorna extrato de uma conta dentro de um periodo.

        PARAMETROS:
        - conta_id: ID da conta
        - data_inicio: Data inicial (string 'YYYY-MM-DD')
        - data_fim: Data final (string 'YYYY-MM-DD')

        RETORNO:
        - list: Transacoes no periodo especificado

        USO:
        - Extrato mensal
        - Consultas fiscais
        - Analise de gastos por periodo
        """
        cursor = None
        try:
            cursor = self.conn.cursor(dictionary=True)

            sql = """
            SELECT * FROM transacao
            WHERE conta_id = %s
            AND DATE(data_hora) BETWEEN %s AND %s
            ORDER BY data_hora DESC
            """

            cursor.execute(sql, (conta_id, data_inicio, data_fim))

            resultados = cursor.fetchall()

            transacoes = []
            for row in resultados:
                transacoes.append(self._row_to_transacao(row))

            print(f"[SUCESSO] Extrato periodo: {len(transacoes)} transacoes")
            return transacoes

        except Error as e:
            print(f"[ERRO] Erro ao buscar extrato por periodo: {e}")
            return []
        finally:
            if cursor:
                cursor.close()

    def resumo_mensal(self, conta_id, ano, mes):
        """
        Retorna resumo financeiro mensal de uma conta.

        PARAMETROS:
        - conta_id: ID da conta
        - ano: Ano para o resumo
        - mes: Mes para o resumo (1-12)

        RETORNO:
        - dict: Dicionario com totais por tipo de transacao

        EXEMPLO DE RETORNO:
        {
            'depositos': 1500.00,
            'saques': 300.00,
            'transferencias_env': 200.00,
            'transferencias_rec': 100.00,
            'total_entradas': 1600.00,
            'total_saidas': 500.00,
            'saldo_final': 1100.00
        }
        """
        cursor = None
        try:
            cursor = self.conn.cursor(dictionary=True)

            # Formata data para YYYY-MM
            periodo = f"{ano:04d}-{mes:02d}"

            sql = """
            SELECT
                tipo,
                COUNT(*) as quantidade,
                SUM(valor) as total
            FROM transacao
            WHERE conta_id = %s
            AND DATE_FORMAT(data_hora, '%%Y-%%m') = %s
            GROUP BY tipo
            """

            cursor.execute(sql, (conta_id, periodo))

            resultados = cursor.fetchall()

            # Inicializa dicionario de resumo
            resumo = {
                'depositos': 0.00,
                'saques': 0.00,
                'transferencias_env': 0.00,  # Enviadas
                'transferencias_rec': 0.00,  # Recebidas
                'total_entradas': 0.00,
                'total_saidas': 0.00
            }

            # Processa resultados
            for row in resultados:
                tipo = row['tipo']
                total = float(row['total']) if row['total'] else 0.00

                if tipo == 'deposito':
                    resumo['depositos'] = total
                    resumo['total_entradas'] += total
                elif tipo == 'saque':
                    resumo['saques'] = total
                    resumo['total_saidas'] += total
                elif tipo == 'transferencia':
                    resumo['transferencias_env'] = total
                    resumo['total_saidas'] += total

            # Calcula transferencias recebidas (conta e destino)
            sql_recebidas = """
            SELECT SUM(valor) as total_recebidas
            FROM transacao
            WHERE conta_destino_id = %s
            AND tipo = 'transferencia'
            AND DATE_FORMAT(data_hora, '%%Y-%%m') = %s
            """

            cursor.execute(sql_recebidas, (conta_id, periodo))
            recebidas = cursor.fetchone()
            if recebidas and recebidas['total_recebidas']:
                resumo['transferencias_rec'] = float(recebidas['total_recebidas'])
                resumo['total_entradas'] += resumo['transferencias_rec']

            # Calcula saldo final
            resumo['saldo_final'] = resumo['total_entradas'] - resumo['total_saidas']

            print(f"[SUCESSO] Resumo mensal: {periodo}")
            return resumo

        except Error as e:
            print(f"[ERRO] Erro ao gerar resumo mensal: {e}")
            return {}
        finally:
            if cursor:
                cursor.close()

    def listar_por_tipo(self, tipo, limite=100):
        """
        Lista transacoes de um tipo especifico.

        PARAMETROS:
        - tipo: 'deposito', 'saque', 'transferencia', 'pagamento'
        - limite: Numero maximo de transacoes

        RETORNO:
        - list: Transacoes do tipo especificado

        USO:
        - Analise de padroes
        - Relatorios especificos
        - Monitoramento de atividades
        """
        cursor = None
        try:
            cursor = self.conn.cursor(dictionary=True)

            sql = """
            SELECT * FROM transacao
            WHERE tipo = %s
            ORDER BY data_hora DESC
            LIMIT %s
            """

            cursor.execute(sql, (tipo, limite))

            resultados = cursor.fetchall()

            transacoes = []
            for row in resultados:
                transacoes.append(self._row_to_transacao(row))

            print(f"[SUCESSO] {len(transacoes)} transacoes do tipo '{tipo}'")
            return transacoes

        except Error as e:
            print(f"[ERRO] Erro ao listar transacoes por tipo: {e}")
            return []
        finally:
            if cursor:
                cursor.close()

    def transacoes_suspeitas(self, valor_minimo=10000.00):
        """
        Retorna transacoes consideradas suspeitas (alto valor).

        PARAMETROS:
        - valor_minimo: Valor minimo para considerar suspeito

        RETORNO:
        - list: Transacoes com valor acima do limite

        USO:
        - Compliance e prevencao a fraude
        - Monitoramento de transacoes grandes
        """
        cursor = None
        try:
            cursor = self.conn.cursor(dictionary=True)

            sql = """
            SELECT * FROM transacao
            WHERE valor >= %s
            ORDER BY valor DESC
            """

            cursor.execute(sql, (valor_minimo,))

            resultados = cursor.fetchall()

            transacoes = []
            for row in resultados:
                transacoes.append(self._row_to_transacao(row))

            print(f"[ATENCAO] {len(transacoes)} transacoes suspeitas ( R$ {valor_minimo:.2f})")
            return transacoes

        except Error as e:
            print(f"[ERRO] Erro ao buscar transacoes suspeitas: {e}")
            return []
        finally:
            if cursor:
                cursor.close()

    def _row_to_transacao(self, row):
        """
        Converte linha do banco para objeto Transacao.

        PARAMETROS:
        - row: Dicionario com dados do banco

        RETORNO:
        - Transacao: Objeto Transacao populado

        CONVERSOES IMPORTANTES:
        - data_hora: Converte string para objeto datetime se disponivel
        - valor: Converte para float
        """
        # Converte data_hora string para objeto datetime se existir
        data_hora = None
        if row['data_hora']:
            try:
                data_hora = row['data_hora']
                # Se for string, converte para datetime
                if isinstance(data_hora, str):
                    data_hora = datetime.strptime(data_hora, '%Y-%m-%d %H:%M:%S')
            except (ValueError, TypeError):
                # Mantem como esta se nao conseguir converter
                pass

        return Transacao(
            id=row['id'],
            tipo=row['tipo'],
            valor=float(row['valor']) if row['valor'] else 0.00,
            conta_id=row['conta_id'],
            conta_destino_id=row['conta_destino_id'],
            descricao=row['descricao'],
            data_hora=data_hora
        )

    def close(self):
        """
        Fecha a conexao se foi criada internamente.
        """
        if not self.usar_conexao_externa and self.db:
            self.db.disconnect()
            print("[CONEXAO] Conexao do TransacaoDAO fechada")


# Exemplo de uso (remova em producao):
if __name__ == "__main__":
    """
    Teste basico do TransacaoDAO.
    Execute: python dao/transacao_dao.py
    """
    print(" TESTE DO TRANSACAODAO")
    print("=" * 50)

    try:
        dao = TransacaoDAO()

        # Para testar, precisamos de contas existentes
        from dao.conta_dao import ContaDAO
        from dao.cliente_dao import ClienteDAO

        conta_dao = ContaDAO(dao.db)
        cliente_dao = ClienteDAO(dao.db)

        # Verifica se temos contas para testar
        contas = conta_dao.listar_por_cliente(1)  # Assume cliente ID 1 existe
        if not contas:
            print("[ATENCAO] Crie contas primeiro para testar transacoes")
        else:
            conta_teste = contas[0]

            # Teste 1: Registrar deposito
            print("\n1. Registrando deposito...")
            transacao_deposito = Transacao(
                tipo='deposito',
                valor=500.00,
                conta_id=conta_teste.id,
                descricao='Deposito teste'
            )
            transacao_id = dao.create(transacao_deposito)

            # Teste 2: Registrar saque
            print("\n2. Registrando saque...")
            transacao_saque = Transacao(
                tipo='saque',
                valor=200.00,
                conta_id=conta_teste.id,
                descricao='Saque teste'
            )
            dao.create(transacao_saque)

            # Teste 3: Extrato simples
            print("\n3. Gerando extrato...")
            extrato = dao.extrato(conta_teste.id, limite=10)
            for t in extrato:
                destino = f"  conta {t.conta_destino_id}" if t.conta_destino_id else ""
                print(f"    {t.data_hora}: {t.tipo} R$ {t.valor:.2f}{destino}")

            # Teste 4: Resumo (se tiver dados suficientes)
            print("\n4. Gerando resumo...")
            ano_atual = datetime.now().year
            mes_atual = datetime.now().month
            resumo = dao.resumo_mensal(conta_teste.id, ano_atual, mes_atual)

            if resumo:
                print(f"   Depositos: R$ {resumo['depositos']:.2f}")
                print(f"   Saques: R$ {resumo['saques']:.2f}")
                print(f"   Transferencias enviadas: R$ {resumo['transferencias_env']:.2f}")
                print(f"   Transferencias recebidas: R$ {resumo['transferencias_rec']:.2f}")
                print(f"   Total entradas: R$ {resumo['total_entradas']:.2f}")
                print(f"   Total saidas: R$ {resumo['total_saidas']:.2f}")
                print(f"   Saldo final: R$ {resumo['saldo_final']:.2f}")

    finally:
        # Garante que conexoes serao fechadas
        dao.close()

    print("\n" + "=" * 50)
    print("[SUCESSO] Teste do TransacaoDAO concluido!")