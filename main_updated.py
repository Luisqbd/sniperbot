"""
Bot Sniper Principal - Versão Completa e Otimizada
Integra todas as funcionalidades: mempool monitoring, security checks, DEX aggregation, Telegram bot
"""

import os
import sys
import signal
import logging
import asyncio
import time
import argparse
from threading import Thread
from functools import wraps

from flask import Flask, request, jsonify

# Importações condicionais para evitar erros
try:
    from web3 import Web3
    WEB3_AVAILABLE = True
except ImportError:
    WEB3_AVAILABLE = False
    Web3 = None

try:
    from telegram import Update
    from telegram.ext import ApplicationBuilder
    TELEGRAM_AVAILABLE = True
except ImportError:
    TELEGRAM_AVAILABLE = False

from config import config
from advanced_sniper_strategy import advanced_sniper
from telegram_bot import telegram_bot, start_telegram_bot, stop_telegram_bot
from mempool_monitor import start_mempool_monitoring, stop_mempool_monitoring
from metrics import init_metrics_server
from utils import escape_md_v2

# Configuração de logging
logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] %(levelname)s: %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("sniper_bot.log")
    ]
)
logger = logging.getLogger(__name__)

# Configurações
RPC_URL = config["RPC_URL"]
TELEGRAM_TOKEN = config["TELEGRAM_TOKEN"]
WEBHOOK_URL = config.get("WEBHOOK_URL", "")
PORT = int(os.getenv("PORT", 10000))

# Web3 connection
if WEB3_AVAILABLE:
    w3 = Web3(Web3.HTTPProvider(RPC_URL))
    if not w3.is_connected():
        logger.error("❌ RPC inacessível")
        w3 = None
else:
    w3 = None
    logger.warning("⚠️ Web3 não disponível - funcionalidades blockchain limitadas")

# Flask app para health checks e webhooks
app = Flask(__name__)

