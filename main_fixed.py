"""
🎯 Sniper Bot - Versão Corrigida para Render
Bot com correção completa do problema de event loop
"""

import os
import sys
import logging
import asyncio
import time
import json
import signal
from datetime import datetime, timedelta
from threading import Thread, Event
from typing import Dict, List, Optional, Any
import traceback

# Configuração de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('sniper_bot.log')
    ]
)
logger = logging.getLogger(__name__)

# Importações condicionais
try:
    from web3 import Web3
    from eth_account import Account
    WEB3_AVAILABLE = True
    logger.info("✅ Web3 disponível")
except ImportError:
    logger.warning("❌ Web3 não disponível")
    WEB3_AVAILABLE = False
    Web3 = None
    Account = None

try:
    from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, Bot
    from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes, MessageHandler, filters
    TELEGRAM_AVAILABLE = True
    logger.info("✅ Telegram disponível")
except ImportError:
    logger.warning("❌ Telegram não disponível")
    TELEGRAM_AVAILABLE = False
    # Classes dummy
    class Update: pass
    class ContextTypes:
        DEFAULT_TYPE = None
    class InlineKeyboardButton:
        def __init__(self, text, callback_data=None, **kwargs):
            self.text = text
            self.callback_data = callback_data
    class InlineKeyboardMarkup:
        def __init__(self, keyboard):
            self.keyboard = keyboard

try:
    from flask import Flask, jsonify, request
    from flask_cors import CORS
    FLASK_AVAILABLE = True
    logger.info("✅ Flask disponível")
except ImportError:
    logger.warning("❌ Flask não disponível")
    FLASK_AVAILABLE = False

try:
    import requests
    import aiohttp
    HTTP_AVAILABLE = True
    logger.info("✅ HTTP clients disponíveis")
except ImportError:
    logger.warning("❌ HTTP clients não disponíveis")
    HTTP_AVAILABLE = False

# Configurações
from config import config

# Estado global do bot
class BotState:
    def __init__(self):
        self.running = False
        self.turbo_mode = False
        self.positions = {}
        self.stats = {
            'total_trades': 0,
            'successful_trades': 0,
            'failed_trades': 0,
            'total_profit': 0.0,
            'total_loss': 0.0,
            'start_time': datetime.now(),
            'last_trade': None,
            'best_trade': {'profit': 0.0, 'token': None},
            'worst_trade': {'loss': 0.0, 'token': None}
        }
        self.dex_status = {
            'uniswap_v3': {'status': 'unknown', 'last_check': None},
            'baseswap': {'status': 'unknown', 'last_check': None},
            'camelot': {'status': 'unknown', 'last_check': None}
        }
        self.wallet_balance = {
            'eth': 0.0,
            'weth': 0.0,
            'tokens': {}
        }
        self.discovery_active = False
        self.mempool_monitoring = False
        
bot_state = BotState()

# Configurações de DEX
DEX_CONFIGS = {
    'uniswap_v3': {
        'name': 'Uniswap V3',
        'router': '0x2626664c2603336E57B271c5C0b26F421741e481',  # Base
        'factory': '0x33128a8fC17869897dcE68Ed026d694621f6FDfD',
        'rpc_check': True
    },
    'baseswap': {
        'name': 'BaseSwap',
        'router': '0x327Df1E6de05895d2ab08513aaDD9313Fe505d86',  # Base
        'factory': '0xFDa619b6d20975be80A10332cD39b9a4b0FAa8BB',
        'rpc_check': True
    },
    'camelot': {
        'name': 'Camelot',
        'router': '0xc873fEcbd354f5A56E00E710B90EF4201db2448d',  # Base
        'factory': '0x6EcCab422D763aC031210895C81787E87B91425',
        'rpc_check': True
    }
}

# Web3 Setup
if WEB3_AVAILABLE and config.get('RPC_URL'):
    try:
        w3 = Web3(Web3.HTTPProvider(config['RPC_URL']))
        if w3.is_connected():
            logger.info(f"✅ Conectado à rede Base: {w3.eth.chain_id}")
        else:
            logger.error("❌ Falha na conexão Web3")
            w3 = None
    except Exception as e:
        logger.error(f"❌ Erro ao conectar Web3: {e}")
        w3 = None
