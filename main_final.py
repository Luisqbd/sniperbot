# main_final.py
import logging
import threading
from flask import Flask, jsonify
from utils.web3_utils import check_web3_connection
from utils.telegram_utils import check_telegram_bot
from utils.http_client import check_http_clients
from sniper_bot import SniperBot
from config import config

# Configuração básica de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Inicializa o aplicativo Flask
app = Flask(__name__)

# --- Funções de Tarefa em Segundo Plano ---

def run_all_strategies(bot: SniperBot):
    """
    Função alvo para a thread que executa as estratégias de sniping.
    """
    try:
        bot.run_all_strategies()
    except Exception as e:
        logging.critical(f"Erro crítico na thread de estratégias: {e}", exc_info=True)

def manage_open_positions(bot: SniperBot):
    """
    Função alvo para a thread que gerencia as posições abertas.
    """
    try:
        bot.manage_open_positions()
    except Exception as e:
        logging.critical(f"Erro crítico na thread de gerenciamento de posições: {e}", exc_info=True)

# --- Rota Flask ---

@app.route('/')
def health_check():
    """Endpoint básico para verificação de saúde (health check) do Render."""
    return jsonify(status="ok", message="Sniper Bot Service is running."), 200

# --- Função Principal de Inicialização ---

def run_app():
    """
    Inicializa todos os serviços, o bot e inicia as tarefas em segundo plano.
    """
    # 1. Verificações Iniciais
    web3_ok = check_web3_connection()
    telegram_ok = check_telegram_bot()
    flask_ok = True  # Se chegou aqui, o Flask está minimamente ok
    http_ok = check_http_clients()

    logging.info(f"✅ Web3 disponível: {web3_ok}")
    logging.info(f"✅ Telegram disponível: {telegram_ok}")
    logging.info(f"✅ Flask disponível: {flask_ok}")
    logging.info(f"✅ HTTP clients disponíveis: {http_ok}")

    # 2. Inicialização do Bot
    logging.info("🚀 Iniciando Sniper Bot Completo v2.0...")
    try:
        # Instancia o bot principal, que estabelece as conexões
        bot = SniperBot(
            private_key=config["PRIVATE_KEY"],
            rpc_url=config["BASE_RPC_URL"],
            telegram_token=config["TELEGRAM_BOT_TOKEN"],
            chat_id=config["TELEGRAM_CHAT_ID"],
            config=config
        )
        logging.info("SniperBot instanciado com sucesso.")

        # 3. Inicia as Tarefas em Segundo Plano com a biblioteca threading
        # Esta é a correção definitiva: passamos o objeto 'bot' diretamente
        # para as threads, garantindo que elas usem as conexões corretas.

        strategy_thread = threading.Thread(target=run_all_strategies, args=(bot,), daemon=True)
        strategy_thread.start()
        logging.info("Thread de estratégias iniciada.")

        positions_thread = threading.Thread(target=manage_open_positions, args=(bot,), daemon=True)
        positions_thread.start()
        logging.info("Thread de gerenciamento de posições iniciada.")

        logging.info("🔄 Background tasks iniciadas com sucesso usando threading.")

    except Exception as e:
        logging.critical(f"Falha crítica ao inicializar o SniperBot ou as threads: {e}", exc_info=True)
        # O aplicativo Flask ainda vai rodar para responder ao health check,
        # mas os logs mostrarão a falha crítica.
        return

    # 4. Inicia o Servidor Flask (bloqueia a thread principal)
    port = int(config.get("PORT", 10000))
    logging.info(f"🌐 Iniciando Flask na porta {port}")
    app.run(host='0.0.0.0', port=port)

if __name__ == '__main__':
    run_app()

# Luis