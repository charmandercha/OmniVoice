import json
import os
import re
from typing import Dict, Any, Optional, List
import subprocess
import importlib
processo = subprocess.Popen(
    ["bash"],
    stdin=subprocess.PIPE,
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE,
    text=True,
    bufsize=1,
    universal_newlines=True
)


class FSM:
    def __init__(self, comandos_file: str, estado_salvo_file: str = 'estado_atual.json'):
        self.estado_salvo_file = estado_salvo_file
        self.caminho_atual: List[str] = []
        # self.pasta = estado_salvo_file['diretorio_atual']
        self.executavel = False

        self.debug = True
        
         # Carrega o JSON de comandos
        with open(comandos_file, 'r') as file:
            self.enderecos: Dict[str, Any] = json.load(file)

        try:
            with open(comandos_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                if not isinstance(data, dict) or 'comandos' not in data:
                    raise ValueError("Formato inválido no arquivo de comandos")
                self.comandos = data['comandos']
                self._log(f"Comandos carregados: {list(self.comandos.keys())}")
        except FileNotFoundError as e:
            raise FileNotFoundError(f"Arquivo não encontrado: {e.filename}")
        except json.JSONDecodeError:
            raise ValueError("Erro ao decodificar arquivo JSON")
            
        self._carregar_estado_salvo()
        
    def _log(self, mensagem: str) -> None:
        if self.debug:
            print(f"[FSM Debug] {mensagem}")
    def executar_comando_bash(self, comando):
        """Envia um comando para o processo bash e retorna a saída."""
        try:
            # Verifica se o comando termina com '&'
            if comando.strip().endswith("&"):
                # Remove o '&' e executa o comando em uma instância isolada do subprocess
                comando = comando.rstrip("&").strip()
                subprocess.Popen(comando, shell=True)
                return f"Comando '{comando}' executado em segundo plano."
            else:
                # Executa o comando no bash interativo
                processo.stdin.write(comando + "\n")
                processo.stdin.flush()  # Garante que o comando seja enviado
                saida = processo.stdout.readline().strip()
                return saida
        except Exception as e:
            # Retorna a mensagem de erro se algo der errado
            return f"Erro ao executar o comando: {e}" 
    def executar_funcao_personalizada(self, nome_funcao, comando_normalizado, *args, **kwargs):
        """
        Executa uma função personalizada a partir de um módulo na pasta custom_functions.
        :param nome_funcao: Nome da função no formato "modulo.funcao".
        :param comando_normalizado: Argumento específico que será passado para a função personalizada.
        :param args: Argumentos posicionais adicionais para a função.
        :param kwargs: Argumentos nomeados adicionais para a função.
        :return: Resultado da função ou mensagem de erro.
        """
        # Divide o nome da função em módulo e função
        modulo_nome, funcao_nome = nome_funcao.split(".")
        
        try:
            # Importa o módulo dinamicamente a partir da pasta custom_functions
            modulo = importlib.import_module(f"custom_functions.{modulo_nome}")
            
            # Obtém a função específica do módulo
            funcao = getattr(modulo, funcao_nome)
            
            # Executa a função com o comando_normalizado e outros parâmetros fornecidos
            resultado = funcao(comando_normalizado, *args, **kwargs)
            print(resultado)  # Exibe o resultado da função no terminal
            return resultado
        except ImportError:
            mensagem = f"Erro: Arquivo '{modulo_nome}.py' não encontrado em custom_functions."
            print(mensagem)
            return mensagem
        except AttributeError:
            mensagem = f"Erro: Função '{funcao_nome}' não encontrada no arquivo '{modulo_nome}.py'."
            print(mensagem)
            return mensagem
    def _normalizar_texto(self, texto: str) -> str:
        if not texto:
            return ""
        texto = texto.strip()
        texto = texto.lower()
        texto = re.sub(r'[^\w\s]', '', texto)
        texto = re.sub(r'\s+', ' ', texto)
        return texto
        
    def _obter_container_atual(self) -> Optional[Dict[str, Any]]:
        """Retorna o container atual com base no caminho_atual"""
        container = self.comandos
        
        for modo in self.caminho_atual:
            if modo in container and container[modo]['tipo'] == 'container':
                container = container[modo]['comandos']
            else:
                return None
        return container
        
    def voltar_ao_pai(self) -> str:
        """Volta ao modo pai (um nível acima)"""
        if not self.caminho_atual:
            return "Já está no nível raiz"
            
        self.caminho_atual.pop()
        self.salvar_estado()
        if self.caminho_atual:
            return f"Voltando para: {' > '.join(self.caminho_atual)}"
        return "Voltando para o nível raiz"
        
    def mudar_modo(self, novo_modo: str) -> str:
        """Muda para outro modo no mesmo nível"""
        novo_modo_norm = self._normalizar_texto(novo_modo)
        
        # Se estiver no nível raiz
        if not self.caminho_atual:
            if novo_modo_norm in self.comandos and self.comandos[novo_modo_norm]['tipo'] == 'container':
                self.caminho_atual = [novo_modo_norm]  # Define o novo caminho
                self.salvar_estado()
                return f"Mudando para modo: {novo_modo}"
            return f"Modo '{novo_modo}' não encontrado no nível raiz"
        
        # Se estiver em algum nível aninhado
        container_pai = self._obter_container_atual()
        if container_pai and novo_modo_norm in container_pai:
            if container_pai[novo_modo_norm]['tipo'] == 'container':
                self.caminho_atual.append(novo_modo_norm)  # Adiciona o novo modo ao caminho
                self.salvar_estado()
                return f"Mudando para modo: {novo_modo}"
        
        return f"Modo '{novo_modo}' não encontrado no nível atual"
    def get_current_state(self) -> Dict[str, Any]:
        # Começa com o dicionário completo de comandos
        current_state = self.enderecos['comandos']
        
        print('Caminho atual:', self.caminho_atual)

        # Navega através do caminho fornecido
        for i, key in enumerate(self.caminho_atual):
            if key in current_state:
                # Se não for o último item do caminho, avança para o próximo nível
                if i < len(self.caminho_atual) - 1:
                    current_state = current_state[key]['comandos']
                else:
                    # Se for o último item, retorna o objeto completo (chave e valor)
                    return {key: current_state[key]}
            else:
                print(f"Chave '{key}' não encontrada no caminho.")
                return {}

        # Caso o caminho esteja vazio, retorna o estado atual completo
        return current_state

           
    def processar_comando(self, comando: str) -> str:
        if not comando or not isinstance(comando, str):
            return "Comando inválido: deve ser uma string não vazia"
            
        comando_normalizado = self._normalizar_texto(comando)

        self._log(f"Processando comando: '{comando_normalizado}'")
        self._log(f"Estado atual: {' > '.join(self.caminho_atual) if self.caminho_atual else 'inicial'}")
       
        # print(self.enderecos)
        objetoAtual = self.get_current_state()
        verificarExecutavel = next(iter(objetoAtual.values()))

        if 'executavel' in verificarExecutavel and verificarExecutavel['executavel'] == True:
            self.executavel = True
            self.executar_funcao_personalizada(verificarExecutavel['funcao'], comando_normalizado)

        # Comandos especiais de navegação
        if comando_normalizado == "voltar":
            return self.voltar_ao_pai()
    
        if comando_normalizado.startswith("modo "):
            
            # novo_modo = comando_original[5:].strip()  # Remove "modo " do início
            return self.mudar_modo(comando_normalizado)

            
        # Outros comandos especiais
        if comando_normalizado == "resetar":
            self.caminho_atual = []
            self.salvar_estado()
            return "Estado resetado para o início"
            
        if comando_normalizado == "ajuda":
            return self.mostrar_ajuda()
            
        if comando_normalizado == "debug":
            container_atual = self._obter_container_atual()
            return f"Debug atual:\nCaminho: {self.caminho_atual}\nContainer atual: {container_atual}"
        
        
            
        # Processamento normal de comandos
        container_atual = self._obter_container_atual()
        
        if container_atual and comando_normalizado in container_atual:
            

            comando_info = container_atual[comando_normalizado]
            
            if comando_info['tipo'] == 'executavel':
            # Verifica se o comando é uma função personalizada
                if comando_info.get('funcao'):
                    # Se houver uma função definida, execute-a
                    resultado = self.executar_funcao_personalizada(comando_info['funcao'])
                    return f"Executando função: {comando_info['funcao']}, Resultado: {resultado}"
                else:
                    # Caso contrário, executa como um comando bash
                    self.executar_comando_bash(comando_info['comando'])
                    return f"Executando comando: {comando_info['comando']}"
            
            elif comando_info['tipo'] == 'container':
                self.caminho_atual.append(comando_normalizado)
                self.salvar_estado()
                
                if comando_info['executavel'] == True:
                    self.executavel = True
                    print(self.executavel)
                else:
                    self.executavel = False
                return f"Entrando no modo: {comando_normalizado}"
                
        return f"Comando '{comando_normalizado}' não encontrado no nível atual"
        
    def mostrar_ajuda(self) -> str:
        """Mostra ajuda com comandos disponíveis e comandos especiais"""
        ajuda = [
            "Comandos especiais:",
            "- resetar: Volta para o estado inicial",
            "- voltar: Volta ao modo pai",
            "- modo <nome>: Muda para outro modo no mesmo nível",
            "- ajuda: Mostra esta mensagem",
            "- debug: Mostra estado interno do sistema",
            "\nComandos disponíveis no estado atual:",
            self.listar_comandos_atuais()
        ]
        return "\n".join(ajuda)
        
    def listar_comandos_atuais(self) -> str:
        """Lista os comandos disponíveis no estado atual"""
        container_atual = self._obter_container_atual()
        if not container_atual:
            return "Nenhum comando disponível no nível raiz"
            
        comandos_disponiveis = []
        for nome, info in container_atual.items():
            descricao = info.get('descricao', 'Sem descrição')
            tipo = info.get('tipo', 'desconhecido')
            comandos_disponiveis.append(f"- {nome} ({tipo}): {descricao}")
            
        return "\n".join(comandos_disponiveis)
        
    def _carregar_estado_salvo(self) -> None:
        try:
            if os.path.exists(self.estado_salvo_file):
                with open(self.estado_salvo_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.caminho_atual = data.get('caminho_atual', [])
                    self._log(f"Estado carregado: {self.caminho_atual}")
            else:
                self._log("Nenhum estado salvo encontrado, iniciando do zero")
        except (json.JSONDecodeError, IOError) as e:
            self._log(f"Erro ao carregar estado: {e}")
            self.caminho_atual = []
            
    def salvar_estado(self) -> None:
        try:
            with open(self.estado_salvo_file, 'w', encoding='utf-8') as f:
                json.dump({'caminho_atual': self.caminho_atual}, f, ensure_ascii=False)
                self._log(f"Estado salvo: {self.caminho_atual}")
        except IOError as e:
            self._log(f"Erro ao salvar estado: {e}")