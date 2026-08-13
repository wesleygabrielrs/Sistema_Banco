"""
Sistema Bancario com MySQL - Interface de Terminal

Este e o programa principal do sistema bancario.
Agora usa MySQL para persistencia de dados atraves dos DAOs.

OPERACOES DISPONIVEIS:
1. Cadastrar cliente     6. Sacar
2. Listar clientes       7. Transferir
3. Cadastrar conta       8. Extrato
4. Listar contas         9. Relatorios
5. Depositar            0. Sair

ANOTACOES:
- Todas as operacoes agora sao persistentes no MySQL
- Cada operacao gera transacao registrada no historico
- O sistema mantem integridade referencial entre tabelas
"""

import sys
import os

# Adiciona o diretorio atual ao path para importar modulos
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from dao.database import Database
from dao.cliente_dao import ClienteDAO
from dao.conta_dao import ContaDAO
from dao.transacao_dao import TransacaoDAO
from modelos.cliente import Cliente
from modelos.conta import Conta
from modelos.transacao import Transacao
from datetime import datetime


class SistemaBancario:
    """
    Classe principal do sistema bancario.
    Gerencia a interface de terminal e coordena os DAOs.
    """

    def __init__(self):
        """Inicializa o sistema com conexao ao MySQL."""
        print("*** INICIANDO SISTEMA BANCARIO COM MYSQL ***")
        print("=" * 50)

        try:
            # Cria conexao compartilhada entre todos DAOs
            self.db = Database()
            self.conn = self.db.connect()

            if not self.conn:
                print("[ERRO] Nao foi possivel conectar ao banco de dados.")
                print("   Verifique se o MySQL esta rodando.")
                sys.exit(1)

            # Inicializa os DAOs
            self.cliente_dao = ClienteDAO(self.db)
            self.conta_dao = ContaDAO(self.db)
            self.transacao_dao = TransacaoDAO(self.db)

            print("Sistema inicializado com sucesso!")
            print("   Banco de dados: MySQL")
            print("   Tabelas: clientes, conta, transacao")

        except Exception as e:
            print(f"[ERRO] Erro ao inicializar sistema: {e}")
            sys.exit(1)

    def menu_principal(self):
        """Exibe o menu principal e gerencia as opcoes."""
        while True:
            print("\n" + "=" * 50)
            print(" SISTEMA BANCARIO - MENU PRINCIPAL")
            print("=" * 50)
            print("1. Cadastrar cliente")
            print("2. Listar clientes")
            print("3. Cadastrar conta")
            print("4. Listar contas")
            print("5. Depositar")
            print("6. Sacar")
            print("7. Transferir")
            print("8. Extrato")
            print("9. Relatorios")
            print("0. Sair")
            print("-" * 50)

            try:
                opcao = input("Escolha uma opcao: ").strip()

                if opcao == "1":
                    self.cadastrar_cliente()
                elif opcao == "2":
                    self.listar_clientes()
                elif opcao == "3":
                    self.cadastrar_conta()
                elif opcao == "4":
                    self.listar_contas()
                elif opcao == "5":
                    self.depositar()
                elif opcao == "6":
                    self.sacar()
                elif opcao == "7":
                    self.transferir()
                elif opcao == "8":
                    self.extrato()
                elif opcao == "9":
                    self.relatorios()
                elif opcao == "0":
                    self.sair()
                    break
                else:
                    print("[ERRO] Opcao invalida. Tente novamente.")

            except KeyboardInterrupt:
                print("\n\nOPERACAO CANCELADA PELO USUARIO.")
                continue
            except Exception as e:
                print(f"[ERRO] Erro: {e}")

    def cadastrar_cliente(self):
        """Cadastra um novo cliente no sistema."""
        print("\n" + "=" * 50)
        print("CADASTRAR CLIENTE")
        print("=" * 50)

        try:
            # Coleta dados do cliente
            nome = input("Nome completo: ").strip()
            if not nome:
                print("[ERRO] Nome e obrigatorio.")
                return

            cpf = input("CPF (formato: 123.456.789-00): ").strip()
            if not cpf:
                print("[ERRO] CPF e obrigatorio.")
                return

            # Verifica se CPF ja existe
            cliente_existente = self.cliente_dao.buscar_por_cpf(cpf)
            if cliente_existente:
                print(f"[ERRO] CPF {cpf} ja cadastrado para {cliente_existente.nome}")
                return

            data_nascimento = input("Data de nascimento (AAAA-MM-DD): ").strip()
            email = input("E-mail (opcional): ").strip() or None
            telefone = input("Telefone (opcional): ").strip() or None
            endereco = input("Endereco (opcional): ").strip() or None

            # Cria objeto Cliente
            cliente = Cliente(
                nome=nome,
                cpf=cpf,
                data_nascimento=data_nascimento,
                email=email,
                telefone=telefone,
                endereco=endereco
            )

            # Salva no banco
            cliente_id = self.cliente_dao.create(cliente)

            if cliente_id:
                print(f"\n[SUCESSO] Cliente cadastrado com sucesso!")
                print(f"   ID: {cliente_id}")
                print(f"   Nome: {nome}")
                print(f"   CPF: {cpf}")

        except Exception as e:
            print(f"[ERRO] Erro ao cadastrar cliente: {e}")

    def listar_clientes(self):
        """Lista todos os clientes cadastrados."""
        print("\n" + "=" * 50)
        print(" LISTA DE CLIENTES")
        print("=" * 50)

        try:
            clientes = self.cliente_dao.listar_todos()

            if not clientes:
                print("  Nenhum cliente cadastrado.")
                return

            print(f"Total de clientes: {len(clientes)}\n")

            for i, cliente in enumerate(clientes, 1):
                print(f"{i}. {cliente.nome}")
                print(f"   CPF: {cliente.cpf}")
                print(f"   E-mail: {cliente.email or 'Nao informado'}")
                print(f"   Telefone: {cliente.telefone or 'Nao informado'}")
                print(f"   Cadastrado em: {cliente.data_cadastro}")
                print("-" * 30)

        except Exception as e:
            print(f"[ERRO] Erro ao listar clientes: {e}")

    def cadastrar_conta(self):
        """Cadastra uma nova conta bancaria."""
        print("\n" + "=" * 50)
        print(" CADASTRAR CONTA BANCARIA")
        print("=" * 50)

        try:
            # Lista clientes para escolha
            clientes = self.cliente_dao.listar_todos()
            if not clientes:
                print("[ERRO] Cadastre um cliente primeiro.")
                return

            print("Clientes disponiveis:")
            for i, cliente in enumerate(clientes, 1):
                print(f"{i}. {cliente.nome} (CPF: {cliente.cpf})")

            # Seleciona cliente
            try:
                escolha = int(input("\nNumero do cliente: ")) - 1
                if escolha < 0 or escolha >= len(clientes):
                    print("[ERRO] Cliente invalido.")
                    return
            except ValueError:
                print("[ERRO] Opcao invalida.")
                return

            cliente = clientes[escolha]

            # Coleta dados da conta
            numero_conta = input("Numero da conta (ex: 1001-1): ").strip()
            if not numero_conta:
                print("[ERRO] Numero da conta e obrigatorio.")
                return

            # Verifica se numero ja existe
            conta_existente = self.conta_dao.buscar_por_numero(numero_conta)
            if conta_existente:
                print(f"[ERRO] Conta {numero_conta} ja cadastrada.")
                return

            try:
                saldo_inicial = float(input("Saldo inicial (R$): ").strip() or "0")
                if saldo_inicial < 0:
                    print("[ERRO] Saldo nao pode ser negativo.")
                    return
            except ValueError:
                print("[ERRO] Valor invalido para saldo.")
                return

            data_abertura = input("Data de abertura (AAAA-MM-DD) [hoje]: ").strip()
            if not data_abertura:
                data_abertura = datetime.now().strftime("%Y-%m-%d")

            print("\nTipos de conta:")
            print("1. Corrente")
            print("2. Poupanca")
            print("3. Salario")

            tipo_opcao = input("Tipo (1-3) [1]: ").strip() or "1"
            tipos = {"1": "corrente", "2": "poupanca", "3": "salario"}
            tipo_conta = tipos.get(tipo_opcao, "corrente")

            # Cria objeto Conta
            conta = Conta(
                clientes_id=cliente.id,
                numero_conta=numero_conta,
                saldo=saldo_inicial,
                data_abertura=data_abertura,
                tipo_conta=tipo_conta,
                status="ativa"
            )

            # Salva no banco
            conta_id = self.conta_dao.create(conta)

            if conta_id:
                print(f"\n[SUCESSO] Conta cadastrada com sucesso!")
                print(f"   Numero: {numero_conta}")
                print(f"   Cliente: {cliente.nome}")
                print(f"   Tipo: {tipo_conta}")
                print(f"   Saldo inicial: R$ {saldo_inicial:.2f}")

                # Registra deposito inicial se houver saldo
                if saldo_inicial > 0:
                    transacao = Transacao(
                        tipo='deposito',
                        valor=saldo_inicial,
                        conta_id=conta_id,
                        descricao='Deposito inicial'
                    )
                    self.transacao_dao.create(transacao)

        except Exception as e:
            print(f"[ERRO] Erro ao cadastrar conta: {e}")

    def listar_contas(self):
        """Lista todas as contas cadastradas."""
        print("\n" + "=" * 50)
        print(" LISTA DE CONTAS")
        print("=" * 50)

        try:
            # Pega todas as contas via clientes
            clientes = self.cliente_dao.listar_todos()
            total_contas = 0

            for cliente in clientes:
                contas = self.conta_dao.listar_por_cliente(cliente.id)
                if contas:
                    print(f"\n {cliente.nome} (CPF: {cliente.cpf})")
                    for conta in contas:
                        total_contas += 1
                        print(f"    {conta.numero_conta}")
                        print(f"     Tipo: {conta.tipo_conta}")
                        print(f"     Saldo: R$ {conta.saldo:.2f}")
                        print(f"     Status: {conta.status}")
                        print(f"     Aberta em: {conta.data_abertura}")
                        print()

            if total_contas == 0:
                print("  Nenhuma conta cadastrada.")

            print(f"\nTotal de contas: {total_contas}")

        except Exception as e:
            print(f"[ERRO] Erro ao listar contas: {e}")

    def selecionar_conta(self, mensagem="Selecionar conta: "):
        """Auxiliar para selecionar uma conta pelo numero."""
        numero_conta = input(mensagem).strip()
        if not numero_conta:
            return None

        conta = self.conta_dao.buscar_por_numero(numero_conta)
        if not conta:
            print(f"[ERRO] Conta {numero_conta} nao encontrada.")
            return None

        return conta

    def depositar(self):
        """Realiza um deposito em uma conta."""
        print("\n" + "=" * 50)
        print(" DEPOSITO")
        print("=" * 50)

        try:
            conta = self.selecionar_conta("Numero da conta para deposito: ")
            if not conta:
                return

            print(f"\nConta: {conta.numero_conta}")
            print(f"Cliente: {self.obter_nome_cliente(conta.clientes_id)}")
            print(f"Saldo atual: R$ {conta.saldo:.2f}")

            try:
                valor = float(input("\nValor do deposito (R$): ").strip())
                if valor <= 0:
                    print("[ERRO] Valor deve ser positivo.")
                    return
            except ValueError:
                print("[ERRO] Valor invalido.")
                return

            descricao = input("Descricao (opcional): ").strip() or "Deposito"

            # Realiza deposito
            sucesso = self.conta_dao.depositar(conta.id, valor)

            if sucesso:
                # Registra transacao
                transacao = Transacao(
                    tipo='deposito',
                    valor=valor,
                    conta_id=conta.id,
                    descricao=descricao
                )
                self.transacao_dao.create(transacao)

                # Atualiza saldo da conta em memoria
                conta.saldo += valor

                print(f"\n[SUCESSO] Deposito realizado com sucesso!")
                print(f"   Novo saldo: R$ {conta.saldo:.2f}")

        except Exception as e:
            print(f"[ERRO] Erro ao realizar deposito: {e}")

    def sacar(self):
        """Realiza um saque de uma conta."""
        print("\n" + "=" * 50)
        print(" SAQUE")
        print("=" * 50)

        try:
            conta = self.selecionar_conta("Numero da conta para saque: ")
            if not conta:
                return

            print(f"\nConta: {conta.numero_conta}")
            print(f"Cliente: {self.obter_nome_cliente(conta.clientes_id)}")
            print(f"Saldo atual: R$ {conta.saldo:.2f}")

            try:
                valor = float(input("\nValor do saque (R$): ").strip())
                if valor <= 0:
                    print("[ERRO] Valor deve ser positivo.")
                    return
            except ValueError:
                print("[ERRO] Valor invalido.")
                return

            descricao = input("Descricao (opcional): ").strip() or "Saque"

            # Realiza saque
            sucesso = self.conta_dao.sacar(conta.id, valor)

            if sucesso:
                # Registra transacao
                transacao = Transacao(
                    tipo='saque',
                    valor=valor,
                    conta_id=conta.id,
                    descricao=descricao
                )
                self.transacao_dao.create(transacao)

                # Atualiza saldo da conta em memoria
                conta.saldo -= valor

                print(f"\n[SUCESSO] Saque realizado com sucesso!")
                print(f"   Novo saldo: R$ {conta.saldo:.2f}")

        except Exception as e:
            print(f"[ERRO] Erro ao realizar saque: {e}")

    def transferir(self):
        """Realiza transferencia entre contas."""
        print("\n" + "=" * 50)
        print(" TRANSFERENCIA")
        print("=" * 50)

        try:
            # Conta origem
            print("CONTA ORIGEM:")
            conta_origem = self.selecionar_conta("Numero da conta origem: ")
            if not conta_origem:
                return

            print(f"\nSaldo disponivel: R$ {conta_origem.saldo:.2f}")

            # Conta destino
            print("\nCONTA DESTINO:")
            conta_destino = self.selecionar_conta("Numero da conta destino: ")
            if not conta_destino:
                return

            if conta_origem.id == conta_destino.id:
                print("[ERRO] Nao e possivel transferir para a mesma conta.")
                return

            try:
                valor = float(input("\nValor da transferencia (R$): ").strip())
                if valor <= 0:
                    print("[ERRO] Valor deve ser positivo.")
                    return
            except ValueError:
                print("[ERRO] Valor invalido.")
                return

            descricao = input("Descricao (opcional): ").strip() or "Transferencia"

            # Realiza transferencia
            sucesso = self.conta_dao.transferir(
                conta_origem.id,
                conta_destino.id,
                valor
            )

            if sucesso:
                # Registra transacao
                transacao = Transacao(
                    tipo='transferencia',
                    valor=valor,
                    conta_id=conta_origem.id,
                    conta_destino_id=conta_destino.id,
                    descricao=descricao
                )
                self.transacao_dao.create(transacao)

                print(f"\n[SUCESSO] Transferencia realizada com sucesso!")
                print(f"   De: {conta_origem.numero_conta}")
                print(f"   Para: {conta_destino.numero_conta}")
                print(f"   Valor: R$ {valor:.2f}")

                # Atualiza saldos em memoria
                conta_origem.saldo -= valor

        except Exception as e:
            print(f"[ERRO] Erro ao realizar transferencia: {e}")

    def extrato(self):
        """Exibe extrato de uma conta."""
        print("\n" + "=" * 50)
        print(" EXTRATO")
        print("=" * 50)

        try:
            conta = self.selecionar_conta("Numero da conta para extrato: ")
            if not conta:
                return

            print(f"\nConta: {conta.numero_conta}")
            print(f"Cliente: {self.obter_nome_cliente(conta.clientes_id)}")
            print(f"Saldo atual: R$ {conta.saldo:.2f}")
            print(f"Tipo: {conta.tipo_conta}")
            print("-" * 50)

            # Obtem extrato
            transacoes = self.transacao_dao.extrato_completo(conta.id, limite=50)

            if not transacoes:
                print("  Nenhuma transacao encontrada.")
                return

            print(f"\nUltimas {len(transacoes)} transacoes:\n")

            for transacao in transacoes:
                data = transacao.data_hora.strftime("%d/%m/%Y %H:%M") if transacao.data_hora else "Data nao disponivel"

                # Formata conforme tipo de transacao
                if transacao.tipo == 'deposito':
                    simbolo = "+"
                    destino = ""
                elif transacao.tipo == 'saque':
                    simbolo = "-"
                    destino = ""
                elif transacao.tipo == 'transferencia':
                    if transacao.conta_id == conta.id:
                        simbolo = "-->"
                        destino = f" para conta {transacao.conta_destino_id}"
                    else:
                        simbolo = "+<-"
                        destino = f" da conta {transacao.conta_id}"
                else:
                    simbolo = "*"
                    destino = ""

                print(f"{simbolo} {data}")
                print(f"   {transacao.tipo.upper()}: R$ {transacao.valor:.2f}{destino}")
                if transacao.descricao:
                    print(f"   Descricao: {transacao.descricao}")
                print()

        except Exception as e:
            print(f"[ERRO] Erro ao gerar extrato: {e}")

    def relatorios(self):
        """Exibe menu de relatorios."""
        print("\n" + "=" * 50)
        print(" RELATORIOS")
        print("=" * 50)
        print("1.  Extrato por periodo")
        print("2.  Resumo mensal")
        print("3. [ATENCAO]  Transacoes suspeitas")
        print("4.   Voltar")

        try:
            opcao = input("\nEscolha uma opcao: ").strip()

            if opcao == "1":
                self.extrato_periodo()
            elif opcao == "2":
                self.resumo_mensal()
            elif opcao == "3":
                self.transacoes_suspeitas()
            elif opcao == "4":
                return
            else:
                print("[ERRO] Opcao invalida.")

        except Exception as e:
            print(f"[ERRO] Erro: {e}")

    def extrato_periodo(self):
        """Gera extrato por periodo especifico."""
        print("\n" + "=" * 30)
        print(" EXTRATO POR PERIODO")
        print("=" * 30)

        try:
            conta = self.selecionar_conta("Numero da conta: ")
            if not conta:
                return

            data_inicio = input("Data inicial (AAAA-MM-DD): ").strip()
            data_fim = input("Data final (AAAA-MM-DD): ").strip()

            if not data_inicio or not data_fim:
                print("[ERRO] Ambas as datas sao obrigatorias.")
                return

            transacoes = self.transacao_dao.extrato_periodo(
                conta.id, data_inicio, data_fim
            )

            print(f"\nExtrato de {data_inicio} a {data_fim}")
            print(f"Conta: {conta.numero_conta}")
            print("-" * 40)

            if not transacoes:
                print("  Nenhuma transacao no periodo.")
                return

            for transacao in transacoes:
                data = transacao.data_hora.strftime("%d/%m") if transacao.data_hora else "N/A"
                print(f"{data} - {transacao.tipo}: R$ {transacao.valor:.2f}")

        except Exception as e:
            print(f"[ERRO] Erro: {e}")

    def resumo_mensal(self):
        """Gera resumo financeiro mensal."""
        print("\n" + "=" * 30)
        print(" RESUMO MENSAL")
        print("=" * 30)

        try:
            conta = self.selecionar_conta("Numero da conta: ")
            if not conta:
                return

            ano = input("Ano (ex: 2026): ").strip()
            mes = input("Mes (1-12): ").strip()

            if not ano or not mes:
                print("[ERRO] Ano e mes sao obrigatorios.")
                return

            resumo = self.transacao_dao.resumo_mensal(
                conta.id, int(ano), int(mes)
            )

            print(f"\nResumo {mes}/{ano} - Conta {conta.numero_conta}")
            print("=" * 40)

            if not resumo:
                print("  Nenhuma transacao no periodo.")
                return

            print(f"Depositos:        R$ {resumo['depositos']:>10.2f}")
            print(f"Saques:           R$ {resumo['saques']:>10.2f}")
            print(f"Transf. enviadas: R$ {resumo['transferencias_env']:>10.2f}")
            print(f"Transf. recebidas: R$ {resumo['transferencias_rec']:>10.2f}")
            print("-" * 40)
            print(f"Total entradas:   R$ {resumo['total_entradas']:>10.2f}")
            print(f"Total saidas:     R$ {resumo['total_saidas']:>10.2f}")
            print("=" * 40)
            print(f"Saldo final:      R$ {resumo['saldo_final']:>10.2f}")

        except Exception as e:
            print(f"[ERRO] Erro: {e}")

    def transacoes_suspeitas(self):
        """Lista transacoes suspeitas (alto valor)."""
        print("\n" + "=" * 30)
        print("[ATENCAO]  TRANSACOES SUSPEITAS")
        print("=" * 30)

        try:
            try:
                limite = float(input("Valor minimo para suspeita (R$) [10000]: ").strip() or "10000")
            except ValueError:
                print("[ERRO] Valor invalido.")
                return

            transacoes = self.transacao_dao.transacoes_suspeitas(limite)

            if not transacoes:
                print(f"  Nenhuma transacao acima de R$ {limite:.2f}")
                return

            print(f"\n{len(transacoes)} transacoes suspeitas ( R$ {limite:.2f}):\n")

            for transacao in transacoes:
                data = transacao.data_hora.strftime("%d/%m/%Y %H:%M") if transacao.data_hora else "N/A"
                print(f" {data} - {transacao.tipo}")
                print(f"  Valor: R$ {transacao.valor:.2f}")
                print(f"  Conta: {transacao.conta_id}")
                if transacao.descricao:
                    print(f"  Descricao: {transacao.descricao}")
                print()

        except Exception as e:
            print(f"[ERRO] Erro: {e}")

    def obter_nome_cliente(self, cliente_id):
        """Obtem nome do cliente pelo ID."""
        try:
            cliente = self.cliente_dao.read(cliente_id)
            return cliente.nome if cliente else "Cliente nao encontrado"
        except:
            return "Cliente nao encontrado"

    def sair(self):
        """Encerra o sistema corretamente."""
        print("\n" + "=" * 50)
        print(" ENCERRANDO SISTEMA BANCARIO")
        print("=" * 50)

        # Fecha conexao com banco
        if self.db:
            self.db.disconnect()

        print("[SUCESSO] Conexao com banco de dados fechada.")
        print(" Ate logo!")
        print("=" * 50)


def main():
    """Funcao principal que inicia o sistema."""
    sistema = SistemaBancario()
    sistema.menu_principal()


if __name__ == "__main__":
    main()