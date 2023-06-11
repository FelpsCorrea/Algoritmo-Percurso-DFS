#!/usr/bin/env python3

# ASDPC
# Felipe Correa Lopes dos Santos

from pika import BlockingConnection  # Biblioteca para estabelecer conexão com o RabbitMQ
from sys import argv
from enum import Enum 

E = Enum("Estado", "INICIADOR OCIOSO VISITADO OK")  # Define os estados possíveis de um nó

# Função para exibir mensagem de erro e encerrar o programa
def error_message():
    print(f'USO: {argv[0]} <id> <v1> [<v2> ...]')
    exit(1)

# Verifica se os argumentos necessários foram fornecidos
if len(argv)<2: error_message()

# Define o id do nó (idx) e a lista de vizinhos (Nx)
idx, Nx = argv[1], argv[2:]

# Variáveis globais
nao_visitados, entrada, iniciador, estado, canal = None, None, False, E.OCIOSO, None

# Função para alterar o estado de um nó
def muda_estado(novo): 
    global estado
    estado = novo

# Função para enviar mensagem para outro nó
def envia(canal, msg, dest):
    msg = f'{idx}:{msg}'
    canal.basic_publish(exchange='', routing_key=dest, body=msg)

# Função que lida com a chegada de uma mensagem
def recebendo(canal, msg, origem):
    global entrada, nao_visitados
    print(f'{msg} recebida de {origem}')
    if estado == E.OCIOSO:
        nao_visitados = list(Nx)  # Copia a lista de nós vizinhos
        nao_visitados.remove(origem)  # Remove o nó que enviou a mensagem da lista de nós não visitados
        entrada = origem  # Define o nó que enviou a mensagem como a entrada
        visita()  # Visita o próximo nó não visitado
    elif estado == E.VISITADO:
        if msg == 'T':
            nao_visitados.remove(origem)
            envia(canal, 'B', origem)
        if msg in ('R', 'B'):  # Se a mensagem recebida for 'R' ou 'B', visita o próximo nó
            visita()

# Função chamada quando o nó inicia uma ação por conta própria
def espontaneamente():
    global nao_visitados, iniciador
    nao_visitados = list(Nx)  # Copia a lista de nós vizinhos
    iniciador = True  # Define o nó como iniciador
    visita()  # Visita o próximo nó não visitado

# Função para visitar o próximo nó na lista de nós não visitados
def visita():
    global estado, canal, nao_visitados
    if nao_visitados:  # Se ainda houver nós não visitados
        prox = nao_visitados.pop(0)  # Obtém o próximo nó da lista
        estado = E.VISITADO  # Muda o estado para VISITADO
        envia(canal, 'T', prox)  # Envia a mensagem 'T' para o próximo nó
    else:
        estado = E.OK  # Se todos os nós foram visitados, muda o estado para OK
        if not iniciador:  # Se o nó não for o iniciador, envia a mensagem 'R' para o nó de entrada
            envia(canal, 'R', entrada)

# Função para lidar com as mensagens recebidas
def trata_msg(canal, metodo, props, body):
    global iniciador
    origem, msg = body.decode().split(':') if len(body.decode().split(':')) == 2 else ('NULL', body.decode())
    if origem == 'STARTER':  # Se a mensagem vier do iniciador
        muda_estado(E.INICIADOR)  # Muda o estado para INICIADOR
        iniciador = True  # Define o nó como iniciador
        espontaneamente()  # Inicia uma ação espontaneamente
    else:
        recebendo(canal, msg, origem)

with BlockingConnection() as conexao:  # Estabelece uma conexão com o RabbitMQ
    with conexao.channel() as canal:  # Cria um canal de comunicação
        canal.queue_declare(queue=idx, auto_delete=True)  # Declara uma fila para o nó
        for viz in Nx:  # Declara uma fila para cada nó vizinho
            canal.queue_declare(queue=viz, auto_delete=True)

        canal.basic_consume(queue=idx, on_message_callback=trata_msg, auto_ack=True)  # Começa a consumir mensagens da fila
        try:
            print(f'{idx} aguardando mensagens')
            canal.start_consuming()  # Inicia o consumo de mensagens
        except KeyboardInterrupt:  # Interrompe o consumo de mensagens se Ctrl+C for pressionado
            canal.stop_consuming()
        print('\nFim')  # Imprime 'Fim' quando o programa termina
