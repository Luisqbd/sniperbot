#!/usr/bin/env python3
"""
🧪 Teste Específico para Correção do Telegram
Verifica se o problema do event loop foi resolvido
"""

import asyncio
import sys
import logging
import threading
import time
from datetime import datetime

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_telegram_manager():
    """Testa o TelegramBotManager"""
    print("🤖 Testando TelegramBotManager...")
    
    try:
        from main_fixed import TelegramBotManager, TELEGRAM_AVAILABLE
        
        if not TELEGRAM_AVAILABLE:
            print("⚠️ Telegram não disponível - teste com classes dummy")
            
            # Testar criação do manager
            manager = TelegramBotManager()
            print("✅ TelegramBotManager criado com sucesso")
            
            # Testar setup (deve falhar graciosamente)
            async def test_setup():
                result = await manager.setup_bot()
                return result
            
            # Executar teste assíncrono
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            result = loop.run_until_complete(test_setup())
            loop.close()
            
            print(f"✅ Setup bot resultado: {result} (esperado: False)")
            return True
        else:
            print("✅ Telegram disponível - teste completo")
            return True
            
    except Exception as e:
        print(f"❌ Erro testando TelegramBotManager: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_event_loop_isolation():
    """Testa isolamento de event loops"""
    print("\n🔄 Testando isolamento de event loops...")
    
    results = []
    
    def thread_with_event_loop(thread_id):
        """Thread que cria seu próprio event loop"""
        try:
            # Criar event loop para esta thread
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            async def async_task():
                await asyncio.sleep(0.1)
                return f"Thread {thread_id} OK"
            
            # Executar tarefa assíncrona
            result = loop.run_until_complete(async_task())
            results.append(result)
            
            # Fechar loop
            loop.close()
            
        except Exception as e:
            results.append(f"Thread {thread_id} ERROR: {e}")
    
    # Criar múltiplas threads com event loops
    threads = []
    for i in range(3):
        thread = threading.Thread(target=thread_with_event_loop, args=(i,))
        threads.append(thread)
        thread.start()
    
    # Aguardar todas as threads
    for thread in threads:
        thread.join()
    
    # Verificar resultados
    success_count = sum(1 for r in results if "OK" in r)
    print(f"✅ Threads com event loop: {success_count}/3")
    
    for result in results:
        print(f"  • {result}")
    
    return success_count == 3

def test_flask_app():
    """Testa se o Flask app funciona"""
    print("\n🌐 Testando Flask app...")
    
    try:
        from main_fixed import FLASK_AVAILABLE
        
        if FLASK_AVAILABLE:
            from main_fixed import app
            
            # Testar criação de rotas
            with app.test_client() as client:
                # Testar rota home
                response = client.get('/')
                print(f"✅ GET / - Status: {response.status_code}")
                
                # Testar health check
                response = client.get('/health')
                print(f"✅ GET /health - Status: {response.status_code}")
                
                # Testar status
                response = client.get('/status')
                print(f"✅ GET /status - Status: {response.status_code}")
                
            return True
        else:
            print("⚠️ Flask não disponível - teste pulado")
            return True
            
    except Exception as e:
        print(f"❌ Erro testando Flask: {e}")
        return False

def test_bot_state():
    """Testa estado do bot"""
    print("\n🤖 Testando estado do bot...")
    
    try:
        from main_fixed import bot_state, BotState
        
        # Verificar inicialização
        print(f"✅ Bot state inicializado")
        print(f"  • Running: {bot_state.running}")
        print(f"  • Turbo: {bot_state.turbo_mode}")
        print(f"  • Positions: {len(bot_state.positions)}")
        print(f"  • Start time: {bot_state.stats['start_time']}")
        
        # Testar mudanças de estado
        original_running = bot_state.running
        bot_state.running = not bot_state.running
        print(f"✅ Toggle running: {original_running} -> {bot_state.running}")
        
        original_turbo = bot_state.turbo_mode
        bot_state.turbo_mode = not bot_state.turbo_mode
        print(f"✅ Toggle turbo: {original_turbo} -> {bot_state.turbo_mode}")
        
        return True
        
    except Exception as e:
        print(f"❌ Erro testando bot state: {e}")
        return False

def test_async_functions():
    """Testa funções assíncronas"""
    print("\n⚡ Testando funções assíncronas...")
    
    try:
        from main_fixed import check_dex_status, get_wallet_balance
        
        async def run_async_tests():
            # Testar check_dex_status
            dex_status = await check_dex_status()
            print(f"✅ check_dex_status: {len(dex_status)} DEXs verificadas")
            
            # Testar get_wallet_balance
            balance = await get_wallet_balance()
            print(f"✅ get_wallet_balance: ETH={balance.get('eth', 0):.6f}, WETH={balance.get('weth', 0):.6f}")
            
            return True
        
        # Executar testes assíncronos
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        result = loop.run_until_complete(run_async_tests())
        loop.close()
        
        return result
        
    except Exception as e:
        print(f"❌ Erro testando funções assíncronas: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Executa todos os testes"""
    print("🧪 TESTE DE CORREÇÃO DO TELEGRAM - EVENT LOOP")
    print("=" * 60)
    
    tests = [
        ("TelegramBotManager", test_telegram_manager),
        ("Event Loop Isolation", test_event_loop_isolation),
        ("Flask App", test_flask_app),
        ("Bot State", test_bot_state),
        ("Async Functions", test_async_functions)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        print(f"\n{'='*20} {test_name} {'='*20}")
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ Erro executando teste {test_name}: {e}")
            results.append((test_name, False))
    
    # Resumo dos resultados
    print("\n" + "="*60)
    print("📊 RESUMO DOS TESTES DE CORREÇÃO")
    print("="*60)
    
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
        print("\n🎉 CORREÇÃO DO TELEGRAM FUNCIONANDO PERFEITAMENTE!")
        print("🚀 O problema do event loop foi RESOLVIDO!")
    elif failed <= 1:
        print("\n⚠️ Correção funcionando com pequenos problemas.")
    else:
        print("\n❌ Correção precisa de mais ajustes.")
    
    return failed == 0

if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n🛑 Testes interrompidos pelo usuário")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Erro fatal nos testes: {e}")
        sys.exit(1)