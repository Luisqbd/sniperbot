"""
Executor de trades avançado com suporte a múltiplas DEXs
Inclui otimização de gas, slippage dinâmico e fallback automático
"""

import asyncio
import logging
import time
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from decimal import Decimal

from web3 import Web3
from eth_account import Account
from eth_utils import to_checksum_address

from config import config
from dex_aggregator import get_best_price, BestQuote
from utils import get_wallet_balance

logger = logging.getLogger(__name__)

@dataclass
class TradeResult:
    """Resultado de um trade"""
    success: bool
    tx_hash: Optional[str]
    amount_out: int
    gas_used: int
    gas_price: int
    total_cost: Decimal
    execution_time: float
    dex_used: str
    error: Optional[str] = None

class TradeExecutor:
    """Executor de trades avançado"""
    
    def __init__(self):
        self.w3 = Web3(Web3.HTTPProvider(config["RPC_URL"]))
        self.account = Account.from_key(config["PRIVATE_KEY"])
        self.wallet_address = config["WALLET"]
        
        # Configurações de gas
        self.base_gas_price = 1_000_000_000  # 1 gwei
        self.max_gas_price = 50_000_000_000  # 50 gwei
        self.gas_multiplier = 1.1  # +10% buffer
        
        # Configurações de slippage
        self.base_slippage = 0.005  # 0.5%
        self.max_slippage = 0.15   # 15%
        
        # Cache de nonces
        self.nonce_cache = {}
        self.last_nonce_update = 0
        
    async def execute_trade(
        self,
        token_in: str,
        token_out: str,
        amount_in: int,
        is_buy: bool,
        max_slippage: Optional[float] = None,
        deadline_seconds: int = 300
    ) -> TradeResult:
        """Executa trade otimizado"""
        
        start_time = time.time()
        
        try:
            logger.info(f"🔄 Executando {'compra' if is_buy else 'venda'} de {amount_in / 1e18:.6f} tokens...")
            
            # Obtém melhor cotação
            best_quote = await get_best_price(token_in, token_out, amount_in, is_buy)
            if not best_quote:
                return TradeResult(
                    success=False,
                    tx_hash=None,
                    amount_out=0,
                    gas_used=0,
                    gas_price=0,
                    total_cost=Decimal("0"),
                    execution_time=time.time() - start_time,
                    dex_used="None",
                    error="Nenhuma cotação disponível"
                )
                
            # Calcula slippage dinâmico
            slippage = max_slippage or self._calculate_dynamic_slippage(best_quote)
            min_amount_out = int(best_quote.dex_quote.amount_out * (1 - slippage))
            
            # Verifica saldo
            if is_buy:
                balance = await get_wallet_balance()
                required_eth = Decimal(str(amount_in / 1e18))
                if balance < required_eth:
                    return TradeResult(
                        success=False,
                        tx_hash=None,
                        amount_out=0,
                        gas_used=0,
                        gas_price=0,
                        total_cost=Decimal("0"),
                        execution_time=time.time() - start_time,
                        dex_used=best_quote.dex_quote.dex_name,
                        error=f"Saldo insuficiente: {balance} < {required_eth}"
                    )
                    
            # Executa trade na DEX selecionada
            result = await self._execute_on_dex(
                best_quote=best_quote,
                token_in=token_in,
                token_out=token_out,
                amount_in=amount_in,
                min_amount_out=min_amount_out,
                is_buy=is_buy,
                deadline_seconds=deadline_seconds
            )
            
            result.execution_time = time.time() - start_time
            
            if result.success:
                logger.info(f"✅ Trade executado: {result.tx_hash} - {result.amount_out / 1e18:.6f} tokens")
            else:
                logger.error(f"❌ Trade falhou: {result.error}")
                
            return result
            
        except Exception as e:
            logger.error(f"❌ Erro executando trade: {e}")
            return TradeResult(
                success=False,
                tx_hash=None,
                amount_out=0,
                gas_used=0,
                gas_price=0,
                total_cost=Decimal("0"),
                execution_time=time.time() - start_time,
                dex_used="Unknown",
                error=str(e)
            )
            
    async def _execute_on_dex(
        self,
        best_quote: BestQuote,
        token_in: str,
        token_out: str,
        amount_in: int,
        min_amount_out: int,
        is_buy: bool,
        deadline_seconds: int
    ) -> TradeResult:
        """Executa trade em uma DEX específica"""
        
        dex_quote = best_quote.dex_quote
        dex_name = dex_quote.dex_name
        
        try:
            # Seleciona método baseado no tipo da DEX
            if dex_quote.dex_type.value == "v2":
                return await self._execute_v2_trade(
                    dex_quote, token_in, token_out, amount_in, min_amount_out, is_buy, deadline_seconds
                )
            elif dex_quote.dex_type.value == "v3":
                return await self._execute_v3_trade(
                    dex_quote, token_in, token_out, amount_in, min_amount_out, is_buy, deadline_seconds
                )
            else:
                raise ValueError(f"Tipo de DEX não suportado: {dex_quote.dex_type}")
                
        except Exception as e:
            logger.error(f"❌ Erro executando na {dex_name}: {e}")
            return TradeResult(
                success=False,
                tx_hash=None,
                amount_out=0,
                gas_used=0,
                gas_price=0,
                total_cost=Decimal("0"),
                execution_time=0,
                dex_used=dex_name,
                error=str(e)
            )
            
    async def _execute_v2_trade(
        self,
        dex_quote,
        token_in: str,
        token_out: str,
        amount_in: int,
        min_amount_out: int,
        is_buy: bool,
        deadline_seconds: int
    ) -> TradeResult:
        """Executa trade em DEX V2 (Uniswap V2 style)"""
        
        # ABI do router V2
        router_abi = [
            {
                "inputs": [
                    {"internalType": "uint256", "name": "amountIn", "type": "uint256"},
                    {"internalType": "uint256", "name": "amountOutMin", "type": "uint256"},
                    {"internalType": "address[]", "name": "path", "type": "address[]"},
                    {"internalType": "address", "name": "to", "type": "address"},
                    {"internalType": "uint256", "name": "deadline", "type": "uint256"}
                ],
                "name": "swapExactTokensForTokens",
                "outputs": [{"internalType": "uint256[]", "name": "amounts", "type": "uint256[]"}],
                "stateMutability": "nonpayable",
                "type": "function"
            },
            {
                "inputs": [
                    {"internalType": "uint256", "name": "amountOutMin", "type": "uint256"},
                    {"internalType": "address[]", "name": "path", "type": "address[]"},
                    {"internalType": "address", "name": "to", "type": "address"},
                    {"internalType": "uint256", "name": "deadline", "type": "uint256"}
                ],
                "name": "swapExactETHForTokens",
                "outputs": [{"internalType": "uint256[]", "name": "amounts", "type": "uint256[]"}],
                "stateMutability": "payable",
                "type": "function"
            },
            {
                "inputs": [
                    {"internalType": "uint256", "name": "amountIn", "type": "uint256"},
                    {"internalType": "uint256", "name": "amountOutMin", "type": "uint256"},
                    {"internalType": "address[]", "name": "path", "type": "address[]"},
                    {"internalType": "address", "name": "to", "type": "address"},
                    {"internalType": "uint256", "name": "deadline", "type": "uint256"}
                ],
                "name": "swapExactTokensForETH",
                "outputs": [{"internalType": "uint256[]", "name": "amounts", "type": "uint256[]"}],
                "stateMutability": "nonpayable",
                "type": "function"
            }
        ]
        
        router = self.w3.eth.contract(
            address=to_checksum_address(dex_quote.router_address),
            abi=router_abi
        )
        
        # Prepara parâmetros
        path = [to_checksum_address(token_in), to_checksum_address(token_out)]
        deadline = int(time.time()) + deadline_seconds
        
        # Seleciona função baseada no tipo de trade
        weth = config["WETH"].lower()
        
        if is_buy and token_in.lower() == weth:
            # Compra com ETH
            function = router.functions.swapExactETHForTokens(
                min_amount_out, path, self.wallet_address, deadline
            )
            value = amount_in
        elif not is_buy and token_out.lower() == weth:
            # Venda para ETH
            function = router.functions.swapExactTokensForETH(
                amount_in, min_amount_out, path, self.wallet_address, deadline
            )
            value = 0
        else:
            # Trade token para token
            function = router.functions.swapExactTokensForTokens(
                amount_in, min_amount_out, path, self.wallet_address, deadline
            )
            value = 0
            
        # Executa transação
        return await self._send_transaction(function, value, dex_quote.dex_name)
        
    async def _execute_v3_trade(
        self,
        dex_quote,
        token_in: str,
        token_out: str,
        amount_in: int,
        min_amount_out: int,
        is_buy: bool,
        deadline_seconds: int
    ) -> TradeResult:
        """Executa trade em DEX V3 (Uniswap V3 style)"""
        
        # Para V3, usamos uma abordagem simplificada
        # Em produção, implementaria o SwapRouter completo
        
        # Por enquanto, fallback para V2
        logger.info(f"Usando fallback V2 para {dex_quote.dex_name}")
        return await self._execute_v2_trade(
            dex_quote, token_in, token_out, amount_in, min_amount_out, is_buy, deadline_seconds
        )
        
    async def _send_transaction(self, function, value: int, dex_name: str) -> TradeResult:
        """Envia transação para a blockchain"""
        
        try:
            # Obtém nonce
            nonce = await self._get_nonce()
            
            # Estima gas
            gas_estimate = function.estimate_gas({
                'from': self.wallet_address,
                'value': value,
                'nonce': nonce
            })
            
            # Adiciona buffer de gas
            gas_limit = int(gas_estimate * self.gas_multiplier)
            
            # Obtém preço do gas otimizado
            gas_price = await self._get_optimal_gas_price()
            
            # Constrói transação
            transaction = function.build_transaction({
                'from': self.wallet_address,
                'value': value,
                'gas': gas_limit,
                'gasPrice': gas_price,
                'nonce': nonce
            })
            
            # Assina transação
            signed_txn = self.account.sign_transaction(transaction)
            
            # Envia transação
            tx_hash = self.w3.eth.send_raw_transaction(signed_txn.rawTransaction)
            
            logger.info(f"📤 Transação enviada: {tx_hash.hex()}")
            
            # Aguarda confirmação
            receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash, timeout=300)
            
            if receipt.status == 1:
                # Calcula amount_out dos logs
                amount_out = self._extract_amount_out_from_logs(receipt.logs)
                
                total_cost = Decimal(str((receipt.gasUsed * gas_price) / 1e18))
                
                return TradeResult(
                    success=True,
                    tx_hash=tx_hash.hex(),
                    amount_out=amount_out,
                    gas_used=receipt.gasUsed,
                    gas_price=gas_price,
                    total_cost=total_cost,
                    execution_time=0,
                    dex_used=dex_name
                )
            else:
                return TradeResult(
                    success=False,
                    tx_hash=tx_hash.hex(),
                    amount_out=0,
                    gas_used=receipt.gasUsed,
                    gas_price=gas_price,
                    total_cost=Decimal(str((receipt.gasUsed * gas_price) / 1e18)),
                    execution_time=0,
                    dex_used=dex_name,
                    error="Transação revertida"
                )
                
        except Exception as e:
            logger.error(f"❌ Erro enviando transação: {e}")
            return TradeResult(
                success=False,
                tx_hash=None,
                amount_out=0,
                gas_used=0,
                gas_price=0,
                total_cost=Decimal("0"),
                execution_time=0,
                dex_used=dex_name,
                error=str(e)
            )
            
    async def _get_nonce(self) -> int:
        """Obtém nonce otimizado com cache"""
        current_time = time.time()
        
        # Atualiza cache se necessário
        if current_time - self.last_nonce_update > 30:  # 30 segundos
            self.nonce_cache[self.wallet_address] = self.w3.eth.get_transaction_count(self.wallet_address)
            self.last_nonce_update = current_time
            
        nonce = self.nonce_cache.get(self.wallet_address, 0)
        
        # Incrementa para próxima transação
        self.nonce_cache[self.wallet_address] = nonce + 1
        
        return nonce
        
    async def _get_optimal_gas_price(self) -> int:
        """Obtém preço de gas otimizado"""
        try:
            # Obtém preço atual da rede
            network_gas_price = self.w3.eth.gas_price
            
            # Aplica otimizações baseadas na urgência
            optimal_price = int(network_gas_price * 1.1)  # +10% para prioridade
            
            # Limita ao máximo configurado
            optimal_price = min(optimal_price, self.max_gas_price)
            optimal_price = max(optimal_price, self.base_gas_price)
            
            return optimal_price
            
        except Exception as e:
            logger.error(f"❌ Erro obtendo gas price: {e}")
            return self.base_gas_price * 2  # Fallback
            
    def _calculate_dynamic_slippage(self, best_quote: BestQuote) -> float:
        """Calcula slippage dinâmico baseado nas condições"""
        
        base_slippage = self.base_slippage
        
        # Aumenta slippage baseado no price impact
        impact_multiplier = 1 + (best_quote.dex_quote.price_impact * 2)
        
        # Aumenta slippage para liquidez baixa
        liquidity_multiplier = 1.0
        if best_quote.dex_quote.liquidity < Decimal("1.0"):
            liquidity_multiplier = 1.5
        elif best_quote.dex_quote.liquidity < Decimal("0.5"):
            liquidity_multiplier = 2.0
            
        # Calcula slippage final
        dynamic_slippage = base_slippage * impact_multiplier * liquidity_multiplier
        
        # Limita ao máximo
        return min(dynamic_slippage, self.max_slippage)
        
    def _extract_amount_out_from_logs(self, logs: List) -> int:
        """Extrai amount_out dos logs da transação"""
        try:
            # Procura por eventos de Transfer ou Swap
            for log in logs:
                # Simplificação: retorna um valor baseado no primeiro log
                if log.data and len(log.data) >= 66:  # 32 bytes em hex
                    # Extrai último valor dos dados (geralmente amount_out)
                    amount_hex = log.data[-64:]  # Últimos 32 bytes
                    return int(amount_hex, 16)
                    
            return 0
            
        except Exception as e:
            logger.debug(f"Erro extraindo amount_out: {e}")
            return 0

# Instância global
trade_executor = TradeExecutor()

async def execute_trade(
    dex_name: str,
    token_in: str,
    token_out: str,
    amount_in: int,
    min_amount_out: int,
    is_buy: bool
) -> dict:
    """Função principal para executar trades"""
    
    result = await trade_executor.execute_trade(
        token_in=token_in,
        token_out=token_out,
        amount_in=amount_in,
        is_buy=is_buy
    )
    
    return {
        "success": result.success,
        "tx_hash": result.tx_hash,
        "amount_out": result.amount_out,
        "gas_used": result.gas_used,
        "total_cost": float(result.total_cost),
        "dex_used": result.dex_used,
        "error": result.error
    }