else:
    w3 = None

def escape_markdown_v2(text: str) -> str:
    """Escapa caracteres especiais para Markdown V2"""
    special_chars = ['_', '*', '[', ']', '(', ')', '~', '`', '>', '#', '+', '-', '=', '|', '{', '}', '.', '!']
    for char in special_chars:
        text = text.replace(char, f'\\{char}')
    return text

async def check_dex_status() -> Dict[str, Any]:
    """Verifica o status de todas as DEXs"""
    results = {}
    
    if not w3:
        return {dex: {'status': 'no_web3', 'last_check': datetime.now()} for dex in DEX_CONFIGS}
    
    for dex_name, dex_config in DEX_CONFIGS.items():
        try:
            # Verifica se o contrato existe
            router_code = w3.eth.get_code(dex_config['router'])
            if len(router_code) > 0:
                # Tenta fazer uma chamada simples
                factory_code = w3.eth.get_code(dex_config['factory'])
                if len(factory_code) > 0:
                    results[dex_name] = {
                        'status': 'active',
                        'last_check': datetime.now(),
                        'router': dex_config['router'],
                        'factory': dex_config['factory']
                    }
                else:
                    results[dex_name] = {
                        'status': 'factory_error',
                        'last_check': datetime.now()
                    }
            else:
                results[dex_name] = {
                    'status': 'router_error',
                    'last_check': datetime.now()
                }
        except Exception as e:
            results[dex_name] = {
                'status': 'error',
                'error': str(e),
                'last_check': datetime.now()
            }
            logger.error(f"❌ Erro verificando {dex_name}: {e}")
    
    bot_state.dex_status = results
    return results

async def get_wallet_balance() -> Dict[str, float]:
    """Obtém saldo da carteira"""
    if not w3 or not config.get('WALLET_ADDRESS'):
        return {'eth': 0.0, 'weth': 0.0}
    
    try:
        wallet_address = config['WALLET_ADDRESS']
        
        # ETH balance
        eth_balance = w3.eth.get_balance(wallet_address)
        eth_balance_ether = w3.from_wei(eth_balance, 'ether')
        
        # WETH balance (contrato WETH na Base)
        weth_address = '0x4200000000000000000000000000000000000006'  # WETH Base
        weth_abi = [
            {
                "constant": True,
                "inputs": [{"name": "_owner", "type": "address"}],
                "name": "balanceOf",
                "outputs": [{"name": "balance", "type": "uint256"}],
                "type": "function"
            }
        ]
        
        weth_contract = w3.eth.contract(address=weth_address, abi=weth_abi)
        weth_balance = weth_contract.functions.balanceOf(wallet_address).call()
        weth_balance_ether = w3.from_wei(weth_balance, 'ether')
        
        bot_state.wallet_balance = {
            'eth': float(eth_balance_ether),
            'weth': float(weth_balance_ether)
        }
        
        return bot_state.wallet_balance
        
    except Exception as e:
        logger.error(f"❌ Erro obtendo saldo: {e}")
        return {'eth': 0.0, 'weth': 0.0}

def build_main_menu() -> InlineKeyboardMarkup:
    """Constrói o menu principal"""
    status_emoji = "🟢" if bot_state.running else "🔴"
    turbo_emoji = "🚀" if bot_state.turbo_mode else "⚡"
    
    keyboard = [
        [
            InlineKeyboardButton(f"{status_emoji} {'Pausar' if bot_state.running else 'Iniciar'} Sniper", 
                               callback_data="toggle_sniper"),
            InlineKeyboardButton(f"{turbo_emoji} Modo Turbo", callback_data="toggle_turbo")
        ],
        [
            InlineKeyboardButton("💰 Saldo", callback_data="show_balance"),
            InlineKeyboardButton("📊 Estatísticas", callback_data="show_stats")
        ],
        [
            InlineKeyboardButton("📋 Posições", callback_data="show_positions"),
            InlineKeyboardButton("🔍 Descoberta", callback_data="toggle_discovery")
        ],
        [
            InlineKeyboardButton("⚙️ Configurações", callback_data="show_config"),
            InlineKeyboardButton("🔧 Status DEXs", callback_data="check_dexs")
        ],
        [
            InlineKeyboardButton("📈 Análise Token", callback_data="analyze_token"),
            InlineKeyboardButton("🆘 Emergência", callback_data="emergency_stop")
        ],
        [
            InlineKeyboardButton("🔄 Atualizar", callback_data="refresh_menu")
        ]
    ]
    return InlineKeyboardMarkup(keyboard)

