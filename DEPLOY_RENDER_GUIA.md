# 🚀 GUIA DE DEPLOY NO RENDER

## 📋 Pré-requisitos

Antes de fazer o deploy, você precisa ter:

1. ✅ Conta no [Render.com](https://render.com) (gratuita)
2. ✅ Repositório GitHub com o código (já feito)
3. ✅ Bot do Telegram criado (via @BotFather)
4. ✅ Carteira com WETH na rede Base
5. ✅ Chave privada da carteira

---

## 🔐 Configurações Obrigatórias

### 1. Variáveis de Blockchain

```env
# RPC da rede Base (use este ou um RPC privado)
RPC_URL=https://mainnet.base.org

# ID da rede Base
CHAIN_ID=8453

# Sua chave privada (SEM o 0x no início)
PRIVATE_KEY=abc123def456... 

# Endereço da sua carteira
WALLET_ADDRESS=0x...

# Endereço do WETH na Base
WETH=0x4200000000000000000000000000000000000006

# Endereço do USDC na Base (opcional)
USDC=0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913
```

### 2. Variáveis do Telegram

```env
# Token do seu bot (obtido via @BotFather)
TELEGRAM_TOKEN=123456789:ABC-DEF...

# Seu chat ID (envie /start para @userinfobot)
TELEGRAM_CHAT_ID=123456789
```

### 3. Variáveis Auth0 (se não usar, deixe valores padrão)

```env
AUTH0_DOMAIN=your-domain.auth0.com
AUTH0_AUDIENCE=https://api.test.com
AUTH0_CLIENT_ID=test_client_id
AUTH0_CLIENT_SECRET=test_client_secret
```

---

## ⚙️ Configurações Otimizadas (Para 0.001990 WETH)

### Trading Básico

```env
# Modo de operação
DRY_RUN=false              # false = real, true = simulação

# Auto-start (RECOMENDADO)
AUTO_START_SNIPER=true     # Inicia automaticamente

# Modo turbo (começar desabilitado)
TURBO_MODE=false           # false = conservador

# Tamanho do trade (40% do saldo)
TRADE_SIZE_ETH=0.0008

# Take profit e stop loss
TAKE_PROFIT_PCT=0.3        # 30% de lucro
STOP_LOSS_PCT=0.12         # 12% de perda

# Slippage e posições
SLIPPAGE_BPS=500           # 5% de slippage
MAX_POSITIONS=2            # Máximo 2 posições
```

### Modo Turbo (Avançado)

```env
# Parâmetros do modo turbo
TURBO_TRADE_SIZE_ETH=0.0012      # 60% do saldo
TURBO_TAKE_PROFIT_PCT=0.5        # 50% de lucro
TURBO_STOP_LOSS_PCT=0.08         # 8% de perda
TURBO_MONITOR_INTERVAL=0.05      # 50ms
TURBO_MAX_POSITIONS=3            # 3 posições
```

### Memecoins

```env
# Filtros de entrada
MEMECOIN_MIN_LIQUIDITY=0.05      # Min 0.05 ETH
MEMECOIN_MIN_HOLDERS=50          # Min 50 holders
MEMECOIN_MAX_AGE_HOURS=24        # Max 24 horas

# Limites de investimento
MEMECOIN_MAX_INVESTMENT=0.0008   # Max por token
MEMECOIN_TARGET_PROFIT=2.0       # Target 2x
```

### Altcoins

```env
# Filtros de market cap
ALTCOIN_MIN_MARKET_CAP=100000        # Min $100k
ALTCOIN_MAX_MARKET_CAP=10000000      # Max $10M
ALTCOIN_MIN_VOLUME_24H=50000         # Min $50k

# Reinvestimento
ALTCOIN_PROFIT_REINVEST_PCT=0.5      # 50%
```

### Timing e Monitoramento

```env
# Intervalos de verificação
DISCOVERY_INTERVAL=1             # 1 segundo
MEMPOOL_MONITOR_INTERVAL=0.2     # 200ms
EXIT_POLL_INTERVAL=3             # 3 segundos

# Rebalanceamento
ENABLE_REBALANCING=true          # Ativa rebalancing
```

### DEXs (Opcional - já tem padrões)

```env
# DEX 1 - Uniswap V2 na Base
DEX_1_NAME=Uniswap V2
DEX_1_FACTORY=0x8909Dc15e40173Ff4699343b6eB8132c65e18eC6
DEX_1_ROUTER=0x4752ba5DBc23f44D87826276BF6Fd6b1C372aD24
DEX_1_TYPE=v2

# DEX 2 - Uniswap V3 na Base
DEX_2_NAME=Uniswap V3
DEX_2_FACTORY=0x33128a8fC17869897dcE68Ed026d694621f6FDfD
DEX_2_ROUTER=0x2626664c2603336E57B271c5C0b26F421741e481
DEX_2_TYPE=v3
```

### Proteções

```env
# Verificações de segurança
BLOCK_UNVERIFIED=true            # Bloqueia não verificados
MAX_GAS_PRICE_GWEI=50            # Max 50 gwei

# Taxas e timeouts
MAX_TAX_PCT=8.0                  # Max 8% de taxa
TOP_HOLDER_LIMIT=30.0            # Max 30% para holder
TX_DEADLINE_SEC=60               # 60s timeout
```

---

## 🌐 Passos para Deploy no Render

### 1. Criar Web Service

1. Acesse [render.com](https://render.com)
2. Clique em "New +"
3. Selecione "Web Service"
4. Conecte seu repositório GitHub
5. Selecione o repositório `sniperbot`

### 2. Configurações do Service

```
Name: sniper-bot-base
Region: Oregon (US West) - ou mais próximo
Branch: main
Runtime: Python 3
Build Command: pip install -r requirements.txt
Start Command: python main_complete.py
```

### 3. Plan

- Selecione "Free" para testes
- Selecione "Starter" ou superior para produção
- Free tier dorme após 15min de inatividade

### 4. Variáveis de Ambiente

No painel do Render, vá em "Environment" e adicione TODAS as variáveis acima.

**IMPORTANTE**: As variáveis são case-sensitive!

### 5. Deploy

- Clique em "Create Web Service"
- Aguarde o build (3-5 minutos)
- Verifique os logs para confirmar sucesso

---

## ✅ Verificação Pós-Deploy

### 1. Verificar Logs

No Render, clique em "Logs" e verifique:

```
✅ "🚀 Iniciando Sniper Bot Completo v2.0..."
✅ "✅ Web3 conectado - Chain ID: 8453"
✅ "🤖 Bot Telegram iniciado"
✅ "🚀 Iniciando sniper automaticamente..." (se AUTO_START=true)
```

### 2. Testar Telegram

1. Abra o Telegram
2. Procure seu bot
3. Envie `/start`
4. Deve aparecer o menu principal

### 3. Testar Health Check

Acesse: `https://seu-app.onrender.com/health`

Deve retornar:
```json
{
  "status": "healthy",
  "uptime": "...",
  "bot_running": true
}
```

### 4. Verificar Saldo

No Telegram:
```
/saldo
```

Deve mostrar seu saldo de ETH e WETH.

---

## 🔧 Troubleshooting

### Problema: Bot não inicia

**Possíveis causas:**
1. Variáveis de ambiente incorretas
2. PRIVATE_KEY inválida
3. RPC não respondendo

**Solução:**
```bash
# Verifique os logs no Render
# Procure por erros como:
- "Variável obrigatória 'PRIVATE_KEY' não informada"
- "PRIVATE_KEY inválida"
- "Connection refused"
```

### Problema: Telegram não responde

**Solução:**
1. Verifique TELEGRAM_TOKEN
2. Verifique TELEGRAM_CHAT_ID
3. Certifique-se que iniciou conversa com o bot
4. Use `/start` para acordar o bot

### Problema: Service dorme (Free tier)

**Solução:**
1. Upgrade para Starter ($7/mês)
2. Ou use um serviço de ping (ex: UptimeRobot)
3. Configure webhook do Render

### Problema: Muitos logs

**Solução:**
No .env, ajuste nível de log:
```env
LOG_LEVEL=INFO  # ou WARNING para menos logs
```

---

## 🔄 Atualização do Bot

### Via GitHub (Automático)

1. Faça push para GitHub:
```bash
git push origin main
```

2. Render detecta automaticamente e faz redeploy

### Manual

1. No Render, clique em "Manual Deploy"
2. Selecione a branch
3. Clique em "Deploy"

---

## 💰 Custos Estimados

### Render Plans

| Plan | Preço | RAM | CPU | Uptime |
|------|-------|-----|-----|--------|
| Free | $0 | 512MB | Shared | 750h/mês |
| Starter | $7/mês | 512MB | Shared | 100% |
| Standard | $25/mês | 2GB | 1 CPU | 100% |
| Pro | $85/mês | 4GB | 2 CPU | 100% |

### Custos de Gas (Base Network)

- **Gas por Trade**: ~$0.10 - $0.50
- **Estimativa Mensal** (10 trades/dia): $30 - $150
- **Mais barato que Ethereum** (10-20x)

### Total Estimado

```
Render Starter:        $7/mês
Gas (médio):          $90/mês
Total:               ~$100/mês

Lucro necessário para breakeven: 0.04 ETH/mês (~$100)
Com 0.002 WETH, precisa fazer ~2x o capital
```

---

## 📊 Monitoramento

### 1. Logs do Render

- Acesse regularmente
- Procure por erros
- Verifique performance

### 2. Telegram

Configure alertas:
```
/status   - A cada hora
/stats    - Diariamente
/saldo    - Antes de dormir
```

### 3. Métricas

Monitore:
- Taxa de acerto (>50% é bom)
- Lucro médio por trade
- Tempo médio de holding
- Slippage médio

---

## 🔐 Segurança

### ⚠️ NUNCA:
- ❌ Compartilhe sua PRIVATE_KEY
- ❌ Commit .env no git
- ❌ Use carteira principal
- ❌ Coloque todo seu capital
- ❌ Desabilite proteções

### ✅ SEMPRE:
- ✅ Use carteira dedicada
- ✅ Comece com DRY_RUN=true
- ✅ Teste antes de investir real
- ✅ Monitore logs
- ✅ Faça backup das configs

---

## 📞 Suporte

- **Render Docs**: [docs.render.com](https://docs.render.com)
- **Telegram**: Use `/help` no bot
- **GitHub**: Issues no repositório
- **Logs**: Sempre verifique primeiro

---

## ✅ Checklist de Deploy

Antes de fazer deploy em produção:

- [ ] Testado em DRY_RUN=true
- [ ] Saldo suficiente na carteira
- [ ] Todas as variáveis configuradas
- [ ] Telegram funcionando
- [ ] Health check OK
- [ ] Comando /saldo funciona
- [ ] Logs sem erros
- [ ] Modo turbo testado
- [ ] Pause/resume testados
- [ ] Auto-start configurado

---

## 🎉 Pronto!

Seu Sniper Bot está configurado e rodando no Render! 🚀

**Próximos passos:**
1. Monitore os primeiros dias de perto
2. Ajuste configurações baseado nos resultados
3. Considere ativar modo turbo quando ganhar experiência
4. Retire lucros regularmente
5. Divirta-se! 💰
