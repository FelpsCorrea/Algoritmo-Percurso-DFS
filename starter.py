#!/usr/bin/env python3

# ASDPC
# Prof. Luiz Lima Jr.

from pika import BlockingConnection
from sys import argv

if len(argv)<3:
    print(f'Uso: {argv[0]} <msg> <dest1> [<dest2> ...]')
    exit(1)

msg = argv[1]
dests = argv[2:]

with BlockingConnection() as conexao:
    with conexao.channel() as canal:
        for d in dests:
            canal.basic_publish(
                exchange="",
                routing_key=d,
                body=f'STARTER:msg')
        print(f'Mensagem "{msg}" enviada para {dests}!')
