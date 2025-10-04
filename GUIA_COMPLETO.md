# 🎯 GUIA COMPLETO DO SNIPER BOT - Português BR

## 📖 Índice

1. [Visão Geral](#visão-geral)
2. [Funcionalidades](#funcionalidades)
3. [Instalação e Configuração](#instalação-e-configuração)
4. [Modo Turbo](#modo-turbo)
5. [Comandos do Telegram](#comandos-do-telegram)
6. [Estratégias de Trading](#estratégias-de-trading)
7. [Proteções e Segurança](#proteções-e-segurança)
8. [FAQ](#faq)
9. [Troubleshooting](#troubleshooting)

---

## 🎯 Visão Geral

O Sniper Bot é um bot avançado de trading automático para a rede Base, especializado em:

- 🎯 **Sniper de Memecoins**: Detecta e compra novos tokens instantaneamente
- 📈 **Trading de Altcoins**: Trading automatizado de tokens DeFi consolidados
- 🚀 **Modo Turbo**: Trading agressivo com maiores recompensas
- 🛡️ **Proteções Avançadas**: Anti-honeypot, anti-rugpull, verificação de contratos
- 🤖 **100% Automático**: Compra e vende automaticamente 24/7

---

## 🚀 Funcionalidades

### Estratégias de Trading

#### 1. Sniper para Memecoins
- ✅ Detecção automática de novos pares em DEXs
- ✅ Monitoramento de mempool para entradas ultra-rápidas
- ✅ Análise de liquidez mínima (0.05 ETH)
- ✅ Verificação de número de holders (min 50)
- ✅ Take profit automático em 2x de lucro
- ✅ Stop loss em 30% de perda

#### 2. Trading de Altcoins
- ✅ Análise fundamentalista de tokens DeFi
- ✅ Swing trading com suportes e resistências
- ✅ Rebalanceamento automático de portfólio
- ✅ Reinvestimento de 50% dos lucros
- ✅ Diversificação automática

#### 3. Modo Turbo 🚀
- ⚡ Monitoramento a cada 50ms (vs 200ms normal)
- 💰 Maior investimento por trade
- 📈 Take profit mais agressivo (50% vs 30%)
- 🎯 Até 3 posições simultâneas
- 🔥 Ideal para mercados voláteis

### Proteções de Segurança

- 🛡️ **Anti-Honeypot**: Detecta tokens que não podem ser vendidos
- 🛡️ **Anti-Rugpull**: Verifica se o criador pode drenar liquidez
- 🛡️ **Verificação de Contratos**: Analisa código malicioso
- 🛡️ **Análise de Liquidez**: Evita tokens com baixa liquidez
- 🛡️ **Fallback entre DEXs**: Usa múltiplas DEXs automaticamente

### Interface Telegram

- 📱 **Botões Interativos**: Controle completo via interface gráfica
- 💬 **Comandos Completos**: Mais de 15 comandos disponíveis
- 🔔 **Alertas em Tempo Real**: Notificações instantâneas de trades
- 📊 **Análise de Tokens**: Verificação de segurança instantânea
- ⏸️ **Pause/Resume**: Pausa temporária sem perder posições
- 🚨 **Parada de Emergência**: Fecha tudo imediatamente

---

## 🛠️ Instalação e Configuração

### Passo 1: Clone o Repositório

```bash
git clone https://github.com/Luisqbd/sniperbot.git
cd sniperbot
```

### Passo 2: Instale as Dependências

```bash
pip install -r requirements.txt
```

### Passo 3: Configure as Variáveis de Ambiente

```bash
cp .env.example .env
nano .env  # ou use seu editor preferido
```

### Configuração Mínima Necessária

```env
# ===== OBRIGATÓRIAS =====
PRIVATE_KEY=sua_chave_privada_aqui
WALLET_ADDRESS=seu_endereco_carteira
RPC_URL=https://mainnet.base.org
TELEGRAM_TOKEN=seu_token_bot_telegram
TELEGRAM_CHAT_ID=seu_chat_id

# ===== CONFIGURAÇÕES BÁSICAS =====
DRY_RUN=false
AUTO_START_SNIPER=true
TURBO_MODE=false
```

### Configuração Otimizada (Para Saldo de 0.001990 WETH)

```env
# ===== TRADING =====
TRADE_SIZE_ETH=0.0008          # 40% do saldo por trade
TAKE_PROFIT_PCT=0.3            # Take profit em 30%
STOP_LOSS_PCT=0.12             # Stop loss em 12%
MAX_POSITIONS=2                # Máximo 2 posições simultâneas
SLIPPAGE_BPS=500               # 5% de slippage

# ===== MEMECOINS =====
MEMECOIN_MIN_LIQUIDITY=0.05    # Mínimo 0.05 ETH
MEMECOIN_MIN_HOLDERS=50        # Mínimo 50 holders
MEMECOIN_MAX_INVESTMENT=0.0008 # Máximo por memecoin
MEMECOIN_TARGET_PROFIT=2.0     # Target 2x

# ===== ALTCOINS =====
ALTCOIN_MIN_MARKET_CAP=100000
ALTCOIN_MAX_MARKET_CAP=10000000
ALTCOIN_MIN_VOLUME_24H=50000

# ===== TIMING =====
DISCOVERY_INTERVAL=1
MEMPOOL_MONITOR_INTERVAL=0.2
EXIT_POLL_INTERVAL=3
```

### Passo 4: Execute o Bot

```bash
python main_complete.py
```

Ou com Docker:

```bash
docker-compose up -d
```

---

## 🚀 Modo Turbo

### O Que é o Modo Turbo?

O Modo Turbo é um modo de operação agressivo que aumenta a velocidade e o potencial de lucro, mas também o risco.

### Diferenças: Normal vs Turbo

| Parâmetro | Modo Normal | Modo Turbo |
|-----------|-------------|------------|
| Monitoramento | 200ms | 50ms |
| Trade Size | 0.0008 ETH | 0.0012 ETH |
| Take Profit | 30% | 50% |
| Stop Loss | 12% | 8% |
| Max Posições | 2 | 3 |
| Risco | Baixo | Médio/Alto |
| Recompensa | Moderada | Alta |

### Como Ativar/Desativar

#### Via Telegram
1. Envie `/start` para abrir o menu
2. Clique no botão "🚀 TURBO" ou "🐢 Normal"
3. O bot alterna automaticamente entre os modos

#### Via .env
```env
TURBO_MODE=true   # Ativa modo turbo
TURBO_MODE=false  # Modo normal
```

### Quando Usar Modo Turbo?

✅ **Use Turbo quando:**
- O mercado está muito volátil
- Há muitas oportunidades surgindo
- Você quer maximizar lucros rapidamente
- Você aceita mais risco

❌ **Evite Turbo quando:**
- O mercado está calmo
- Você quer preservar capital
- É sua primeira vez usando o bot
- Você tem pouco saldo disponível

---

## 📱 Comandos do Telegram

### Comandos Principais

#### `/start`
Inicia o bot e mostra o menu principal com todos os botões interativos.

#### `/help`
Mostra a lista completa de comandos disponíveis.

#### `/status`
Mostra o status atual do bot incluindo:
- Estado (ativo/inativo)
- Modo (turbo/normal)
- Posições ativas
- Taxa de acerto
- Lucro total

#### `/balance` ou `/saldo`
Mostra o saldo da carteira:
- ETH disponível
- WETH disponível
- Valor total em USD

#### `/positions` ou `/posicoes`
Lista todas as posições ativas com:
- Token
- Preço de entrada
- Preço atual
- PnL (lucro/prejuízo)
- Tempo da posição

#### `/stats`
Mostra estatísticas detalhadas:
- Total de trades
- Trades vencedores/perdedores
- Taxa de acerto
- Lucro total
- Melhor e pior trade
- ROI médio

### Comandos de Controle

#### `/snipe`
Inicia o sniper automático. O bot começará a:
- Monitorar mempool
- Detectar novos tokens
- Executar compras automaticamente
- Gerenciar posições

#### `/stop`
Para o sniper. As posições ativas continuam sendo monitoradas.

#### `/pause`
Pausa temporariamente o bot:
- Não abre novas posições
- Mantém posições existentes
- Continue monitorando para stop loss/take profit

#### `/resume`
Retoma a operação normal após pausa.

### Comandos de Análise

#### `/analyze <endereço_token>`
Analisa um token específico mostrando:
- Nome e símbolo
- Preço atual
- Supply e holders
- Score de segurança
- Análise de honeypot
- Análise de rugpull
- Avisos e alertas

Exemplo:
```
/analyze 0x1234567890abcdef...
```

#### `/check <endereço_token>`
Verifica apenas a segurança do token:
- Status (seguro/arriscado)
- Score de risco
- Honeypot check
- Rugpull check

#### `/price <endereço_token>`
Consulta apenas o preço do token em múltiplas DEXs.

### Comandos de Configuração

#### `/config`
Mostra todas as configurações atuais:
- Trade size
- Take profit
- Stop loss
- Max posições
- Modo turbo

#### `/set_trade_size <valor>`
Altera o tamanho do trade em ETH.

Exemplo:
```
/set_trade_size 0.001
```

#### `/set_stop_loss <percentual>`
Altera o stop loss em porcentagem.

Exemplo:
```
/set_stop_loss 15
```
(Para 15% de stop loss)

#### `/set_take_profit <nível1> <nível2> <nível3> <nível4>`
Altera os níveis de take profit.

Exemplo:
```
/set_take_profit 25 50 100 200
```
(Para 25%, 50%, 100%, 200%)

#### `/set_max_positions <número>`
Altera o máximo de posições simultâneas.

Exemplo:
```
/set_max_positions 3
```

### Botões Interativos

#### Menu Principal
- **🚀 Iniciar Sniper** - Liga o sniper
- **🛑 Parar Sniper** - Desliga o sniper
- **📊 Status** - Status detalhado
- **💰 Saldo** - Saldo da carteira
- **🎯 Posições** - Lista posições ativas
- **📈 Estatísticas** - Estatísticas de performance
- **⚙️ Configurações** - Menu de configurações
- **🚀 Modo Turbo** / **🐢 Normal** - Toggle turbo
- **🏓 Ping** - Testa se bot está respondendo
- **🚨 PARADA DE EMERGÊNCIA** - Para tudo

#### Menu de Configurações
- **💰 Trade Size** - Altera tamanho do trade
- **🛡️ Stop Loss** - Altera stop loss
- **📈 Take Profit** - Altera take profit
- **🎯 Max Posições** - Altera máximo de posições
- **🔙 Voltar** - Volta ao menu principal

---

## 📈 Estratégias de Trading

### Para Memecoins

#### Critérios de Entrada
1. **Liquidez**: Mínimo 0.05 ETH
2. **Holders**: Mínimo 50 holders
3. **Idade**: Máximo 24 horas
4. **Segurança**: Passou em todos os checks de segurança
5. **Hype**: Análise de social media (opcional)

#### Critérios de Saída
1. **Take Profit**: 2x de lucro (200%)
2. **Stop Loss**: 30% de perda
3. **Timeout**: 24h se lucro < 50%
4. **Honeypot Detectado**: Saída imediata

#### Estratégia
```
Entrada → 0.0008 ETH
Target: 2x (0.0016 ETH)
Stop Loss: -30% (0.00056 ETH)
```

### Para Altcoins

#### Critérios de Entrada
1. **Market Cap**: Entre $100k e $10M
2. **Volume 24h**: Mínimo $50k
3. **Liquidez**: Estável e crescente
4. **Fundamentals**: Projeto verificado
5. **Momento**: Análise técnica positiva

#### Critérios de Saída
1. **Take Profit Parcial**:
   - 25% em +25%
   - 25% em +50%
   - 25% em +100%
   - 25% em +200%
2. **Stop Loss**: 15% de perda
3. **Trailing Stop**: 5% do pico

#### Estratégia
```
Entrada → 0.0008 ETH
Saídas Parciais:
  25% em +25% → 0.00025 ETH
  25% em +50% → 0.0004 ETH
  25% em +100% → 0.0006 ETH
  25% em +200% → 0.001 ETH
```

### Rebalanceamento de Portfólio

O bot rebalanceia automaticamente:

1. **Diariamente**: Ajusta alocação entre posições
2. **Após Lucro**: Reinveste 50% em novas oportunidades
3. **Após Perda**: Reduz exposição temporariamente
4. **Max Posições**: Mantém no máximo 2-3 posições

---

## 🛡️ Proteções e Segurança

### Verificações Automáticas

#### 1. Honeypot Check
- ✅ Tenta simular venda do token
- ✅ Verifica se pode realmente vender
- ✅ Consulta múltiplas APIs de honeypot
- ❌ Bloqueia tokens que não podem ser vendidos

#### 2. Rugpull Check
- ✅ Verifica quem pode pausar o contrato
- ✅ Analisa balanço do owner (max 30%)
- ✅ Verifica se liquidez está travada
- ❌ Bloqueia tokens com alto risco de rugpull

#### 3. Contract Verification
- ✅ Verifica se o contrato está verificado
- ✅ Analisa o código fonte
- ✅ Detecta funções maliciosas
- ❌ Bloqueia contratos suspeitos

#### 4. Liquidity Check
- ✅ Verifica liquidez mínima
- ✅ Analisa estabilidade da liquidez
- ✅ Detecta remoção súbita de liquidez
- ❌ Sai imediatamente se liquidez cair

### Proteções de Trading

#### Stop Loss Obrigatório
Todas as posições têm stop loss automático:
- Modo Normal: 12%
- Modo Turbo: 8%
- Não pode ser desabilitado

#### Trailing Stop Loss
Quando a posição está no lucro:
- Ajusta stop loss automaticamente
- Protege 95% do lucro alcançado
- Permite "respirar" 5%

#### Limite de Posições
- Máximo de posições simultâneas
- Normal: 2 posições
- Turbo: 3 posições
- Previne over-exposure

#### Ajuste Automático de Gas
- Monitora congestionamento da rede
- Ajusta gas price automaticamente
- Limite máximo: 50 gwei
- Previne overpaying

#### Fallback entre DEXs
- Tenta múltiplas DEXs automaticamente
- Uniswap V3
- BaseSwap
- Camelot
- Escolhe o melhor preço

---

## ❓ FAQ

### 1. O bot funciona 24/7?

Sim! Com `AUTO_START_SNIPER=true`, o bot inicia automaticamente e opera 24/7 sem intervenção.

### 2. Quanto preciso investir?

O mínimo recomendado é 0.002 ETH (ou WETH). Para o saldo de 0.001990 WETH, as configurações padrão são:
- Trade size: 0.0008 ETH por trade
- Máximo 2 posições: 0.0016 ETH total
- Reserva para gas: 0.0003 ETH

### 3. Posso alterar as configurações em tempo real?

Sim! Use os comandos `/set_*` ou os botões de configuração no Telegram. As mudanças são aplicadas imediatamente.

### 4. O que acontece se o bot cair?

Se o bot reiniciar:
- Posições ativas são mantidas no blockchain
- O bot retoma monitoramento automaticamente
- Take profit e stop loss continuam ativos

### 5. Como sei se um trade foi lucrativo?

Você receberá notificações no Telegram:
- ✅ "Posição aberta" ao entrar
- 📈 "Take profit parcial" a cada saída parcial
- 💰 "Posição fechada com lucro" ao fechar
- 📊 Relatório com % de lucro

### 6. Posso usar múltiplas carteiras?

Não nativamente, mas você pode rodar múltiplas instâncias do bot com diferentes configurações.

### 7. O bot cobra taxas?

Não! O bot é open-source e gratuito. Você só paga:
- Gas fees (Base Network)
- Slippage nas trades
- Taxas das DEXs (0.3%)

### 8. É seguro deixar minha chave privada no .env?

⚠️ **IMPORTANTE**: 
- Nunca compartilhe seu arquivo .env
- Nunca commit .env no git
- Use uma carteira dedicada para o bot
- Não coloque todo seu capital nela

### 9. Posso testar sem arriscar dinheiro real?

Sim! Use `DRY_RUN=true` no .env. O bot:
- Simula todas as operações
- Não gasta ETH/WETH real
- Logs mostram o que seria feito
- Perfeito para testes

### 10. Qual a taxa de acerto esperada?

Depende do mercado, mas tipicamente:
- Memecoins: 40-50% (mas lucros são grandes)
- Altcoins: 60-70% (lucros menores)
- Com modo turbo: Mais volátil

---

## 🔧 Troubleshooting

### Problema: Bot não inicia

**Solução:**
```bash
# Verifique se todas as dependências estão instaladas
pip install -r requirements.txt

# Verifique se o .env está configurado
cat .env | grep -E "PRIVATE_KEY|TELEGRAM_TOKEN"

# Verifique os logs
tail -f sniper_bot.log
```

### Problema: Telegram não responde

**Solução:**
1. Verifique se o token está correto
2. Verifique se adicionou o bot no chat
3. Use `/start` para acordar o bot
4. Verifique logs: `grep "Telegram" sniper_bot.log`

### Problema: Nenhum trade sendo executado

**Possíveis causas:**
1. `DRY_RUN=true` (só simula)
2. Filtros muito restritivos
3. Mercado sem oportunidades
4. Saldo insuficiente

**Solução:**
```bash
# Verifique o status
/status no Telegram

# Verifique saldo
/saldo no Telegram

# Ajuste os filtros no .env
MEMECOIN_MIN_LIQUIDITY=0.01  # Menos restritivo
MEMECOIN_MIN_HOLDERS=20      # Menos restritivo
```

### Problema: Muitos trades perdedores

**Solução:**
1. Desative modo turbo temporariamente
2. Aumente filtros de segurança
3. Reduza trade size
4. Aumente stop loss para 15%

### Problema: Bot consumindo muito gas

**Solução:**
```env
# Adicione limite de gas no .env
MAX_GAS_PRICE_GWEI=30  # Não paga mais que 30 gwei
```

### Problema: Erro "Insufficient funds"

**Solução:**
1. Verifique saldo: `/saldo`
2. Converta ETH para WETH se necessário
3. Reduza `TRADE_SIZE_ETH`
4. Reduza `MAX_POSITIONS`

### Logs Importantes

```bash
# Ver logs em tempo real
tail -f sniper_bot.log

# Buscar erros
grep "ERROR" sniper_bot.log

# Buscar trades
grep "Trade" sniper_bot.log

# Buscar lucros
grep "Profit" sniper_bot.log
```

---

## 📞 Suporte

- **GitHub Issues**: [github.com/Luisqbd/sniperbot/issues](https://github.com/Luisqbd/sniperbot/issues)
- **Telegram Support**: @SniperBotSupport
- **Documentação**: [README.md](README.md)

---

## ⚖️ Disclaimer

⚠️ **AVISO IMPORTANTE:**

- Trading de criptomoedas envolve riscos significativos
- Você pode perder todo o capital investido
- Este bot não garante lucros
- Use apenas capital que você pode perder
- Faça sua própria pesquisa (DYOR)
- Não somos consultores financeiros
- Use por sua conta e risco

---

## 🎉 Conclusão

Parabéns por configurar o Sniper Bot! 🚀

**Próximos Passos:**

1. ✅ Configure o .env com seus valores
2. ✅ Teste com `DRY_RUN=true` primeiro
3. ✅ Comece com modo normal (sem turbo)
4. ✅ Use trade size pequeno inicialmente
5. ✅ Monitore via Telegram constantemente
6. ✅ Ajuste configurações baseado nos resultados

**Dicas Finais:**

- 📊 Acompanhe as estatísticas regularmente
- 🛡️ Nunca desabilite as proteções
- 💰 Retire lucros periodicamente
- 🎯 Seja paciente e disciplinado
- 📈 Aprenda com cada trade

**Boa sorte e bons trades! 🚀💰**
