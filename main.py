import whisper
import numpy as np
import pyaudio
import sys
import signal
from core.command_processor_full import FSM
# Configurações
MODEL_NAME = "large-v3"

SAMPLE_RATE = 16000
CHUNK = 1024
FORMAT = pyaudio.paInt16
CHANNELS = 1
SILENCE_THRESHOLD = 500  # Ajuste conforme necessário para filtrar silêncio
fsm = FSM('comandos.json')

# Inicializa o modelo Whisper
print("Carregando o modelo Whisper...")
model = whisper.load_model(MODEL_NAME).to("cuda")
print(f"Modelo {MODEL_NAME} carregado e pronto para uso.")

# Função para capturar áudio do microfone
def capture_audio():
    p = pyaudio.PyAudio()
    stream = p.open(format=FORMAT,
                    channels=CHANNELS,
                    rate=SAMPLE_RATE,
                    input=True,
                    frames_per_buffer=CHUNK)

    print("Capturando áudio... Pressione Ctrl+C para parar.")

    try:
        while True:
            data = stream.read(CHUNK, exception_on_overflow=False)
            audio_data = np.frombuffer(data, dtype=np.int16)
            yield audio_data
    except KeyboardInterrupt:
        print("\nParando a captura de áudio...")
    finally:
        stream.stop_stream()
        stream.close()
        p.terminate()

# Função para transcrever áudio em tempo real
def transcribe_audio():
    audio_generator = capture_audio()
    audio_buffer = np.array([], dtype=np.int16)

    for audio_chunk in audio_generator:
        audio_buffer = np.append(audio_buffer, audio_chunk)

        # Verifica se o buffer tem áudio suficiente para transcrever
        if len(audio_buffer) >= SAMPLE_RATE * 5:  # 5 segundos de áudio
            audio_buffer_float = audio_buffer.astype(np.float32) / 32768.0

            # Transcreve o áudio
            result = model.transcribe(audio_buffer_float, language="pt")
            transcription = result["text"]
            
            # Exibe a transcrição
            
            fsm.processar_comando(transcription)
            # Limpa o buffer para evitar acumulação excessiva
            audio_buffer = np.array([], dtype=np.int16)

# Função para encerrar o script corretamente
def signal_handler(sig, frame):
    print("\nEncerrando o script...")
    sys.exit(0)

# Configura o handler para Ctrl+C
signal.signal(signal.SIGINT, signal_handler)

# Inicia a transcrição em tempo real
if __name__ == "__main__":
    transcribe_audio()