Este projeto é um sistema de reconhecimento de comandos de voz que executa ações com base em um arquivo JSON. Ele permite a navegação hierárquica entre modos e suporta a extensão de funcionalidades através de plugins em Python.

Como Funciona

    Reconhecimento de Voz: O sistema escuta o áudio do usuário e compara com os comandos definidos em um arquivo JSON.

    Estrutura Hierárquica: Os comandos são organizados em uma estrutura de árvore, permitindo modos e submodos (ex: "Modo Jogo" → "Modo Steam").

    Plugins: Comandos personalizados podem ser adicionados através de funções em Python.

1. Adicionar Comandos

Edite o arquivo comandos.json para adicionar novos comandos ou modos. Exemplo:

{
  "Modo Jogo": {
    "comandos": {
      "iniciar jogo": "comando_iniciar_jogo",
      "fechar jogo": "comando_fechar_jogo"
    }
  }
}


2. Adicionar Plugins

Crie funções em Python e registre-as no sistema. Exemplo (busca.py):

def search_For(texto):
    return f"You will do something with this: {texto}"

3. Executar o Sistema

Use o script start.sh para iniciar o sistema:

./start.sh


projeto/
│
├── comandos.json          # Arquivo de configuração dos comandos
├── main.py                # Script principal
├── start.sh               # Script Bash para iniciar o sistema
├── requirements.txt       # Dependências do projeto
└── plugins/               # Pasta para plugins personalizados
    └── meu_plugin.py      # Exemplo de plugin


    Requisitos

    Python 3.x

    Bibliotecas listadas em requirements.txt

Instale as dependências com:


pip install -r requirements.txt
