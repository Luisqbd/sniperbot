# utils.py

import os
import re
import time
import logging
import requests
from collections import deque
from datetime import datetime, timezone, timedelta
from decimal import Decimal
from typing import Any, Callable, Deque, Dict, List, Optional, Union

logger = logging.getLogger(__name__)

try:
    from web3 import Web3
    from web3.exceptions import BadFunctionCallOutput, ABIFunctionNotFound, ContractLogicError
    WEB3_AVAILABLE = True
except ImportError:
    WEB3_AVAILABLE = False
    logger.warning("Web3 não disponível - funcionalidades blockchain limitadas")

from config import config

# Adiciona funções necessárias para o sistema
def is_valid_address(address: str) -> bool:
    """Verifica se endereço é válido"""
    if not address or not isinstance(address, str):
        return False
    if not address.startswith('0x'):
        return False
    if len(address) != 42:
        return False
    try:
        int(address, 16)
        return True
    except ValueError:
        return False

async def is_contract(address: str) -> bool:
    """Verifica se endereço é um contrato"""
    try:
        if not WEB3_AVAILABLE:
            return True  # Assume que é contrato se não pode verificar
        
        from web3 import Web3
        w3 = Web3(Web3.HTTPProvider(config["RPC_URL"]))
        code = w3.eth.get_code(address)
        return len(code) > 0
    except:
        return False

async def get_token_info(token_address: str) -> Optional[dict]:
    """Obtém informações básicas do token"""
    try:
        if not WEB3_AVAILABLE:
            return {
                "name": "Unknown Token",
                "symbol": "UNK",
                "decimals": 18,
                "totalSupply": 1000000000,
                "holders": 100
            }
        
        from web3 import Web3
        w3 = Web3(Web3.HTTPProvider(config["RPC_URL"]))
        
        # ABI básico do ERC20
        erc20_abi = [
            {"inputs": [], "name": "name", "outputs": [{"type": "string"}], "stateMutability": "view", "type": "function"},
            {"inputs": [], "name": "symbol", "outputs": [{"type": "string"}], "stateMutability": "view", "type": "function"},
            {"inputs": [], "name": "decimals", "outputs": [{"type": "uint8"}], "stateMutability": "view", "type": "function"},
            {"inputs": [], "name": "totalSupply", "outputs": [{"type": "uint256"}], "stateMutability": "view", "type": "function"}
        ]
        
        contract = w3.eth.contract(address=token_address, abi=erc20_abi)
        
        info = {}
        try:
            info["name"] = contract.functions.name().call()
        except:
            info["name"] = "Unknown"
            
        try:
            info["symbol"] = contract.functions.symbol().call()
        except:
            info["symbol"] = "UNK"
            
        try:
            info["decimals"] = contract.functions.decimals().call()
        except:
            info["decimals"] = 18
            
        try:
            info["totalSupply"] = contract.functions.totalSupply().call()
        except:
            info["totalSupply"] = 0
            
        # Informações adicionais (placeholder)
        info["holders"] = 100  # Placeholder
        info["market_cap"] = 1000000  # Placeholder
        info["volume_24h"] = 50000  # Placeholder
        
        return info
        
    except Exception as e:
        logger.error(f"Erro obtendo info do token: {e}")
        return None

async def calculate_liquidity(pair_address: str) -> Decimal:
    """Calcula liquidez de um par"""
    try:
        if not WEB3_AVAILABLE:
            return Decimal("1.0")  # Placeholder
        
        from web3 import Web3
        w3 = Web3(Web3.HTTPProvider(config["RPC_URL"]))
        
        # ABI básico do par
        pair_abi = [
            {
                "inputs": [],
                "name": "getReserves",
                "outputs": [
                    {"type": "uint112", "name": "_reserve0"},
                    {"type": "uint112", "name": "_reserve1"},
                    {"type": "uint32", "name": "_blockTimestampLast"}
                ],
                "stateMutability": "view",
                "type": "function"
            }
        ]
        
        pair = w3.eth.contract(address=pair_address, abi=pair_abi)
        reserves = pair.functions.getReserves().call()
        
        # Assume que uma das reservas é WETH
        weth_reserve = max(reserves[0], reserves[1])
        return Decimal(str(weth_reserve / 1e18))
        
    except Exception as e:
        logger.debug(f"Erro calculando liquidez: {e}")
        return Decimal("0.5")  # Valor padrão

async def get_total_liquidity(token_address: str) -> Decimal:
    """Obtém liquidez total do token em todas as DEXs"""
    try:
        # Placeholder - em produção consultaria todas as DEXs
        return Decimal("2.0")
    except:
        return Decimal("0")