class SniperBot:
    """Classe principal do Sniper Bot"""
    
    def __init__(self):
        self.is_running = False
        self.start_time = time.time()
        self.components = {
            "advanced_sniper": False,
            "telegram_bot": False,
            "mempool_monitor": False,
            "metrics_server": False,
            "flask_server": False
        }
        
    async def start_all_components(self):
        """Inicia todos os componentes do bot"""
        logger.info("🚀 Iniciando Sniper Bot...")
        
        try:
            # 1. Inicia servidor de métricas
            await self._start_metrics_server()
            
            # 2. Inicia bot do Telegram
            await self._start_telegram_bot()
            
            # 3. Inicia estratégia avançada
            await self._start_advanced_strategy()
            
            # 4. Inicia monitoramento de mempool
            await self._start_mempool_monitoring()
            
            # 5. Inicia servidor Flask
            await self._start_flask_server()
            
            self.is_running = True
            logger.info("✅ Todos os componentes iniciados com sucesso!")
            
            # Envia notificação de inicialização
            await self._send_startup_notification()
            
        except Exception as e:
            logger.error(f"❌ Erro ao iniciar componentes: {e}")
            await self.stop_all_components()
            raise
            
    async def stop_all_components(self):
        """Para todos os componentes do bot"""
        logger.info("🛑 Parando Sniper Bot...")
        
        self.is_running = False
        
        # Para componentes em ordem reversa
        await self._stop_flask_server()
        await self._stop_mempool_monitoring()
        await self._stop_advanced_strategy()
        await self._stop_telegram_bot()
        await self._stop_metrics_server()
        
        logger.info("✅ Todos os componentes parados")
        
    async def _start_metrics_server(self):
        """Inicia servidor de métricas Prometheus"""
        try:
            init_metrics_server(8000)
            self.components["metrics_server"] = True
            logger.info("✅ Servidor de métricas iniciado na porta 8000")
        except Exception as e:
            logger.error(f"❌ Erro ao iniciar métricas: {e}")
            
    async def _start_telegram_bot(self):
        """Inicia bot do Telegram"""
        try:
            if TELEGRAM_AVAILABLE and TELEGRAM_TOKEN:
                await start_telegram_bot()
                self.components["telegram_bot"] = True
                logger.info("✅ Bot do Telegram iniciado")
            else:
                logger.warning("⚠️ Telegram não disponível")
        except Exception as e:
            logger.error(f"❌ Erro ao iniciar Telegram: {e}")
            
    async def _start_advanced_strategy(self):
        """Inicia estratégia avançada de sniper"""
        try:
            await advanced_sniper.start_strategy()
            self.components["advanced_sniper"] = True
            logger.info("✅ Estratégia avançada iniciada")
        except Exception as e:
            logger.error(f"❌ Erro ao iniciar estratégia: {e}")
            
    async def _start_mempool_monitoring(self):
        """Inicia monitoramento de mempool"""
        try:
            asyncio.create_task(start_mempool_monitoring())
            self.components["mempool_monitor"] = True
            logger.info("✅ Monitoramento de mempool iniciado")
        except Exception as e:
            logger.error(f"❌ Erro ao iniciar mempool: {e}")
            
    async def _start_flask_server(self):
        """Inicia servidor Flask"""
        try:
            # Flask roda em thread separada
            flask_thread = Thread(target=self._run_flask_server, daemon=True)
            flask_thread.start()
            self.components["flask_server"] = True
            logger.info(f"✅ Servidor Flask iniciado na porta {PORT}")
        except Exception as e:
            logger.error(f"❌ Erro ao iniciar Flask: {e}")
            
    def _run_flask_server(self):
        """Executa servidor Flask"""
        app.run(host="0.0.0.0", port=PORT, debug=False)
        
    async def _stop_metrics_server(self):
        """Para servidor de métricas"""
        if self.components["metrics_server"]:
            self.components["metrics_server"] = False
            logger.info("🛑 Servidor de métricas parado")
            
    async def _stop_telegram_bot(self):
        """Para bot do Telegram"""
        if self.components["telegram_bot"]:
            try:
                await stop_telegram_bot()
                self.components["telegram_bot"] = False
                logger.info("🛑 Bot do Telegram parado")
            except Exception as e:
                logger.error(f"❌ Erro ao parar Telegram: {e}")
                
    async def _stop_advanced_strategy(self):
        """Para estratégia avançada"""
        if self.components["advanced_sniper"]:
            try:
                await advanced_sniper.stop_strategy()
                self.components["advanced_sniper"] = False
                logger.info("🛑 Estratégia avançada parada")
            except Exception as e:
                logger.error(f"❌ Erro ao parar estratégia: {e}")
                
    async def _stop_mempool_monitoring(self):
        """Para monitoramento de mempool"""
        if self.components["mempool_monitor"]:
            try:
                await stop_mempool_monitoring()
                self.components["mempool_monitor"] = False
                logger.info("🛑 Monitoramento de mempool parado")
            except Exception as e:
                logger.error(f"❌ Erro ao parar mempool: {e}")
                
    async def _stop_flask_server(self):
        """Para servidor Flask"""
        if self.components["flask_server"]:
            self.components["flask_server"] = False
            logger.info("🛑 Servidor Flask parado")
            
    async def _send_startup_notification(self):
        """Envia notificação de inicialização"""
        try:
            if self.components["telegram_bot"]:
                uptime = time.time() - self.start_time
                message = (
                    f"🚀 *SNIPER BOT INICIADO*\n\n"
                    f"*Componentes Ativos:*\n"
                    f"• Estratégia Avançada: {'✅' if self.components['advanced_sniper'] else '❌'}\n"
                    f"• Telegram Bot: {'✅' if self.components['telegram_bot'] else '❌'}\n"
                    f"• Mempool Monitor: {'✅' if self.components['mempool_monitor'] else '❌'}\n"
                    f"• Métricas: {'✅' if self.components['metrics_server'] else '❌'}\n"
                    f"• Flask Server: {'✅' if self.components['flask_server'] else '❌'}\n\n"
                    f"*Configurações:*\n"
                    f"• Trade Size: `{config.get('TRADE_SIZE_ETH', 0.001)}` ETH\n"
                    f"• Max Posições: `{config.get('MAX_POSITIONS', 3)}`\n"
                    f"• Stop Loss: `{config.get('STOP_LOSS_PCT', 0.15)*100:.1f}%`\n"
                    f"• Take Profit: `{config.get('TAKE_PROFIT_PCT', 0.25)*100:.1f}%`\n\n"
                    f"*Rede:* Base (Chain ID: {config.get('CHAIN_ID', 8453)})\n"
                    f"*Modo:* {'🧪 DRY RUN' if config.get('DRY_RUN', True) else '💰 LIVE TRADING'}\n\n"
                    f"Bot pronto para operar\\! 🎯"
                )
                
                await telegram_bot.send_alert(message)
                
        except Exception as e:
            logger.error(f"❌ Erro enviando notificação: {e}")
            
    def get_status(self):
        """Retorna status dos componentes"""
        uptime = time.time() - self.start_time
        return {
            "is_running": self.is_running,
            "uptime_seconds": uptime,
            "components": self.components.copy(),
            "stats": advanced_sniper.get_performance_stats() if self.components["advanced_sniper"] else {},
            "web3_connected": w3.is_connected() if w3 else False,
            "config": {
                "chain_id": config.get("CHAIN_ID"),
                "trade_size_eth": config.get("TRADE_SIZE_ETH"),
                "max_positions": config.get("MAX_POSITIONS"),
                "dry_run": config.get("DRY_RUN")
            }
        }

