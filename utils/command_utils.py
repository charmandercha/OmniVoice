from Levenshtein import distance as levenshtein_distance

def encontrar_comando_mais_proximo(comando, comandos_disponiveis):
    menor_distancia = float('inf')
    comando_mais_proximo = None

    for cmd in comandos_disponiveis:
        dist = levenshtein_distance(comando, cmd)
        if dist < menor_distancia:
            menor_distancia = dist
            comando_mais_proximo = cmd

    if menor_distancia <= 2:
        return comando_mais_proximo
    return None