"""
Monitor de Mempool para detecção de novos tokens e memecoins
Monitora transações pendentes via WebSocket RPC para identificar lançamentos
"""

import asyncio
import json
import logging
import time
from typing import Dict, List, Optional, Callable, Set
from dataclasses import dataclass
from decimal import Decimal

import websockets
import aiohttp
from web3 import Web3
from eth_utils import to_checksum_address

from config import config
from utils import is_contract, get_token_info, calculate_liquidity

logger = logging.getLogger(__name__)

@dataclass
class NewTokenEvent:
    """Evento de novo token detectado"""
    token_address: str
    pair_address: str
    dex_name: str
    liquidity_eth: Decimal
    block_number: int
    transaction_hash: str
    timestamp: int
    holders_count: int = 0
    social_score: float = 0.0
    is_memecoin: bool = False

class MempoolMonitor:
    """Monitor de mempool para detecção de novos tokens"""
    
    def __init__(self):
        self.w3 = Web3(Web3.HTTPProvider(config["RPC_URL"]))
        self.ws_url = config["RPC_URL"].replace("https://", "wss://").replace("http://", "ws://")
        self.is_running = False
        self.callbacks: List[Callable] = []
        self.processed_pairs: Set[str] = set()
        self.memecoin_detector = MemecoinDetector()
        
        # Configurações de filtros
        self.min_liquidity = Decimal(str(config.get("MEMECOIN_MIN_LIQUIDITY", 0.05)))
        self.max_age_hours = config.get("MEMECOIN_MAX_AGE_HOURS", 24)
        self.min_holders = config.get("MEMECOIN_MIN_HOLDERS", 10)
        
    def add_callback(self, callback: Callable):
        """Adiciona callback para novos tokens detectados"""
        self.callbacks.append(callback)
        
    async def start_monitoring(self):
        """Inicia monitoramento do mempool"""
        if self.is_running:
            logger.warning("Monitor já está rodando")
            return
            
        self.is_running = True
        logger.info("🔍 Iniciando monitoramento de mempool...")
        
        try:
            # Monitora via WebSocket se disponível, senão usa polling
            if self.ws_url.startswith("ws"):
                await self._monitor_websocket()
            else:
                await self._monitor_polling()
        except Exception as e:
            logger.error(f"❌ Erro no monitoramento: {e}")
        finally:
            self.is_running = False
            
    async def stop_monitoring(self):
        """Para o monitoramento"""
        self.is_running = False
        logger.info("🛑 Parando monitoramento de mempool")
        
    async def _monitor_websocket(self):
        """Monitora via WebSocket RPC"""
        try:
            async with websockets.connect(self.ws_url) as websocket:
                # Subscreve a novos blocos
                subscribe_msg = {
                    "id": 1,
                    "method": "eth_subscribe",
                    "params": ["newHeads"]
                }
                await websocket.send(json.dumps(subscribe_msg))
                
                # Subscreve a transações pendentes
                pending_msg = {
                    "id": 2,
                    "method": "eth_subscribe", 
                    "params": ["newPendingTransactions"]
                }
                await websocket.send(json.dumps(pending_msg))
                
                logger.info("✅ Conectado ao WebSocket RPC")
                
                while self.is_running:
                    try:
                        message = await asyncio.wait_for(websocket.recv(), timeout=30)
                        data = json.loads(message)
                        await self._process_websocket_message(data)
                    except asyncio.TimeoutError:
                        # Ping para manter conexão viva
                        ping_msg = {"id": 999, "method": "net_version", "params": []}
                        await websocket.send(json.dumps(ping_msg))
                        
        except Exception as e:
            logger.error(f"❌ Erro WebSocket: {e}")
            # Fallback para polling
            await self._monitor_polling()
            
    async def _monitor_polling(self):
        """Monitora via polling de blocos"""
        logger.info("📊 Usando polling de blocos (fallback)")
        last_block = self.w3.eth.block_number
        
        while self.is_running:
            try:
                current_block = self.w3.eth.block_number
                
                if current_block > last_block:
                    # Processa novos blocos
                    for block_num in range(last_block + 1, current_block + 1):
                        await self._process_block(block_num)
                    last_block = current_block
                    
                await asyncio.sleep(1)  # Verifica a cada segundo
                
            except Exception as e:
                logger.error(f"❌ Erro no polling: {e}")
                await asyncio.sleep(5)
                
    async def _process_websocket_message(self, data: dict):
        """Processa mensagem do WebSocket"""
        if "params" not in data:
            return
            
        result = data["params"].get("result")
        if not result:
            return
            
        # Se é um novo bloco
        if "number" in result:
            block_number = int(result["number"], 16)
            await self._process_block(block_number)
            
        # Se é uma transação pendente
        elif isinstance(result, str) and result.startswith("0x"):
            await self._process_pending_transaction(result)
            
    async def _process_block(self, block_number: int):
        """Processa um bloco específico"""
        try:
            block = self.w3.eth.get_block(block_number, full_transactions=True)
            
            for tx in block.transactions:
                await self._analyze_transaction(tx, block_number)
                
        except Exception as e:
            logger.error(f"❌ Erro processando bloco {block_number}: {e}")
            
    async def _process_pending_transaction(self, tx_hash: str):
        """Processa transação pendente"""
        try:
            tx = self.w3.eth.get_transaction(tx_hash)
            await self._analyze_transaction(tx, None)
        except Exception as e:
            logger.debug(f"Erro processando tx pendente {tx_hash}: {e}")
            
    async def _analyze_transaction(self, tx, block_number: Optional[int]):
        """Analisa transação para detectar novos pares"""
        try:
            # Verifica se é transação para factory de DEX
            if not tx.to:
                return
                
            # Verifica se é criação de par
            receipt = None
            if block_number:
                try:
                    receipt = self.w3.eth.get_transaction_receipt(tx.hash)
                except:
                    return
                    
            # Analisa logs para eventos de criação de par
            if receipt and receipt.logs:
                for log in receipt.logs:
                    await self._analyze_log(log, tx, block_number)
                    
        except Exception as e:
            logger.debug(f"Erro analisando transação: {e}")
            
    async def _analyze_log(self, log, tx, block_number: int):
        """Analisa log de evento para detectar novos pares"""
        try:
            # Verifica se é evento PairCreated (Uniswap V2/V3 style)
            pair_created_topic = "0x0d3648bd0f6ba80134a33ba9275ac585d9d315f0ad8355cddefde31afa28d0e9"
            
            if log.topics and log.topics[0].hex() == pair_created_topic:
                await self._handle_pair_created(log, tx, block_number)
                
        except Exception as e:
            logger.debug(f"Erro analisando log: {e}")
            
    async def _handle_pair_created(self, log, tx, block_number: int):
        """Processa evento de par criado"""
        try:
            # Extrai endereços do log
            if len(log.topics) < 3:
                return
                
            token0 = to_checksum_address("0x" + log.topics[1].hex()[-40:])
            token1 = to_checksum_address("0x" + log.topics[2].hex()[-40:])
            pair_address = to_checksum_address("0x" + log.data.hex()[-40:])
            
            # Verifica se já processamos este par
            if pair_address in self.processed_pairs:
                return
                
            self.processed_pairs.add(pair_address)
            
            # Identifica qual token é WETH/USDC
            weth = config["WETH"]
            usdc = config["USDC"]
            
            new_token = None
            if token0.lower() in [weth.lower(), usdc.lower()]:
                new_token = token1
            elif token1.lower() in [weth.lower(), usdc.lower()]:
                new_token = token0
            else:
                return  # Par não tem WETH/USDC
                
            # Verifica se é contrato válido
            if not await is_contract(new_token):
                return
                
            # Calcula liquidez
            liquidity = await calculate_liquidity(pair_address)
            if liquidity < self.min_liquidity:
                return
                
            # Detecta se é memecoin
            is_memecoin = await self.memecoin_detector.is_memecoin(new_token)
            
            # Cria evento
            event = NewTokenEvent(
                token_address=new_token,
                pair_address=pair_address,
                dex_name=self._get_dex_name(log.address),
                liquidity_eth=liquidity,
                block_number=block_number,
                transaction_hash=tx.hash.hex(),
                timestamp=int(time.time()),
                is_memecoin=is_memecoin
            )
            
            # Notifica callbacks
            for callback in self.callbacks:
                try:
                    await callback(event)
                except Exception as e:
                    logger.error(f"❌ Erro no callback: {e}")
                    
            logger.info(f"🎯 Novo token detectado: {new_token[:10]}... (Liquidez: {liquidity:.4f} ETH)")
            
        except Exception as e:
            logger.error(f"❌ Erro processando par criado: {e}")
            
    def _get_dex_name(self, factory_address: str) -> str:
        """Identifica nome da DEX pelo endereço da factory"""
        factory_address = factory_address.lower()
        
        for dex in config["DEXES"]:
            if dex.factory.lower() == factory_address:
                return dex.name
                
        return "Unknown"

