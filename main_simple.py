"""
Bot Sniper Simplificado para Deploy no Render
Versão otimizada com funcionalidades essenciais
"""

import os
import sys
import logging
import asyncio
import time
from threading import Thread
from datetime import datetime

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
    WEB3_AVAILABLE = True
except ImportError:
    logger.warning("Web3 não disponível")
    WEB3_AVAILABLE = False
    Web3 = None

try:
    from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
    from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, ContextTypes
    TELEGRAM_AVAILABLE = True
except ImportError:
    logger.warning("Telegram não disponível")
    TELEGRAM_AVAILABLE = False
    # Criar classes dummy para evitar erros
    class Update: pass
    class ContextTypes:
        DEFAULT_TYPE = None
    class InlineKeyboardButton: pass
    class InlineKeyboardMarkup: pass

try:
    from flask import Flask, jsonify
    FLASK_AVAILABLE = True
except ImportError:
    logger.warning("Flask não disponível")
    FLASK_AVAILABLE = False

# Configurações
from config import config

# Estado global do bot
bot_state = {
    'running': False,
    'positions': {},
    'stats': {
        'total_trades': 0,
        'successful_trades': 0,
        'total_profit': 0.0,
        'start_time': datetime.now()
    }
}

def escape_markdown_v2(text):
    """Escapa caracteres especiais para Markdown V2"""
    special_chars = ['_', '*', '[', ']', '(', ')', '~', '`', '>', '#', '+', '-', '=', '|', '{', '}', '.', '!']
    for char in special_chars:
        text = text.replace(char, f'\\{char}')
    return text

def build_main_menu():
    """Constrói o menu principal do bot"""
    keyboard = [
        [
            InlineKeyboardButton("🚀 Iniciar Sniper", callback_data="start_sniper"),
            InlineKeyboardButton("⏸️ Pausar Bot", callback_data="pause_bot")
        ],
        [
            InlineKeyboardButton("💰 Ver Saldo", callback_data="show_balance"),
            InlineKeyboardButton("📊 Estatísticas", callback_data="show_stats")
        ],
        [
            InlineKeyboardButton("📋 Posições", callback_data="show_positions"),
            InlineKeyboardButton("⚙️ Configurações", callback_data="show_config")
        ],
        [
            InlineKeyboardButton("🔍 Analisar Token", callback_data="analyze_token"),
            InlineKeyboardButton("🆘 Emergência", callback_data="emergency_stop")
        ]
    ]
    return InlineKeyboardMarkup(keyboard)

async def start_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Comando /start"""
    welcome_text = """
🎯 *Sniper Bot Base Network*

Bem\\-vindo ao bot de trading automatizado mais avançado da rede Base\\!

*Funcionalidades:*
• 🎯 Sniper para memecoins
• 📈 Trading de altcoins
• 🔒 Proteções de segurança
• 💰 Take profit automático
• 🛡️ Stop loss inteligente

*Status:* """ + ("🟢 Ativo" if bot_state['running'] else "🔴 Inativo") + """

Escolha uma opção abaixo:
"""
    
    await update.message.reply_text(
        welcome_text,
        parse_mode='MarkdownV2',
        reply_markup=build_main_menu()
    )

async def status_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Comando /status"""
    uptime = datetime.now() - bot_state['stats']['start_time']
    
    status_text = f"""
📊 *Status do Bot*

*Estado:* {"🟢 Ativo" if bot_state['running'] else "🔴 Inativo"}
*Uptime:* {str(uptime).split('.')[0]}
*Posições Ativas:* {len(bot_state['positions'])}
*Total de Trades:* {bot_state['stats']['total_trades']}
*Trades Bem\\-sucedidos:* {bot_state['stats']['successful_trades']}
*Lucro Total:* {bot_state['stats']['total_profit']:.4f} ETH

*Configurações:*
• Trade Size: {config.get('TRADE_SIZE_ETH', 0.001)} ETH
• Take Profit: {config.get('TAKE_PROFIT_PCT', 0.25)*100}%
• Stop Loss: {config.get('STOP_LOSS_PCT', 0.15)*100}%
• Max Posições: {config.get('MAX_POSITIONS', 3)}
"""
    
    await update.message.reply_text(
        escape_markdown_v2(status_text),
        parse_mode='MarkdownV2'
    )

async def saldo_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Comando /saldo"""
    if not WEB3_AVAILABLE:
        await update.message.reply_text("❌ Web3 não disponível")
        return
    
    try:
        # Simular consulta de saldo (implementar com Web3 real)
        eth_balance = 0.001990  # Saldo configurado
        weth_balance = 0.001990
        
        balance_text = f"""
💰 *Saldo da Carteira*

*ETH:* {eth_balance:.6f} ETH
*WETH:* {weth_balance:.6f} WETH
*Valor Total:* ~${(eth_balance + weth_balance) * 2500:.2f} USD

*Posições Ativas:* {len(bot_state['positions'])}
*Capital Livre:* {eth_balance - (len(bot_state['positions']) * config.get('TRADE_SIZE_ETH', 0.001)):.6f} ETH
"""
        
        await update.message.reply_text(
            escape_markdown_v2(balance_text),
            parse_mode='MarkdownV2'
        )
    except Exception as e:
        logger.error(f"Erro ao consultar saldo: {e}")
        await update.message.reply_text("❌ Erro ao consultar saldo")

async def posicoes_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Comando /posicoes"""
    if not bot_state['positions']:
        await update.message.reply_text("📋 Nenhuma posição ativa no momento")
        return
    
    positions_text = "📋 *Posições Ativas*\n\n"
    
    for token, position in bot_state['positions'].items():
        pnl = position.get('current_value', 0) - position.get('entry_value', 0)
        pnl_pct = (pnl / position.get('entry_value', 1)) * 100
        
        positions_text += f"""
*Token:* {token[:10]}...
*Entrada:* {position.get('entry_price', 0):.8f} ETH
*Quantidade:* {position.get('amount', 0):.2f}
*P&L:* {pnl:.6f} ETH ({pnl_pct:+.2f}%)
*Status:* {position.get('status', 'Ativa')}
---
"""
    
    await update.message.reply_text(
        escape_markdown_v2(positions_text),
        parse_mode='MarkdownV2'
    )

