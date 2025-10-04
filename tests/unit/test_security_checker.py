"""
Testes unitários para o verificador de segurança
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch
from decimal import Decimal

from security_checker import SecurityChecker, SecurityReport, HoneypotDatabase


class TestSecurityChecker:
    """Testes para SecurityChecker"""
    
    @pytest.fixture
    def security_checker(self):
        """Instância do SecurityChecker para testes"""
        return SecurityChecker()
    
    @pytest.mark.asyncio
    async def test_check_token_security_safe_token(self, security_checker, mock_aiohttp_session):
        """Testa verificação de token seguro"""
        token_address = "0x1234567890123456789012345678901234567890"
        
        with patch('aiohttp.ClientSession', return_value=mock_aiohttp_session):
            with patch.object(security_checker, '_check_rugpull_risk', return_value=0.1):
                with patch.object(security_checker, '_check_liquidity_risk', return_value=0.1):
                    with patch.object(security_checker, '_check_contract_risk', return_value=0.1):
                        report = await security_checker.check_token_security(token_address)
        
        assert isinstance(report, SecurityReport)
        assert report.token_address == token_address
        assert report.is_safe == True
        assert report.risk_score < 0.3
        assert len(report.warnings) == 0
    
    @pytest.mark.asyncio
    async def test_check_token_security_risky_token(self, security_checker, mock_aiohttp_session):
        """Testa verificação de token arriscado"""
        token_address = "0x1234567890123456789012345678901234567890"
        
        # Mock para retornar honeypot
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json = AsyncMock(return_value={"IsHoneypot": True})
        mock_aiohttp_session.get.return_value.__aenter__.return_value = mock_response
        
        with patch('aiohttp.ClientSession', return_value=mock_aiohttp_session):
            with patch.object(security_checker, '_check_rugpull_risk', return_value=0.8):
                with patch.object(security_checker, '_check_liquidity_risk', return_value=0.7):
                    with patch.object(security_checker, '_check_contract_risk', return_value=0.6):
                        report = await security_checker.check_token_security(token_address)
        
        assert report.is_safe == False
        assert report.risk_score > 0.3
        assert len(report.warnings) > 0
    
    @pytest.mark.asyncio
    async def test_check_honeypot_api_success(self, security_checker, mock_aiohttp_session):
        """Testa verificação de honeypot via API"""
        token_address = "0x1234567890123456789012345678901234567890"
        
        with patch('aiohttp.ClientSession', return_value=mock_aiohttp_session):
            risk = await security_checker._check_honeypot(token_address)
        
        assert risk == 0.0  # Não é honeypot
    
    @pytest.mark.asyncio
    async def test_check_honeypot_api_failure(self, security_checker):
        """Testa fallback quando API falha"""
        token_address = "0x1234567890123456789012345678901234567890"
        
        with patch.object(security_checker, '_simulate_honeypot_check', return_value=0.2):
            with patch('aiohttp.ClientSession', side_effect=Exception("API Error")):
                risk = await security_checker._check_honeypot(token_address)
        
        assert risk == 0.2  # Usa simulação
    
    @pytest.mark.asyncio
    async def test_simulate_honeypot_check(self, security_checker):
        """Testa simulação de honeypot"""
        token_address = "0x1234567890123456789012345678901234567890"
        
        # Mock para trade bem-sucedido
        with patch('security_checker.simulate_trade') as mock_simulate:
            mock_simulate.side_effect = [
                {"success": True, "amount_out": 950000000000000000},  # Compra
                {"success": True, "amount_out": 900000000000000000}   # Venda
            ]
            
            risk = await security_checker._simulate_honeypot_check(token_address)
        
        assert risk < 0.5  # Não é honeypot
    
    @pytest.mark.asyncio
    async def test_simulate_honeypot_check_cant_sell(self, security_checker):
        """Testa simulação quando não consegue vender (honeypot)"""
        token_address = "0x1234567890123456789012345678901234567890"
        
        with patch('security_checker.simulate_trade') as mock_simulate:
            mock_simulate.side_effect = [
                {"success": True, "amount_out": 950000000000000000},  # Compra OK
                {"success": False, "error": "Cannot sell"}            # Venda falha
            ]
            
            risk = await security_checker._simulate_honeypot_check(token_address)
        
        assert risk == 1.0  # É honeypot
    
    @pytest.mark.asyncio
    async def test_check_rugpull_risk_high_owner_balance(self, security_checker):
        """Testa detecção de risco de rugpull com owner tendo muito supply"""
        token_address = "0x1234567890123456789012345678901234567890"
        
        mock_token_info = {
            "owner": "0x9876543210987654321098765432109876543210",
            "can_pause": True,
            "can_blacklist": True,
            "totalSupply": 1000000000,
            "ownerBalance": 600000000,  # 60% do supply
            "creationTime": 1234567890
        }
        
        with patch('security_checker.get_token_info', return_value=mock_token_info):
            risk = await security_checker._check_rugpull_risk(token_address)
        
        assert risk > 0.5  # Alto risco
    
    @pytest.mark.asyncio
    async def test_check_liquidity_risk_low_liquidity(self, security_checker):
        """Testa detecção de risco de liquidez baixa"""
        token_address = "0x1234567890123456789012345678901234567890"
        
        with patch('security_checker.get_total_liquidity', return_value=Decimal("0.05")):
            with patch('security_checker.get_token_info', return_value={"holders": 5}):
                risk = await security_checker._check_liquidity_risk(token_address)
        
        assert risk > 0.5  # Alto risco por liquidez baixa
    
    @pytest.mark.asyncio
    async def test_check_contract_risk_malicious_patterns(self, security_checker):
        """Testa detecção de padrões maliciosos no contrato"""
        token_address = "0x1234567890123456789012345678901234567890"
        
        # Mock bytecode com padrão malicioso
        malicious_code = b'selfdestruct'
        
        with patch.object(security_checker.w3.eth, 'get_code', return_value=malicious_code):
            risk = await security_checker._check_contract_risk(token_address)
        
        assert risk > 0.0  # Detectou padrão malicioso


class TestHoneypotDatabase:
    """Testes para HoneypotDatabase"""
    
    @pytest.fixture
    def honeypot_db(self):
        """Instância do HoneypotDatabase para testes"""
        return HoneypotDatabase()
    
    @pytest.mark.asyncio
    async def test_is_known_honeypot_true(self, honeypot_db):
        """Testa detecção de honeypot conhecido"""
        token_address = "0x1234567890123456789012345678901234567890"
        
        # Adiciona à lista de honeypots
        await honeypot_db.add_honeypot(token_address)
        
        result = await honeypot_db.is_known_honeypot(token_address)
        assert result == True
    
    @pytest.mark.asyncio
    async def test_is_known_safe_token(self, honeypot_db):
        """Testa detecção de token seguro conhecido"""
        token_address = "0x1234567890123456789012345678901234567890"
        
        # Adiciona à lista de seguros
        await honeypot_db.add_safe_token(token_address)
        
        result = await honeypot_db.is_known_honeypot(token_address)
        assert result == False
    
    @pytest.mark.asyncio
    async def test_is_unknown_token(self, honeypot_db):
        """Testa token desconhecido"""
        token_address = "0x1234567890123456789012345678901234567890"
        
        result = await honeypot_db.is_known_honeypot(token_address)
        assert result is None


@pytest.mark.asyncio
async def test_check_token_safety_function():
    """Testa função principal de verificação de segurança"""
    from security_checker import check_token_safety
    
    token_address = "0x1234567890123456789012345678901234567890"
    
    with patch('security_checker.security_checker') as mock_checker:
        mock_report = SecurityReport(
            token_address=token_address,
            is_safe=True,
            risk_score=0.2,
            honeypot_risk=0.1,
            rugpull_risk=0.2,
            liquidity_risk=0.1,
            contract_risk=0.3,
            warnings=[],
            timestamp=1234567890
        )
        mock_checker.check_token_security = AsyncMock(return_value=mock_report)
        
        result = await check_token_safety(token_address)
        
        assert result == mock_report
        mock_checker.check_token_security.assert_called_once_with(token_address)


@pytest.mark.asyncio
async def test_is_token_safe_function():
    """Testa função simplificada de verificação"""
    from security_checker import is_token_safe
    
    token_address = "0x1234567890123456789012345678901234567890"
    
    with patch('security_checker.check_token_safety') as mock_check:
        mock_check.return_value = Mock(is_safe=True)
        
        result = await is_token_safe(token_address)
        
        assert result == True
        mock_check.assert_called_once_with(token_address)