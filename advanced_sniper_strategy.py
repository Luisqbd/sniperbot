"""
Estratégia avançada de sniper para memecoins e altcoins
Combina múltiplas estratégias com proteções e otimizações
"""

import asyncio
import logging
import time
from typing import Dict, List, Optional, Set
from dataclasses import dataclass, asdict
from decimal import Decimal
from enum import Enum

from web3 import Web3

from config import config
from mempool_monitor import mempool_monitor, NewTokenEvent, add_mempool_callback
from security_checker import check_token_safety, SecurityReport
from dex_aggregator import get_best_price, execute_best_trade
from utils import get_token_info, get_wallet_balance
from risk_manager import risk_manager
from notifier import send as _send_telegram_alert

async def send_telegram_alert(message: str):
    """Wrapper assíncrono para envio de alertas do Telegram"""
    try:
        _send_telegram_alert(message)
    except Exception as e:
        logger.error(f"Erro enviando alerta: {e}")

logger = logging.getLogger(__name__)

class StrategyType(Enum):
    MEMECOIN_SNIPER = "memecoin_sniper"
    ALTCOIN_SWING = "altcoin_swing"
    ARBITRAGE = "arbitrage"

class PositionStatus(Enum):
    ACTIVE = "active"
    TAKING_PROFIT = "taking_profit"
    STOP_LOSS = "stop_loss"
    CLOSED = "closed"

@dataclass
class Position:
    """Posição de trading"""
    token_address: str
    token_symbol: str
    strategy_type: StrategyType
    entry_price: float
    entry_amount: Decimal
    entry_time: int
    current_price: float
    current_value: Decimal
    pnl: float
    pnl_percentage: float
    status: PositionStatus
    take_profit_levels: List[float]
    stop_loss_price: float
    trailing_stop_price: float
    dex_name: str
    transaction_hash: str
    
    def to_dict(self) -> dict:
        """Converte para dicionário"""
        data = asdict(self)
        data['strategy_type'] = self.strategy_type.value
        data['status'] = self.status.value
        data['entry_amount'] = str(self.entry_amount)
        data['current_value'] = str(self.current_value)
        return data

