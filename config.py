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

Como usar:
1. Crie um arquivo .env na raiz do projeto para desenvolvimento.
2. Defina as variáveis necessárias (ex: TELEGRAM_BOT_TOKEN).
3. No código da aplicação, importe o objeto `config`:
   from config import config
4. Acesse as variáveis:
   token = config["TELEGRAM_BOT_TOKEN"]

Para adicionar uma nova variável:
1. Adicione a variável ao seu arquivo .env.example.
2. Adicione a chamada `get_env` correspondente no final deste arquivo.
"""
import os
import logging
from decimal import Decimal, InvalidOperation
from dotenv import load_dotenv

# Carrega as variáveis de ambiente do arquivo .env (se existir)
# Essencial para desenvolvimento local. Em produção (Render), as variáveis
# são injetadas diretamente no ambiente.
load_dotenv()

# Configuração básica de logging para o módulo de configuração
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def get_env(key, default=None, required=False, var_type=str):
    """
    Busca uma variável de ambiente, com validação e conversão de tipo.

    Args:
        key (str): Nome da variável de ambiente.
        default: Valor padrão a ser usado se a variável não for encontrada.
        required (bool): Se True, lança um erro se a variável não for encontrada.
        var_type (type): O tipo para o qual o valor deve ser convertido (str, int, bool, float, Decimal).

    Returns:
        O valor da variável de ambiente, convertido para o tipo especificado.

    Raises:
        RuntimeError: Se a variável é obrigatória e não está definida.
        ValueError: Se a conversão de tipo falhar.
    """
    value = os.getenv(key, default)

    if required and value is None:
        logging.error(f"Variável de ambiente obrigatória '{key}' não foi definida.")
        raise RuntimeError(f"Variável obrigatória '{key}' não informada")

    if value is None:
        return default

    try:
        if var_type == bool:
            return value.lower() in ('true', '1', 't', 'y', 'yes')
        if var_type == Decimal:
            return Decimal(str(value))
        return var_type(value)
    except (ValueError, InvalidOperation) as e:
        logging.error(f"Não foi possível converter a variável '{key}' com valor '{value}' para o tipo '{var_type.__name__}'. Erro: {e}")
        raise ValueError(f"Variável '{key}' possui um formato inválido.") from e

# --- Dicionário de Configuração ---
# Todas as variáveis de ambiente são carregadas e armazenadas neste dicionário.
config = {}

# --- Configurações Essenciais ---
config["TELEGRAM_BOT_TOKEN"] = get_env("TELEGRAM_BOT_TOKEN", required=True)
config["TELEGRAM_CHAT_ID"] = get_env("TELEGRAM_CHAT_ID", required=True)
config["PRIVATE_KEY"] = get_env("PRIVATE_KEY", required=True)
config["BASE_RPC_URL"] = get_env("BASE_RPC_URL", required=True)

# --- Configurações de Estratégia de Trading (com valores padrão otimizados) ---
config["TRADE_SIZE_ETH"] = get_env("TRADE_SIZE_ETH", default="0.0008", var_type=Decimal)
config["TAKE_PROFIT_PCT"] = get_env("TAKE_PROFIT_PCT", default="0.3", var_type=float)
config["STOP_LOSS_PCT"] = get_env("STOP_LOSS_PCT", default="0.12", var_type=float)
config["MAX_POSITIONS"] = get_env("MAX_POSITIONS", default=2, var_type=int)
config["SLIPPAGE_BPS"] = get_env("SLIPPAGE_BPS", default=500, var_type=int) # 5%

# --- Configurações de Descoberta de Memecoins ---
config["MEMECOIN_MIN_LIQUIDITY"] = get_env("MEMECOIN_MIN_LIQUIDITY", default="0.05", var_type=Decimal)
config["MEMECOIN_MIN_HOLDERS"] = get_env("MEMECOIN_MIN_HOLDERS", default=50, var_type=int)
config["MEMECOIN_MAX_INVESTMENT"] = get_env("MEMECOIN_MAX_INVESTMENT", default="0.0008", var_type=Decimal)
config["MEMECOIN_TARGET_PROFIT"] = get_env("MEMECOIN_TARGET_PROFIT", default=2.0, var_type=float) # 2x

# --- Configurações de Trading de Altcoins (Swing Trade) ---
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
config["BASESCAN_API_KEY"] = get_env("BASESCAN_API_KEY", required=True)
config["HONEYPOT_CHECK_ENABLED"] = get_env("HONEYPOT_CHECK_ENABLED", default=True, var_type=bool)

# --- Configurações de Desempenho e Timing ---
config["DISCOVERY_INTERVAL"] = get_env("DISCOVERY_INTERVAL", default=1, var_type=int)
config["MEMPOOL_MONITOR_INTERVAL"] = get_env("MEMPOOL_MONITOR_INTERVAL", default=0.2, var_type=float)
config["EXIT_POLL_INTERVAL"] = get_env("EXIT_POLL_INTERVAL", default=3, var_type=int)

# --- Configurações de Autenticação (Opcionais) ---
# **CORREÇÃO APLICADA AQUI**
# Estas variáveis são para um possível painel web e não são essenciais para o bot do Telegram.
# Torná-las opcionais (`required=False`) permite que o bot funcione sem elas.
config["AUTH0_DOMAIN"]        = get_env("AUTH0_DOMAIN",        required=False)
config["AUTH0_CLIENT_ID"]     = get_env("AUTH0_CLIENT_ID",     required=False)
config["AUTH0_CLIENT_SECRET"] = get_env("AUTH0_CLIENT_SECRET", required=False)
config["AUTH0_AUDIENCE"]      = get_env("AUTH0_AUDIENCE",      required=False)
config["FLASK_SECRET_KEY"]    = get_env("FLASK_SECRET_KEY",    default="uma-chave-secreta-default-para-desenvolvimento")

# --- Log de verificação ---
# Loga uma mensagem para confirmar que o módulo de configuração foi carregado.
# Não loga os valores das chaves por segurança.
logging.info("Módulo de configuração carregado. %d variáveis processadas.", len(config))
if not config.get("TELEGRAM_BOT_TOKEN"):
    logging.warning("Token do Telegram não encontrado. O bot não funcionará.")
if not config.get("PRIVATE_KEY"):
    logging.warning("Chave privada não encontrada. As transações não funcionarão.")