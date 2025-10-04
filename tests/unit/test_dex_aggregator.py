"""
Testes unitários para o agregador de DEXs
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch
from decimal import Decimal

from dex_aggregator import DexAggregator, DexQuote, BestQuote, DexType


class TestDexAggregator:
    """Testes para DexAggregator"""
    
    @pytest.fixture
    def dex_aggregator(self):
        """Instância do DexAggregator para testes"""
        return DexAggregator()
    
    @pytest.fixture
    def mock_dex_config(self):
        """Mock de configuração de DEX"""
        from config import DexConfig
        return DexConfig(
            name="TestDEX",
            factory="0x1234567890123456789012345678901234567890",
            router="0x0987654321098765432109876543210987654321",
            type="v2"
        )
    
    @pytest.mark.asyncio
    async def test_get_best_quote_success(self, dex_aggregator, mock_dex_quote):
        """Testa obtenção de melhor cotação com sucesso"""
        token_in = "0x1111111111111111111111111111111111111111"
        token_out = "0x2222222222222222222222222222222222222222"
        amount_in = 1000000000000000000  # 1 ETH
        
        with patch.object(dex_aggregator, '_get_dex_quote', return_value=mock_dex_quote):
            with patch.object(dex_aggregator, '_select_best_quote') as mock_select:
                mock_best = BestQuote(
                    dex_quote=mock_dex_quote,
                    net_amount=900000000000000000,
                    total_cost=50000000000000000,
                    efficiency_score=0.85
                )
                mock_select.return_value = mock_best
                
                result = await dex_aggregator.get_best_quote(token_in, token_out, amount_in, True)
        
        assert result == mock_best
        assert result.dex_quote.dex_name == "TestDEX"
    
    @pytest.mark.asyncio
    async def test_get_best_quote_no_quotes(self, dex_aggregator):
        """Testa quando nenhuma cotação está disponível"""
        token_in = "0x1111111111111111111111111111111111111111"
        token_out = "0x2222222222222222222222222222222222222222"
        amount_in = 1000000000000000000
        
        with patch.object(dex_aggregator, '_get_dex_quote', return_value=None):
            result = await dex_aggregator.get_best_quote(token_in, token_out, amount_in, True)
        
        assert result is None
    
    @pytest.mark.asyncio
    async def test_get_v2_quote_success(self, dex_aggregator, mock_dex_config):
        """Testa cotação V2 com sucesso"""
        token_in = "0x1111111111111111111111111111111111111111"
        token_out = "0x2222222222222222222222222222222222222222"
        amount_in = 1000000000000000000
        
        # Mock do contrato do router
        mock_router = Mock()
        mock_router.functions.getAmountsOut.return_value.call.return_value = [
            amount_in, 950000000000000000  # 0.95 ETH out
        ]
        
        with patch.object(dex_aggregator.w3.eth, 'contract', return_value=mock_router):
            with patch.object(dex_aggregator, '_calculate_price_impact_v2', return_value=0.05):
                with patch.object(dex_aggregator, '_estimate_swap_gas_v2', return_value=200000):
                    with patch.object(dex_aggregator, '_get_pair_liquidity_v2', return_value=Decimal("2.0")):
                        quote = await dex_aggregator._get_v2_quote(mock_dex_config, token_in, token_out, amount_in, True)
        
        assert quote.dex_name == "TestDEX"
        assert quote.dex_type == DexType.UNISWAP_V2
        assert quote.amount_out == 950000000000000000
        assert quote.is_available == True
    
    @pytest.mark.asyncio
    async def test_get_v2_quote_failure(self, dex_aggregator, mock_dex_config):
        """Testa falha na cotação V2"""
        token_in = "0x1111111111111111111111111111111111111111"
        token_out = "0x2222222222222222222222222222222222222222"
        amount_in = 1000000000000000000
        
        with patch.object(dex_aggregator.w3.eth, 'contract', side_effect=Exception("Contract error")):
            quote = await dex_aggregator._get_v2_quote(mock_dex_config, token_in, token_out, amount_in, True)
        
        assert quote.is_available == False
        assert quote.error == "Contract error"
    
    @pytest.mark.asyncio
    async def test_calculate_price_impact_v2(self, dex_aggregator, mock_dex_config):
        """Testa cálculo de price impact V2"""
        token_in = "0x1111111111111111111111111111111111111111"
        token_out = "0x2222222222222222222222222222222222222222"
        amount_in = 1000000000000000000
        amount_out = 950000000000000000
        
        # Mock das reservas do par
        with patch.object(dex_aggregator, '_get_pair_reserves_v2', return_value=(10000000000000000000, 10000000000000000000)):
            impact = await dex_aggregator._calculate_price_impact_v2(mock_dex_config, token_in, token_out, amount_in, amount_out)
        
        assert 0 <= impact <= 1.0
    
    @pytest.mark.asyncio
    async def test_select_best_quote_single_quote(self, dex_aggregator, mock_dex_quote):
        """Testa seleção com uma única cotação"""
        quotes = [mock_dex_quote]
        
        with patch.object(dex_aggregator, '_get_current_gas_price', return_value=20000000000):
            best = await dex_aggregator._select_best_quote(quotes, True)
        
        assert best is not None
        assert best.dex_quote == mock_dex_quote
    
    @pytest.mark.asyncio
    async def test_select_best_quote_multiple_quotes(self, dex_aggregator):
        """Testa seleção entre múltiplas cotações"""
        quote1 = DexQuote(
            dex_name="DEX1",
            dex_type=DexType.UNISWAP_V2,
            router_address="0x1111111111111111111111111111111111111111",
            amount_out=950000000000000000,
            price_impact=0.05,
            gas_estimate=200000,
            slippage=0.02,
            liquidity=Decimal("2.0"),
            is_available=True
        )
        
        quote2 = DexQuote(
            dex_name="DEX2",
            dex_type=DexType.UNISWAP_V2,
            router_address="0x2222222222222222222222222222222222222222",
            amount_out=960000000000000000,  # Melhor preço
            price_impact=0.03,
            gas_estimate=180000,
            slippage=0.015,
            liquidity=Decimal("3.0"),
            is_available=True
        )
        
        quotes = [quote1, quote2]
        
        with patch.object(dex_aggregator, '_get_current_gas_price', return_value=20000000000):
            best = await dex_aggregator._select_best_quote(quotes, True)
        
        assert best is not None
        assert best.dex_quote.dex_name == "DEX2"  # Melhor cotação
    
    @pytest.mark.asyncio
    async def test_select_best_quote_filters_high_impact(self, dex_aggregator):
        """Testa filtro de price impact alto"""
        quote_high_impact = DexQuote(
            dex_name="HighImpactDEX",
            dex_type=DexType.UNISWAP_V2,
            router_address="0x1111111111111111111111111111111111111111",
            amount_out=1100000000000000000,  # Preço muito bom
            price_impact=0.20,  # Mas impact muito alto
            gas_estimate=200000,
            slippage=0.02,
            liquidity=Decimal("0.5"),
            is_available=True
        )
        
        quotes = [quote_high_impact]
        
        with patch.object(dex_aggregator, '_get_current_gas_price', return_value=20000000000):
            best = await dex_aggregator._select_best_quote(quotes, True)
        
        assert best is None  # Filtrado por price impact alto
    
    def test_calculate_efficiency_score(self, dex_aggregator, mock_dex_quote):
        """Testa cálculo do score de eficiência"""
        net_amount = 950000000000000000
        total_cost = 50000000000000000
        
        score = dex_aggregator._calculate_efficiency_score(mock_dex_quote, net_amount, total_cost)
        
        assert 0 <= score <= 1.0
    
    @pytest.mark.asyncio
    async def test_get_current_gas_price_cached(self, dex_aggregator):
        """Testa cache do preço de gas"""
        # Primeiro call
        with patch.object(dex_aggregator.w3.eth, 'gas_price', 20000000000):
            price1 = await dex_aggregator._get_current_gas_price()
        
        # Segundo call (deve usar cache)
        with patch.object(dex_aggregator.w3.eth, 'gas_price', 30000000000):
            price2 = await dex_aggregator._get_current_gas_price()
        
        assert price1 == price2  # Usou cache
    
    @pytest.mark.asyncio
    async def test_get_pair_address_v2_success(self, dex_aggregator, mock_dex_config):
        """Testa obtenção de endereço do par V2"""
        token_in = "0x1111111111111111111111111111111111111111"
        token_out = "0x2222222222222222222222222222222222222222"
        pair_address = "0x3333333333333333333333333333333333333333"
        
        # Mock da factory
        mock_factory = Mock()
        mock_factory.functions.getPair.return_value.call.return_value = pair_address
        
        with patch.object(dex_aggregator.w3.eth, 'contract', return_value=mock_factory):
            result = await dex_aggregator._get_pair_address_v2(mock_dex_config, token_in, token_out)
        
        assert result == pair_address
    
    @pytest.mark.asyncio
    async def test_get_pair_address_v2_not_exists(self, dex_aggregator, mock_dex_config):
        """Testa quando par não existe"""
        token_in = "0x1111111111111111111111111111111111111111"
        token_out = "0x2222222222222222222222222222222222222222"
        
        # Mock da factory retornando endereço zero
        mock_factory = Mock()
        mock_factory.functions.getPair.return_value.call.return_value = "0x0000000000000000000000000000000000000000"
        
        with patch.object(dex_aggregator.w3.eth, 'contract', return_value=mock_factory):
            result = await dex_aggregator._get_pair_address_v2(mock_dex_config, token_in, token_out)
        
        assert result is None


@pytest.mark.asyncio
async def test_get_best_price_function():
    """Testa função principal de obtenção de melhor preço"""
    from dex_aggregator import get_best_price
    
    token_in = "0x1111111111111111111111111111111111111111"
    token_out = "0x2222222222222222222222222222222222222222"
    amount_in = 1000000000000000000
    
    with patch('dex_aggregator.dex_aggregator') as mock_aggregator:
        mock_quote = Mock()
        mock_aggregator.get_best_quote = AsyncMock(return_value=mock_quote)
        
        result = await get_best_price(token_in, token_out, amount_in, True)
        
        assert result == mock_quote
        mock_aggregator.get_best_quote.assert_called_once_with(token_in, token_out, amount_in, True)


@pytest.mark.asyncio
async def test_execute_best_trade_function():
    """Testa função de execução de melhor trade"""
    from dex_aggregator import execute_best_trade
    
    token_in = "0x1111111111111111111111111111111111111111"
    token_out = "0x2222222222222222222222222222222222222222"
    amount_in = 1000000000000000000
    
    mock_quote = Mock()
    mock_quote.dex_quote.dex_name = "TestDEX"
    mock_quote.net_amount = 950000000000000000
    
    with patch('dex_aggregator.get_best_price', return_value=mock_quote):
        with patch('dex_aggregator.execute_trade') as mock_execute:
            mock_execute.return_value = {"success": True, "tx_hash": "0xabc123"}
            
            result = await execute_best_trade(token_in, token_out, amount_in, True)
    
    assert result["success"] == True
    assert "tx_hash" in result