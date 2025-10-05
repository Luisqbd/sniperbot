# -*- coding: utf-8 -*-
"""
Módulo de Configuração Centralizado

Este módulo carrega e valida todas as configurações necessárias para a aplicação
a partir de variáveis de ambiente. Utiliza o padrão de ter um arquivo .env
para desenvolvimento local e espera que as variáveis sejam fornecidas diretamente
no ambiente de produção (ex: Render, Heroku).

Responsabilidades:
- Carregar variáveis de um arquivo .env.
- Validar a presença de variáveis obrigatórias.
- Converter tipos de dados (int, float, bool, Decimal).
- Fornecer um objeto `config` centralizado para toda a aplicação.
"""
import os
import logging
from decimal import Decimal, InvalidOperation
from dotenv import load_dotenv

# Carrega as variáveis de ambiente do arquivo .env (se existir)
load_dotenv()

# Configuração básica de logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def get_env(key, default=None, required=False, var_type=str):
    """
    Busca uma variável de ambiente, com validação e conversão de tipo.
    """
    value = os.getenv(key, default)

    if required and value is None:
        logging.error(f"Variável de ambiente obrigatória '{key}' não foi definida.")
        raise RuntimeError(f"Variável obrigatória '{key}' não informada")

    if value is None:
        return default

    try:
        if var_type == bool:
            # **CORREÇÃO APLICADA AQUI**
            # Converte o valor para string antes de chamar .lower() para evitar o AttributeError
            return str(value).lower() in ('true', '1', 't', 'y', 'yes')
        if var_type == Decimal:
            return Decimal(str(value))
        if value == '': # Retorna default se a variável de ambiente estiver vazia
            return default
        return var_type(value)
    except (ValueError, InvalidOperation) as e:
        logging.error(f"Não foi possível converter a variável '{key}' com valor '{value}' para o tipo '{var_type.__name__}'. Erro: {e}")
        raise ValueError(f"Variável '{key}' possui um formato inválido.") from e

# --- Dicionário de Configuração ---
config = {}

# --- Configurações Essenciais ---
config["TELEGRAM_BOT_TOKEN"] = get_env("TELEGRAM_BOT_TOKEN", required=True)
config["TELEGRAM_CHAT_ID"] = get_env("TELEGRAM_CHAT_ID", required=True)
config["PRIVATE_KEY"] = get_env("PRIVATE_KEY", required=True)
config["BASE_RPC_URL"] = get_env("BASE_RPC_URL", required=True)
config["BASESCAN_API_KEY"] = get_env("BASESCAN_API_KEY", required=True)

# --- Configurações de Estratégia de Trading ---
config["TRADE_SIZE_ETH"] = get_env("TRADE_SIZE_ETH", default="0.0008", var_type=Decimal)
config["TAKE_PROFIT_PCT"] = get_env("TAKE_PROFIT_PCT", default="0.3", var_type=float)
config["STOP_LOSS_PCT"] = get_env("STOP_LOSS_PCT", default="0.12", var_type=float)
config["MAX_POSITIONS"] = get_env("MAX_POSITIONS", default=2, var_type=int)
config["SLIPPAGE_BPS"] = get_env("SLIPPAGE_BPS", default=500, var_type=int)

# --- Configurações de Descoberta de Memecoins ---
config["MEMECOIN_MIN_LIQUIDITY"] = get_env("MEMECOIN_MIN_LIQUIDITY", default="0.05", var_type=Decimal)
config["MEMECOIN_MIN_HOLDERS"] = get_env("MEMECOIN_MIN_HOLDERS", default=50, var_type=int)
config["MEMECOIN_MAX_INVESTMENT"] = get_env("MEMECOIN_MAX_INVESTMENT", default="0.0008", var_type=Decimal)
config["MEMECOIN_TARGET_PROFIT"] = get_env("MEMECOIN_TARGET_PROFIT", default=2.0, var_type=float)

# --- Configurações de Trading de Altcoins ---
config["ALTCOIN_MIN_MARKET_CAP"] = get_env("ALTCOIN_MIN_MARKET_CAP", default=100000, var_type=int)
config["ALTCOIN_MAX_MARKET_CAP"] = get_env("ALTCOIN_MAX_MARKET_CAP", default=10000000, var_type=int)
config["ALTCOIN_PROFIT_REINVEST_PCT"] = get_env("ALTCOIN_PROFIT_REINVEST_PCT", default=0.5, var_type=float)

# --- Configurações de Modo Turbo ---
config["TURBO_MODE"] = get_env("TURBO_MODE", default=False, var_type=bool)
config["TURBO_TRADE_SIZE_ETH"] = get_env("TURBO_TRADE_SIZE_ETH", default="0.0012", var_type=Decimal)
config["TURBO_STOP_LOSS_PCT"] = get_env("TURBO_STOP_LOSS_PCT", default=0.08, var_type=float)
config["TURBO_MAX_POSITIONS"] = get_env("TURBO_MAX_POSITIONS", default=3, var_type=int)

# --- Configurações de Automação ---
config["AUTO_START_SNIPER"] = get_env("AUTO_START_SNIPER", default=True, var_type=bool)

# --- Configurações de Proteção e Fallback ---
config["HONEYPOT_CHECK_ENABLED"] = get_env("HONEYPOT_CHECK_ENABLED", default=True, var_type=bool)

# --- Configurações de Desempenho e Timing ---
config["DISCOVERY_INTERVAL"] = get_env("DISCOVERY_INTERVAL", default=1, var_type=int)
config["MEMPOOL_MONITOR_INTERVAL"] = get_env("MEMPOOL_MONITOR_INTERVAL", default=0.2, var_type=float)
config["EXIT_POLL_INTERVAL"] = get_env("EXIT_POLL_INTERVAL", default=3, var_type=int)

# --- Configurações de Autenticação (Opcionais) ---
config["AUTH0_DOMAIN"]        = get_env("AUTH0_DOMAIN",        required=False)
config["AUTH0_CLIENT_ID"]     = get_env("AUTH0_CLIENT_ID",     required=False)
config["AUTH0_CLIENT_SECRET"] = get_env("AUTH0_CLIENT_SECRET", required=False)
config["AUTH0_AUDIENCE"]      = get_env("AUTH0_AUDIENCE",      required=False)
config["FLASK_SECRET_KEY"]    = get_env("FLASK_SECRET_KEY",    default="uma-chave-secreta-default")

# --- Log de verificação ---
logging.info("Módulo de configuração carregado. %d variáveis processadas.", len(config))