class Transacao:
    def __init__(self, tipo, valor, conta_id, conta_destino_id=None,descricao=None, id=None, data_hora=None):
        self.id = id
        self.tipo = tipo
        self.valor = float(valor)
        self.conta_id = conta_id
        self.conta_destino_id = conta_destino_id
        self.descricao = descricao
        self.data_hora = data_hora
    def __str__(self):
        destino = f" para conta {self.conta_destino_id}" if self.conta_destino_id else ""
        return f"{self.tipo}: R$ {self.valor:.2f}{destino} ({self.data_hora})"
        