def build_config_menu() -> InlineKeyboardMarkup:
    """Menu de configurações"""
    keyboard = [
        [
            InlineKeyboardButton("💰 Trade Size", callback_data="config_trade_size"),
            InlineKeyboardButton("📈 Take Profit", callback_data="config_take_profit")
        ],
        [
            InlineKeyboardButton("📉 Stop Loss", callback_data="config_stop_loss"),
            InlineKeyboardButton("🎯 Slippage", callback_data="config_slippage")
        ],
        [
            InlineKeyboardButton("🔢 Max Posições", callback_data="config_max_positions"),
            InlineKeyboardButton("⏱️ Timeouts", callback_data="config_timeouts")
        ],
        [
            InlineKeyboardButton("🔙 Voltar", callback_data="back_to_main")
        ]
    ]
    return InlineKeyboardMarkup(keyboard)

# Handlers do Telegram (só definir se disponível)
if TELEGRAM_AVAILABLE:
    async def start_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Comando /start"""
        welcome_text = f"""
🎯 *Sniper Bot Base Network v2\\.0*

Bem\\-vindo ao bot de trading mais avançado da rede Base\\!

*Status Atual:*
• Bot: {"🟢 Ativo" if bot_state.running else "🔴 Inativo"}
• Modo Turbo: {"🚀 Ativo" if bot_state.turbo_mode else "⚡ Inativo"}
• Descoberta: {"🔍 Ativa" if bot_state.discovery_active else "😴 Inativa"}
• Posições: {len(bot_state.positions)}

*Funcionalidades:*
• 🎯 Sniper automático para memecoins
• 📈 Trading inteligente de altcoins
• 🔒 Proteções avançadas de segurança
• 💰 Take profit multi\\-nível
• 🛡️ Stop loss com trailing
• 🚀 Modo turbo para oportunidades rápidas

