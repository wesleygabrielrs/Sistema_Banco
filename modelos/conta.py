

class Conta:
    def __init__(self, clientes_id, numero_conta,
                 saldo=0.00, data_abertura=None,
                 tipo_conta='corrente', status='ativa',
                 id=None):
        self.id = id  
        self.clientes_id = clientes_id  
        self.numero_conta = numero_conta  
        self.saldo = float(saldo)  
        self.data_abertura = data_abertura  
        self.tipo_conta = tipo_conta  
        self.status = status 
        

    def __str__(self):
        return f"Conta {self.id}: {self.numero_conta} - Saldo: R$ {self.saldo:.2f}"

    def depositar(self, valor):
        self.saldo += valor

    def sacar(self, valor):
        if valor <= self.saldo:
            self.saldo -= valor
        else:
            print("Saldo insuficiente")

    def transferir(self, valor, conta_destino):
        if valor <= self.saldo:
            self.saldo -= valor
            conta_destino.depositar(valor)
        else:
            print("Saldo insuficiente")

    #def mostrar_extrato(self):
        #for extrato in self.extrato:
            #print(extrato)

