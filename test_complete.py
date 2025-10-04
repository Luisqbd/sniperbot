#!/usr/bin/env python3
"""
🧪 Script de Teste Completo do Sniper Bot
Testa todas as funcionalidades principais
"""

import asyncio
import sys
import logging
from datetime import datetime

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_web3_connection():
    """Testa conexão Web3"""
    print("🔗 Testando conexão Web3...")
    try:
        from main_complete import w3, config
        if w3 and w3.is_connected():
            chain_id = w3.eth.chain_id
            block_number = w3.eth.block_number
            print(f"✅ Web3 conectado - Chain ID: {chain_id}, Block: {block_number}")
            return True
        else:
            print("❌ Web3 não conectado")
            return False
    except Exception as e:
        print(f"❌ Erro Web3: {e}")
        return False

async def test_dex_status():
    """Testa verificação de DEXs"""
    print("\n🔧 Testando status das DEXs...")
    try:
        from main_complete import check_dex_status, DEX_CONFIGS
        
        dex_status = await check_dex_status()
        
        for dex_name, status_info in dex_status.items():
            status = status_info.get('status', 'unknown')
            emoji = "✅" if status == 'active' else "❌" if status == 'error' else "⚠️"
            print(f"{emoji} {DEX_CONFIGS.get(dex_name, {}).get('name', dex_name)}: {status}")
        
        active_count = sum(1 for s in dex_status.values() if s.get('status') == 'active')
        print(f"📊 DEXs ativas: {active_count}/{len(DEX_CONFIGS)}")
        
        return active_count > 0
    except Exception as e:
        print(f"❌ Erro testando DEXs: {e}")
        return False

async def test_wallet_balance():
    """Testa consulta de saldo"""
    print("\n💰 Testando consulta de saldo...")
    try:
        from main_complete import get_wallet_balance
        
        balance = await get_wallet_balance()
        
        print(f"💎 ETH: {balance.get('eth', 0):.6f} ETH")
        print(f"💎 WETH: {balance.get('weth', 0):.6f} WETH")
        print(f"💰 Total: {balance.get('eth', 0) + balance.get('weth', 0):.6f} ETH")
        
        return balance.get('eth', 0) > 0 or balance.get('weth', 0) > 0
    except Exception as e:
        print(f"❌ Erro consultando saldo: {e}")
        return False

def test_bot_state():
    """Testa estado do bot"""
    print("\n🤖 Testando estado do bot...")
    try:
        from main_complete import bot_state
        
        print(f"🔄 Running: {bot_state.running}")
        print(f"🚀 Turbo Mode: {bot_state.turbo_mode}")
        print(f"🔍 Discovery: {bot_state.discovery_active}")
        print(f"📊 Positions: {len(bot_state.positions)}")
        print(f"📈 Total Trades: {bot_state.stats['total_trades']}")
        print(f"⏱️ Start Time: {bot_state.stats['start_time']}")
        
        return True
    except Exception as e:
        print(f"❌ Erro testando estado: {e}")
        return False

def test_telegram_imports():
    """Testa importações do Telegram"""
    print("\n📱 Testando importações Telegram...")
    try:
        from main_complete import TELEGRAM_AVAILABLE
        if TELEGRAM_AVAILABLE:
            print("✅ Telegram disponível")
            return True
        else:
            print("⚠️ Telegram não disponível (esperado em ambiente de teste)")
            return True  # Não é erro crítico
    except Exception as e:
        print(f"❌ Erro testando Telegram: {e}")
        return False

def test_flask_imports():
    """Testa importações do Flask"""
    print("\n🌐 Testando importações Flask...")
    try:
        from main_complete import FLASK_AVAILABLE
        if FLASK_AVAILABLE:
            print("✅ Flask disponível")
            return True
        else:
            print("⚠️ Flask não disponível (esperado em ambiente de teste)")
            return True  # Não é erro crítico
    except Exception as e:
        print(f"❌ Erro testando Flask: {e}")
        return False

def test_config():
    """Testa configurações"""
    print("\n⚙️ Testando configurações...")
    try:
        from main_complete import config
        
        required_configs = [
            'RPC_URL', 'PRIVATE_KEY', 'WALLET_ADDRESS',
            'TRADE_SIZE_ETH', 'TAKE_PROFIT_PCT', 'STOP_LOSS_PCT'
        ]
        
        missing_configs = []
        for key in required_configs:
            if not config.get(key):
                missing_configs.append(key)
        
        if missing_configs:
            print(f"⚠️ Configurações faltando: {', '.join(missing_configs)}")
        else:
            print("✅ Todas as configurações principais presentes")
        
        print(f"💰 Trade Size: {config.get('TRADE_SIZE_ETH', 'N/A')} ETH")
        print(f"📈 Take Profit: {config.get('TAKE_PROFIT_PCT', 'N/A')}")
        print(f"📉 Stop Loss: {config.get('STOP_LOSS_PCT', 'N/A')}")
        print(f"🎯 Max Positions: {config.get('MAX_POSITIONS', 'N/A')}")
        
        return len(missing_configs) == 0
    except Exception as e:
        print(f"❌ Erro testando config: {e}")
        return False

