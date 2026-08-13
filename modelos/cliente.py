class Cliente:
    def __init__(self, nome, cpf, data_nascimento,
                 email=None, telefone=None, endereco=None,
                 id=None, data_cadastro=None):
        self.id = id  # Sera preenchido pelo MySQL (AUTO_INCREMENT)
        self.nome = nome
        self.cpf = cpf
        self.data_nascimento = data_nascimento  # Formato: "YYYY-MM-DD"
        self.email = email
        self.telefone = telefone
        self.endereco = endereco
        self.data_cadastro = data_cadastro  # Sera preenchido pelo MySQL

    def __str__(self):
        return f"Cliente {self.id}: {self.nome} (CPF: {self.cpf})"