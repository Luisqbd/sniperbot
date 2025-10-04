"""
Configurações compartilhadas para testes
"""

import pytest
import asyncio
import os
from unittest.mock import Mock, AsyncMock
from decimal import Decimal

# Configurar variáveis de ambiente para testes
os.environ.update({
    "RPC_URL": "http://localhost:8545",
    "CHAIN_ID": "8453",
    "PRIVATE_KEY": "0x0000000000000000000000000000000000000000000000000000000000000001",
    "WALLET_ADDRESS": "0x0000000000000000000000000000000000000000",
    "TELEGRAM_TOKEN": "123456789:ABCDEFGHIJKLMNOPQRSTUVWXYZ",
    "TELEGRAM_CHAT_ID": "123456789",
    "AUTH0_DOMAIN": "test.auth0.com",
    "AUTH0_AUDIENCE": "https://api.test.com",
    "AUTH0_CLIENT_ID": "test_client_id",
    "AUTH0_CLIENT_SECRET": "test_client_secret",
    "DRY_RUN": "true",
    "TRADE_SIZE_ETH": "0.001",
    "SLIPPAGE_BPS": "500",
    "TAKE_PROFIT_PCT": "0.25",
    "STOP_LOSS_PCT": "0.15"
})

@pytest.fixture(scope="session")
def event_loop():
    """Cria event loop para testes assíncronos"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture
def mock_web3():
    """Mock do Web3"""
    mock = Mock()
    mock.eth.get_balance.return_value = int(0.002 * 1e18)  # 0.002 ETH
    mock.eth.get_code.return_value = b'0x608060405234801561001057600080fd5b50'
    mock.eth.gas_price = 20_000_000_000  # 20 gwei
    mock.eth.block_number = 1000000
    mock.is_connected.return_value = True
    return mock

@pytest.fixture
def mock_token_info():
    """Mock de informações de token"""
    return {
        "name": "Test Token",
        "symbol": "TEST",
        "decimals": 18,
        "totalSupply": 1000000000,
        "holders": 100,
        "market_cap": 1000000,
        "volume_24h": 50000
    }

@pytest.fixture
def mock_security_report():
    """Mock de relatório de segurança"""
    from security_checker import SecurityReport
    return SecurityReport(
        token_address="0x1234567890123456789012345678901234567890",
        is_safe=True,
        risk_score=0.2,
        honeypot_risk=0.1,
        rugpull_risk=0.2,
        liquidity_risk=0.1,
        contract_risk=0.3,
        warnings=[],
        timestamp=1234567890
    )

@pytest.fixture
def mock_dex_quote():
    """Mock de cotação de DEX"""
    from dex_aggregator import DexQuote, DexType
    return DexQuote(
        dex_name="TestDEX",
        dex_type=DexType.UNISWAP_V2,
        router_address="0x1234567890123456789012345678901234567890",
        amount_out=950000000000000000,  # 0.95 ETH
        price_impact=0.05,
        gas_estimate=200000,
        slippage=0.02,
        liquidity=Decimal("2.0"),
        is_available=True
    )

@pytest.fixture
def mock_new_token_event():
    """Mock de evento de novo token"""
    from mempool_monitor import NewTokenEvent
    return NewTokenEvent(
        token_address="0x1234567890123456789012345678901234567890",
        pair_address="0x0987654321098765432109876543210987654321",
        dex_name="TestDEX",
        liquidity_eth=Decimal("1.5"),
        block_number=1000000,
        transaction_hash="0xabcdef1234567890abcdef1234567890abcdef1234567890abcdef1234567890",
        timestamp=1234567890,
        holders_count=100,
        social_score=0.7,
        is_memecoin=True
    )

@pytest.fixture
async def mock_telegram_bot():
    """Mock do bot do Telegram"""
    bot = AsyncMock()
    bot.send_message = AsyncMock()
    bot.edit_message_text = AsyncMock()
    return bot

@pytest.fixture
def sample_trade_result():
    """Resultado de trade de exemplo"""
    from trade_executor_advanced import TradeResult
    return TradeResult(
        success=True,
        tx_hash="0xabcdef1234567890abcdef1234567890abcdef1234567890abcdef1234567890",
        amount_out=950000000000000000,
        gas_used=180000,
        gas_price=25000000000,
        total_cost=Decimal("0.0045"),
        execution_time=2.5,
        dex_used="TestDEX"
    )

@pytest.fixture
def mock_position():
    """Mock de posição de trading"""
    from advanced_sniper_strategy import Position, StrategyType, PositionStatus
    from decimal import Decimal
    import time
    
    return Position(
        token_address="0x1234567890123456789012345678901234567890",
        token_symbol="TEST",
        strategy_type=StrategyType.MEMECOIN_SNIPER,
        entry_price=0.000001,
        entry_amount=Decimal("1000000"),
        entry_time=int(time.time()) - 3600,  # 1 hora atrás
        current_price=0.0000012,
        current_value=Decimal("1200000"),
        pnl=200000.0,
        pnl_percentage=20.0,
        status=PositionStatus.ACTIVE,
        take_profit_levels=[0.25, 0.50, 1.0, 2.0],
        stop_loss_price=0.00000085,
        trailing_stop_price=0.0,
        dex_name="TestDEX",
        transaction_hash="0xabcdef1234567890abcdef1234567890abcdef1234567890abcdef1234567890"
    )

class MockAsyncContext:
    """Context manager mock para operações assíncronas"""
    def __init__(self, return_value=None):
        self.return_value = return_value
        
    async def __aenter__(self):
        return self.return_value
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        pass

@pytest.fixture
def mock_aiohttp_session():
    """Mock de sessão aiohttp"""
    session = AsyncMock()
    response = AsyncMock()
    response.status = 200
    response.json = AsyncMock(return_value={"IsHoneypot": False})
    session.get.return_value = MockAsyncContext(response)
    return session