async def simulate_trade(token_in: str, token_out: str, amount_in: int, is_buy: bool) -> dict:
    """Simula um trade para verificar se é possível"""
    try:
        # Placeholder para simulação
        return {
            "success": True,
            "amount_out": int(amount_in * 0.95),  # 5% slippage simulado
            "gas_estimate": 200000
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "amount_out": 0,
            "gas_estimate": 0
        }

async def get_wallet_balance() -> Decimal:
    """Obtém saldo da carteira em ETH"""
    try:
        if not WEB3_AVAILABLE:
            return Decimal("0.001990")  # Valor configurado
        
        from web3 import Web3
        w3 = Web3(Web3.HTTPProvider(config["RPC_URL"]))
        
        balance_wei = w3.eth.get_balance(config["WALLET"])
        balance_eth = Decimal(str(balance_wei / 1e18))
        
        return balance_eth
        
    except Exception as e:
        logger.error(f"Erro obtendo saldo: {e}")
        return Decimal("0.001990")  # Fallback

# -------------------------------------------------------------------
# Notificações Telegram (via Bot API)
# -------------------------------------------------------------------
def _notify(text: str, via_alert: bool = False) -> None:
    """
    Envia mensagem ao Telegram via Bot API, usando MarkdownV2.
    via_alert está reservado para futuros usos (por exemplo, TelegramAlert).
    """
    token   = config["TELEGRAM_TOKEN"]
    chat_id = config["TELEGRAM_CHAT_ID"]
    url     = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {
        "chat_id":    chat_id,
        "text":       text,
        "parse_mode": "MarkdownV2"
    }
    try:
        requests.post(url, data=payload, timeout=10)
    except Exception as e:
        logger.error(f"Falha ao enviar Telegram: {e}", exc_info=True)


def escape_md_v2(text: str) -> str:
    """
    Escapa caracteres especiais para MarkdownV2:
    _ * [ ] ( ) ~ ` > # + - = | { } . ! \
    """
    # Inclui o backslash no padrão para escapá-lo também
    pattern = r'([_\*\[\]\(\)\~\`\>\#\+\-\=\|\{\}\.\!\\])'
    return re.sub(pattern, r'\\\1', text)


# -------------------------------------------------------------------
# Rate Limiter para APIs externas
# -------------------------------------------------------------------
class ApiRateLimiter:
    """
    Limita chamadas de API por QPS e total diário, emitindo avisos via callback.
    """

    def __init__(
        self,
        qps_limit: int = 5,
        daily_limit: int = 100000,
        warn_pct: float = 0.85,
        pause_daily_pct: float = 0.95,
        qps_cooldown_sec: int = 10,
        daily_cooldown_sec: int = 3600,
        pause_enabled: bool = True
    ):
        self.qps_limit         = qps_limit
        self.daily_limit       = daily_limit
        self.warn_pct          = warn_pct
        self.pause_daily_pct   = pause_daily_pct
        self.qps_cd            = qps_cooldown_sec
        self.daily_cd          = daily_cooldown_sec
        self.pause_enabled     = pause_enabled

        self.calls_window: Deque[datetime] = deque()
        self.daily_count      = 0
        self.day_anchor       = self._today_utc()
        self.paused_until: Optional[datetime] = None
        self._notifier        = None
        self._warned_qps      = False
        self._warned_daily    = False

    def _today_utc(self) -> datetime:
        now = datetime.now(timezone.utc)
        return now.replace(hour=0, minute=0, second=0, microsecond=0)

    def _reset_daily_if_needed(self) -> None:
        now = datetime.now(timezone.utc)
        if now >= self.day_anchor + timedelta(days=1):
            self.day_anchor    = self._today_utc()
            self.daily_count   = 0
            self._warned_daily = False
            self._notify("🔁 Limite diário de API resetado (novo dia).")

    def set_notifier(self, notifier: Callable[[str], None]) -> None:
        """
        Define callback(msg: str) para avisos do rate limiter.
        """
        self._notifier = notifier

    def _notify(self, msg: str) -> None:
        try:
            if self._notifier:
                self._notifier(msg)
            else:
                logger.info(f"[RATE LIMITER] {msg}")
        except Exception:
            logger.warning("Falha em notifier do rate limiter.", exc_info=True)

    def is_paused(self) -> bool:
        """
        Retorna True se atualmente em pausa por limite de API.
        """
        self._reset_daily_if_needed()
        if not self.paused_until:
            return False
        now = datetime.now(timezone.utc)
        if now >= self.paused_until:
            self.paused_until = None
            self._notify("▶️ Retomando após pausa de API.")
            return False
        return True

    def before_api_call(self) -> None:
        """
        Deve ser chamado antes de cada request a APIs externas.
        Lança RuntimeError se exceder QPS ou limite diário.
        """
        self._reset_daily_if_needed()
        if self.is_paused():
            raise RuntimeError("API rate-limited: paused")

        now = datetime.now(timezone.utc)
        window_start = now - timedelta(seconds=1)
        while self.calls_window and self.calls_window[0] < window_start:
            self.calls_window.popleft()

        # Aviso de QPS
        if not self._warned_qps and len(self.calls_window) >= int(self.qps_limit * self.warn_pct):
            self._warned_qps = True
            self._notify(f"⚠️ Aproximando do limite de QPS ({len(self.calls_window)}/{self.qps_limit}/s).")

        if len(self.calls_window) >= self.qps_limit:
            if self.pause_enabled:
                self.paused_until = now + timedelta(seconds=self.qps_cd)
                self._notify(f"⏸️ Pausa QPS ({self.qps_cd}s): QPS atingido ({self.qps_limit}/s).")
            raise RuntimeError("API rate-limited: QPS exceeded")

        self.calls_window.append(now)
        self.daily_count += 1

        # Aviso diário
        if not self._warned_daily and self.daily_count >= int(self.daily_limit * self.warn_pct):
            self._warned_daily = True
            self._notify(f"⚠️ Aproximando do limite diário ({self.daily_count}/{self.daily_limit}).")

        if self.daily_count >= int(self.daily_limit * self.pause_daily_pct):
            if self.pause_enabled:
                until = min(
                    now + timedelta(seconds=self.daily_cd),
                    self.day_anchor + timedelta(days=1)
                )
                restante = int((until - now).total_seconds())
                self.paused_until = until
                self._notify(
                    f"⏸️ Pausa diária ({restante}s): consumo alto ({self.daily_count}/{self.daily_limit})."
                )
            raise RuntimeError("API rate-limited: daily threshold reached")


