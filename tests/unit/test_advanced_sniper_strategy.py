"""
Testes unitários para a estratégia avançada de sniper
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch
from decimal import Decimal
import time

from advanced_sniper_strategy import AdvancedSniperStrategy, Position, StrategyType, PositionStatus


class TestAdvancedSniperStrategy:
    """Testes para AdvancedSniperStrategy"""
    
    @pytest.fixture
    def strategy(self):
        """Instância da estratégia para testes"""
        return AdvancedSniperStrategy()
    
    @pytest.mark.asyncio
    async def test_start_strategy(self, strategy):
        """Testa inicialização da estratégia"""
        with patch('advanced_sniper_strategy.add_mempool_callback') as mock_callback:
            with patch('advanced_sniper_strategy.mempool_monitor') as mock_monitor:
                with patch('advanced_sniper_strategy.send_telegram_alert') as mock_alert:
                    mock_monitor.start_monitoring = AsyncMock()
                    mock_alert.return_value = None
                    
                    await strategy.start_strategy()
        
        assert strategy.is_running == True
        mock_callback.assert_called_once()
        mock_monitor.start_monitoring.assert_called_once()
        mock_alert.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_stop_strategy(self, strategy):
        """Testa parada da estratégia"""
        strategy.is_running = True
        
        with patch('advanced_sniper_strategy.mempool_monitor') as mock_monitor:
            with patch('advanced_sniper_strategy.send_telegram_alert') as mock_alert:
                mock_monitor.stop_monitoring = AsyncMock()
                mock_alert.return_value = None
                
                await strategy.stop_strategy()
        
        assert strategy.is_running == False
        mock_monitor.stop_monitoring.assert_called_once()
        mock_alert.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_on_new_token_memecoin(self, strategy, mock_new_token_event, mock_security_report):
        """Testa processamento de novo memecoin"""
        strategy.is_running = True
        mock_new_token_event.is_memecoin = True
        
        with patch('advanced_sniper_strategy.check_token_safety', return_value=mock_security_report):
            with patch.object(strategy, '_execute_memecoin_strategy') as mock_execute:
                mock_execute.return_value = None
                
                await strategy._on_new_token(mock_new_token_event)
        
        mock_execute.assert_called_once_with(mock_new_token_event, mock_security_report)
    
    @pytest.mark.asyncio
    async def test_on_new_token_altcoin(self, strategy, mock_new_token_event, mock_security_report):
        """Testa processamento de novo altcoin"""
        strategy.is_running = True
        mock_new_token_event.is_memecoin = False
        
        with patch('advanced_sniper_strategy.check_token_safety', return_value=mock_security_report):
            with patch.object(strategy, '_execute_altcoin_strategy') as mock_execute:
                mock_execute.return_value = None
                
                await strategy._on_new_token(mock_new_token_event)
        
        mock_execute.assert_called_once_with(mock_new_token_event, mock_security_report)
    
    @pytest.mark.asyncio
    async def test_on_new_token_unsafe(self, strategy, mock_new_token_event):
        """Testa rejeição de token inseguro"""
        strategy.is_running = True
        
        unsafe_report = Mock()
        unsafe_report.is_safe = False
        unsafe_report.warnings = ["High risk token"]
        
        with patch('advanced_sniper_strategy.check_token_safety', return_value=unsafe_report):
            with patch.object(strategy, '_execute_memecoin_strategy') as mock_execute:
                await strategy._on_new_token(mock_new_token_event)
        
        mock_execute.assert_not_called()  # Não deve executar para token inseguro
    
    @pytest.mark.asyncio
    async def test_on_new_token_max_positions(self, strategy, mock_new_token_event, mock_security_report):
        """Testa limite máximo de posições"""
        strategy.is_running = True
        strategy.max_positions = 1
        
        # Adiciona uma posição existente
        strategy.positions["existing"] = Mock()
        
        with patch('advanced_sniper_strategy.check_token_safety', return_value=mock_security_report):
            with patch.object(strategy, '_execute_memecoin_strategy') as mock_execute:
                await strategy._on_new_token(mock_new_token_event)
        
        mock_execute.assert_not_called()  # Não deve executar se atingiu limite
    
    @pytest.mark.asyncio
    async def test_execute_memecoin_strategy_success(self, strategy, mock_new_token_event, mock_security_report, mock_token_info):
        """Testa execução bem-sucedida da estratégia de memecoin"""
        mock_new_token_event.liquidity_eth = Decimal("0.1")  # Liquidez suficiente
        mock_new_token_event.holders_count = 100  # Holders suficientes
        
        with patch('advanced_sniper_strategy.get_token_info', return_value=mock_token_info):
            with patch('advanced_sniper_strategy.get_wallet_balance', return_value=Decimal("0.01")):
                with patch.object(strategy, '_execute_buy_order') as mock_buy:
                    mock_buy.return_value = None
                    
                    await strategy._execute_memecoin_strategy(mock_new_token_event, mock_security_report)
        
        mock_buy.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_execute_memecoin_strategy_insufficient_liquidity(self, strategy, mock_new_token_event, mock_security_report):
        """Testa rejeição por liquidez insuficiente"""
        mock_new_token_event.liquidity_eth = Decimal("0.01")  # Liquidez baixa
        
        with patch.object(strategy, '_execute_buy_order') as mock_buy:
            await strategy._execute_memecoin_strategy(mock_new_token_event, mock_security_report)
        
        mock_buy.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_execute_buy_order_success(self, strategy, mock_token_info, sample_trade_result):
        """Testa execução bem-sucedida de ordem de compra"""
        token_address = "0x1234567890123456789012345678901234567890"
        amount_eth = Decimal("0.001")
        
        mock_quote = Mock()
        mock_quote.dex_quote.dex_name = "TestDEX"
        
        with patch('advanced_sniper_strategy.get_best_price', return_value=mock_quote):
            with patch('advanced_sniper_strategy.execute_best_trade') as mock_execute:
                mock_execute.return_value = {
                    "success": True,
                    "amount_out": 1000000000000000000,
                    "tx_hash": "0xabc123"
                }
                
                with patch.object(strategy, '_notify_position_opened') as mock_notify:
                    await strategy._execute_buy_order(
                        token_address, amount_eth, StrategyType.MEMECOIN_SNIPER, "TestDEX", mock_token_info
                    )
        
        assert len(strategy.positions) == 1
        assert token_address in strategy.positions
        mock_notify.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_execute_buy_order_no_quote(self, strategy, mock_token_info):
        """Testa falha quando não há cotação disponível"""
        token_address = "0x1234567890123456789012345678901234567890"
        amount_eth = Decimal("0.001")
        
        with patch('advanced_sniper_strategy.get_best_price', return_value=None):
            with patch.object(strategy, '_notify_position_opened') as mock_notify:
                await strategy._execute_buy_order(
                    token_address, amount_eth, StrategyType.MEMECOIN_SNIPER, "TestDEX", mock_token_info
                )
        
        assert len(strategy.positions) == 0
        mock_notify.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_update_positions(self, strategy, mock_position):
        """Testa atualização de posições"""
        strategy.positions[mock_position.token_address] = mock_position
        
        with patch.object(strategy, '_get_current_price', return_value=0.0000015):
            await strategy._update_positions()
        
        position = strategy.positions[mock_position.token_address]
        assert position.current_price == 0.0000015
        assert position.pnl_percentage > 0  # Lucro
    
    @pytest.mark.asyncio
    async def test_check_exit_conditions_stop_loss(self, strategy, mock_position):
        """Testa saída por stop loss"""
        mock_position.current_price = 0.0000008  # Abaixo do stop loss
        strategy.positions[mock_position.token_address] = mock_position
        
        with patch.object(strategy, '_execute_exit') as mock_exit:
            await strategy._check_exit_conditions()
        
        mock_exit.assert_called_once_with(mock_position, "Stop Loss")
    
    @pytest.mark.asyncio
    async def test_check_exit_conditions_take_profit(self, strategy, mock_position):
        """Testa saída por take profit"""
        mock_position.pnl_percentage = 30.0  # Acima do primeiro take profit (25%)
        strategy.positions[mock_position.token_address] = mock_position
        
        with patch.object(strategy, '_execute_partial_exit') as mock_exit:
            await strategy._check_exit_conditions()
        
        mock_exit.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_execute_partial_exit_success(self, strategy, mock_position):
        """Testa saída parcial bem-sucedida"""
        with patch('advanced_sniper_strategy.execute_best_trade') as mock_execute:
            mock_execute.return_value = {
                "success": True,
                "amount_out": 250000000000000000,  # 0.25 ETH
                "tx_hash": "0xdef456"
            }
            
            with patch.object(strategy, '_notify_partial_exit') as mock_notify:
                await strategy._execute_partial_exit(mock_position, 0, 0.25)
        
        assert mock_position.status == PositionStatus.TAKING_PROFIT
        mock_notify.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_execute_exit_success(self, strategy, mock_position):
        """Testa saída completa bem-sucedida"""
        token_address = mock_position.token_address
        strategy.positions[token_address] = mock_position
        
        with patch('advanced_sniper_strategy.execute_best_trade') as mock_execute:
            mock_execute.return_value = {
                "success": True,
                "amount_out": 1200000000000000000,  # 1.2 ETH (lucro)
                "tx_hash": "0xghi789"
            }
            
            with patch.object(strategy, '_notify_position_closed') as mock_notify:
                await strategy._execute_exit(mock_position, "Take Profit")
        
        assert token_address not in strategy.positions
        assert strategy.stats["total_profit"] > 0
        mock_notify.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_check_memecoin_exit_conditions_target_reached(self, strategy, mock_position):
        """Testa saída de memecoin ao atingir target 2x"""
        mock_position.pnl_percentage = 200.0  # 2x
        
        with patch.object(strategy, '_execute_exit') as mock_exit:
            await strategy._check_memecoin_exit_conditions(mock_position)
        
        mock_exit.assert_called_once_with(mock_position, "Target 2x atingido")
    
    @pytest.mark.asyncio
    async def test_check_memecoin_exit_conditions_timeout(self, strategy, mock_position):
        """Testa saída de memecoin por timeout"""
        # Simula posição de 25 horas atrás
        mock_position.entry_time = int(time.time()) - 25 * 3600
        mock_position.pnl_percentage = 30.0  # Menos de 50%
        
        with patch.object(strategy, '_execute_exit') as mock_exit:
            await strategy._check_memecoin_exit_conditions(mock_position)
        
        mock_exit.assert_called_once_with(mock_position, "Timeout 24h")
    
    @pytest.mark.asyncio
    async def test_rebalance_portfolio(self, strategy):
        """Testa rebalanceamento do portfólio"""
        strategy.stats["total_profit"] = Decimal("0.1")  # Lucro para reinvestir
        original_trade_size = strategy.trade_size_eth
        
        with patch('advanced_sniper_strategy.send_telegram_alert') as mock_alert:
            await strategy._rebalance_portfolio()
        
        assert strategy.trade_size_eth > original_trade_size
        mock_alert.assert_called_once()
    
    def test_get_performance_stats(self, strategy):
        """Testa obtenção de estatísticas de performance"""
        strategy.stats["total_trades"] = 10
        strategy.stats["winning_trades"] = 7
        strategy.stats["total_profit"] = Decimal("0.05")
        
        stats = strategy.get_performance_stats()
        
        assert stats["total_trades"] == 10
        assert stats["winning_trades"] == 7
        assert stats["win_rate"] == 70.0
        assert stats["total_profit"] == 0.05
    
    def test_get_active_positions(self, strategy, mock_position):
        """Testa obtenção de posições ativas"""
        strategy.positions[mock_position.token_address] = mock_position
        
        positions = strategy.get_active_positions()
        
        assert len(positions) == 1
        assert positions[0]["token_symbol"] == "TEST"
        assert positions[0]["strategy_type"] == "memecoin_sniper"
    
    @pytest.mark.asyncio
    async def test_get_current_price_success(self, strategy):
        """Testa obtenção de preço atual"""
        token_address = "0x1234567890123456789012345678901234567890"
        
        mock_quote = Mock()
        mock_quote.dex_quote.amount_out = 1200000000000000000  # 1.2 ETH
        
        with patch('advanced_sniper_strategy.get_best_price', return_value=mock_quote):
            price = await strategy._get_current_price(token_address)
        
        assert price == 1.2
    
    @pytest.mark.asyncio
    async def test_get_current_price_no_quote(self, strategy):
        """Testa quando não consegue obter preço"""
        token_address = "0x1234567890123456789012345678901234567890"
        
        with patch('advanced_sniper_strategy.get_best_price', return_value=None):
            price = await strategy._get_current_price(token_address)
        
        assert price is None
    
    @pytest.mark.asyncio
    async def test_notify_position_opened(self, strategy, mock_position):
        """Testa notificação de posição aberta"""
        with patch('advanced_sniper_strategy.send_telegram_alert') as mock_alert:
            await strategy._notify_position_opened(mock_position)
        
        mock_alert.assert_called_once()
        call_args = mock_alert.call_args[0][0]
        assert "NOVA POSIÇÃO ABERTA" in call_args
        assert mock_position.token_symbol in call_args
    
    @pytest.mark.asyncio
    async def test_notify_partial_exit(self, strategy, mock_position):
        """Testa notificação de saída parcial"""
        with patch('advanced_sniper_strategy.send_telegram_alert') as mock_alert:
            await strategy._notify_partial_exit(mock_position, 0.25, 0.001)
        
        mock_alert.assert_called_once()
        call_args = mock_alert.call_args[0][0]
        assert "TAKE PROFIT 25%" in call_args
    
    @pytest.mark.asyncio
    async def test_notify_position_closed(self, strategy, mock_position):
        """Testa notificação de posição fechada"""
        with patch('advanced_sniper_strategy.send_telegram_alert') as mock_alert:
            await strategy._notify_position_closed(mock_position, "Take Profit", 0.002)
        
        mock_alert.assert_called_once()
        call_args = mock_alert.call_args[0][0]
        assert "POSIÇÃO FECHADA" in call_args
        assert "Take Profit" in call_args