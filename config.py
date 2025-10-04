# -*- coding: utf-8 -*-
"""
Módulo de Configuração

Este módulo centraliza o carregamento e o acesso às configurações do bot.
As configurações são carregadas de variáveis de ambiente (arquivo .env) e
disponibilizadas através de um dicionário e de uma classe de estado global.
"""

import os
import logging
from dotenv import load_dotenv
from typing import Dict, Any

# Configura o logger
logger = logging.getLogger(__name__)

# Carrega as variáveis de ambiente do arquivo .env
load_dotenv()

def get_env_var(var_name: str, default: Any = None) -> Any:
    """Busca uma variável de ambiente."""
    return os.getenv(var_name, default)

def get_typed_env_var(var_name: str, default: Any, var_type: type) -> Any:
    """Busca uma variável de ambiente e a converte para o tipo desejado."""
    value = get_env_var(var_name)
    if value is None:
        return default
    try:
        return var_type(value)
    except (ValueError, TypeError):
        logger.warning(
            f"Não foi possível converter a variável de ambiente '{var_name}' para o tipo {var_type}. "
            f"Usando o valor padrão: {default}"
        )
        return default

# --- Dicionário de Configurações ---
config: Dict[str, Any] = {
    # --- Chaves de API e Carteira ---
    "TELEGRAM_BOT_TOKEN": get_env_var("TELEGRAM_BOT_TOKEN"),
    "TELEGRAM_CHAT_ID": get_env_var("TELEGRAM_CHAT_ID"),
    "PRIVATE_KEY": get_env_var("PRIVATE_KEY"),
    "BASESCAN_API_KEY": get_env_var("BASESCAN_API_KEY"),
    "WALLET_ADDRESS": None, # Será preenchido pelo web3_utils

    # --- Configurações de Rede ---
    "RPC_URL": get_env_var("RPC_URL", "https://mainnet.base.org"),
    "RPC_URL_WSS": get_env_var("RPC_URL_WSS", "wss://mainnet.base.org"),

    # --- Estratégia de Sniper ---
    "MEMECOIN_INVESTMENT_AMOUNT_USD": get_typed_env_var("MEMECOIN_INVESTMENT_AMOUNT_USD", 8.0, float),
    "MEMECOIN_PROFIT_TARGET_MULTIPLIER": get_typed_env_var("MEMECOIN_PROFIT_TARGET_MULTIPLIER", 2.0, float),
    "MEMECOIN_STOP_LOSS_PERCENTAGE": get_typed_env_var("MEMECOIN_STOP_LOSS_PERCENTAGE", 0.30, float),

    # --- Configurações de Transação ---
    "MAX_SLIPPAGE_PERCENT": get_typed_env_var("MAX_SLIPPAGE_PERCENT", 25.0, float),

    # --- Modo Turbo ---
    "TURBO_MODE_INVESTMENT_AMOUNT_USD": get_typed_env_var("TURBO_MODE_INVESTMENT_AMOUNT_USD", 15.0, float),
    "TURBO_MODE_MAX_SLIPPAGE_PERCENT": get_typed_env_var("TURBO_MODE_MAX_SLIPPAGE_PERCENT", 50.0, float),
    "TURBO_MODE_GAS_BUMP_GWEI": get_typed_env_var("TURBO_MODE_GAS_BUMP_GWEI", 0.1, float),

    # --- Endereços de Contratos (Rede Base) ---
    "WETH_ADDRESS": get_env_var("WETH_ADDRESS", "0x4200000000000000000000000000000000000006"),
    "DEX_ROUTERS": {
        "baseswap": get_env_var("BASESWAP_ROUTER_ADDRESS", "0x327Df1E6de05895d2ab08525862d053346e2f5FB"),
        "uniswap_v3": get_env_var("UNISWAP_V3_ROUTER_ADDRESS", "0x2626664c2603336E57B271c5C0b26F421741e481"),
    }
}

# --- Estado Global do Bot ---
class BotState:
    """Classe para manter o estado global e dinâmico do bot."""
    def __init__(self):
        self.is_running: bool = False
        self.is_turbo_mode: bool = False
        self.open_positions: Dict[str, Any] = {}
        self.daily_profit: float = 0.0
        self.eth_price_usd: float = 3000.0
        self.wallet_balance: Dict[str, float] = {'eth': 0.0, 'weth': 0.0}

bot_state = BotState()

# Validação de configurações críticas
_CRITICAL_VARS = ["TELEGRAM_BOT_TOKEN", "TELEGRAM_CHAT_ID", "PRIVATE_KEY", "RPC_URL"]
for var in _CRITICAL_VARS:
    if not config.get(var):
        error_message = f"Variável de ambiente crítica '{var}' não foi definida. O bot não pode iniciar."
        logger.critical(error_message)
        raise ValueError(error_message)
