import mysql.connector
from mysql.connector import Error


import mysql.connector
from mysql.connector import Error

class Database:
    def __init__(self, host='127.0.0.1', database='mydb', user='root',password=''):
        self.host = host
        self.database = database
        self.user = user
        self.password = password
        self.connection = None

    def connect(self):
        try:
            self.connection = mysql.connector.connect(
                host=self.host,
                database=self.database,
                user=self.user,
                password=self.password
            )
            print("[SUCESSO] Conexao com MySQL estabelecida!")
            return self.connection
        except Error as e:
            print(f"[ERRO] Erro ao conectar ao MySQL: {e}")
            return None
    def disconnect(self):
        if self.connection:
            self.connection.close()
            print("[CONEXAO] Conexao com MySQL fechada!")