import config
from sniper import SniperBot
from turbo_mode import TurboMode
from telegram_bot import TelegramBot
from pump_detector import PumpDetector
from trade_history import TradeHistory
from strategies import TradingStrategies
from protections import Protections
from rebalance import Rebalance
from fallback_dex import FallbackDex

def main():
    config.load()
    sniper = SniperBot(config)
    turbo = TurboMode(config)
    telegram = TelegramBot(config, sniper)
    pump = PumpDetector(config)
    history = TradeHistory(config)
    strategies = TradingStrategies(config)
    protections = Protections(config)
    rebalance = Rebalance(config)
    fallback = FallbackDex(config)

    # Inicialização dos módulos
    telegram.start()
    sniper.run(strategies, protections, turbo, pump, fallback)
    history.track()
    rebalance.execute()

if __name__ == "__main__":
    main()