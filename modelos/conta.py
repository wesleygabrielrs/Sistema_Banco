class Conta:
    def __init__(self, numero, saldo,):
        self.numero = numero
        self.saldo = saldo
        self.extrato = [] 

    def depositar(self, valor):
        self.saldo += valor
        self.extrato.append(f"Depósito de R$ {valor}")

    def sacar(self, valor):
        if valor <= self.saldo:
            self.saldo -= valor
            self.extrato.append(f"Saque de R${valor}")
        else:
            print("Saldo insuficiente")

    def transferir(self, valor, conta_destino):
        if valor <= self.saldo:
            self.saldo -= valor
            conta_destino.depositar(valor)
            self.extrato.append(f"Transferência de {valor} para a conta {conta_destino.numero}")
        else:
            print("Saldo insuficiente")

    def mostrar_extrato(self):
        for extrato in self.extrato:
            print(extrato)