class MemecoinDetector:
    """Detector de memecoins baseado em heurísticas"""
    
    def __init__(self):
        self.memecoin_keywords = [
            "meme", "dog", "cat", "pepe", "wojak", "chad", "moon", "rocket",
            "inu", "shiba", "doge", "floki", "elon", "safe", "baby", "mini"
        ]
        self.scam_keywords = [
            "scam", "fake", "test", "copy", "clone", "rug", "honeypot"
        ]
        
    async def is_memecoin(self, token_address: str) -> bool:
        """Verifica se token é memecoin baseado em múltiplos fatores"""
        try:
            # Obtém informações do token
            token_info = await get_token_info(token_address)
            if not token_info:
                return False
                
            name = token_info.get("name", "").lower()
            symbol = token_info.get("symbol", "").lower()
            
            # Verifica palavras-chave de scam
            for keyword in self.scam_keywords:
                if keyword in name or keyword in symbol:
                    return False
                    
            # Verifica palavras-chave de memecoin
            memecoin_score = 0
            for keyword in self.memecoin_keywords:
                if keyword in name or keyword in symbol:
                    memecoin_score += 1
                    
            # Verifica supply (memecoins geralmente têm supply alto)
            total_supply = token_info.get("totalSupply", 0)
            if total_supply > 1_000_000_000:  # > 1B tokens
                memecoin_score += 1
                
            # Verifica se tem liquidez baixa mas suficiente
            # (memecoins começam com pouca liquidez)
            # Este check já foi feito no monitor principal
            
            return memecoin_score >= 2
            
        except Exception as e:
            logger.error(f"❌ Erro detectando memecoin {token_address}: {e}")
            return False

