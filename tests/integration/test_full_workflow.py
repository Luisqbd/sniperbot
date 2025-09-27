"""
Testes de integração para o workflow completo do bot
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch
from decimal import Decimal

from advanced_sniper_strategy import advanced_sniper
from mempool_monitor import NewTokenEvent
from security_checker import SecurityReport
from telegram_bot import telegram_bot


class TestFullWorkflow:
    """Testes de integração do workflow completo"""
    
    @pytest.mark.asyncio
    async def test_complete_memecoin_workflow(self):
        """Testa workflow completo de detecção e trade de memecoin"""
        
        # 1. Simula detecção de novo token
        new_token_event = NewTokenEvent(
            token_address="0x1234567890123456789012345678901234567890",
            pair_address="0x0987654321098765432109876543210987654321",
            dex_name="TestDEX",
            liquidity_eth=Decimal("1.0"),
            block_number=1000000,
            transaction_hash="0xabc123",
            timestamp=1234567890,
            holders_count=100,
            social_score=0.8,
            is_memecoin=True
        )
        
        # 2. Mock de verificação de segurança (token seguro)
        security_report = SecurityReport(
            token_address=new_token_event.token_address,
            is_safe=True,
            risk_score=0.2,
            honeypot_risk=0.1,
            rugpull_risk=0.1,
            liquidity_risk=0.1,
            contract_risk=0.1,
            warnings=[],
            timestamp=1234567890
        )
        
        # 3. Mock de informações do token
        token_info = {
            "name": "TestMemeCoin",
            "symbol": "TMC",
            "decimals": 18,
            "totalSupply": 1000000000,
            "holders": 100
        }
        
        # 4. Mock de cotação
        mock_quote = Mock()
        mock_quote.dex_quote.dex_name = "TestDEX"
        mock_quote.dex_quote.amount_out = 1000000000000000000  # 1 token
        
        # 5. Mock de execução de trade
        trade_result = {
            "success": True,
            "amount_out": 1000000000000000000,
            "tx_hash": "0xdef456",
            "gas_used": 180000,
            "total_cost": 0.0045,
            "dex_used": "TestDEX"
        }
        
        # Configura mocks
        with patch('advanced_sniper_strategy.check_token_safety', return_value=security_report):
            with patch('advanced_sniper_strategy.get_token_info', return_value=token_info):
                with patch('advanced_sniper_strategy.get_wallet_balance', return_value=Decimal("0.01")):
                    with patch('advanced_sniper_strategy.get_best_price', return_value=mock_quote):
                        with patch('advanced_sniper_strategy.execute_best_trade', return_value=trade_result):
                            with patch('advanced_sniper_strategy.send_telegram_alert') as mock_alert:
                                
                                # Inicia estratégia
                                advanced_sniper.is_running = True
                                advanced_sniper.positions.clear()
                                
                                # Processa novo token
                                await advanced_sniper._on_new_token(new_token_event)
        
        # Verifica resultados
        assert len(advanced_sniper.positions) == 1
        assert new_token_event.token_address in advanced_sniper.positions
        
        position = advanced_sniper.positions[new_token_event.token_address]
        assert position.token_symbol == "TMC"
        assert position.dex_name == "TestDEX"
        assert position.transaction_hash == "0xdef456"
        
        # Verifica notificação
        mock_alert.assert_called()
        
    @pytest.mark.asyncio
    async def test_security_rejection_workflow(self):
        """Testa workflow quando token é rejeitado por segurança"""
        
        # Token inseguro
        new_token_event = NewTokenEvent(
            token_address="0x1234567890123456789012345678901234567890",
            pair_address="0x0987654321098765432109876543210987654321",
            dex_name="TestDEX",
            liquidity_eth=Decimal("1.0"),
            block_number=1000000,
            transaction_hash="0xabc123",
            timestamp=1234567890,
            holders_count=100,
            social_score=0.8,
            is_memecoin=True
        )
        
        # Relatório de segurança negativo
        security_report = SecurityReport(
            token_address=new_token_event.token_address,
            is_safe=False,
            risk_score=0.8,
            honeypot_risk=0.9,
            rugpull_risk=0.7,
            liquidity_risk=0.8,
            contract_risk=0.8,
            warnings=["Alto risco de honeypot", "Alto risco de rugpull"],
            timestamp=1234567890
        )
        
        with patch('advanced_sniper_strategy.check_token_safety', return_value=security_report):
            with patch('advanced_sniper_strategy.execute_best_trade') as mock_trade:
                
                advanced_sniper.is_running = True
                advanced_sniper.positions.clear()
                
                await advanced_sniper._on_new_token(new_token_event)
        
        # Verifica que não executou trade
        assert len(advanced_sniper.positions) == 0
        mock_trade.assert_not_called()
        
    @pytest.mark.asyncio
    async def test_position_exit_workflow(self):
        """Testa workflow completo de saída de posição"""
        
        # Cria posição mock
        from advanced_sniper_strategy import Position, StrategyType, PositionStatus
        import time
        
        position = Position(
            token_address="0x1234567890123456789012345678901234567890",
            token_symbol="TEST",
            strategy_type=StrategyType.MEMECOIN_SNIPER,
            entry_price=0.000001,
            entry_amount=Decimal("1000000"),
            entry_time=int(time.time()) - 3600,
            current_price=0.0000025,  # 2.5x lucro
            current_value=Decimal("2500000"),
            pnl=1500000.0,
            pnl_percentage=150.0,
            status=PositionStatus.ACTIVE,
            take_profit_levels=[0.25, 0.50, 1.0, 2.0],
            stop_loss_price=0.00000085,
            trailing_stop_price=0.0,
            dex_name="TestDEX",
            transaction_hash="0xabc123"
        )
        
        advanced_sniper.positions[position.token_address] = position
        
        # Mock de execução de venda
        sell_result = {
            "success": True,
            "amount_out": 2500000000000000000,  # 2.5 ETH
            "tx_hash": "0xsell123"
        }
        
        with patch('advanced_sniper_strategy.execute_best_trade', return_value=sell_result):
            with patch('advanced_sniper_strategy.send_telegram_alert') as mock_alert:
                
                # Executa saída por take profit
                await advanced_sniper._execute_exit(position, "Take Profit 150%")
        
        # Verifica que posição foi removida
        assert position.token_address not in advanced_sniper.positions
        
        # Verifica que lucro foi contabilizado
        assert advanced_sniper.stats["total_profit"] > 0
        assert advanced_sniper.stats["winning_trades"] > 0
        
        # Verifica notificação
        mock_alert.assert_called()
        
    @pytest.mark.asyncio
    async def test_telegram_integration_workflow(self):
        """Testa integração completa com Telegram"""
        
        # Mock do update do Telegram
        mock_update = Mock()
        mock_update.message.reply_text = AsyncMock()
        mock_update.effective_user.id = 123456789
        
        # Mock do context
        mock_context = Mock()
        mock_context.args = ["0x1234567890123456789012345678901234567890"]
        
        # Mock de informações do token
        token_info = {
            "name": "TestToken",
            "symbol": "TEST",
            "decimals": 18,
            "totalSupply": 1000000000,
            "holders": 100
        }
        
        # Mock de relatório de segurança
        security_report = SecurityReport(
            token_address="0x1234567890123456789012345678901234567890",
            is_safe=True,
            risk_score=0.2,
            honeypot_risk=0.1,
            rugpull_risk=0.1,
            liquidity_risk=0.1,
            contract_risk=0.3,
            warnings=[],
            timestamp=1234567890
        )
        
        # Mock de cotação
        mock_quote = Mock()
        mock_quote.dex_quote.amount_out = 1200000000000000000  # 1.2 ETH
        mock_quote.dex_quote.dex_name = "TestDEX"
        
        with patch('telegram_bot.get_token_info', return_value=token_info):
            with patch('telegram_bot.check_token_safety', return_value=security_report):
                with patch('telegram_bot.get_best_price', return_value=mock_quote):
                    
                    # Testa comando de análise
                    await telegram_bot.analyze_command(mock_update, mock_context)
        
        # Verifica que resposta foi enviada
        mock_update.message.reply_text.assert_called()
        call_args = mock_update.message.reply_text.call_args[0][0]
        assert "ANÁLISE DO TOKEN" in call_args
        assert "TestToken" in call_args
        assert "✅ Seguro" in call_args
        
    @pytest.mark.asyncio
    async def test_dex_fallback_workflow(self):
        """Testa workflow de fallback entre DEXs"""
        
        from dex_aggregator import DexQuote, BestQuote, DexType
        
        # Primeira DEX falha
        quote1 = DexQuote(
            dex_name="DEX1",
            dex_type=DexType.UNISWAP_V2,
            router_address="0x1111111111111111111111111111111111111111",
            amount_out=0,  # Falha
            price_impact=1.0,
            gas_estimate=0,
            slippage=1.0,
            liquidity=Decimal("0"),
            is_available=False,
            error="Insufficient liquidity"
        )
        
        # Segunda DEX funciona
        quote2 = DexQuote(
            dex_name="DEX2",
            dex_type=DexType.UNISWAP_V2,
            router_address="0x2222222222222222222222222222222222222222",
            amount_out=950000000000000000,
            price_impact=0.05,
            gas_estimate=200000,
            slippage=0.02,
            liquidity=Decimal("2.0"),
            is_available=True
        )
        
        best_quote = BestQuote(
            dex_quote=quote2,
            net_amount=930000000000000000,
            total_cost=20000000000000000,
            efficiency_score=0.85
        )
        
        with patch('dex_aggregator.dex_aggregator') as mock_aggregator:
            mock_aggregator.get_best_quote = AsyncMock(return_value=best_quote)
            
            from dex_aggregator import get_best_price
            result = await get_best_price(
                "0x1111111111111111111111111111111111111111",
                "0x2222222222222222222222222222222222222222",
                1000000000000000000,
                True
            )
        
        # Verifica que usou a segunda DEX
        assert result.dex_quote.dex_name == "DEX2"
        assert result.dex_quote.is_available == True
        
    @pytest.mark.asyncio
    async def test_error_handling_workflow(self):
        """Testa tratamento de erros no workflow"""
        
        new_token_event = NewTokenEvent(
            token_address="0x1234567890123456789012345678901234567890",
            pair_address="0x0987654321098765432109876543210987654321",
            dex_name="TestDEX",
            liquidity_eth=Decimal("1.0"),
            block_number=1000000,
            transaction_hash="0xabc123",
            timestamp=1234567890,
            holders_count=100,
            social_score=0.8,
            is_memecoin=True
        )
        
        # Simula erro na verificação de segurança
        with patch('advanced_sniper_strategy.check_token_safety', side_effect=Exception("API Error")):
            with patch('advanced_sniper_strategy.execute_best_trade') as mock_trade:
                
                advanced_sniper.is_running = True
                advanced_sniper.positions.clear()
                
                # Não deve quebrar o sistema
                await advanced_sniper._on_new_token(new_token_event)
        
        # Verifica que não executou trade devido ao erro
        assert len(advanced_sniper.positions) == 0
        mock_trade.assert_not_called()
        
    @pytest.mark.asyncio
    async def test_performance_monitoring_workflow(self):
        """Testa workflow de monitoramento de performance"""
        
        # Simula algumas estatísticas
        advanced_sniper.stats["total_trades"] = 10
        advanced_sniper.stats["winning_trades"] = 7
        advanced_sniper.stats["total_profit"] = Decimal("0.05")
        advanced_sniper.stats["best_trade"] = 0.02
        advanced_sniper.stats["worst_trade"] = -0.005
        
        # Obtém estatísticas
        stats = advanced_sniper.get_performance_stats()
        
        # Verifica cálculos
        assert stats["total_trades"] == 10
        assert stats["winning_trades"] == 7
        assert stats["win_rate"] == 70.0
        assert stats["total_profit"] == 0.05
        assert stats["best_trade"] == 0.02
        assert stats["worst_trade"] == -0.005
        assert "uptime_hours" in stats
        
    @pytest.mark.asyncio
    async def test_rebalancing_workflow(self):
        """Testa workflow de rebalanceamento automático"""
        
        # Simula lucros acumulados
        advanced_sniper.stats["total_profit"] = Decimal("0.1")
        original_trade_size = advanced_sniper.trade_size_eth
        
        with patch('advanced_sniper_strategy.send_telegram_alert') as mock_alert:
            await advanced_sniper._rebalance_portfolio()
        
        # Verifica que trade size aumentou
        assert advanced_sniper.trade_size_eth > original_trade_size
        
        # Verifica notificação
        mock_alert.assert_called()
        call_args = mock_alert.call_args[0][0]
        assert "Rebalanceamento" in call_args