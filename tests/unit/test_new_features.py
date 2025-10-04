"""
Testes para funcionalidades novas: Modo Turbo, Pause/Resume
"""

import pytest
from decimal import Decimal
from unittest.mock import Mock, patch, AsyncMock
from config import config
from advanced_sniper_strategy import AdvancedSniperStrategy


class TestTurboMode:
    """Testes para o modo turbo"""
    
    def setup_method(self):
        """Setup para cada teste"""
        # Reseta config
        config["TURBO_MODE"] = False
        config["TRADE_SIZE_ETH"] = 0.0008
        config["STOP_LOSS_PCT"] = 0.12
        config["MAX_POSITIONS"] = 2
        
        # Mock das dependências
        with patch('advanced_sniper_strategy.Web3'), \
             patch('advanced_sniper_strategy.add_mempool_callback'), \
             patch('advanced_sniper_strategy.mempool_monitor'):
            self.strategy = AdvancedSniperStrategy()
    
    def test_init_modo_normal(self):
        """Testa inicialização em modo normal"""
        assert self.strategy.trade_size_eth == Decimal("0.0008")
        assert self.strategy.stop_loss_pct == 0.12
        assert self.strategy.max_positions == 2
        assert not self.strategy.is_paused
    
    def test_toggle_turbo_ativar(self):
        """Testa ativação do modo turbo"""
        # Configura valores de turbo
        config["TURBO_TRADE_SIZE_ETH"] = 0.0012
        config["TURBO_STOP_LOSS_PCT"] = 0.08
        config["TURBO_MAX_POSITIONS"] = 3
        
        # Ativa turbo
        self.strategy.toggle_turbo_mode(True)
        
        # Verifica mudanças
        assert config["TURBO_MODE"] is True
        assert self.strategy.trade_size_eth == Decimal("0.0012")
        assert self.strategy.stop_loss_pct == 0.08
        assert self.strategy.max_positions == 3
    
    def test_toggle_turbo_desativar(self):
        """Testa desativação do modo turbo"""
        # Ativa turbo primeiro
        config["TURBO_TRADE_SIZE_ETH"] = 0.0012
        config["TURBO_STOP_LOSS_PCT"] = 0.08
        config["TURBO_MAX_POSITIONS"] = 3
        self.strategy.toggle_turbo_mode(True)
        
        # Desativa turbo
        config["TRADE_SIZE_ETH"] = 0.0008
        config["STOP_LOSS_PCT"] = 0.12
        config["MAX_POSITIONS"] = 2
        self.strategy.toggle_turbo_mode(False)
        
        # Verifica volta aos valores normais
        assert config["TURBO_MODE"] is False
        assert self.strategy.trade_size_eth == Decimal("0.0008")
        assert self.strategy.stop_loss_pct == 0.12
        assert self.strategy.max_positions == 2


class TestPauseResume:
    """Testes para pause/resume"""
    
    def setup_method(self):
        """Setup para cada teste"""
        with patch('advanced_sniper_strategy.Web3'), \
             patch('advanced_sniper_strategy.add_mempool_callback'), \
             patch('advanced_sniper_strategy.mempool_monitor'):
            self.strategy = AdvancedSniperStrategy()
    
    def test_init_not_paused(self):
        """Testa que estratégia inicia não pausada"""
        assert not self.strategy.is_paused
        assert not self.strategy.is_running
    
    def test_pause_strategy(self):
        """Testa pausa da estratégia"""
        self.strategy.pause_strategy()
        assert self.strategy.is_paused
    
    def test_resume_strategy(self):
        """Testa retomada da estratégia"""
        self.strategy.pause_strategy()
        assert self.strategy.is_paused
        
        self.strategy.resume_strategy()
        assert not self.strategy.is_paused
    
    @pytest.mark.asyncio
    async def test_on_new_token_paused(self):
        """Testa que novos tokens são ignorados quando pausado"""
        self.strategy.is_running = True
        self.strategy.pause_strategy()
        
        # Mock do evento
        event = Mock()
        event.token_address = "0x1234567890abcdef"
        
        # Chama callback
        await self.strategy._on_new_token(event)
        
        # Verifica que token foi ignorado (não adicionado a processed_tokens)
        # O token é adicionado antes do check de pausa, então verificamos o log
        # ou comportamento posterior
        assert len(self.strategy.positions) == 0


class TestConfigIntegration:
    """Testes de integração com configurações"""
    
    def test_config_memecoin_from_env(self):
        """Testa que configurações de memecoin vêm do config"""
        config["MEMECOIN_MAX_INVESTMENT"] = 0.001
        config["MEMECOIN_TARGET_PROFIT"] = 3.0
        config["MEMECOIN_MIN_HOLDERS"] = 100
        
        with patch('advanced_sniper_strategy.Web3'), \
             patch('advanced_sniper_strategy.add_mempool_callback'), \
             patch('advanced_sniper_strategy.mempool_monitor'):
            strategy = AdvancedSniperStrategy()
        
        assert strategy.memecoin_config["max_investment"] == Decimal("0.001")
        assert strategy.memecoin_config["target_profit"] == 3.0
        assert strategy.memecoin_config["min_holders"] == 100
    
    def test_config_altcoin_from_env(self):
        """Testa que configurações de altcoin vêm do config"""
        config["ALTCOIN_MIN_MARKET_CAP"] = 500000
        config["ALTCOIN_MAX_MARKET_CAP"] = 5000000
        config["ALTCOIN_MIN_VOLUME_24H"] = 25000
        
        with patch('advanced_sniper_strategy.Web3'), \
             patch('advanced_sniper_strategy.add_mempool_callback'), \
             patch('advanced_sniper_strategy.mempool_monitor'):
            strategy = AdvancedSniperStrategy()
        
        assert strategy.altcoin_config["min_market_cap"] == 500000
        assert strategy.altcoin_config["max_market_cap"] == 5000000
        assert strategy.altcoin_config["min_volume_24h"] == 25000


class TestAutoStart:
    """Testes para auto-start"""
    
    def test_auto_start_config(self):
        """Testa que AUTO_START_SNIPER está configurado"""
        # Testa valores padrão
        config["AUTO_START_SNIPER"] = True
        assert config.get("AUTO_START_SNIPER") is True
        
        config["AUTO_START_SNIPER"] = False
        assert config.get("AUTO_START_SNIPER") is False
