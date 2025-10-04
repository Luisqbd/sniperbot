from sniper import SniperBot

def test_sniper_run():
    config = {}
    sniper = SniperBot(config)
    assert hasattr(sniper, "run")