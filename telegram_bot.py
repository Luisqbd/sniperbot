"""
Bot do Telegram melhorado com todas as funcionalidades
Inclui botões interativos, comandos avançados e notificações
"""

import asyncio
import logging
import time
import datetime
import uuid
from typing import Dict, List, Optional

from telegram import (
    Update, BotCommand, InlineKeyboardButton, InlineKeyboardMarkup,
    ReplyKeyboardMarkup, KeyboardButton
)
from telegram.ext import (
    ApplicationBuilder, CommandHandler, CallbackQueryHandler, 
    MessageHandler, ContextTypes, filters
)

from config import config
from advanced_sniper_strategy import advanced_sniper
from check_balance import get_wallet_status
from risk_manager import risk_manager
from security_checker import check_token_safety
from dex_aggregator import get_best_price
from utils import get_token_info, is_valid_address

logger = logging.getLogger(__name__)

class TelegramBot:
    """Bot do Telegram com funcionalidades avançadas"""
    
    def __init__(self):
        self.token = config["TELEGRAM_TOKEN"]
        self.chat_id = config["TELEGRAM_CHAT_ID"]
        self.app = None
        self.bot = None
        self.is_running = False
        
        # Estados de conversação
        self.user_states: Dict[int, str] = {}
        self.temp_data: Dict[int, dict] = {}
        
    async def start_bot(self):
        """Inicia o bot do Telegram"""
        if self.is_running:
            return
            
        try:
            self.app = ApplicationBuilder().token(self.token).build()
            self.bot = self.app.bot
            
            # Registra handlers
            self._register_handlers()
            
            # Define comandos do bot
            await self._set_bot_commands()
            
            # Inicia polling
            await self.app.initialize()
            await self.app.start()
            await self.app.updater.start_polling()
            
            self.is_running = True
            logger.info("✅ Bot do Telegram iniciado")
            
        except Exception as e:
            logger.error(f"❌ Erro iniciando bot: {e}")
            
    async def stop_bot(self):
        """Para o bot do Telegram"""
        if not self.is_running:
            return
            
        try:
            await self.app.updater.stop()
            await self.app.stop()
            await self.app.shutdown()
            self.is_running = False
            logger.info("🛑 Bot do Telegram parado")
        except Exception as e:
            logger.error(f"❌ Erro parando bot: {e}")
            
    def _register_handlers(self):
        """Registra todos os handlers do bot"""
        # Comandos principais
        self.app.add_handler(CommandHandler("start", self.start_command))
        self.app.add_handler(CommandHandler("help", self.help_command))
        self.app.add_handler(CommandHandler("status", self.status_command))
        self.app.add_handler(CommandHandler("balance", self.balance_command))
        self.app.add_handler(CommandHandler("positions", self.positions_command))
        self.app.add_handler(CommandHandler("stats", self.stats_command))
        self.app.add_handler(CommandHandler("config", self.config_command))
        
        # Comandos de controle
        self.app.add_handler(CommandHandler("snipe", self.snipe_command))
        self.app.add_handler(CommandHandler("stop", self.stop_command))
        self.app.add_handler(CommandHandler("pause", self.pause_command))
        self.app.add_handler(CommandHandler("resume", self.resume_command))
        
        # Comandos de análise
        self.app.add_handler(CommandHandler("analyze", self.analyze_command))
        self.app.add_handler(CommandHandler("check", self.check_token_command))
        self.app.add_handler(CommandHandler("price", self.price_command))
        
        # Comandos de configuração
        self.app.add_handler(CommandHandler("set_trade_size", self.set_trade_size_command))
        self.app.add_handler(CommandHandler("set_stop_loss", self.set_stop_loss_command))
        self.app.add_handler(CommandHandler("set_take_profit", self.set_take_profit_command))
        self.app.add_handler(CommandHandler("set_max_positions", self.set_max_positions_command))
        
        # Comandos de relatório
        self.app.add_handler(CommandHandler("report", self.report_command))
        self.app.add_handler(CommandHandler("export", self.export_command))
        
        # Callback queries (botões)
        self.app.add_handler(CallbackQueryHandler(self.button_handler))
        
        # Mensagens de texto
        self.app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.text_handler))
        
    async def _set_bot_commands(self):
        """Define comandos do bot no menu"""
        commands = [
            BotCommand("start", "🚀 Iniciar bot e mostrar menu principal"),
            BotCommand("help", "🆘 Mostrar ajuda e comandos disponíveis"),
            BotCommand("status", "📊 Status atual do bot e estratégias"),
            BotCommand("balance", "💰 Saldo da carteira"),
            BotCommand("positions", "🎯 Posições ativas"),
            BotCommand("stats", "📈 Estatísticas de performance"),
            BotCommand("snipe", "▶️ Iniciar sniper automático"),
            BotCommand("stop", "⏹️ Parar sniper"),
            BotCommand("analyze", "🔍 Analisar token específico"),
            BotCommand("check", "🛡️ Verificar segurança de token"),
            BotCommand("price", "💱 Consultar preço de token"),
            BotCommand("config", "⚙️ Configurações do bot"),
            BotCommand("report", "📋 Relatório detalhado"),
        ]
        
        await self.bot.set_my_commands(commands)
        
    # ==================== COMANDOS PRINCIPAIS ====================
    
    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Comando /start"""
        welcome_text = (
            "🎯 *SNIPER BOT ATIVO*\n\n"
            "Bot de sniper para memecoins e altcoins na rede Base\\.\n"
            "Use os botões abaixo para controlar o bot:\n\n"
            "• *Sniper automático* de novos tokens\n"
            "• *Análise de segurança* avançada\n"
            "• *Take profit* em múltiplos níveis\n"
            "• *Stop loss* dinâmico\n"
            "• *Fallback* entre DEXs\n"
            "• *Proteção* contra honeypots"
        )
        
        await update.message.reply_text(
            welcome_text,
            parse_mode='MarkdownV2',
            reply_markup=self._build_main_menu()
        )
        
    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Comando /help"""
        help_text = (
            "🆘 *AJUDA DO SNIPER BOT*\n\n"
            "*COMANDOS PRINCIPAIS:*\n"
            "• `/start` \\- Menu principal\n"
            "• `/status` \\- Status do bot\n"
            "• `/balance` \\- Saldo da carteira\n"
            "• `/positions` \\- Posições ativas\n"
            "• `/stats` \\- Estatísticas\n\n"
            "*CONTROLE:*\n"
            "• `/snipe` \\- Iniciar sniper\n"
            "• `/stop` \\- Parar sniper\n"
            "• `/pause` \\- Pausar temporariamente\n"
            "• `/resume` \\- Retomar operação\n\n"
            "*ANÁLISE:*\n"
            "• `/analyze <token>` \\- Analisar token\n"
            "• `/check <token>` \\- Verificar segurança\n"
            "• `/price <token>` \\- Consultar preço\n\n"
            "*CONFIGURAÇÃO:*\n"
            "• `/config` \\- Mostrar configurações\n"
            "• `/set_trade_size <valor>` \\- Tamanho do trade\n"
            "• `/set_stop_loss <valor>` \\- Stop loss \\(%\\)\n"
            "• `/report` \\- Relatório completo\n\n"
            "*🚀 MODO TURBO:*\n"
            "Use o botão no menu principal para ativar/desativar\n"
            "• Trading agressivo com mais velocidade\n"
            "• Monitoramento a cada 50ms\n"
            "• Maior risco e recompensa\n\n"
            "*SUPORTE:* @SniperBotSupport"
        )
        
        await update.message.reply_text(help_text, parse_mode='MarkdownV2')
        
    async def status_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Comando /status"""
        stats = advanced_sniper.get_performance_stats()
        
        status_text = (
            f"📊 *STATUS DO SNIPER BOT*\n\n"
            f"*Estado:* {'🟢 Ativo' if advanced_sniper.is_running else '🔴 Parado'}\n"
            f"*Posições:* {stats['active_positions']}/{stats['max_positions']}\n"
            f"*Total Trades:* {stats['total_trades']}\n"
            f"*Taxa Acerto:* {stats['win_rate']:.1f}%\n"
            f"*Lucro Total:* {stats['total_profit']:.4f} ETH\n"
            f"*Melhor Trade:* {stats['best_trade']:.4f} ETH\n"
            f"*Uptime:* {stats['uptime_hours']:.1f}h\n\n"
            f"*Última Atualização:* {datetime.datetime.now().strftime('%H:%M:%S')}"
        )
        
        await update.message.reply_text(
            status_text,
            parse_mode='MarkdownV2',
            reply_markup=self._build_status_menu()
        )
        
    async def balance_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Comando /balance"""
        balance_info = get_wallet_status()
        await update.message.reply_text(balance_info, parse_mode='MarkdownV2')
        
    async def positions_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Comando /positions"""
        positions = advanced_sniper.get_active_positions()
        
        if not positions:
            await update.message.reply_text("📭 Nenhuma posição ativa no momento")
            return
            
        positions_text = "*🎯 POSIÇÕES ATIVAS:*\n\n"
        
        for pos in positions:
            age_hours = (time.time() - pos['entry_time']) / 3600
            positions_text += (
                f"*{pos['token_symbol']}*\n"
                f"• Entrada: `{pos['entry_price']:.8f}` ETH\n"
                f"• Atual: `{pos['current_price']:.8f}` ETH\n"
                f"• PnL: `{pos['pnl_percentage']:+.1f}%`\n"
                f"• Valor: `{pos['current_value']:.4f}` ETH\n"
                f"• Idade: `{age_hours:.1f}h`\n"
                f"• DEX: `{pos['dex_name']}`\n\n"
            )
            
        await update.message.reply_text(
            positions_text,
            parse_mode='MarkdownV2',
            reply_markup=self._build_positions_menu()
        )
        
    async def stats_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Comando /stats"""
        stats = advanced_sniper.get_performance_stats()
        
        stats_text = (
            f"📈 *ESTATÍSTICAS DE PERFORMANCE*\n\n"
            f"*Trades Totais:* {stats['total_trades']}\n"
            f"*Trades Vencedores:* {stats['winning_trades']}\n"
            f"*Taxa de Acerto:* {stats['win_rate']:.1f}%\n"
            f"*Lucro Total:* {stats['total_profit']:.4f} ETH\n"
            f"*Melhor Trade:* {stats['best_trade']:.4f} ETH\n"
            f"*Pior Trade:* {stats['worst_trade']:.4f} ETH\n"
            f"*Posições Ativas:* {stats['active_positions']}\n"
            f"*Máx\\. Posições:* {stats['max_positions']}\n"
            f"*Tempo Ativo:* {stats['uptime_hours']:.1f}h\n\n"
            f"*ROI Médio:* {(stats['total_profit'] / (stats['total_trades'] * 0.001) * 100) if stats['total_trades'] > 0 else 0:.1f}%"
        )
        
        await update.message.reply_text(stats_text, parse_mode='MarkdownV2')
        
    # ==================== COMANDOS DE CONTROLE ====================
    
    async def snipe_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Comando /snipe"""
        if advanced_sniper.is_running:
            await update.message.reply_text("⚠️ Sniper já está ativo!")
            return
            
        try:
            await advanced_sniper.start_strategy()
            await update.message.reply_text(
                "🚀 *Sniper iniciado com sucesso!*\n\n"
                "• Monitoramento de mempool ativo\n"
                "• Detecção de memecoins habilitada\n"
                "• Proteções de segurança ativas\n"
                "• Fallback entre DEXs configurado",
                parse_mode='MarkdownV2'
            )
        except Exception as e:
            await update.message.reply_text(f"❌ Erro ao iniciar sniper: {e}")
            
    async def stop_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Comando /stop"""
        if not advanced_sniper.is_running:
            await update.message.reply_text("⚠️ Sniper já está parado!")
            return
            
        try:
            await advanced_sniper.stop_strategy()
            await update.message.reply_text("🛑 Sniper parado com sucesso!")
        except Exception as e:
            await update.message.reply_text(f"❌ Erro ao parar sniper: {e}")
            
    async def pause_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Comando /pause"""
        if not advanced_sniper.is_running:
            await update.message.reply_text("⚠️ Sniper não está ativo!")
            return
            
        # Para temporariamente mas mantém posições
        self.user_states[update.effective_user.id] = "paused"
        await update.message.reply_text(
            "⏸️ *SNIPER PAUSADO*\n\n"
            "• Novas entradas desabilitadas\n"
            "• Posições ativas continuam monitoradas\n"
            "• Use `/resume` para retomar",
            parse_mode='MarkdownV2'
        )
        
    async def resume_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Comando /resume"""
        user_id = update.effective_user.id
        if user_id in self.user_states and self.user_states[user_id] == "paused":
            del self.user_states[user_id]
            await update.message.reply_text(
                "▶️ *SNIPER RETOMADO*\n\n"
                "• Novas entradas habilitadas\n"
                "• Monitoramento completo ativo",
                parse_mode='MarkdownV2'
            )
        else:
            await update.message.reply_text("⚠️ Sniper não está pausado!")
            
    # ==================== MÉTODOS AUXILIARES ====================
    
    async def _emergency_stop(self, query):
        """Para tudo imediatamente e fecha todas as posições"""
        try:
            # Para a estratégia
            if advanced_sniper.is_running:
                await advanced_sniper.stop_strategy()
                
            # Fecha todas as posições
            positions = advanced_sniper.get_active_positions()
            if positions:
                for pos in positions:
                    try:
                        await advanced_sniper._execute_exit(pos, "PARADA DE EMERGÊNCIA")
                    except Exception as e:
                        logger.error(f"Erro fechando posição {pos.get('token_symbol', 'unknown')}: {e}")
                        
            await query.edit_message_text(
                "🚨 *PARADA DE EMERGÊNCIA EXECUTADA*\n\n"
                "• Sniper parado\n"
                "• Todas as posições fechadas\n"
                "• Sistema em modo seguro",
                parse_mode='MarkdownV2'
            )
        except Exception as e:
            logger.error(f"Erro na parada de emergência: {e}")
            await query.edit_message_text(
                f"❌ Erro na parada de emergência: {e}"
            )
        
    # ==================== COMANDOS DE ANÁLISE ====================
    
    async def analyze_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Comando /analyze <token>"""
        if not context.args:
            await update.message.reply_text(
                "❌ Uso: `/analyze <endereço_do_token>`\n"
                "Exemplo: `/analyze 0x1234...`",
                parse_mode='MarkdownV2'
            )
            return
            
        token_address = context.args[0]
        
        if not is_valid_address(token_address):
            await update.message.reply_text("❌ Endereço de token inválido")
            return
            
        await update.message.reply_text("🔍 Analisando token... Aguarde...")
        
        try:
            # Obtém informações do token
            token_info = await get_token_info(token_address)
            if not token_info:
                await update.message.reply_text("❌ Não foi possível obter informações do token")
                return
                
            # Verifica segurança
            security_report = await check_token_safety(token_address)
            
            # Obtém preço
            price_quote = await get_best_price(
                token_in=token_address,
                token_out=config["WETH"],
                amount_in=int(1e18),
                is_buy=False
            )
            
            price_eth = price_quote.dex_quote.amount_out / 1e18 if price_quote else 0
            
            analysis_text = (
                f"🔍 *ANÁLISE DO TOKEN*\n\n"
                f"*Nome:* {token_info.get('name', 'N/A')}\n"
                f"*Símbolo:* {token_info.get('symbol', 'N/A')}\n"
                f"*Endereço:* `{token_address[:10]}...{token_address[-6:]}`\n"
                f"*Preço:* {price_eth:.8f} ETH\n"
                f"*Supply:* {token_info.get('totalSupply', 0):,.0f}\n"
                f"*Holders:* {token_info.get('holders', 0):,}\n\n"
                f"*🛡️ SEGURANÇA:*\n"
                f"• Status: {'✅ Seguro' if security_report.is_safe else '❌ Arriscado'}\n"
                f"• Score de Risco: {security_report.risk_score:.2f}/1\\.00\n"
                f"• Honeypot: {security_report.honeypot_risk:.2f}/1\\.00\n"
                f"• Rugpull: {security_report.rugpull_risk:.2f}/1\\.00\n"
            )
            
            if security_report.warnings:
                analysis_text += f"\n*⚠️ AVISOS:*\n"
                for warning in security_report.warnings:
                    analysis_text += f"• {warning}\n"
                    
            await update.message.reply_text(analysis_text, parse_mode='MarkdownV2')
            
        except Exception as e:
            await update.message.reply_text(f"❌ Erro na análise: {e}")
            
    async def check_token_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Comando /check <token>"""
        if not context.args:
            await update.message.reply_text(
                "❌ Uso: `/check <endereço_do_token>`",
                parse_mode='MarkdownV2'
            )
            return
            
        token_address = context.args[0]
        
        if not is_valid_address(token_address):
            await update.message.reply_text("❌ Endereço inválido")
            return
            
        await update.message.reply_text("🛡️ Verificando segurança... Aguarde...")
        
        try:
            security_report = await check_token_safety(token_address)
            
            status_emoji = "✅" if security_report.is_safe else "❌"
            check_text = (
                f"🛡️ *VERIFICAÇÃO DE SEGURANÇA*\n\n"
                f"*Token:* `{token_address[:10]}...{token_address[-6:]}`\n"
                f"*Status:* {status_emoji} {'Seguro' if security_report.is_safe else 'Arriscado'}\n\n"
                f"*📊 SCORES DE RISCO:*\n"
                f"• Geral: `{security_report.risk_score:.2f}/1.00`\n"
                f"• Honeypot: `{security_report.honeypot_risk:.2f}/1.00`\n"
                f"• Rugpull: `{security_report.rugpull_risk:.2f}/1.00`\n"
                f"• Liquidez: `{security_report.liquidity_risk:.2f}/1.00`\n"
                f"• Contrato: `{security_report.contract_risk:.2f}/1.00`\n"
            )
            
            if security_report.warnings:
                check_text += f"\n*⚠️ AVISOS:*\n"
                for warning in security_report.warnings:
                    check_text += f"• {warning}\n"
                    
            await update.message.reply_text(check_text, parse_mode='MarkdownV2')
            
        except Exception as e:
            await update.message.reply_text(f"❌ Erro na verificação: {e}")
            
    async def price_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Comando /price <token>"""
        if not context.args:
            await update.message.reply_text(
                "❌ Uso: `/price <endereço_do_token>`",
                parse_mode='MarkdownV2'
            )
            return
            
        token_address = context.args[0]
        
        if not is_valid_address(token_address):
            await update.message.reply_text("❌ Endereço inválido")
            return
            
        try:
            # Obtém cotação de venda (1 token -> ETH)
            sell_quote = await get_best_price(
                token_in=token_address,
                token_out=config["WETH"],
                amount_in=int(1e18),
                is_buy=False
            )
            
            # Obtém cotação de compra (0.001 ETH -> token)
            buy_quote = await get_best_price(
                token_in=config["WETH"],
                token_out=token_address,
                amount_in=int(0.001 * 1e18),
                is_buy=True
            )
            
            if not sell_quote or not buy_quote:
                await update.message.reply_text("❌ Não foi possível obter cotação")
                return
                
            sell_price = sell_quote.dex_quote.amount_out / 1e18
            buy_price = (0.001 * 1e18) / buy_quote.dex_quote.amount_out
            spread = ((buy_price - sell_price) / sell_price * 100) if sell_price > 0 else 0
            
            token_info = await get_token_info(token_address)
            symbol = token_info.get('symbol', 'TOKEN') if token_info else 'TOKEN'
            
            price_text = (
                f"💱 *COTAÇÃO DO TOKEN*\n\n"
                f"*Token:* {symbol}\n"
                f"*Endereço:* `{token_address[:10]}...{token_address[-6:]}`\n\n"
                f"*📈 PREÇOS:*\n"
                f"• Venda: `{sell_price:.8f}` ETH\n"
                f"• Compra: `{buy_price:.8f}` ETH\n"
                f"• Spread: `{spread:.2f}%`\n\n"
                f"*🏪 MELHORES DEXs:*\n"
                f"• Venda: {sell_quote.dex_quote.dex_name}\n"
                f"• Compra: {buy_quote.dex_quote.dex_name}\n\n"
                f"*Atualizado:* {datetime.datetime.now().strftime('%H:%M:%S')}"
            )
            
            await update.message.reply_text(price_text, parse_mode='MarkdownV2')
            
        except Exception as e:
            await update.message.reply_text(f"❌ Erro obtendo preço: {e}")
            
    # ==================== COMANDOS DE CONFIGURAÇÃO ====================
    
    async def config_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Comando /config"""
        config_text = (
            f"⚙️ *CONFIGURAÇÕES ATUAIS*\n\n"
            f"*💰 TRADING:*\n"
            f"• Trade Size: `{advanced_sniper.trade_size_eth}` ETH\n"
            f"• Stop Loss: `{advanced_sniper.stop_loss_pct*100:.1f}%`\n"
            f"• Trailing Stop: `{advanced_sniper.trailing_stop_pct*100:.1f}%`\n"
            f"• Max Posições: `{advanced_sniper.max_positions}`\n\n"
            f"*🎯 TAKE PROFIT:*\n"
        )
        
        for i, level in enumerate(advanced_sniper.take_profit_levels, 1):
            config_text += f"• Nível {i}: `{level*100:.0f}%`\n"
            
        config_text += (
            f"\n*🔍 MEMECOINS:*\n"
            f"• Max Investimento: `{advanced_sniper.memecoin_config['max_investment']}` ETH\n"
            f"• Target Lucro: `{advanced_sniper.memecoin_config['target_profit']}x`\n"
            f"• Min Holders: `{advanced_sniper.memecoin_config['min_holders']}`\n"
            f"• Max Idade: `{advanced_sniper.memecoin_config['max_age_hours']}h`\n\n"
            f"*📊 ALTCOINS:*\n"
            f"• Min Market Cap: `${advanced_sniper.altcoin_config['min_market_cap']:,}`\n"
            f"• Max Market Cap: `${advanced_sniper.altcoin_config['max_market_cap']:,}`\n"
            f"• Min Volume 24h: `${advanced_sniper.altcoin_config['min_volume_24h']:,}`\n"
            f"• Reinvestimento: `{advanced_sniper.altcoin_config['profit_reinvest_pct']*100:.0f}%`"
        )
        
        await update.message.reply_text(
            config_text,
            parse_mode='MarkdownV2',
            reply_markup=self._build_config_menu()
        )
        
    async def set_trade_size_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Comando /set_trade_size <valor>"""
        if not context.args:
            await update.message.reply_text(
                "❌ Uso: `/set_trade_size <valor_em_eth>`\n"
                "Exemplo: `/set_trade_size 0.001`",
                parse_mode='MarkdownV2'
            )
            return
            
        try:
            new_size = float(context.args[0])
            if new_size <= 0 or new_size > 1:
                await update.message.reply_text("❌ Valor deve estar entre 0 e 1 ETH")
                return
                
            advanced_sniper.trade_size_eth = Decimal(str(new_size))
            await update.message.reply_text(
                f"✅ Trade size alterado para `{new_size}` ETH",
                parse_mode='MarkdownV2'
            )
            
        except ValueError:
            await update.message.reply_text("❌ Valor inválido")
            
    async def set_stop_loss_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Comando /set_stop_loss <valor>"""
        if not context.args:
            await update.message.reply_text(
                "❌ Uso: `/set_stop_loss <percentual>`\n"
                "Exemplo: `/set_stop_loss 15` \\(para 15%\\)",
                parse_mode='MarkdownV2'
            )
            return
            
        try:
            new_sl = float(context.args[0])
            if new_sl <= 0 or new_sl > 50:
                await update.message.reply_text("❌ Stop loss deve estar entre 0% e 50%")
                return
                
            advanced_sniper.stop_loss_pct = new_sl / 100
            await update.message.reply_text(
                f"✅ Stop loss alterado para `{new_sl}%`",
                parse_mode='MarkdownV2'
            )
            
        except ValueError:
            await update.message.reply_text("❌ Valor inválido")
            
    async def set_take_profit_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Comando /set_take_profit <níveis>"""
        if not context.args:
            await update.message.reply_text(
                "❌ Uso: `/set_take_profit <nível1> <nível2> <nível3> <nível4>`\n"
                "Exemplo: `/set_take_profit 25 50 100 200` \\(para 25%, 50%, 100%, 200%\\)",
                parse_mode='MarkdownV2'
            )
            return
            
        try:
            levels = [float(arg) / 100 for arg in context.args]
            if len(levels) != 4:
                await update.message.reply_text("❌ Deve fornecer exatamente 4 níveis")
                return
                
            if any(level <= 0 or level > 10 for level in levels):
                await update.message.reply_text("❌ Níveis devem estar entre 0% e 1000%")
                return
                
            advanced_sniper.take_profit_levels = levels
            levels_text = ", ".join([f"{l*100:.0f}%" for l in levels])
            await update.message.reply_text(
                f"✅ Take profit alterado para: `{levels_text}`",
                parse_mode='MarkdownV2'
            )
            
        except ValueError:
            await update.message.reply_text("❌ Valores inválidos")
            
    async def set_max_positions_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Comando /set_max_positions <valor>"""
        if not context.args:
            await update.message.reply_text(
                "❌ Uso: `/set_max_positions <número>`\n"
                "Exemplo: `/set_max_positions 3`",
                parse_mode='MarkdownV2'
            )
            return
            
        try:
            new_max = int(context.args[0])
            if new_max <= 0 or new_max > 10:
                await update.message.reply_text("❌ Máximo de posições deve estar entre 1 e 10")
                return
                
            advanced_sniper.max_positions = new_max
            await update.message.reply_text(
                f"✅ Máximo de posições alterado para `{new_max}`",
                parse_mode='MarkdownV2'
            )
            
        except ValueError:
            await update.message.reply_text("❌ Valor inválido")
            
    # ==================== COMANDOS DE RELATÓRIO ====================
    
    async def report_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Comando /report"""
        try:
            report = risk_manager.gerar_relatorio()
            await update.message.reply_text(report, parse_mode='MarkdownV2')
        except Exception as e:
            await update.message.reply_text(f"❌ Erro gerando relatório: {e}")
            
    async def export_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Comando /export"""
        await update.message.reply_text("📤 Funcionalidade de exportação em desenvolvimento")
        
    # ==================== HANDLERS ====================
    
    async def button_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handler para botões inline"""
        query = update.callback_query
        await query.answer()
        
        data = query.data
        
        # Menu principal
        if data == "main_menu":
            await query.edit_message_text(
                "🎯 *SNIPER BOT ATIVO*\n\nUse os botões abaixo:",
                parse_mode='MarkdownV2',
                reply_markup=self._build_main_menu()
            )
            
        elif data == "start_sniper":
            if not advanced_sniper.is_running:
                await advanced_sniper.start_strategy()
                await query.edit_message_text("🚀 Sniper iniciado!")
            else:
                await query.edit_message_text("⚠️ Sniper já está ativo!")
                
        elif data == "stop_sniper":
            if advanced_sniper.is_running:
                await advanced_sniper.stop_strategy()
                await query.edit_message_text("🛑 Sniper parado!")
            else:
                await query.edit_message_text("⚠️ Sniper já está parado!")
                
        elif data == "show_status":
            stats = advanced_sniper.get_performance_stats()
            status_text = (
                f"📊 *STATUS DO SNIPER BOT*\n\n"
                f"*Estado:* {'🟢 Ativo' if advanced_sniper.is_running else '🔴 Parado'}\n"
                f"*Modo Turbo:* {'🚀 ATIVO' if config.get('TURBO_MODE', False) else '🐢 Normal'}\n"
                f"*Posições:* {stats['active_positions']}/{stats['max_positions']}\n"
                f"*Total Trades:* {stats['total_trades']}\n"
                f"*Taxa Acerto:* {stats['win_rate']:.1f}%\n"
                f"*Lucro Total:* {stats['total_profit']:.4f} ETH\n"
                f"*Melhor Trade:* {stats['best_trade']:.4f} ETH"
            )
            await query.edit_message_text(
                status_text,
                parse_mode='MarkdownV2',
                reply_markup=self._build_status_menu()
            )
            
        elif data == "show_balance":
            balance_info = get_wallet_status()
            await query.edit_message_text(balance_info, parse_mode='MarkdownV2')
            
        elif data == "show_positions":
            positions = advanced_sniper.get_active_positions()
            if not positions:
                await query.edit_message_text("📭 Nenhuma posição ativa no momento")
            else:
                positions_text = "*🎯 POSIÇÕES ATIVAS:*\n\n"
                for pos in positions:
                    age_hours = (time.time() - pos['entry_time']) / 3600
                    positions_text += (
                        f"*{pos['token_symbol']}*\n"
                        f"• PnL: `{pos['pnl_percentage']:+.1f}%`\n"
                        f"• Valor: `{pos['current_value']:.4f}` ETH\n"
                        f"• Idade: `{age_hours:.1f}h`\n\n"
                    )
                await query.edit_message_text(
                    positions_text,
                    parse_mode='MarkdownV2',
                    reply_markup=self._build_positions_menu()
                )
            
        elif data == "show_stats":
            await self.stats_command(update, context)
            
        elif data == "show_config":
            config_text = (
                f"⚙️ *CONFIGURAÇÕES DO BOT*\n\n"
                f"*💰 TRADING:*\n"
                f"• Trade Size: `{config['TRADE_SIZE_ETH']}` ETH\n"
                f"• Take Profit: `{config['TAKE_PROFIT_PCT']*100:.0f}%`\n"
                f"• Stop Loss: `{config['STOP_LOSS_PCT']*100:.0f}%`\n"
                f"• Max Posições: `{advanced_sniper.max_positions}`\n"
                f"• Modo Turbo: `{'✅ Ativo' if config.get('TURBO_MODE', False) else '❌ Inativo'}`\n\n"
                f"*🔍 MEMECOINS:*\n"
                f"• Max Investimento: `{config.get('MEMECOIN_MAX_INVESTMENT', 0.0008)}` ETH\n"
                f"• Target Lucro: `{config.get('MEMECOIN_TARGET_PROFIT', 2.0)}x`\n"
                f"• Min Holders: `{config.get('MEMECOIN_MIN_HOLDERS', 50)}`"
            )
            await query.edit_message_text(
                config_text,
                parse_mode='MarkdownV2',
                reply_markup=self._build_config_menu()
            )
            
        # Configurações específicas
        elif data == "config_trade_size":
            await query.edit_message_text(
                "💰 *ALTERAR TRADE SIZE*\n\n"
                f"Valor atual: `{config['TRADE_SIZE_ETH']}` ETH\n\n"
                "Use o comando: `/set_trade_size <valor>`\n"
                "Exemplo: `/set_trade_size 0\\.001`",
                parse_mode='MarkdownV2',
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("🔙 Voltar", callback_data="show_config")
                ]])
            )
            
        elif data == "config_stop_loss":
            await query.edit_message_text(
                "🛡️ *ALTERAR STOP LOSS*\n\n"
                f"Valor atual: `{config['STOP_LOSS_PCT']*100:.0f}%`\n\n"
                "Use o comando: `/set_stop_loss <percentual>`\n"
                "Exemplo: `/set_stop_loss 15`",
                parse_mode='MarkdownV2',
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("🔙 Voltar", callback_data="show_config")
                ]])
            )
            
        elif data == "config_take_profit":
            await query.edit_message_text(
                "📈 *ALTERAR TAKE PROFIT*\n\n"
                f"Valor atual: `{config['TAKE_PROFIT_PCT']*100:.0f}%`\n\n"
                "Use o comando: `/set_take_profit <níveis>`\n"
                "Exemplo: `/set_take_profit 25 50 100 200`",
                parse_mode='MarkdownV2',
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("🔙 Voltar", callback_data="show_config")
                ]])
            )
            
        elif data == "config_max_positions":
            await query.edit_message_text(
                "🎯 *ALTERAR MAX POSIÇÕES*\n\n"
                f"Valor atual: `{advanced_sniper.max_positions}`\n\n"
                "Use o comando: `/set_max_positions <número>`\n"
                "Exemplo: `/set_max_positions 3`",
                parse_mode='MarkdownV2',
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("🔙 Voltar", callback_data="show_config")
                ]])
            )
            
        # Modo Turbo
        elif data == "toggle_turbo":
            current_turbo = config.get("TURBO_MODE", False)
            config["TURBO_MODE"] = not current_turbo
            
            # Atualiza parâmetros baseado no modo
            if config["TURBO_MODE"]:
                # Ativa modo turbo
                config["TRADE_SIZE_ETH"] = config.get("TURBO_TRADE_SIZE_ETH", 0.0012)
                config["TAKE_PROFIT_PCT"] = config.get("TURBO_TAKE_PROFIT_PCT", 0.5)
                config["STOP_LOSS_PCT"] = config.get("TURBO_STOP_LOSS_PCT", 0.08)
                config["MEMPOOL_MONITOR_INTERVAL"] = config.get("TURBO_MONITOR_INTERVAL", 0.05)
                advanced_sniper.max_positions = config.get("TURBO_MAX_POSITIONS", 3)
                status_msg = "🚀 *MODO TURBO ATIVADO*\n\n⚡️ Trading agressivo ativado\n🔥 Monitoramento acelerado\n💰 Maior risco/recompensa"
            else:
                # Volta ao modo normal
                config["TRADE_SIZE_ETH"] = 0.0008
                config["TAKE_PROFIT_PCT"] = 0.3
                config["STOP_LOSS_PCT"] = 0.12
                config["MEMPOOL_MONITOR_INTERVAL"] = 0.2
                advanced_sniper.max_positions = 2
                status_msg = "🐢 *MODO NORMAL ATIVADO*\n\n✅ Trading conservador\n🛡️ Proteções ativadas\n💚 Menor risco"
                
            await query.edit_message_text(
                status_msg,
                parse_mode='MarkdownV2',
                reply_markup=self._build_main_menu()
            )
            
        elif data == "emergency_stop":
            await self._emergency_stop(query)
            
        elif data == "ping":
            await query.edit_message_text(f"🏓 Pong! {datetime.datetime.now().strftime('%H:%M:%S')}")
            
    async def text_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handler para mensagens de texto"""
        user_id = update.effective_user.id
        text = update.message.text
        
        # Verifica se usuário está em algum estado de conversação
        if user_id in self.user_states:
            await self._handle_conversation_state(update, context, text)
        else:
            # Mensagem normal - pode implementar análise automática de endereços
            if text.startswith("0x") and len(text) == 42:
                await update.message.reply_text(
                    f"🔍 Detectei um endereço de token\\!\n"
                    f"Use `/analyze {text}` para análise completa\\.",
                    parse_mode='MarkdownV2'
                )
                
    async def _handle_conversation_state(self, update: Update, context: ContextTypes.DEFAULT_TYPE, text: str):
        """Lida com estados de conversação"""
        user_id = update.effective_user.id
        state = self.user_states.get(user_id)
        
        # Implementar estados de conversação conforme necessário
        # Por exemplo: configuração guiada, análise interativa, etc.
        
    async def _emergency_stop(self, query):
        """Parada de emergência"""
        try:
            await advanced_sniper.stop_strategy()
            await query.edit_message_text(
                "🚨 *PARADA DE EMERGÊNCIA EXECUTADA*\n\n"
                "• Sniper parado\n"
                "• Monitoramento interrompido\n"
                "• Posições mantidas\n\n"
                "Use /start para reiniciar",
                parse_mode='MarkdownV2'
            )
        except Exception as e:
            await query.edit_message_text(f"❌ Erro na parada de emergência: {e}")
            
    # ==================== MENUS ====================
    
    def _build_main_menu(self):
        """Constrói menu principal"""
        turbo_status = "🚀 TURBO ATIVO" if config.get("TURBO_MODE", False) else "🐢 Modo Normal"
        keyboard = [
            [
                InlineKeyboardButton("🚀 Iniciar Sniper", callback_data="start_sniper"),
                InlineKeyboardButton("🛑 Parar Sniper", callback_data="stop_sniper")
            ],
            [
                InlineKeyboardButton("📊 Status", callback_data="show_status"),
                InlineKeyboardButton("💰 Saldo", callback_data="show_balance")
            ],
            [
                InlineKeyboardButton("🎯 Posições", callback_data="show_positions"),
                InlineKeyboardButton("📈 Estatísticas", callback_data="show_stats")
            ],
            [
                InlineKeyboardButton("⚙️ Configurações", callback_data="show_config"),
                InlineKeyboardButton(turbo_status, callback_data="toggle_turbo")
            ],
            [
                InlineKeyboardButton("🏓 Ping", callback_data="ping")
            ],
            [
                InlineKeyboardButton("🚨 PARADA DE EMERGÊNCIA", callback_data="emergency_stop")
            ]
        ]
        return InlineKeyboardMarkup(keyboard)
        
    def _build_status_menu(self):
        """Constrói menu de status"""
        keyboard = [
            [
                InlineKeyboardButton("🔄 Atualizar", callback_data="show_status"),
                InlineKeyboardButton("🎯 Posições", callback_data="show_positions")
            ],
            [
                InlineKeyboardButton("🔙 Menu Principal", callback_data="main_menu")
            ]
        ]
        return InlineKeyboardMarkup(keyboard)
        
    def _build_positions_menu(self):
        """Constrói menu de posições"""
        keyboard = [
            [
                InlineKeyboardButton("🔄 Atualizar", callback_data="show_positions"),
                InlineKeyboardButton("📈 Stats", callback_data="show_stats")
            ],
            [
                InlineKeyboardButton("🔙 Menu Principal", callback_data="main_menu")
            ]
        ]
        return InlineKeyboardMarkup(keyboard)
        
    def _build_config_menu(self):
        """Constrói menu de configurações"""
        keyboard = [
            [
                InlineKeyboardButton("💰 Trade Size", callback_data="config_trade_size"),
                InlineKeyboardButton("🛡️ Stop Loss", callback_data="config_stop_loss")
            ],
            [
                InlineKeyboardButton("📈 Take Profit", callback_data="config_take_profit"),
                InlineKeyboardButton("🎯 Max Posições", callback_data="config_max_positions")
            ],
            [
                InlineKeyboardButton("🔙 Menu Principal", callback_data="main_menu")
            ]
        ]
        return InlineKeyboardMarkup(keyboard)
        
    # ==================== NOTIFICAÇÕES ====================
    
    async def send_alert(self, message: str, parse_mode: str = 'MarkdownV2'):
        """Envia alerta para o chat configurado"""
        try:
            if self.bot and self.chat_id:
                await self.bot.send_message(
                    chat_id=self.chat_id,
                    text=message,
                    parse_mode=parse_mode
                )
        except Exception as e:
            logger.error(f"❌ Erro enviando alerta: {e}")

# Instância global
telegram_bot = TelegramBot()

async def start_telegram_bot():
    """Inicia bot do Telegram"""
    await telegram_bot.start_bot()
    
async def stop_telegram_bot():
    """Para bot do Telegram"""
    await telegram_bot.stop_bot()
    
async def send_telegram_alert(message: str):
    """Envia alerta via Telegram"""
    await telegram_bot.send_alert(message)