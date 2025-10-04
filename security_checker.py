"""
Sistema de verificação de segurança para tokens
Verifica honeypots, rugpulls e contratos maliciosos
"""

import asyncio
import logging
import time
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from decimal import Decimal

import aiohttp
from web3 import Web3
from eth_utils import to_checksum_address

from config import config
from utils import get_token_info, simulate_trade

logger = logging.getLogger(__name__)

@dataclass
class SecurityReport:
    """Relatório de segurança de um token"""
    token_address: str
    is_safe: bool
    risk_score: float  # 0.0 = seguro, 1.0 = muito arriscado
    honeypot_risk: float
    rugpull_risk: float
    liquidity_risk: float
    contract_risk: float
    warnings: List[str]
    timestamp: int

class SecurityChecker:
    """Verificador de segurança para tokens"""
    
    def __init__(self):
        self.w3 = Web3(Web3.HTTPProvider(config["RPC_URL"]))
        self.cache: Dict[str, SecurityReport] = {}
        self.cache_ttl = 300  # 5 minutos
        
        # APIs de verificação
        self.honeypot_apis = [
            "https://api.honeypot.is/v2/IsHoneypot",
            "https://aywt3wreda.execute-api.eu-west-1.amazonaws.com/default/IsHoneypot"
        ]
        
        # Padrões de contratos maliciosos
        self.malicious_patterns = [
            "selfdestruct",
            "delegatecall",
            "suicide",
            "transfer(address,uint256)",  # Sem return
        ]
        
    async def check_token_security(self, token_address: str) -> SecurityReport:
        """Verifica segurança completa de um token"""
        token_address = to_checksum_address(token_address)
        
        # Verifica cache
        if token_address in self.cache:
            report = self.cache[token_address]
            if time.time() - report.timestamp < self.cache_ttl:
                return report
                
        logger.info(f"🔍 Verificando segurança do token {token_address[:10]}...")
        
        warnings = []
        
        # Verificações paralelas
        tasks = [
            self._check_honeypot(token_address),
            self._check_rugpull_risk(token_address),
            self._check_liquidity_risk(token_address),
            self._check_contract_risk(token_address)
        ]
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        honeypot_risk = results[0] if not isinstance(results[0], Exception) else 0.5
        rugpull_risk = results[1] if not isinstance(results[1], Exception) else 0.5
        liquidity_risk = results[2] if not isinstance(results[2], Exception) else 0.5
        contract_risk = results[3] if not isinstance(results[3], Exception) else 0.5
        
        # Calcula score de risco geral
        risk_score = (honeypot_risk + rugpull_risk + liquidity_risk + contract_risk) / 4
        
        # Determina se é seguro
        is_safe = risk_score < 0.3  # Threshold de segurança
        
        # Adiciona warnings baseado nos riscos
        if honeypot_risk > 0.7:
            warnings.append("⚠️ Alto risco de honeypot")
        if rugpull_risk > 0.7:
            warnings.append("⚠️ Alto risco de rugpull")
        if liquidity_risk > 0.7:
            warnings.append("⚠️ Liquidez insuficiente ou instável")
        if contract_risk > 0.7:
            warnings.append("⚠️ Contrato com funções suspeitas")
            
        report = SecurityReport(
            token_address=token_address,
            is_safe=is_safe,
            risk_score=risk_score,
            honeypot_risk=honeypot_risk,
            rugpull_risk=rugpull_risk,
            liquidity_risk=liquidity_risk,
            contract_risk=contract_risk,
            warnings=warnings,
            timestamp=int(time.time())
        )
        
        # Salva no cache
        self.cache[token_address] = report
        
        if is_safe:
            logger.info(f"✅ Token {token_address[:10]}... aprovado (risco: {risk_score:.2f})")
        else:
            logger.warning(f"❌ Token {token_address[:10]}... rejeitado (risco: {risk_score:.2f})")
            
        return report
        
    async def _check_honeypot(self, token_address: str) -> float:
        """Verifica se token é honeypot usando APIs externas"""
        try:
            # Tenta múltiplas APIs
            for api_url in self.honeypot_apis:
                try:
                    async with aiohttp.ClientSession() as session:
                        params = {"address": token_address}
                        async with session.get(api_url, params=params, timeout=10) as response:
                            if response.status == 200:
                                data = await response.json()
                                
                                # Processa resposta da API
                                if "IsHoneypot" in data:
                                    return 1.0 if data["IsHoneypot"] else 0.0
                                elif "honeypot" in data:
                                    return 1.0 if data["honeypot"] else 0.0
                                    
                except Exception as e:
                    logger.debug(f"Erro na API {api_url}: {e}")
                    continue
                    
            # Fallback: simulação de trade
            return await self._simulate_honeypot_check(token_address)
            
        except Exception as e:
            logger.error(f"❌ Erro verificando honeypot: {e}")
            return 0.5  # Risco médio se não conseguir verificar
            
    async def _simulate_honeypot_check(self, token_address: str) -> float:
        """Simula compra e venda para detectar honeypot"""
        try:
            # Simula compra pequena
            buy_result = await simulate_trade(
                token_in=config["WETH"],
                token_out=token_address,
                amount_in=Web3.to_wei(0.001, 'ether'),  # 0.001 ETH
                is_buy=True
            )
            
            if not buy_result["success"]:
                return 0.8  # Não consegue comprar = suspeito
                
            # Simula venda
            sell_result = await simulate_trade(
                token_in=token_address,
                token_out=config["WETH"],
                amount_in=buy_result["amount_out"],
                is_buy=False
            )
            
            if not sell_result["success"]:
                return 1.0  # Não consegue vender = honeypot
                
            # Verifica slippage excessivo
            expected_eth = Web3.to_wei(0.001, 'ether')
            actual_eth = sell_result["amount_out"]
            slippage = 1 - (actual_eth / expected_eth)
            
            if slippage > 0.5:  # > 50% slippage
                return 0.9
            elif slippage > 0.3:  # > 30% slippage
                return 0.6
            else:
                return 0.1  # Parece seguro
                
        except Exception as e:
            logger.error(f"❌ Erro simulando honeypot: {e}")
            return 0.5
            
    async def _check_rugpull_risk(self, token_address: str) -> float:
        """Verifica risco de rugpull"""
        try:
            risk_score = 0.0
            
            # Obtém informações do token
            token_info = await get_token_info(token_address)
            if not token_info:
                return 0.8
                
            # Verifica ownership
            owner = token_info.get("owner")
            if owner and owner != "0x0000000000000000000000000000000000000000":
                risk_score += 0.3  # Tem owner = risco
                
            # Verifica se pode pausar
            if token_info.get("can_pause", False):
                risk_score += 0.2
                
            # Verifica se pode blacklist
            if token_info.get("can_blacklist", False):
                risk_score += 0.2
                
            # Verifica distribuição de tokens
            total_supply = token_info.get("totalSupply", 0)
            if total_supply > 0:
                # Verifica se owner tem muito supply
                owner_balance = token_info.get("ownerBalance", 0)
                owner_percentage = owner_balance / total_supply
                
                if owner_percentage > 0.5:  # > 50%
                    risk_score += 0.4
                elif owner_percentage > 0.2:  # > 20%
                    risk_score += 0.2
                    
            # Verifica idade do contrato
            creation_time = token_info.get("creationTime", 0)
            if creation_time > 0:
                age_hours = (time.time() - creation_time) / 3600
                if age_hours < 1:  # < 1 hora
                    risk_score += 0.3
                elif age_hours < 24:  # < 24 horas
                    risk_score += 0.1
                    
            return min(risk_score, 1.0)
            
        except Exception as e:
            logger.error(f"❌ Erro verificando rugpull: {e}")
            return 0.5
            
    async def _check_liquidity_risk(self, token_address: str) -> float:
        """Verifica risco relacionado à liquidez"""
        try:
            risk_score = 0.0
            
            # Verifica liquidez total
            from utils import get_total_liquidity
            liquidity = await get_total_liquidity(token_address)
            
            if liquidity < Decimal("0.1"):  # < 0.1 ETH
                risk_score += 0.5
            elif liquidity < Decimal("1.0"):  # < 1 ETH
                risk_score += 0.2
                
            # Verifica se liquidez está locked
            # TODO: Implementar verificação de liquidity lock
            
            # Verifica número de holders
            token_info = await get_token_info(token_address)
            holders = token_info.get("holders", 0) if token_info else 0
            
            if holders < 10:
                risk_score += 0.3
            elif holders < 50:
                risk_score += 0.1
                
            return min(risk_score, 1.0)
            
        except Exception as e:
            logger.error(f"❌ Erro verificando liquidez: {e}")
            return 0.5
            
    async def _check_contract_risk(self, token_address: str) -> float:
        """Verifica riscos no código do contrato"""
        try:
            risk_score = 0.0
            
            # Obtém bytecode do contrato
            code = self.w3.eth.get_code(token_address)
            if not code or code == b'':
                return 1.0  # Não é contrato
                
            code_hex = code.hex()
            
            # Verifica padrões maliciosos
            for pattern in self.malicious_patterns:
                if pattern.encode().hex() in code_hex:
                    risk_score += 0.2
                    
            # Verifica se é proxy
            # Proxies podem ser atualizados = risco
            proxy_patterns = [
                "delegatecall",
                "implementation",
                "upgrade"
            ]
            
            for pattern in proxy_patterns:
                if pattern.encode().hex() in code_hex:
                    risk_score += 0.3
                    break
                    
            # Verifica tamanho do código
            # Contratos muito pequenos podem ser suspeitos
            if len(code) < 1000:  # < 1KB
                risk_score += 0.2
                
            return min(risk_score, 1.0)
            
        except Exception as e:
            logger.error(f"❌ Erro verificando contrato: {e}")
            return 0.5

