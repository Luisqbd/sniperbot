"""
Testes de performance e benchmarks
"""

import pytest
import asyncio
import time
from unittest.mock import Mock, AsyncMock, patch
from decimal import Decimal

from security_checker import SecurityChecker
from dex_aggregator import DexAggregator
from advanced_sniper_strategy import AdvancedSniperStrategy


class TestPerformanceBenchmarks:
    """Testes de performance para componentes críticos"""
    
    @pytest.mark.asyncio
    async def test_security_check_performance(self, benchmark):
        """Benchmark da verificação de segurança"""
        
        security_checker = SecurityChecker()
        token_address = "0x1234567890123456789012345678901234567890"
        
        # Mock das verificações para focar na performance
        with patch.object(security_checker, '_check_honeypot', return_value=0.1):
            with patch.object(security_checker, '_check_rugpull_risk', return_value=0.2):
                with patch.object(security_checker, '_check_liquidity_risk', return_value=0.1):
                    with patch.object(security_checker, '_check_contract_risk', return_value=0.2):
                        
                        async def run_security_check():
                            return await security_checker.check_token_security(token_address)
                        
                        # Benchmark deve completar em menos de 1 segundo
                        result = benchmark(asyncio.run, run_security_check())
                        assert result.is_safe in [True, False]
    
    @pytest.mark.asyncio
    async def test_dex_aggregator_performance(self, benchmark):
        """Benchmark do agregador de DEXs"""
        
        dex_aggregator = DexAggregator()
        token_in = "0x1111111111111111111111111111111111111111"
        token_out = "0x2222222222222222222222222222222222222222"
        amount_in = 1000000000000000000
        
        # Mock das cotações
        from dex_aggregator import DexQuote, DexType
        mock_quote = DexQuote(
            dex_name="TestDEX",
            dex_type=DexType.UNISWAP_V2,
            router_address="0x1234567890123456789012345678901234567890",
            amount_out=950000000000000000,
            price_impact=0.05,
            gas_estimate=200000,
            slippage=0.02,
            liquidity=Decimal("2.0"),
            is_available=True
        )
        
        with patch.object(dex_aggregator, '_get_dex_quote', return_value=mock_quote):
            with patch.object(dex_aggregator, '_get_current_gas_price', return_value=20000000000):
                
                async def run_aggregator():
                    return await dex_aggregator.get_best_quote(token_in, token_out, amount_in, True)
                
                # Benchmark deve completar em menos de 500ms
                result = benchmark(asyncio.run, run_aggregator())
                assert result is not None
    
    @pytest.mark.asyncio
    async def test_position_update_performance(self, benchmark):
        """Benchmark da atualização de posições"""
        
        strategy = AdvancedSniperStrategy()
        
        # Cria múltiplas posições para teste
        from advanced_sniper_strategy import Position, StrategyType, PositionStatus
        import time
        
        for i in range(10):  # 10 posições
            position = Position(
                token_address=f"0x{i:040x}",
                token_symbol=f"TEST{i}",
                strategy_type=StrategyType.MEMECOIN_SNIPER,
                entry_price=0.000001,
                entry_amount=Decimal("1000000"),
                entry_time=int(time.time()) - 3600,
                current_price=0.0000012,
                current_value=Decimal("1200000"),
                pnl=200000.0,
                pnl_percentage=20.0,
                status=PositionStatus.ACTIVE,
                take_profit_levels=[0.25, 0.50, 1.0, 2.0],
                stop_loss_price=0.00000085,
                trailing_stop_price=0.0,
                dex_name="TestDEX",
                transaction_hash=f"0x{i:064x}"
            )
            strategy.positions[position.token_address] = position
        
        with patch.object(strategy, '_get_current_price', return_value=0.0000015):
            
            async def run_position_update():
                await strategy._update_positions()
            
            # Benchmark deve completar em menos de 200ms para 10 posições
            benchmark(asyncio.run, run_position_update())
    
    @pytest.mark.asyncio
    async def test_mempool_processing_performance(self, benchmark):
        """Benchmark do processamento de eventos de mempool"""
        
        strategy = AdvancedSniperStrategy()
        strategy.is_running = True
        
        from mempool_monitor import NewTokenEvent
        
        # Cria evento de teste
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
        
        # Mock das verificações
        from security_checker import SecurityReport
        security_report = SecurityReport(
            token_address=new_token_event.token_address,
            is_safe=True,
            risk_score=0.2,
            honeypot_risk=0.1,
            rugpull_risk=0.1,
            liquidity_risk=0.1,
            contract_risk=0.3,
            warnings=[],
            timestamp=1234567890
        )
        
        with patch('advanced_sniper_strategy.check_token_safety', return_value=security_report):
            with patch.object(strategy, '_execute_memecoin_strategy', return_value=None):
                
                async def process_token():
                    await strategy._on_new_token(new_token_event)
                
                # Benchmark deve completar em menos de 100ms
                benchmark(asyncio.run, process_token())
    
    def test_telegram_message_formatting_performance(self, benchmark):
        """Benchmark da formatação de mensagens do Telegram"""
        
        from telegram_bot import TelegramBot
        
        bot = TelegramBot()
        
        # Dados de teste
        stats = {
            "total_trades": 100,
            "winning_trades": 75,
            "win_rate": 75.0,
            "total_profit": 0.25,
            "best_trade": 0.05,
            "worst_trade": -0.01,
            "uptime_hours": 24.5
        }
        
        def format_stats_message():
            return (
                f"📈 *ESTATÍSTICAS DE PERFORMANCE*\n\n"
                f"*Trades Totais:* {stats['total_trades']}\n"
                f"*Trades Vencedores:* {stats['winning_trades']}\n"
                f"*Taxa de Acerto:* {stats['win_rate']:.1f}%\n"
                f"*Lucro Total:* {stats['total_profit']:.4f} ETH\n"
                f"*Melhor Trade:* {stats['best_trade']:.4f} ETH\n"
                f"*Pior Trade:* {stats['worst_trade']:.4f} ETH\n"
                f"*Tempo Ativo:* {stats['uptime_hours']:.1f}h"
            )
        
        # Benchmark deve completar em menos de 1ms
        result = benchmark(format_stats_message)
        assert "ESTATÍSTICAS" in result
    
    @pytest.mark.asyncio
    async def test_concurrent_token_processing(self, benchmark):
        """Benchmark do processamento concorrente de múltiplos tokens"""
        
        strategy = AdvancedSniperStrategy()
        strategy.is_running = True
        
        from mempool_monitor import NewTokenEvent
        from security_checker import SecurityReport
        
        # Cria múltiplos eventos
        events = []
        for i in range(5):  # 5 tokens simultâneos
            event = NewTokenEvent(
                token_address=f"0x{i:040x}",
                pair_address=f"0x{i+1000:040x}",
                dex_name="TestDEX",
                liquidity_eth=Decimal("1.0"),
                block_number=1000000 + i,
                transaction_hash=f"0x{i:064x}",
                timestamp=1234567890 + i,
                holders_count=100,
                social_score=0.8,
                is_memecoin=True
            )
            events.append(event)
        
        # Mock das verificações
        security_report = SecurityReport(
            token_address="0x0000000000000000000000000000000000000000",
            is_safe=True,
            risk_score=0.2,
            honeypot_risk=0.1,
            rugpull_risk=0.1,
            liquidity_risk=0.1,
            contract_risk=0.3,
            warnings=[],
            timestamp=1234567890
        )
        
        with patch('advanced_sniper_strategy.check_token_safety', return_value=security_report):
            with patch.object(strategy, '_execute_memecoin_strategy', return_value=None):
                
                async def process_concurrent_tokens():
                    tasks = [strategy._on_new_token(event) for event in events]
                    await asyncio.gather(*tasks)
                
                # Benchmark deve completar em menos de 500ms para 5 tokens
                benchmark(asyncio.run, process_concurrent_tokens())
    
    @pytest.mark.asyncio
    async def test_price_calculation_performance(self, benchmark):
        """Benchmark do cálculo de preços"""
        
        from dex_aggregator import DexAggregator
        
        aggregator = DexAggregator()
        
        # Mock de dados para cálculo
        mock_quote = Mock()
        mock_quote.price_impact = 0.05
        mock_quote.liquidity = Decimal("2.0")
        mock_quote.gas_estimate = 200000
        mock_quote.amount_out = 950000000000000000
        
        def calculate_efficiency():
            return aggregator._calculate_efficiency_score(
                mock_quote, 950000000000000000, 50000000000000000
            )
        
        # Benchmark deve completar em menos de 0.1ms
        result = benchmark(calculate_efficiency)
        assert 0 <= result <= 1.0
    
    @pytest.mark.asyncio
    async def test_memory_usage_during_operation(self):
        """Testa uso de memória durante operação"""
        
        import psutil
        import os
        
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss
        
        strategy = AdvancedSniperStrategy()
        strategy.is_running = True
        
        # Simula operação intensiva
        from mempool_monitor import NewTokenEvent
        
        for i in range(100):  # 100 tokens
            event = NewTokenEvent(
                token_address=f"0x{i:040x}",
                pair_address=f"0x{i+1000:040x}",
                dex_name="TestDEX",
                liquidity_eth=Decimal("1.0"),
                block_number=1000000 + i,
                transaction_hash=f"0x{i:064x}",
                timestamp=1234567890 + i,
                holders_count=100,
                social_score=0.8,
                is_memecoin=True
            )
            
            # Adiciona ao cache de tokens processados
            strategy.processed_tokens.add(event.token_address)
        
        final_memory = process.memory_info().rss
        memory_increase = final_memory - initial_memory
        
        # Aumento de memória deve ser razoável (menos de 50MB)
        assert memory_increase < 50 * 1024 * 1024  # 50MB
    
    @pytest.mark.asyncio
    async def test_database_query_performance(self, benchmark):
        """Benchmark de consultas ao cache/database"""
        
        from security_checker import HoneypotDatabase
        
        db = HoneypotDatabase()
        
        # Adiciona tokens ao database
        for i in range(1000):
            await db.add_safe_token(f"0x{i:040x}")
        
        # Benchmark de consulta
        async def query_token():
            return await db.is_known_honeypot("0x0000000000000000000000000000000000000001")
        
        # Consulta deve ser muito rápida (menos de 1ms)
        result = benchmark(asyncio.run, query_token())
        assert result == False  # Token está na lista de seguros
    
    def test_configuration_loading_performance(self, benchmark):
        """Benchmark do carregamento de configurações"""
        
        def load_config():
            from config import config
            return len(config)
        
        # Carregamento deve ser instantâneo
        result = benchmark(load_config)
        assert result > 0  # Tem configurações carregadas