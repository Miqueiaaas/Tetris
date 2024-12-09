from tetris import TetrisGame
import mysql.connector
import threading
import serial
import time

class TetrisComBancoDeDados:
    def __init__(self, host, user, password, database, collation):
        self.conexao = mysql.connector.connect(
            host=host,
            user=user,
            password=password,
            database=database,
            collation=collation
        )
        self.cursor = self.conexao.cursor()

        self.arduino = serial.Serial('/dev/ttyUSB0', 9600)
        time.sleep(2)

        self.move_left = False
        self.move_right = False
        self.move_down = False
        self.rotate = False

    def fechar_conexao(self):
        self.cursor.close()
        self.conexao.close()

    def pegaPontos(self, pontos):
        comando = 'INSERT INTO ranking(nome, pontos) VALUES(%s, %s);'
        nome = 'Raimundex'  # Nome do jogador (pode ser personalizado)
        self.cursor.execute(comando, (nome, pontos))
        self.conexao.commit()

    def handle_serial_input(self):
        """Lê os dados da porta serial e controla o jogo."""
        if self.arduino.in_waiting > 0:
            data = self.arduino.readline().decode('utf-8').strip()
            print(f"Recebido do Arduino: {data}")  # Adicione esta linha para ver o que o Arduino está enviando
            if data == "1":
                self.move_left = True
            elif data == "2":
                self.move_right = True
            elif data == "3":
                self.move_down = True
            elif data == "4":
                self.rotate = True

    def inicia_jogo(self):
        self.jogo = TetrisGame()
        # Inicia thread para lidar com entradas seriais (controle via Arduino)
        serial_thread = threading.Thread(target=self.handle_serial_input)
        serial_thread.daemon = True  # Torna a thread em segundo plano
        serial_thread.start()

        # Executa o jogo
        self.jogo.run()
        if not self.jogo.running:  # Verifica se o jogo terminou
            pontos = self.jogo.endScore
            print(f"Pontuação obtida: {pontos}")
            self.pegaPontos(pontos)
            self.fechar_conexao()

def run_tetris():
    """Função para rodar o jogo."""
    arduino = serial.Serial('/dev/ttyUSB0', 9600)  # Ajuste para a porta correta do seu Arduino
    tetris = TetrisGame(arduino)  # Passe o parâmetro arduino aqui
    tetris.run()


if __name__ == "__main__":
    run_tetris()

# Função principal
if __name__ == "__main__":
    # Criação de uma thread para o jogo Tetris
    tetris_thread = threading.Thread(target=run_tetris)
    tetris_thread.start()

    tetris_thread.join()  # Espera a execução da thread do jogo terminar antes de fechar o programa. eu to usando a porta certa (/dev/ttyUSB0)