class AdvancedSniperStrategy:
    """Estratégia avançada de sniper com múltiplas funcionalidades"""
    
    def __init__(self):
        self.w3 = Web3(Web3.HTTPProvider(config["RPC_URL"]))
        self.is_running = False
        self.is_paused = False  # Estado de pausa
        self.positions: Dict[str, Position] = {}
        self.processed_tokens: Set[str] = set()
        
        # Configurações da estratégia (ajustadas dinamicamente pelo modo turbo)
        self.max_positions = config.get("MAX_POSITIONS", 3)
        self.trade_size_eth = Decimal(str(config.get("TRADE_SIZE_ETH", 0.001)))
        self.min_liquidity = Decimal(str(config.get("MEMECOIN_MIN_LIQUIDITY", 0.05)))
        
        # Configurações de take profit e stop loss
        self.take_profit_levels = [0.25, 0.50, 1.0, 2.0]  # 25%, 50%, 100%, 200%
        self.stop_loss_pct = config.get("STOP_LOSS_PCT", 0.15)  # 15%
        self.trailing_stop_pct = 0.12  # 12%
        
        # Configurações de memecoin
        self.memecoin_config = {
            "max_investment": Decimal(str(config.get("MEMECOIN_MAX_INVESTMENT", 0.008))),
            "target_profit": config.get("MEMECOIN_TARGET_PROFIT", 2.0),
            "max_age_hours": config.get("MEMECOIN_MAX_AGE_HOURS", 24),
            "min_holders": config.get("MEMECOIN_MIN_HOLDERS", 50),
            "social_score_threshold": 0.3
        }
        
        # Configurações de altcoin
        self.altcoin_config = {
            "min_market_cap": config.get("ALTCOIN_MIN_MARKET_CAP", 1_000_000),
            "max_market_cap": config.get("ALTCOIN_MAX_MARKET_CAP", 100_000_000),
            "min_volume_24h": config.get("ALTCOIN_MIN_VOLUME_24H", 100_000),
            "rebalance_interval": 86400,  # 24 horas
            "profit_reinvest_pct": config.get("ALTCOIN_PROFIT_REINVEST_PCT", 0.5)
        }
        
        # Estatísticas
        self.stats = {
            "total_trades": 0,
            "winning_trades": 0,
            "total_profit": Decimal("0"),
            "best_trade": 0.0,
            "worst_trade": 0.0,
            "start_time": int(time.time())
        }
        
        logger.info(f"✅ Estratégia inicializada - Modo Turbo: {config.get('TURBO_MODE', False)}")
        logger.info(f"💰 Trade Size: {self.trade_size_eth} ETH")
        logger.info(f"🛡️ Stop Loss: {self.stop_loss_pct*100:.1f}%")
        logger.info(f"📈 Take Profit: {config.get('TAKE_PROFIT_PCT', 0.3)*100:.1f}%")
        
    async def start_strategy(self):
        """Inicia a estratégia de sniper"""
        if self.is_running:
            logger.warning("Estratégia já está rodando")
            return
            
        self.is_running = True
        logger.info("🚀 Iniciando estratégia avançada de sniper...")
        
        # Adiciona callback para novos tokens
        add_mempool_callback(self._on_new_token)
        
        # Inicia monitoramento de mempool
        asyncio.create_task(mempool_monitor.start_monitoring())
        
        # Inicia loop de monitoramento de posições
        asyncio.create_task(self._position_monitor_loop())
        
        # Inicia rebalanceamento de portfólio
        asyncio.create_task(self._portfolio_rebalance_loop())
        
        await send_telegram_alert("🚀 Sniper Bot iniciado com sucesso!")
        
    async def stop_strategy(self):
        """Para a estratégia"""
        self.is_running = False
        await mempool_monitor.stop_monitoring()
        logger.info("🛑 Estratégia de sniper parada")
        await send_telegram_alert("🛑 Sniper Bot parado")
        
    def pause_strategy(self):
        """Pausa a estratégia temporariamente (mantém posições)"""
        self.is_paused = True
        logger.info("⏸️ Estratégia pausada - posições continuam monitoradas")
        
    def resume_strategy(self):
        """Retoma a estratégia"""
        self.is_paused = False
        logger.info("▶️ Estratégia retomada")
        
    def toggle_turbo_mode(self, enable: bool):
        """Ativa ou desativa modo turbo"""
        config["TURBO_MODE"] = enable
        
        if enable:
            # Ativa modo turbo
            self.trade_size_eth = Decimal(str(config.get("TURBO_TRADE_SIZE_ETH", 0.0012)))
            self.stop_loss_pct = config.get("TURBO_STOP_LOSS_PCT", 0.08)
            self.max_positions = config.get("TURBO_MAX_POSITIONS", 3)
            logger.info("🚀 Modo TURBO ativado - Trading agressivo")
        else:
            # Volta ao modo normal
            self.trade_size_eth = Decimal(str(config.get("TRADE_SIZE_ETH", 0.0008)))
            self.stop_loss_pct = config.get("STOP_LOSS_PCT", 0.12)
            self.max_positions = config.get("MAX_POSITIONS", 2)
            logger.info("🐢 Modo NORMAL ativado - Trading conservador")
        
    async def _on_new_token(self, event: NewTokenEvent):
        """Callback para novos tokens detectados"""
        try:
            if not self.is_running:
                return
                
            # Verifica se estratégia está pausada
            if self.is_paused:
                logger.debug(f"⏸️ Estratégia pausada - ignorando token {event.token_address[:10]}...")
                return
                
            token_address = event.token_address
            
            # Verifica se já processamos este token
            if token_address in self.processed_tokens:
                return
                
            self.processed_tokens.add(token_address)
            
            logger.info(f"🎯 Analisando novo token: {token_address[:10]}...")
            
            # Verifica se temos posições disponíveis
            if len(self.positions) >= self.max_positions:
                logger.info("⚠️ Máximo de posições atingido")
                return
                
            # Verifica segurança do token
            security_report = await check_token_safety(token_address)
            if not security_report.is_safe:
                logger.warning(f"❌ Token rejeitado por segurança: {security_report.warnings}")
                return
                
            # Determina estratégia baseada no tipo de token
            if event.is_memecoin:
                await self._execute_memecoin_strategy(event, security_report)
            else:
                await self._execute_altcoin_strategy(event, security_report)
                
        except Exception as e:
            logger.error(f"❌ Erro processando novo token: {e}")
            
    async def _execute_memecoin_strategy(self, event: NewTokenEvent, security_report: SecurityReport):
        """Executa estratégia para memecoins"""
        try:
            token_address = event.token_address
            
            # Verifica critérios específicos de memecoin
            if event.liquidity_eth < self.min_liquidity:
                logger.info(f"❌ Liquidez insuficiente: {event.liquidity_eth}")
                return
                
            if event.holders_count < self.memecoin_config["min_holders"]:
                logger.info(f"❌ Poucos holders: {event.holders_count}")
                return
                
            # Obtém informações do token
            token_info = await get_token_info(token_address)
            if not token_info:
                logger.warning("❌ Não foi possível obter informações do token")
                return
                
            # Calcula tamanho da posição
            position_size = min(
                self.memecoin_config["max_investment"],
                self.trade_size_eth
            )
            
            # Verifica saldo disponível
            wallet_balance = await get_wallet_balance()
            if wallet_balance < position_size:
                logger.warning(f"❌ Saldo insuficiente: {wallet_balance} < {position_size}")
                return
                
            # Executa compra
            await self._execute_buy_order(
                token_address=token_address,
                amount_eth=position_size,
                strategy_type=StrategyType.MEMECOIN_SNIPER,
                dex_name=event.dex_name,
                token_info=token_info
            )
            
        except Exception as e:
            logger.error(f"❌ Erro na estratégia de memecoin: {e}")
            
    async def _execute_altcoin_strategy(self, event: NewTokenEvent, security_report: SecurityReport):
        """Executa estratégia para altcoins fundamentadas"""
        try:
            token_address = event.token_address
            
            # Obtém informações do token
            token_info = await get_token_info(token_address)
            if not token_info:
                return
                
            # Verifica critérios de altcoin
            market_cap = token_info.get("market_cap", 0)
            volume_24h = token_info.get("volume_24h", 0)
            
            if market_cap < self.altcoin_config["min_market_cap"]:
                logger.info(f"❌ Market cap muito baixo: ${market_cap:,.0f}")
                return
                
            if market_cap > self.altcoin_config["max_market_cap"]:
                logger.info(f"❌ Market cap muito alto: ${market_cap:,.0f}")
                return
                
            if volume_24h < self.altcoin_config["min_volume_24h"]:
                logger.info(f"❌ Volume 24h insuficiente: ${volume_24h:,.0f}")
                return
                
            # Calcula tamanho da posição (maior para altcoins)
            position_size = self.trade_size_eth * Decimal("2")  # 2x para altcoins
            
            # Executa compra
            await self._execute_buy_order(
                token_address=token_address,
                amount_eth=position_size,
                strategy_type=StrategyType.ALTCOIN_SWING,
                dex_name=event.dex_name,
                token_info=token_info
            )
            
        except Exception as e:
            logger.error(f"❌ Erro na estratégia de altcoin: {e}")
            
    async def _execute_buy_order(
        self, 
        token_address: str, 
        amount_eth: Decimal, 
        strategy_type: StrategyType,
        dex_name: str,
        token_info: dict
    ):
        """Executa ordem de compra"""
        try:
            weth_address = config["WETH"]
            amount_wei = int(amount_eth * Decimal("1e18"))
            
            # Obtém melhor preço
            best_quote = await get_best_price(
                token_in=weth_address,
                token_out=token_address,
                amount_in=amount_wei,
                is_buy=True
            )
            
            if not best_quote:
                logger.warning("❌ Nenhuma cotação disponível")
                return
                
            # Executa trade
            result = await execute_best_trade(
                token_in=weth_address,
                token_out=token_address,
                amount_in=amount_wei,
                is_buy=True
            )
            
            if not result.get("success"):
                logger.error(f"❌ Falha na compra: {result.get('error')}")
                return
                
            # Cria posição
            position = Position(
                token_address=token_address,
                token_symbol=token_info.get("symbol", "UNKNOWN"),
                strategy_type=strategy_type,
                entry_price=float(amount_eth / Decimal(str(result["amount_out"] / 1e18))),
                entry_amount=Decimal(str(result["amount_out"] / 1e18)),
                entry_time=int(time.time()),
                current_price=float(amount_eth / Decimal(str(result["amount_out"] / 1e18))),
                current_value=amount_eth,
                pnl=0.0,
                pnl_percentage=0.0,
                status=PositionStatus.ACTIVE,
                take_profit_levels=self.take_profit_levels.copy(),
                stop_loss_price=float(amount_eth / Decimal(str(result["amount_out"] / 1e18))) * (1 - self.stop_loss_pct),
                trailing_stop_price=0.0,
                dex_name=best_quote.dex_quote.dex_name,
                transaction_hash=result["tx_hash"]
            )
            
            self.positions[token_address] = position
            self.stats["total_trades"] += 1
            
            # Notifica compra
            await self._notify_position_opened(position)
            
            logger.info(f"✅ Posição aberta: {token_info.get('symbol')} - {amount_eth} ETH")
            
        except Exception as e:
            logger.error(f"❌ Erro executando compra: {e}")
            
    async def _position_monitor_loop(self):
        """Loop de monitoramento de posições"""
        while self.is_running:
            try:
                await self._update_positions()
                await self._check_exit_conditions()
                await asyncio.sleep(5)  # Verifica a cada 5 segundos
            except Exception as e:
                logger.error(f"❌ Erro no monitoramento de posições: {e}")
                await asyncio.sleep(10)
                
    async def _update_positions(self):
        """Atualiza preços e valores das posições"""
        for token_address, position in self.positions.items():
            try:
                if position.status != PositionStatus.ACTIVE:
                    continue
                    
                # Obtém preço atual
                current_price = await self._get_current_price(token_address)
                if not current_price:
                    continue
                    
                # Atualiza posição
                position.current_price = current_price
                position.current_value = Decimal(str(current_price)) * position.entry_amount
                position.pnl = float(position.current_value - (position.entry_price * position.entry_amount))
                position.pnl_percentage = (current_price / position.entry_price - 1) * 100
                
                # Atualiza trailing stop
                if position.pnl_percentage > 0:
                    new_trailing_stop = current_price * (1 - self.trailing_stop_pct)
                    if new_trailing_stop > position.trailing_stop_price:
                        position.trailing_stop_price = new_trailing_stop
                        
            except Exception as e:
                logger.error(f"❌ Erro atualizando posição {token_address}: {e}")
                
    async def _check_exit_conditions(self):
        """Verifica condições de saída das posições"""
        for token_address, position in list(self.positions.items()):
            try:
                if position.status != PositionStatus.ACTIVE:
                    continue
                    
                # Verifica stop loss
                if position.current_price <= position.stop_loss_price:
                    await self._execute_exit(position, "Stop Loss")
                    continue
                    
                # Verifica trailing stop
                if position.trailing_stop_price > 0 and position.current_price <= position.trailing_stop_price:
                    await self._execute_exit(position, "Trailing Stop")
                    continue
                    
                # Verifica take profit levels
                for i, tp_level in enumerate(position.take_profit_levels):
                    if position.pnl_percentage >= tp_level * 100:
                        await self._execute_partial_exit(position, i, tp_level)
                        break
                        
                # Verifica condições específicas por estratégia
                if position.strategy_type == StrategyType.MEMECOIN_SNIPER:
                    await self._check_memecoin_exit_conditions(position)
                elif position.strategy_type == StrategyType.ALTCOIN_SWING:
                    await self._check_altcoin_exit_conditions(position)
                    
            except Exception as e:
                logger.error(f"❌ Erro verificando saída {token_address}: {e}")
                
    async def _check_memecoin_exit_conditions(self, position: Position):
        """Verifica condições específicas de saída para memecoins"""
        # Saída automática ao atingir 2x (200% de lucro)
        if position.pnl_percentage >= 200:
            await self._execute_exit(position, "Target 2x atingido")
            
        # Saída por tempo (24h para memecoins)
        age_hours = (time.time() - position.entry_time) / 3600
        if age_hours > 24 and position.pnl_percentage < 50:  # Se não teve 50% em 24h
            await self._execute_exit(position, "Timeout 24h")
            
    async def _check_altcoin_exit_conditions(self, position: Position):
        """Verifica condições específicas de saída para altcoins"""
        # Lógica mais conservadora para altcoins
        age_days = (time.time() - position.entry_time) / 86400
        
        # Saída por tempo (7 dias para altcoins)
        if age_days > 7 and position.pnl_percentage < 20:  # Se não teve 20% em 7 dias
            await self._execute_exit(position, "Timeout 7 dias")
            
    async def _execute_partial_exit(self, position: Position, level_index: int, tp_level: float):
        """Executa saída parcial no take profit"""
        try:
            # Remove o nível de take profit já atingido
            position.take_profit_levels.pop(level_index)
            
            # Vende 25% da posição
            sell_amount = position.entry_amount * Decimal("0.25")
            
            result = await execute_best_trade(
                token_in=position.token_address,
                token_out=config["WETH"],
                amount_in=int(sell_amount * Decimal("1e18")),
                is_buy=False
            )
            
            if result.get("success"):
                # Atualiza posição
                position.entry_amount -= sell_amount
                position.status = PositionStatus.TAKING_PROFIT
                
                profit = float(Decimal(str(result["amount_out"] / 1e18)) - (sell_amount * Decimal(str(position.entry_price))))
                self.stats["total_profit"] += Decimal(str(profit))
                
                await self._notify_partial_exit(position, tp_level, profit)
                
                logger.info(f"✅ Take profit {tp_level*100:.0f}%: {position.token_symbol} - Lucro: {profit:.4f} ETH")
                
        except Exception as e:
            logger.error(f"❌ Erro na saída parcial: {e}")
            
    async def _execute_exit(self, position: Position, reason: str):
        """Executa saída completa da posição"""
        try:
            result = await execute_best_trade(
                token_in=position.token_address,
                token_out=config["WETH"],
                amount_in=int(position.entry_amount * Decimal("1e18")),
                is_buy=False
            )
            
            if result.get("success"):
                # Calcula lucro/prejuízo
                exit_value = Decimal(str(result["amount_out"] / 1e18))
                entry_value = position.entry_amount * Decimal(str(position.entry_price))
                pnl = float(exit_value - entry_value)
                
                # Atualiza estatísticas
                self.stats["total_profit"] += Decimal(str(pnl))
                if pnl > 0:
                    self.stats["winning_trades"] += 1
                    if pnl > self.stats["best_trade"]:
                        self.stats["best_trade"] = pnl
                else:
                    if pnl < self.stats["worst_trade"]:
                        self.stats["worst_trade"] = pnl
                        
                # Remove posição
                position.status = PositionStatus.CLOSED
                del self.positions[position.token_address]
                
                await self._notify_position_closed(position, reason, pnl)
                
                logger.info(f"✅ Posição fechada: {position.token_symbol} - {reason} - PnL: {pnl:.4f} ETH")
                
        except Exception as e:
            logger.error(f"❌ Erro fechando posição: {e}")
            
    async def _portfolio_rebalance_loop(self):
        """Loop de rebalanceamento do portfólio"""
        while self.is_running:
            try:
                await asyncio.sleep(self.altcoin_config["rebalance_interval"])
                await self._rebalance_portfolio()
            except Exception as e:
                logger.error(f"❌ Erro no rebalanceamento: {e}")
                await asyncio.sleep(3600)  # Tenta novamente em 1 hora
                
    async def _rebalance_portfolio(self):
        """Rebalanceia o portfólio reinvestindo lucros"""
        try:
            total_profit = self.stats["total_profit"]
            if total_profit <= 0:
                return
                
            # Reinveste parte dos lucros
            reinvest_amount = total_profit * Decimal(str(self.altcoin_config["profit_reinvest_pct"]))
            
            if reinvest_amount > Decimal("0.01"):  # Mínimo 0.01 ETH
                # Aumenta tamanho das próximas posições
                self.trade_size_eth += reinvest_amount / Decimal("10")  # Distribui em 10 trades
                
                logger.info(f"📈 Portfólio rebalanceado: +{reinvest_amount:.4f} ETH reinvestidos")
                await send_telegram_alert(f"📈 Rebalanceamento: +{reinvest_amount:.4f} ETH reinvestidos")
                
        except Exception as e:
            logger.error(f"❌ Erro no rebalanceamento: {e}")
            
    async def _get_current_price(self, token_address: str) -> Optional[float]:
        """Obtém preço atual do token"""
        try:
            # Usa cotação pequena para obter preço
            quote = await get_best_price(
                token_in=token_address,
                token_out=config["WETH"],
                amount_in=int(1e18),  # 1 token
                is_buy=False
            )
            
            if quote:
                return quote.dex_quote.amount_out / 1e18
            return None
            
        except Exception as e:
            logger.debug(f"Erro obtendo preço de {token_address}: {e}")
            return None
            
    async def _notify_position_opened(self, position: Position):
        """Notifica abertura de posição"""
        message = (
            f"🎯 NOVA POSIÇÃO ABERTA\n\n"
            f"Token: {position.token_symbol}\n"
            f"Estratégia: {position.strategy_type.value}\n"
            f"Valor: {position.entry_amount:.4f} ETH\n"
            f"Preço: {position.entry_price:.8f}\n"
            f"DEX: {position.dex_name}\n"
            f"TX: {position.transaction_hash[:10]}..."
        )
        await send_telegram_alert(message)
        
    async def _notify_partial_exit(self, position: Position, tp_level: float, profit: float):
        """Notifica saída parcial"""
        message = (
            f"💰 TAKE PROFIT {tp_level*100:.0f}%\n\n"
            f"Token: {position.token_symbol}\n"
            f"Lucro: +{profit:.4f} ETH\n"
            f"PnL: +{position.pnl_percentage:.1f}%"
        )
        await send_telegram_alert(message)
        
    async def _notify_position_closed(self, position: Position, reason: str, pnl: float):
        """Notifica fechamento de posição"""
        emoji = "💰" if pnl > 0 else "📉"
        message = (
            f"{emoji} POSIÇÃO FECHADA\n\n"
            f"Token: {position.token_symbol}\n"
            f"Motivo: {reason}\n"
            f"PnL: {pnl:+.4f} ETH ({position.pnl_percentage:+.1f}%)\n"
            f"Duração: {(time.time() - position.entry_time) / 3600:.1f}h"
        )
        await send_telegram_alert(message)
        
    def get_performance_stats(self) -> dict:
        """Retorna estatísticas de performance"""
        total_trades = self.stats["total_trades"]
        winning_trades = self.stats["winning_trades"]
        win_rate = (winning_trades / total_trades * 100) if total_trades > 0 else 0
        
        return {
            "active_positions": len(self.positions),
            "max_positions": self.max_positions,
            "total_trades": total_trades,
            "winning_trades": winning_trades,
            "win_rate": win_rate,
            "total_profit": float(self.stats["total_profit"]),
            "best_trade": self.stats["best_trade"],
            "worst_trade": self.stats["worst_trade"],
            "uptime_hours": (time.time() - self.stats["start_time"]) / 3600
        }
        
    def get_active_positions(self) -> List[dict]:
        """Retorna posições ativas"""
        return [pos.to_dict() for pos in self.positions.values()]

# Instância global
advanced_sniper = AdvancedSniperStrategy()