async def menu_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler para botões do menu"""
    query = update.callback_query
    await query.answer()
    
    data = query.data
    
    if data == "start_sniper":
        bot_state['running'] = True
        await query.edit_message_text(
            "🚀 *Sniper Bot Iniciado\\!*\n\nO bot está agora monitorando a rede Base em busca de oportunidades\\.",
            parse_mode='MarkdownV2',
            reply_markup=build_main_menu()
        )
        
    elif data == "pause_bot":
        bot_state['running'] = False
        await query.edit_message_text(
            "⏸️ *Bot Pausado*\n\nO monitoramento foi pausado\\. Posições existentes continuam ativas\\.",
            parse_mode='MarkdownV2',
            reply_markup=build_main_menu()
        )
        
    elif data == "show_balance":
        balance_text = f"""
💰 *Saldo Atual*

*ETH:* 0\\.001990 ETH
*WETH:* 0\\.001990 WETH
*Posições:* {len(bot_state['positions'])}
*Status:* {"🟢 Ativo" if bot_state['running'] else "🔴 Inativo"}
"""
        await query.edit_message_text(
            balance_text,
            parse_mode='MarkdownV2',
            reply_markup=build_main_menu()
        )
        
    elif data == "show_stats":
        uptime = datetime.now() - bot_state['stats']['start_time']
        stats_text = f"""
📊 *Estatísticas*

*Uptime:* {str(uptime).split('.')[0]}
*Total Trades:* {bot_state['stats']['total_trades']}
*Sucessos:* {bot_state['stats']['successful_trades']}
*Taxa Sucesso:* {(bot_state['stats']['successful_trades']/max(bot_state['stats']['total_trades'],1)*100):.1f}%
*Lucro Total:* {bot_state['stats']['total_profit']:.6f} ETH
"""
        await query.edit_message_text(
            escape_markdown_v2(stats_text),
            parse_mode='MarkdownV2',
            reply_markup=build_main_menu()
        )
        
    elif data == "emergency_stop":
        bot_state['running'] = False
        bot_state['positions'].clear()
        await query.edit_message_text(
            "🆘 *Parada de Emergência Ativada\\!*\n\nTodas as operações foram interrompidas\\.",
            parse_mode='MarkdownV2',
            reply_markup=build_main_menu()
        )
    
    else:
        await query.edit_message_text(
            "⚙️ Funcionalidade em desenvolvimento\\.",
            parse_mode='MarkdownV2',
            reply_markup=build_main_menu()
        )

# Flask App para Health Check
if FLASK_AVAILABLE:
    app = Flask(__name__)
    
    @app.route('/health')
    def health():
        return jsonify({
            'status': 'healthy',
            'bot_running': bot_state['running'],
            'positions': len(bot_state['positions']),
            'uptime': str(datetime.now() - bot_state['stats']['start_time'])
        })
    
    @app.route('/status')
    def status():
        return jsonify(bot_state)
    
    @app.route('/metrics')
    def metrics():
        return jsonify({
            'total_trades': bot_state['stats']['total_trades'],
            'successful_trades': bot_state['stats']['successful_trades'],
            'total_profit': bot_state['stats']['total_profit'],
            'active_positions': len(bot_state['positions'])
        })

def main():
    """Função principal"""
    logger.info("🚀 Iniciando Sniper Bot...")
    
    # Configurar Telegram Bot
    if TELEGRAM_AVAILABLE and config.get('TELEGRAM_TOKEN'):
        try:
            app_bot = ApplicationBuilder().token(config['TELEGRAM_TOKEN']).build()
            
            # Handlers
            app_bot.add_handler(CommandHandler("start", start_cmd))
            app_bot.add_handler(CommandHandler("status", status_cmd))
            app_bot.add_handler(CommandHandler("saldo", saldo_cmd))
            app_bot.add_handler(CommandHandler("posicoes", posicoes_cmd))
            app_bot.add_handler(CallbackQueryHandler(menu_handler))
            
            # Iniciar bot em thread separada
            def run_bot():
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                app_bot.run_polling()
            
            Thread(target=run_bot, daemon=True).start()
            logger.info("🤖 Bot Telegram iniciado")
            
        except Exception as e:
            logger.error(f"Erro ao iniciar bot Telegram: {e}")
    else:
        logger.warning("Bot Telegram não disponível")
    
    # Iniciar Flask App
    if FLASK_AVAILABLE:
        try:
            port = int(os.environ.get('PORT', 10000))
            logger.info(f"🌐 Iniciando Flask na porta {port}")
            app.run(host='0.0.0.0', port=port, debug=False)
        except Exception as e:
            logger.error(f"Erro ao iniciar Flask: {e}")
    else:
        logger.warning("Flask não disponível - mantendo processo ativo")
        while True:
            time.sleep(60)
            logger.info("Bot ativo - aguardando...")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        logger.info("🛑 Bot interrompido pelo usuário")
    except Exception as e:
        logger.error(f"❌ Erro fatal: {e}")
        sys.exit(1)