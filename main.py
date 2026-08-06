from modelos.banco import Banco


banco = Banco()
while True:
    print("\n1 Criar conta | 2 Depositar | 3 Sacar | 4 Transferir | 5 Extrato | 0 Sair")
    Opcao = int(input("Escolha: "))
    if Opcao == 1:
        saldo_inicial = float(input("Saldo inicial: "))
        conta = banco.cadastrar_conta(saldo_inicial)
        print(f"Conta criada: {conta.numero}")

    elif Opcao == 2:
        numero = int(input("Número da conta: "))
        valor = float(input("Valor do depósito: "))
        conta = banco.buscar_conta(numero)
        if conta:
            conta.depositar(valor)
            print(f"Depósito realizado: {valor} na conta {numero}")
        else:
            print("Conta não encontrada.")

    elif Opcao == 3:
        numero = int(input("Número da conta: "))
        valor = float(input("Valor do Saque: "))
        conta = banco.buscar_conta(numero)
        if conta:
            conta.sacar(valor)
        else:
            print("Conta não encontrada")

    

    elif Opcao == 4:
        numero = int(input("Número da conta: "))
        conta = banco.buscar_conta(numero)
        destino = int(input("Número da conta destino: "))
        conta_destino = banco.buscar_conta(destino)
        valor = float(input("Valor da transferência: "))
        if conta:
            conta.transferir(valor, conta_destino)
        else:
            print("Conta não encontrada")

    elif Opcao == 5:
        numero = int(input("Número da conta: "))
        conta = banco.buscar_conta(numero)
        if conta:
            conta.mostrar_extrato()
        else:
            print("Conta não encontrada")
    
    elif Opcao == 0:
        break

       