class SocialSentimentAnalyzer:
    """Analisador de sentimento social para tokens"""
    
    def __init__(self):
        self.twitter_keywords = ["moon", "gem", "100x", "rocket", "diamond", "hands"]
        self.telegram_channels = []  # Lista de canais para monitorar
        
    async def analyze_sentiment(self, token_address: str, token_name: str) -> float:
        """Analisa sentimento social do token (0.0 a 1.0)"""
        try:
            # Placeholder para análise de sentimento
            # Em produção, integraria com APIs do Twitter, Telegram, etc.
            
            score = 0.0
            
            # Verifica menções em redes sociais
            # score += await self._check_twitter_mentions(token_name)
            # score += await self._check_telegram_mentions(token_name)
            # score += await self._check_reddit_mentions(token_name)
            
            # Por enquanto, retorna score baseado em keywords
            name_lower = token_name.lower()
            for keyword in self.twitter_keywords:
                if keyword in name_lower:
                    score += 0.1
                    
            return min(score, 1.0)
            
        except Exception as e:
            logger.error(f"❌ Erro analisando sentimento: {e}")
            return 0.0

# Instância global do monitor
mempool_monitor = MempoolMonitor()

async def start_mempool_monitoring():
    """Inicia monitoramento de mempool"""
    await mempool_monitor.start_monitoring()
    
async def stop_mempool_monitoring():
    """Para monitoramento de mempool"""
    await mempool_monitor.stop_monitoring()
    
def add_mempool_callback(callback: Callable):
    """Adiciona callback para novos tokens"""
    mempool_monitor.add_callback(callback)