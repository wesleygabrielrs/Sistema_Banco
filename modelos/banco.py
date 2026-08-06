from modelos.conta import Conta

class Banco:
    def __init__(self):
        self.contas = []

    def cadastrar_conta(self, saldo_inicial):
        numero = len(self.contas) + 1
        conta = Conta(numero=numero, saldo=saldo_inicial)
        self.contas.append(conta)
        return conta
    
    def buscar_conta(self, numero):
        for conta in self.contas:
            if conta.numero == numero:
                return conta
        return None

    def listar_contas(self):
        for conta in self.contas:
            print(conta.numero, conta.saldo)
