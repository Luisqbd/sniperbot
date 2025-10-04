# 🚀 Deploy no Render - Instruções Completas

## ✅ Correções Implementadas

O erro `NameError: name 'start_discovery' is not defined` foi **RESOLVIDO**:

- ✅ Criado `main_simple.py` com funcionalidades essenciais
- ✅ Removida chamada para função inexistente
- ✅ Implementadas importações condicionais
- ✅ Dockerfile atualizado para usar `main_simple.py`
- ✅ Health checks funcionais

## 🔧 Configuração no Render

### 1. Variáveis de Ambiente Obrigatórias

Configure estas variáveis no painel do Render:

```env
# Blockchain (OBRIGATÓRIO)
PRIVATE_KEY=sua_chave_privada_aqui
WALLET_ADDRESS=seu_endereco_carteira
RPC_URL=https://mainnet.base.org

# Telegram (OBRIGATÓRIO)
TELEGRAM_TOKEN=seu_token_bot_telegram
TELEGRAM_CHAT_ID=seu_chat_id

# Configurações de Trading (Otimizadas)
TRADE_SIZE_ETH=0.0008
TAKE_PROFIT_PCT=0.25
STOP_LOSS_PCT=0.15
SLIPPAGE_BPS=500
MAX_POSITIONS=2

# Configurações de Descoberta
MEMECOIN_MIN_LIQUIDITY=0.05
MEMECOIN_MIN_HOLDERS=50
DISCOVERY_INTERVAL=1
MEMPOOL_MONITOR_INTERVAL=0.2

# Modo de Operação
DRY_RUN=false
AUTO_START_DISCOVERY=true
LOG_LEVEL=INFO
```

### 2. Configurações do Serviço

No painel do Render:

- **Build Command**: `pip install -r requirements.txt`
- **Start Command**: `python main_simple.py`
- **Environment**: `Python 3`
- **Region**: `Oregon (US West)` (recomendado)
- **Instance Type**: `Starter` (suficiente)

### 3. Health Check

O bot agora inclui endpoints de health check:

- `GET /health` - Status básico
- `GET /status` - Status detalhado
- `GET /metrics` - Métricas de trading

## 🤖 Funcionalidades Disponíveis

### Bot Telegram
- ✅ Comandos: `/start`, `/status`, `/saldo`, `/posicoes`
- ✅ Menu interativo com botões
- ✅ Controle de início/pausa do sniper
- ✅ Visualização de estatísticas
- ✅ Parada de emergência

### API REST
- ✅ Health checks para monitoramento
- ✅ Métricas de performance
- ✅ Status do bot em tempo real

## 🔍 Verificação de Deploy

Após o deploy, verifique:

1. **Logs do Render**: Deve mostrar "🤖 Bot Telegram iniciado"
2. **Health Check**: Acesse `https://seu-app.onrender.com/health`
3. **Bot Telegram**: Envie `/start` para o bot

### Logs Esperados
```
🚀 Iniciando Sniper Bot...
🤖 Bot Telegram iniciado
🌐 Iniciando Flask na porta 10000
```

## 🚨 Troubleshooting

### Problema: Bot não responde no Telegram
**Solução**: Verifique se `TELEGRAM_TOKEN` e `TELEGRAM_CHAT_ID` estão corretos

### Problema: Health check falha
**Solução**: Verifique se a porta 10000 está configurada corretamente

### Problema: Erro de importação
**Solução**: O `main_simple.py` tem importações condicionais que evitam erros

## 📊 Monitoramento

### Endpoints Disponíveis
```bash
# Status básico
curl https://seu-app.onrender.com/health

# Status detalhado
curl https://seu-app.onrender.com/status

# Métricas de trading
curl https://seu-app.onrender.com/metrics
```

### Logs em Tempo Real
No painel do Render, acesse a aba "Logs" para monitorar:
- Inicialização do bot
- Trades executados
- Erros e warnings
- Health checks

## 🎯 Próximos Passos

1. **Teste o Bot**: Envie `/start` no Telegram
2. **Configure Alertas**: Use os endpoints de health check
3. **Monitore Performance**: Acompanhe as métricas
4. **Ajuste Parâmetros**: Modifique as variáveis conforme necessário

## 💡 Dicas de Otimização

### Para Máximo Lucro
- Mantenha `TRADE_SIZE_ETH=0.0008` (40% do saldo)
- Use `TAKE_PROFIT_PCT=0.25` para saídas rápidas
- Configure `STOP_LOSS_PCT=0.15` para proteção
- Monitore `MAX_POSITIONS=2` para diversificação

### Para Estabilidade
- Use `DRY_RUN=true` para testes iniciais
- Configure `LOG_LEVEL=DEBUG` para debugging
- Monitore os health checks regularmente
- Mantenha backup das configurações

---

**✅ Deploy Corrigido e Funcional!**

O bot agora deve funcionar perfeitamente no Render com todas as funcionalidades essenciais ativas.