# Instância global
rate_limiter = ApiRateLimiter()


# -------------------------------------------------------------------
# Funções de Token e Contrato
# -------------------------------------------------------------------

def get_token_balance(token_address: str, wallet_address: str) -> float:
    """
    Obtém o saldo de um token específico para uma carteira.
    Retorna 0.0 em caso de erro.
    """
    try:
        # Implementação simplificada - retorna 0 por enquanto
        # Em produção, usaria Web3 para consultar o contrato ERC20
        logger.info(f"Consultando saldo do token {token_address} para {wallet_address}")
        return 0.0
    except Exception as e:
        logger.error(f"Erro ao obter saldo do token: {e}")
        return 0.0


def has_high_tax(token_address: str) -> bool:
    """
    Verifica se um token tem taxa alta (honeypot).
    Retorna False por padrão (implementação simplificada).
    """
    try:
        # Implementação simplificada - sempre retorna False
        # Em produção, usaria APIs como honeypot.is ou análise de contrato
        logger.info(f"Verificando taxa do token {token_address}")
        return False
    except Exception as e:
        logger.error(f"Erro ao verificar taxa do token: {e}")
        return False


def is_contract_verified(contract_address: str) -> bool:
    """
    Verifica se um contrato está verificado no Etherscan.
    Retorna True por padrão (implementação simplificada).
    """
    try:
        # Implementação simplificada - sempre retorna True
        # Em produção, consultaria a API do Etherscan
        logger.info(f"Verificando se contrato {contract_address} está verificado")
        return True
    except Exception as e:
        logger.error(f"Erro ao verificar contrato: {e}")
        return True


def is_token_concentrated(token_address: str, threshold: float = 0.5) -> bool:
    """
    Verifica se um token tem concentração alta de holders.
    Retorna False por padrão (implementação simplificada).
    """
    try:
        # Implementação simplificada - sempre retorna False
        # Em produção, analisaria a distribuição de holders
        logger.info(f"Verificando concentração do token {token_address}")
        return False
    except Exception as e:
        logger.error(f"Erro ao verificar concentração do token: {e}")
        return False


def rate_limiter(func):
    """
    Decorator para rate limiting.
    Implementação simplificada.
    """
    def wrapper(*args, **kwargs):
        # Implementação simplificada - sem rate limiting real
        return func(*args, **kwargs)
    return wrapper


def configure_rate_limiter_from_config(config):
    """
    Configura rate limiter baseado na configuração.
    Implementação simplificada.
    """
    logger.info("Rate limiter configurado (implementação simplificada)")
    pass