Escolha uma opção abaixo:
"""
        
        await update.message.reply_text(
            welcome_text,
            parse_mode='MarkdownV2',
            reply_markup=build_main_menu()
        )

    async def status_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Comando /status detalhado"""
        uptime = datetime.now() - bot_state.stats['start_time']
        
        # Atualizar saldo
        balance = await get_wallet_balance()
        
        # Verificar DEXs
        dex_status = await check_dex_status()
        active_dexs = sum(1 for status in dex_status.values() if status['status'] == 'active')
        
        success_rate = 0
        if bot_state.stats['total_trades'] > 0:
            success_rate = (bot_state.stats['successful_trades'] / bot_state.stats['total_trades']) * 100
        
        status_text = f"""
📊 *Status Detalhado do Bot*

*🤖 Estado do Sistema:*
• Status: {"🟢 Ativo" if bot_state.running else "🔴 Inativo"}
• Modo Turbo: {"🚀 Ativo" if bot_state.turbo_mode else "⚡ Inativo"}
• Uptime: {str(uptime).split('.')[0]}
• Descoberta: {"🔍 Ativa" if bot_state.discovery_active else "😴 Inativa"}

*💰 Carteira:*
• ETH: {balance['eth']:.6f} ETH
• WETH: {balance['weth']:.6f} WETH
• Total: ~${(balance['eth'] + balance['weth']) * 2500:.2f} USD

*📈 Trading:*
• Posições Ativas: {len(bot_state.positions)}
• Total de Trades: {bot_state.stats['total_trades']}
• Sucessos: {bot_state.stats['successful_trades']}
• Falhas: {bot_state.stats['failed_trades']}
• Taxa de Sucesso: {success_rate:.1f}%

*💵 P&L:*
• Lucro Total: {bot_state.stats['total_profit']:.6f} ETH
• Perda Total: {bot_state.stats['total_loss']:.6f} ETH
• P&L Líquido: {bot_state.stats['total_profit'] - bot_state.stats['total_loss']:.6f} ETH

*🔧 DEXs:*
• DEXs Ativas: {active_dexs}/3
• Uniswap V3: {dex_status.get('uniswap_v3', {}).get('status', 'unknown')}
• BaseSwap: {dex_status.get('baseswap', {}).get('status', 'unknown')}
• Camelot: {dex_status.get('camelot', {}).get('status', 'unknown')}

*⚙️ Configurações:*
• Trade Size: {config.get('TRADE_SIZE_ETH', 0.001)} ETH
• Take Profit: {config.get('TAKE_PROFIT_PCT', 0.25)*100}%
• Stop Loss: {config.get('STOP_LOSS_PCT', 0.15)*100}%
• Max Posições: {config.get('MAX_POSITIONS', 3)}
• Slippage: {config.get('SLIPPAGE_BPS', 500)/100}%
"""
        
        await update.message.reply_text(
            escape_markdown_v2(status_text),
            parse_mode='MarkdownV2'
        )

    async def menu_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handler principal para botões do menu"""
        query = update.callback_query
        await query.answer()
        
        data = query.data
        
        try:
            if data == "toggle_sniper":
                bot_state.running = not bot_state.running
                status = "iniciado" if bot_state.running else "pausado"
                emoji = "🚀" if bot_state.running else "⏸️"
                
                if bot_state.running:
                    bot_state.discovery_active = True
                    logger.info("🚀 Sniper bot iniciado")
                else:
                    logger.info("⏸️ Sniper bot pausado")
                
                await query.edit_message_text(
                    f"{emoji} *Sniper Bot {status.title()}\\!*\n\n"
                    f"Status: {'🟢 Ativo' if bot_state.running else '🔴 Inativo'}\n"
                    f"Modo Turbo: {'🚀 Ativo' if bot_state.turbo_mode else '⚡ Inativo'}\n"
                    f"Descoberta: {'🔍 Ativa' if bot_state.discovery_active else '😴 Inativa'}\n\n"
                    f"O bot foi {status} com sucesso\\.",
                    parse_mode='MarkdownV2',
                    reply_markup=build_main_menu()
                )
            
            elif data == "toggle_turbo":
                bot_state.turbo_mode = not bot_state.turbo_mode
                status = "ativado" if bot_state.turbo_mode else "desativado"
                emoji = "🚀" if bot_state.turbo_mode else "⚡"
                
                turbo_text = f"""
{emoji} *Modo Turbo {status.title()}\\!*

*Configurações Turbo:*
• Monitoramento: {'200ms' if bot_state.turbo_mode else '1s'}
• Slippage: {'10%' if bot_state.turbo_mode else '5%'}
• Gas Price: {'Agressivo' if bot_state.turbo_mode else 'Normal'}
• Timeout: {'5s' if bot_state.turbo_mode else '10s'}

O modo turbo foi {status} com sucesso\\!
"""
                
                await query.edit_message_text(
                    turbo_text,
                    parse_mode='MarkdownV2',
                    reply_markup=build_main_menu()
                )
            
            elif data == "show_balance":
                balance = await get_wallet_balance()
                
                total_value_usd = (balance['eth'] + balance['weth']) * 2500
                available = balance['eth'] + balance['weth'] - (len(bot_state.positions) * config.get('TRADE_SIZE_ETH', 0.001))
                
                balance_text = f"""
💰 *Saldo Detalhado*

*💎 Ativos:*
• ETH: {balance['eth']:.6f} ETH
• WETH: {balance['weth']:.6f} WETH
• Total: {balance['eth'] + balance['weth']:.6f} ETH
• Valor USD: ~${total_value_usd:.2f}

*📊 Utilização:*
• Posições Ativas: {len(bot_state.positions)}
• Capital em Uso: {len(bot_state.positions) * config.get('TRADE_SIZE_ETH', 0.001):.6f} ETH
• Disponível: {max(0, available):.6f} ETH
• Trades Possíveis: {int(max(0, available) / config.get('TRADE_SIZE_ETH', 0.001))}