# Instância global do bot
sniper_bot = SniperBot()

# ==================== FLASK ROUTES ====================

@app.route("/health")
def health_check():
    """Health check endpoint"""
    return jsonify({
        "status": "healthy" if sniper_bot.is_running else "starting",
        "timestamp": time.time(),
        "uptime": time.time() - sniper_bot.start_time
    })

@app.route("/status")
def status():
    """Status detalhado do bot"""
    return jsonify(sniper_bot.get_status())

@app.route("/metrics")
def metrics():
    """Endpoint de métricas customizadas"""
    stats = advanced_sniper.get_performance_stats()
    return jsonify({
        "trading_metrics": stats,
        "system_metrics": {
            "uptime": time.time() - sniper_bot.start_time,
            "components_active": sum(sniper_bot.components.values()),
            "total_components": len(sniper_bot.components)
        }
    })

@app.route("/webhook", methods=["POST"])
def webhook():
    """Webhook para integrações externas"""
    try:
        data = request.get_json()
        logger.info(f"Webhook recebido: {data}")
        
        # Processa webhook conforme necessário
        # Por exemplo: alertas externos, sinais de trading, etc.
        
        return jsonify({"status": "received"})
    except Exception as e:
        logger.error(f"Erro processando webhook: {e}")
        return jsonify({"error": str(e)}), 400

@app.route("/emergency_stop", methods=["POST"])
def emergency_stop():
    """Parada de emergência"""
    try:
        asyncio.create_task(sniper_bot.stop_all_components())
        return jsonify({"status": "emergency_stop_initiated"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ==================== SIGNAL HANDLERS ====================

def signal_handler(signum, frame):
    """Handler para sinais do sistema"""
    logger.info(f"Sinal recebido: {signum}")
    
    async def shutdown():
        await sniper_bot.stop_all_components()
        
    asyncio.create_task(shutdown())
    sys.exit(0)

# Registra handlers de sinal
signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)

# ==================== MAIN FUNCTION ====================

async def main():
    """Função principal"""
    parser = argparse.ArgumentParser(description="Sniper Bot para Base Network")
    parser.add_argument("--dry-run", action="store_true", help="Modo de teste (sem trades reais)")
    parser.add_argument("--config-file", help="Arquivo de configuração customizado")
    parser.add_argument("--log-level", default="INFO", help="Nível de log (DEBUG, INFO, WARNING, ERROR)")
    
    args = parser.parse_args()
    
    # Configura nível de log
    logging.getLogger().setLevel(getattr(logging, args.log_level.upper()))
    
    # Override dry run se especificado
    if args.dry_run:
        os.environ["DRY_RUN"] = "true"
        logger.info("🧪 Modo DRY RUN ativado via argumento")
    
    try:
        # Inicia todos os componentes
        await sniper_bot.start_all_components()
        
        # Mantém o bot rodando
        logger.info("🎯 Bot em execução. Pressione Ctrl+C para parar.")
        
        while sniper_bot.is_running:
            await asyncio.sleep(1)
            
            # Health check periódico
            if int(time.time()) % 300 == 0:  # A cada 5 minutos
                logger.info(f"💓 Health check - Uptime: {time.time() - sniper_bot.start_time:.0f}s")
                
    except KeyboardInterrupt:
        logger.info("🛑 Interrupção do usuário")
    except Exception as e:
        logger.error(f"❌ Erro fatal: {e}")
    finally:
        await sniper_bot.stop_all_components()

if __name__ == "__main__":
    # Verifica dependências críticas
    if not WEB3_AVAILABLE:
        logger.error("❌ Web3 não disponível. Instale com: pip install web3")
        sys.exit(1)
        
    if not TELEGRAM_AVAILABLE:
        logger.warning("⚠️ Telegram não disponível. Bot funcionará sem notificações.")
    
    # Verifica configurações críticas
    required_configs = ["PRIVATE_KEY", "RPC_URL", "TELEGRAM_TOKEN"]
    missing_configs = [cfg for cfg in required_configs if not config.get(cfg)]
    
    if missing_configs:
        logger.error(f"❌ Configurações obrigatórias ausentes: {missing_configs}")
        logger.error("Configure as variáveis no arquivo .env")
        sys.exit(1)
    
    # Inicia o bot
    try:
        asyncio.run(main())
    except Exception as e:
        logger.error(f"❌ Erro ao iniciar: {e}")
        sys.exit(1)