"""
Agregador de DEXs para encontrar melhores preços e fallback
Suporta múltiplas DEXs na rede Base com otimização automática
"""

import asyncio
import logging
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from decimal import Decimal
from enum import Enum

from web3 import Web3
from eth_utils import to_checksum_address

from config import config
from utils import get_token_info

logger = logging.getLogger(__name__)

class DexType(Enum):
    UNISWAP_V2 = "v2"
    UNISWAP_V3 = "v3"

@dataclass
class DexQuote:
    """Cotação de uma DEX"""
    dex_name: str
    dex_type: DexType
    router_address: str
    amount_out: int
    price_impact: float
    gas_estimate: int
    slippage: float
    liquidity: Decimal
    is_available: bool
    error: Optional[str] = None

@dataclass
class BestQuote:
    """Melhor cotação encontrada"""
    dex_quote: DexQuote
    net_amount: int  # Após descontar gas
    total_cost: int  # Gas + slippage
    efficiency_score: float  # Score geral

class DexAggregator:
    """Agregador de DEXs para otimização de preços"""
    
    def __init__(self):
        self.w3 = Web3(Web3.HTTPProvider(config["RPC_URL"]))
        self.dexes = config["DEXES"]
        self.gas_price_cache = {}
        self.cache_ttl = 30  # 30 segundos
        
        # Configurações de otimização
        self.max_slippage = config.get("SLIPPAGE_BPS", 500) / 10000  # 5%
        self.max_price_impact = 0.15  # 15%
        self.min_liquidity = Decimal("0.1")  # 0.1 ETH
        
    async def get_best_quote(
        self, 
        token_in: str, 
        token_out: str, 
        amount_in: int,
        is_buy: bool = True
    ) -> Optional[BestQuote]:
        """Encontra a melhor cotação entre todas as DEXs"""
        
        logger.info(f"🔍 Buscando melhor preço para {amount_in} tokens...")
        
        # Obtém cotações de todas as DEXs em paralelo
        tasks = []
        for dex in self.dexes:
            task = self._get_dex_quote(dex, token_in, token_out, amount_in, is_buy)
            tasks.append(task)
            
        quotes = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Filtra cotações válidas
        valid_quotes = []
        for i, quote in enumerate(quotes):
            if isinstance(quote, Exception):
                logger.debug(f"Erro na DEX {self.dexes[i].name}: {quote}")
                continue
            if quote and quote.is_available:
                valid_quotes.append(quote)
                
        if not valid_quotes:
            logger.warning("❌ Nenhuma DEX disponível")
            return None
            
        # Encontra a melhor cotação
        best_quote = await self._select_best_quote(valid_quotes, is_buy)
        
        if best_quote:
            dex_name = best_quote.dex_quote.dex_name
            amount_out = best_quote.dex_quote.amount_out
            logger.info(f"✅ Melhor preço: {dex_name} - {amount_out} tokens")
            
        return best_quote
        
    async def _get_dex_quote(
        self, 
        dex_config, 
        token_in: str, 
        token_out: str, 
        amount_in: int,
        is_buy: bool
    ) -> DexQuote:
        """Obtém cotação de uma DEX específica"""
        
        try:
            if dex_config.type == "v2":
                return await self._get_v2_quote(dex_config, token_in, token_out, amount_in, is_buy)
            elif dex_config.type == "v3":
                return await self._get_v3_quote(dex_config, token_in, token_out, amount_in, is_buy)
            else:
                raise ValueError(f"Tipo de DEX não suportado: {dex_config.type}")
                
        except Exception as e:
            logger.debug(f"Erro obtendo cotação da {dex_config.name}: {e}")
            return DexQuote(
                dex_name=dex_config.name,
                dex_type=DexType.UNISWAP_V2 if dex_config.type == "v2" else DexType.UNISWAP_V3,
                router_address=dex_config.router,
                amount_out=0,
                price_impact=1.0,
                gas_estimate=0,
                slippage=1.0,
                liquidity=Decimal("0"),
                is_available=False,
                error=str(e)
            )
            
    async def _get_v2_quote(self, dex_config, token_in: str, token_out: str, amount_in: int, is_buy: bool) -> DexQuote:
        """Obtém cotação de DEX V2 (Uniswap V2 style)"""
        
        # ABI do router V2
        router_abi = [
            {
                "inputs": [
                    {"internalType": "uint256", "name": "amountIn", "type": "uint256"},
                    {"internalType": "address[]", "name": "path", "type": "address[]"}
                ],
                "name": "getAmountsOut",
                "outputs": [{"internalType": "uint256[]", "name": "amounts", "type": "uint256[]"}],
                "stateMutability": "view",
                "type": "function"
            }
        ]
        
        router = self.w3.eth.contract(
            address=to_checksum_address(dex_config.router),
            abi=router_abi
        )
        
        # Path do trade
        path = [to_checksum_address(token_in), to_checksum_address(token_out)]
        
        # Obtém amounts out
        amounts = router.functions.getAmountsOut(amount_in, path).call()
        amount_out = amounts[-1]
        
        # Calcula price impact
        price_impact = await self._calculate_price_impact_v2(
            dex_config, token_in, token_out, amount_in, amount_out
        )
        
        # Estima gas
        gas_estimate = await self._estimate_swap_gas_v2(dex_config, path, amount_in, is_buy)
        
        # Obtém liquidez do par
        liquidity = await self._get_pair_liquidity_v2(dex_config, token_in, token_out)
        
        # Calcula slippage esperado
        slippage = min(price_impact * 1.5, self.max_slippage)  # 50% buffer
        
        return DexQuote(
            dex_name=dex_config.name,
            dex_type=DexType.UNISWAP_V2,
            router_address=dex_config.router,
            amount_out=amount_out,
            price_impact=price_impact,
            gas_estimate=gas_estimate,
            slippage=slippage,
            liquidity=liquidity,
            is_available=True
        )
        
    async def _get_v3_quote(self, dex_config, token_in: str, token_out: str, amount_in: int, is_buy: bool) -> DexQuote:
        """Obtém cotação de DEX V3 (Uniswap V3 style)"""
        
        # Para V3, usamos quoter se disponível
        # Senão, fallback para estimativa baseada em V2
        
        try:
            # Tenta usar quoter V3
            return await self._get_v3_quoter_quote(dex_config, token_in, token_out, amount_in, is_buy)
        except:
            # Fallback para estimativa V2
            logger.debug(f"Fallback para V2 na {dex_config.name}")
            return await self._get_v2_quote(dex_config, token_in, token_out, amount_in, is_buy)
            
    async def _get_v3_quoter_quote(self, dex_config, token_in: str, token_out: str, amount_in: int, is_buy: bool) -> DexQuote:
        """Obtém cotação usando Quoter V3"""
        
        # ABI simplificado do quoter V3
        quoter_abi = [
            {
                "inputs": [
                    {"internalType": "address", "name": "tokenIn", "type": "address"},
                    {"internalType": "address", "name": "tokenOut", "type": "address"},
                    {"internalType": "uint24", "name": "fee", "type": "uint24"},
                    {"internalType": "uint256", "name": "amountIn", "type": "uint256"},
                    {"internalType": "uint160", "name": "sqrtPriceLimitX96", "type": "uint160"}
                ],
                "name": "quoteExactInputSingle",
                "outputs": [{"internalType": "uint256", "name": "amountOut", "type": "uint256"}],
                "stateMutability": "nonpayable",
                "type": "function"
            }
        ]
        
        # Endereço do quoter (pode variar por DEX)
        quoter_address = self._get_quoter_address(dex_config.name)
        if not quoter_address:
            raise ValueError("Quoter não disponível")
            
        quoter = self.w3.eth.contract(
            address=to_checksum_address(quoter_address),
            abi=quoter_abi
        )
        
        # Fees comuns no V3 (0.05%, 0.3%, 1%)
        fees = [500, 3000, 10000]
        best_amount_out = 0
        best_fee = fees[0]
        
        for fee in fees:
            try:
                amount_out = quoter.functions.quoteExactInputSingle(
                    to_checksum_address(token_in),
                    to_checksum_address(token_out),
                    fee,
                    amount_in,
                    0  # sqrtPriceLimitX96 = 0 (sem limite)
                ).call()
                
                if amount_out > best_amount_out:
                    best_amount_out = amount_out
                    best_fee = fee
                    
            except:
                continue
                
        if best_amount_out == 0:
            raise ValueError("Nenhuma pool V3 disponível")
            
        # Calcula métricas
        price_impact = await self._calculate_price_impact_v3(
            dex_config, token_in, token_out, amount_in, best_amount_out, best_fee
        )
        
        gas_estimate = await self._estimate_swap_gas_v3(dex_config, token_in, token_out, best_fee, is_buy)
        liquidity = await self._get_pool_liquidity_v3(dex_config, token_in, token_out, best_fee)
        slippage = min(price_impact * 1.2, self.max_slippage)  # 20% buffer para V3
        
        return DexQuote(
            dex_name=dex_config.name,
            dex_type=DexType.UNISWAP_V3,
            router_address=dex_config.router,
            amount_out=best_amount_out,
            price_impact=price_impact,
            gas_estimate=gas_estimate,
            slippage=slippage,
            liquidity=liquidity,
            is_available=True
        )
        
    def _get_quoter_address(self, dex_name: str) -> Optional[str]:
        """Retorna endereço do quoter para cada DEX"""
        quoters = {
            "UniswapV3": "0x61fFE014bA17989E743c5F6cB21bF9697530B21e",
            "SushiSwapV3": "0x64e8802FE490fa7cc61d3463958199161Bb608A7",
            "PancakeSwapV3": "0xB048Bbc1Ee6b733FFfCFb9e9CeF7375518e25997",
            # Adicionar outros conforme necessário
        }
        return quoters.get(dex_name)
        
    async def _calculate_price_impact_v2(self, dex_config, token_in: str, token_out: str, amount_in: int, amount_out: int) -> float:
        """Calcula price impact para DEX V2"""
        try:
            # Obtém reservas do par
            reserves = await self._get_pair_reserves_v2(dex_config, token_in, token_out)
            if not reserves:
                return 0.5  # Assume alto impact se não conseguir obter reservas
                
            reserve_in, reserve_out = reserves
            
            # Calcula preço antes e depois
            price_before = reserve_out / reserve_in
            price_after = (reserve_out - amount_out) / (reserve_in + amount_in)
            
            price_impact = abs(price_before - price_after) / price_before
            return min(price_impact, 1.0)
            
        except Exception as e:
            logger.debug(f"Erro calculando price impact V2: {e}")
            return 0.5
            
    async def _calculate_price_impact_v3(self, dex_config, token_in: str, token_out: str, amount_in: int, amount_out: int, fee: int) -> float:
        """Calcula price impact para DEX V3"""
        try:
            # Para V3, o cálculo é mais complexo devido às pools concentradas
            # Usamos uma aproximação baseada no ratio de amounts
            
            # Obtém preço spot da pool
            spot_price = await self._get_v3_spot_price(dex_config, token_in, token_out, fee)
            if not spot_price:
                return 0.3
                
            # Calcula preço efetivo do trade
            effective_price = amount_out / amount_in
            
            price_impact = abs(spot_price - effective_price) / spot_price
            return min(price_impact, 1.0)
            
        except Exception as e:
            logger.debug(f"Erro calculando price impact V3: {e}")
            return 0.3
            
    async def _select_best_quote(self, quotes: List[DexQuote], is_buy: bool) -> Optional[BestQuote]:
        """Seleciona a melhor cotação baseada em múltiplos fatores"""
        
        if not quotes:
            return None
            
        best_quotes = []
        gas_price = await self._get_current_gas_price()
        
        for quote in quotes:
            # Filtra cotações com problemas
            if quote.price_impact > self.max_price_impact:
                continue
            if quote.liquidity < self.min_liquidity:
                continue
                
            # Calcula custo total (gas + slippage)
            gas_cost = quote.gas_estimate * gas_price
            slippage_cost = int(quote.amount_out * quote.slippage)
            total_cost = gas_cost + slippage_cost
            
            # Amount líquido após custos
            net_amount = quote.amount_out - slippage_cost
            
            # Score de eficiência (maior = melhor)
            efficiency_score = self._calculate_efficiency_score(quote, net_amount, total_cost)
            
            best_quotes.append(BestQuote(
                dex_quote=quote,
                net_amount=net_amount,
                total_cost=total_cost,
                efficiency_score=efficiency_score
            ))
            
        if not best_quotes:
            return None
            
        # Ordena por efficiency score
        best_quotes.sort(key=lambda x: x.efficiency_score, reverse=True)
        
        return best_quotes[0]
        
    def _calculate_efficiency_score(self, quote: DexQuote, net_amount: int, total_cost: int) -> float:
        """Calcula score de eficiência da cotação"""
        
        # Fatores do score
        amount_score = net_amount / 1e18  # Normaliza para ETH
        liquidity_score = min(float(quote.liquidity), 10.0) / 10.0  # Max 10 ETH
        impact_score = 1.0 - quote.price_impact  # Menor impact = melhor
        gas_score = 1.0 - min(quote.gas_estimate / 500000, 1.0)  # Normaliza gas
        
        # Pesos dos fatores
        weights = {
            "amount": 0.4,
            "liquidity": 0.2,
            "impact": 0.3,
            "gas": 0.1
        }
        
        score = (
            amount_score * weights["amount"] +
            liquidity_score * weights["liquidity"] +
            impact_score * weights["impact"] +
            gas_score * weights["gas"]
        )
        
        return score
        
    async def _get_current_gas_price(self) -> int:
        """Obtém preço atual do gas com cache"""
        try:
            current_time = asyncio.get_event_loop().time()
            
            # Verifica cache
            if "gas_price" in self.gas_price_cache:
                cached_time, cached_price = self.gas_price_cache["gas_price"]
                if current_time - cached_time < self.cache_ttl:
                    return cached_price
                    
            # Obtém preço atual
            gas_price = self.w3.eth.gas_price
            
            # Adiciona buffer para congestionamento
            gas_price = int(gas_price * 1.1)  # +10%
            
            # Salva no cache
            self.gas_price_cache["gas_price"] = (current_time, gas_price)
            
            return gas_price
            
        except Exception as e:
            logger.error(f"❌ Erro obtendo gas price: {e}")
            return 20_000_000_000  # 20 gwei default
            
    async def _get_pair_reserves_v2(self, dex_config, token_in: str, token_out: str) -> Optional[Tuple[int, int]]:
        """Obtém reservas de um par V2"""
        try:
            # ABI do par V2
            pair_abi = [
                {
                    "inputs": [],
                    "name": "getReserves",
                    "outputs": [
                        {"internalType": "uint112", "name": "_reserve0", "type": "uint112"},
                        {"internalType": "uint112", "name": "_reserve1", "type": "uint112"},
                        {"internalType": "uint32", "name": "_blockTimestampLast", "type": "uint32"}
                    ],
                    "stateMutability": "view",
                    "type": "function"
                }
            ]
            
            # Calcula endereço do par
            pair_address = await self._get_pair_address_v2(dex_config, token_in, token_out)
            if not pair_address:
                return None
                
            pair = self.w3.eth.contract(address=pair_address, abi=pair_abi)
            reserves = pair.functions.getReserves().call()
            
            # Determina ordem dos tokens
            token0 = min(token_in.lower(), token_out.lower())
            if token_in.lower() == token0:
                return reserves[0], reserves[1]  # reserve_in, reserve_out
            else:
                return reserves[1], reserves[0]  # reserve_in, reserve_out
                
        except Exception as e:
            logger.debug(f"Erro obtendo reservas V2: {e}")
            return None
            
    async def _get_pair_address_v2(self, dex_config, token_in: str, token_out: str) -> Optional[str]:
        """Calcula endereço do par V2"""
        try:
            # ABI da factory V2
            factory_abi = [
                {
                    "inputs": [
                        {"internalType": "address", "name": "tokenA", "type": "address"},
                        {"internalType": "address", "name": "tokenB", "type": "address"}
                    ],
                    "name": "getPair",
                    "outputs": [{"internalType": "address", "name": "pair", "type": "address"}],
                    "stateMutability": "view",
                    "type": "function"
                }
            ]
            
            factory = self.w3.eth.contract(
                address=to_checksum_address(dex_config.factory),
                abi=factory_abi
            )
            
            pair_address = factory.functions.getPair(
                to_checksum_address(token_in),
                to_checksum_address(token_out)
            ).call()
            
            if pair_address == "0x0000000000000000000000000000000000000000":
                return None
                
            return pair_address
            
        except Exception as e:
            logger.debug(f"Erro obtendo endereço do par: {e}")
            return None
            
    async def _get_pair_liquidity_v2(self, dex_config, token_in: str, token_out: str) -> Decimal:
        """Obtém liquidez de um par V2"""
        try:
            reserves = await self._get_pair_reserves_v2(dex_config, token_in, token_out)
            if not reserves:
                return Decimal("0")
                
            # Assume que um dos tokens é WETH
            weth = config["WETH"].lower()
            if token_in.lower() == weth:
                return Decimal(str(reserves[0] / 1e18))
            elif token_out.lower() == weth:
                return Decimal(str(reserves[1] / 1e18))
            else:
                # Converte para ETH usando preço
                # Simplificação: assume liquidez média
                return Decimal("1.0")
                
        except Exception as e:
            logger.debug(f"Erro obtendo liquidez V2: {e}")
            return Decimal("0")
            
    async def _estimate_swap_gas_v2(self, dex_config, path: List[str], amount_in: int, is_buy: bool) -> int:
        """Estima gas para swap V2"""
        # Estimativas baseadas em dados históricos
        base_gas = 150_000  # Gas base para swap
        
        # Adiciona gas por hop
        hops = len(path) - 1
        hop_gas = 50_000 * (hops - 1)  # Gas adicional por hop extra
        
        return base_gas + hop_gas
        
    async def _estimate_swap_gas_v3(self, dex_config, token_in: str, token_out: str, fee: int, is_buy: bool) -> int:
        """Estima gas para swap V3"""
        # V3 geralmente usa mais gas que V2
        return 200_000
        
    async def _get_pool_liquidity_v3(self, dex_config, token_in: str, token_out: str, fee: int) -> Decimal:
        """Obtém liquidez de pool V3"""
        try:
            # Simplificação: retorna liquidez estimada
            # Em produção, consultaria a pool V3 diretamente
            return Decimal("2.0")
        except:
            return Decimal("0")
            
    async def _get_v3_spot_price(self, dex_config, token_in: str, token_out: str, fee: int) -> Optional[float]:
        """Obtém preço spot de pool V3"""
        try:
            # Simplificação: usa cotação pequena para estimar preço spot
            small_amount = 1000  # 1000 wei
            quote = await self._get_v3_quoter_quote(dex_config, token_in, token_out, small_amount, True)
            if quote.is_available:
                return quote.amount_out / small_amount
            return None
        except:
            return None

# Instância global
dex_aggregator = DexAggregator()

async def get_best_price(token_in: str, token_out: str, amount_in: int, is_buy: bool = True) -> Optional[BestQuote]:
    """Função principal para obter melhor preço"""
    return await dex_aggregator.get_best_quote(token_in, token_out, amount_in, is_buy)
    
async def execute_best_trade(token_in: str, token_out: str, amount_in: int, is_buy: bool = True) -> dict:
    """Executa trade na DEX com melhor preço"""
    best_quote = await get_best_price(token_in, token_out, amount_in, is_buy)
    
    if not best_quote:
        return {"success": False, "error": "Nenhuma DEX disponível"}
        
    # Executa trade na DEX selecionada
    from trade_executor import execute_trade
    
    return await execute_trade(
        dex_name=best_quote.dex_quote.dex_name,
        token_in=token_in,
        token_out=token_out,
        amount_in=amount_in,
        min_amount_out=best_quote.net_amount,
        is_buy=is_buy
    )