def test_menu_functions():
    """Testa funções de menu"""
    print("\n📋 Testando funções de menu...")
    try:
        from main_complete import build_main_menu, build_config_menu, escape_markdown_v2
        
        # Testar construção de menus
        main_menu = build_main_menu()
        config_menu = build_config_menu()
        
        print("✅ Menu principal construído")
        print("✅ Menu de configurações construído")
        
        # Testar escape de markdown
        test_text = "Test_text*with[special]chars"
        escaped = escape_markdown_v2(test_text)
        print(f"✅ Markdown escape: '{test_text}' -> '{escaped}'")
        
        return True
    except Exception as e:
        print(f"❌ Erro testando menus: {e}")
        return False

async def test_dex_contracts():
    """Testa contratos das DEXs"""
    print("\n📜 Testando contratos das DEXs...")
    try:
        from main_complete import w3, DEX_CONFIGS
        
        if not w3:
            print("⚠️ Web3 não disponível, pulando teste de contratos")
            return True
        
        results = {}
        for dex_name, dex_config in DEX_CONFIGS.items():
            try:
                router_address = dex_config['router']
                router_code = w3.eth.get_code(router_address)
                
                if len(router_code) > 0:
                    print(f"✅ {dex_config['name']}: Contrato encontrado")
                    results[dex_name] = True
                else:
                    print(f"❌ {dex_config['name']}: Contrato não encontrado")
                    results[dex_name] = False
            except Exception as e:
                print(f"❌ {dex_config['name']}: Erro - {e}")
                results[dex_name] = False
        
        success_count = sum(results.values())
        print(f"📊 Contratos válidos: {success_count}/{len(DEX_CONFIGS)}")
        
        return success_count > 0
    except Exception as e:
        print(f"❌ Erro testando contratos: {e}")
        return False

async def run_all_tests():
    """Executa todos os testes"""
    print("🧪 INICIANDO TESTES COMPLETOS DO SNIPER BOT")
    print("=" * 50)
    
    tests = [
        ("Web3 Connection", test_web3_connection()),
        ("Config", test_config()),
        ("Bot State", test_bot_state()),
        ("Telegram Imports", test_telegram_imports()),
        ("Flask Imports", test_flask_imports()),
        ("Menu Functions", test_menu_functions()),
        ("DEX Status", test_dex_status()),
        ("Wallet Balance", test_wallet_balance()),
        ("DEX Contracts", test_dex_contracts())
    ]
    
    results = []
    
    for test_name, test_coro in tests:
        print(f"\n{'='*20} {test_name} {'='*20}")
        try:
            if asyncio.iscoroutine(test_coro):
                result = await test_coro
            else:
                result = test_coro
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ Erro executando teste {test_name}: {e}")
            results.append((test_name, False))
    
    # Resumo dos resultados
    print("\n" + "="*50)
    print("📊 RESUMO DOS TESTES")
    print("="*50)
    
    passed = 0
    failed = 0
    
    for test_name, result in results:
        status = "✅ PASSOU" if result else "❌ FALHOU"
        print(f"{status} - {test_name}")
        if result:
            passed += 1
        else:
            failed += 1
    
    print(f"\n📈 RESULTADO FINAL:")
    print(f"✅ Testes Passaram: {passed}")
    print(f"❌ Testes Falharam: {failed}")
    print(f"📊 Taxa de Sucesso: {(passed/(passed+failed)*100):.1f}%")
    
    if failed == 0:
        print("\n🎉 TODOS OS TESTES PASSARAM! Bot está pronto para deploy!")
    elif failed <= 2:
        print("\n⚠️ Alguns testes falharam, mas o bot deve funcionar.")
    else:
        print("\n❌ Muitos testes falharam. Verifique a configuração.")
    
    return failed == 0

if __name__ == "__main__":
    try:
        success = asyncio.run(run_all_tests())
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n🛑 Testes interrompidos pelo usuário")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Erro fatal nos testes: {e}")
        sys.exit(1)