class HoneypotDatabase:
    """Database de honeypots conhecidos"""
    
    def __init__(self):
        self.known_honeypots: set = set()
        self.known_safe: set = set()
        self.last_update = 0
        
    async def is_known_honeypot(self, token_address: str) -> Optional[bool]:
        """Verifica se token é honeypot conhecido"""
        token_address = token_address.lower()
        
        if token_address in self.known_honeypots:
            return True
        elif token_address in self.known_safe:
            return False
        else:
            return None
            
    async def add_honeypot(self, token_address: str):
        """Adiciona token à lista de honeypots"""
        self.known_honeypots.add(token_address.lower())
        
    async def add_safe_token(self, token_address: str):
        """Adiciona token à lista de seguros"""
        self.known_safe.add(token_address.lower())
        
    async def update_database(self):
        """Atualiza database com listas externas"""
        try:
            # TODO: Implementar sync com databases externos
            # Por exemplo: GitHub repos com listas de honeypots
            pass
        except Exception as e:
            logger.error(f"❌ Erro atualizando database: {e}")

# Instâncias globais
security_checker = SecurityChecker()
honeypot_db = HoneypotDatabase()

async def check_token_safety(token_address: str) -> SecurityReport:
    """Função principal para verificar segurança de token"""
    return await security_checker.check_token_security(token_address)
    
async def is_token_safe(token_address: str) -> bool:
    """Verifica se token é seguro (função simplificada)"""
    report = await check_token_safety(token_address)
    return report.is_safe