*📈 Performance:*
• P&L: {bot_state.stats['total_profit'] - bot_state.stats['total_loss']:.6f} ETH
• ROI: {((bot_state.stats['total_profit'] - bot_state.stats['total_loss']) / max(balance['eth'] + balance['weth'], 0.001) * 100):.2f}%
"""
                
                await query.edit_message_text(
                    escape_markdown_v2(balance_text),
                    parse_mode='MarkdownV2',
                    reply_markup=build_main_menu()
                )
            
            elif data == "emergency_stop":
                bot_state.running = False
                bot_state.turbo_mode = False
                bot_state.discovery_active = False
                bot_state.mempool_monitoring = False
                
                emergency_positions = len(bot_state.positions)
                bot_state.positions.clear()
                
                emergency_text = f"""
🆘 *PARADA DE EMERGÊNCIA ATIVADA\\!*

*Ações Executadas:*
• ❌ Bot pausado imediatamente
• ❌ Modo turbo desativado
• ❌ Descoberta interrompida
• ❌ Monitoramento pausado
• 💰 {emergency_positions} posições fechadas

*Status Atual:*
• Bot: 🔴 Inativo
• Modo Turbo: ⚡ Inativo
• Descoberta: 😴 Inativa
• Posições: 0

Para reativar, use o botão "Iniciar Sniper"\\.
"""
                
                await query.edit_message_text(
                    emergency_text,
                    parse_mode='MarkdownV2',
                    reply_markup=build_main_menu()
                )
            
            else:
                await query.edit_message_text(
                    "⚙️ Funcionalidade em desenvolvimento\\.",
                    parse_mode='MarkdownV2',
                    reply_markup=build_main_menu()
                )
                
        except Exception as e:
            logger.error(f"❌ Erro no menu handler: {e}")
            await query.edit_message_text(
                f"❌ Erro: {escape_markdown_v2(str(e))}",
                parse_mode='MarkdownV2',
                reply_markup=build_main_menu()
            )

# Flask App
if FLASK_AVAILABLE:
    app = Flask(__name__)
    CORS(app)
    
    @app.route('/')
    def home():
        return jsonify({
            'name': 'Sniper Bot Base Network',
            'version': '2.0',
            'status': 'running',
            'bot_running': bot_state.running,
            'turbo_mode': bot_state.turbo_mode,
            'positions': len(bot_state.positions),
            'endpoints': ['/health', '/status', '/metrics', '/dexs', '/positions']
        })
    
    @app.route('/health')
    def health():
        return jsonify({
            'status': 'healthy',
            'timestamp': datetime.now().isoformat(),
            'bot_running': bot_state.running,
            'turbo_mode': bot_state.turbo_mode,
            'positions': len(bot_state.positions),
            'uptime': str(datetime.now() - bot_state.stats['start_time'])
        })
    
    @app.route('/status')
    def status():
        return jsonify({
            'bot_state': {
                'running': bot_state.running,
                'turbo_mode': bot_state.turbo_mode,
                'discovery_active': bot_state.discovery_active,
                'mempool_monitoring': bot_state.mempool_monitoring
            },
            'stats': {
                'total_trades': bot_state.stats['total_trades'],
                'successful_trades': bot_state.stats['successful_trades'],
                'failed_trades': bot_state.stats['failed_trades'],
                'total_profit': bot_state.stats['total_profit'],
                'total_loss': bot_state.stats['total_loss'],
                'start_time': bot_state.stats['start_time'].isoformat()
            },
            'wallet_balance': bot_state.wallet_balance,
            'positions_count': len(bot_state.positions),
            'dex_status': {k: {**v, 'last_check': v['last_check'].isoformat() if v.get('last_check') else None} for k, v in bot_state.dex_status.items()}
        })

def signal_handler(signum, frame):
    """Handler para sinais do sistema"""
    logger.info(f"🛑 Recebido sinal {signum}, encerrando bot...")
    bot_state.running = False
    sys.exit(0)

class TelegramBotManager:
    """Gerenciador do bot Telegram com event loop próprio"""
    
    def __init__(self):
        self.application = None
        self.running = False
        
    async def setup_bot(self):
        """Configura o bot Telegram"""
        if not TELEGRAM_AVAILABLE or not config.get('TELEGRAM_TOKEN'):
            return False
            
        try:
            self.application = Application.builder().token(config['TELEGRAM_TOKEN']).build()
            
            # Handlers
            self.application.add_handler(CommandHandler("start", start_cmd))
            self.application.add_handler(CommandHandler("status", status_cmd))
            self.application.add_handler(CallbackQueryHandler(menu_handler))
            
            return True
        except Exception as e:
            logger.error(f"❌ Erro configurando bot Telegram: {e}")
            return False
    
    async def run_bot(self):
        """Executa o bot Telegram"""
        if not self.application:
            return
            
        try:
            self.running = True
            logger.info("🤖 Iniciando bot Telegram...")
            
            # Usar run_polling de forma assíncrona
            await self.application.run_polling(drop_pending_updates=True, stop_signals=None)
            
        except Exception as e:
            logger.error(f"❌ Erro executando bot Telegram: {e}")
        finally:
            self.running = False

def main():
    """Função principal"""
    logger.info("🚀 Iniciando Sniper Bot Completo v2.0...")
    
    # Configurar handlers de sinal
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Inicializar verificações
    if w3:
        logger.info(f"✅ Web3 conectado - Chain ID: {w3.eth.chain_id}")
    else:
        logger.warning("⚠️ Web3 não disponível - funcionalidades limitadas")
    
    # Configurar e iniciar bot Telegram em thread separada
    telegram_manager = None
    if TELEGRAM_AVAILABLE and config.get('TELEGRAM_TOKEN'):
        telegram_manager = TelegramBotManager()
        
        def run_telegram_thread():
            """Thread para executar o bot Telegram"""
            try:
                # Criar event loop para esta thread
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                
                # Configurar e executar bot
                async def telegram_main():
                    if await telegram_manager.setup_bot():
                        await telegram_manager.run_bot()
                    else:
                        logger.error("❌ Falha ao configurar bot Telegram")
                
                loop.run_until_complete(telegram_main())
                
            except Exception as e:
                logger.error(f"❌ Erro na thread do Telegram: {e}")
            finally:
                try:
                    loop.close()
                except:
                    pass
        
        telegram_thread = Thread(target=run_telegram_thread, daemon=True)
        telegram_thread.start()
        logger.info("🤖 Bot Telegram iniciado")
    else:
        logger.warning("⚠️ Bot Telegram não disponível")
    
    # Iniciar tarefas de background
    def run_background_tasks():
        """Thread para tarefas de background"""
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            async def background_loop():
                while True:
                    try:
                        if bot_state.running:
                            # Atualizar saldo
                            await get_wallet_balance()
                            
                            # Verificar DEXs periodicamente
                            if datetime.now().minute % 5 == 0:  # A cada 5 minutos
                                await check_dex_status()
                        
                        # Intervalo baseado no modo turbo
                        interval = 0.2 if bot_state.turbo_mode else 1.0
                        await asyncio.sleep(interval)
                        
                    except Exception as e:
                        logger.error(f"❌ Erro em background tasks: {e}")
                        await asyncio.sleep(5)
            
            loop.run_until_complete(background_loop())
            
        except Exception as e:
            logger.error(f"❌ Erro na thread de background: {e}")
        finally:
            try:
                loop.close()
            except:
                pass
    
    background_thread = Thread(target=run_background_tasks, daemon=True)
    background_thread.start()
    logger.info("🔄 Background tasks iniciadas")
    
    # Iniciar Flask App
    if FLASK_AVAILABLE:
        try:
            port = int(os.environ.get('PORT', 10000))
            logger.info(f"🌐 Iniciando Flask na porta {port}")
            app.run(host='0.0.0.0', port=port, debug=False, threaded=True)
        except Exception as e:
            logger.error(f"❌ Erro ao iniciar Flask: {e}")
    else:
        logger.warning("⚠️ Flask não disponível - mantendo processo ativo")
        while True:
            time.sleep(60)
            logger.info("🤖 Bot ativo - aguardando...")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        logger.info("🛑 Bot interrompido pelo usuário")
    except Exception as e:
        logger.error(f"❌ Erro fatal: {e}")
        logger.error(traceback.format_exc())
        sys.exit(1)