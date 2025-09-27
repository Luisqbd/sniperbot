# 🎯 Sniper Bot - Base Network

Bot avançado de trading automatizado para criptomoedas na rede Base, especializado em detecção e trading de memecoins e altcoins com estratégias inteligentes e proteções de segurança.

## 🚀 Funcionalidades Principais

### 📈 Estratégias de Trading
- **Sniper para Memecoins**: Detecção automática de tokens recém-lançados com análise de liquidez, holders e hype social
- **Swing Trading para Altcoins**: Trading automatizado de tokens DeFi consolidados com rebalanceamento de portfólio
- **Take Profit Multi-nível**: Saídas parciais em 25%, 50%, 100% e 200% de lucro
- **Trailing Stop Loss**: Proteção dinâmica contra perdas com ajuste automático

### 🔒 Proteções e Segurança
- **Verificação de Honeypots**: Detecção automática de tokens maliciosos
- **Análise de Rugpull**: Verificação de riscos de abandono do projeto
- **Fallback entre DEXs**: Agregador inteligente (BaseSwap, Uniswap v3, Camelot)
- **Ajuste Automático de Gas**: Otimização baseada no congestionamento da rede

### 📱 Interface Telegram
- **Comandos Completos**: `/start`, `/status`, `/saldo`, `/posicoes`, `/config`, `/analisar`
- **Botões Interativos**: Controle total via interface gráfica
- **Alertas em Tempo Real**: Notificações de trades, lucros e oportunidades
- **Análise de Tokens**: Verificação instantânea de segurança e potencial

### 🏗️ Infraestrutura
- **Deploy Automático**: Dockerfile e render.yaml configurados
- **CI/CD**: GitHub Actions com testes automatizados
- **Monitoramento**: Métricas Prometheus e health checks
- **Logs Estruturados**: Sistema completo de logging e debugging

## ⚙️ Configuração Otimizada

### Parâmetros de Trading (Otimizados para saldo de 0.001990 WETH)
```env
TRADE_SIZE_ETH=0.0008          # Tamanho por trade (40% do saldo)
TAKE_PROFIT_PCT=0.25           # Take profit em 25%
STOP_LOSS_PCT=0.15             # Stop loss em 15%
SLIPPAGE_BPS=500               # Slippage de 5%
MAX_POSITIONS=2                # Máximo 2 posições simultâneas
```

### Detecção de Memecoins
```env
MEMECOIN_MIN_LIQUIDITY=0.05    # Mínimo 0.05 ETH de liquidez
MEMECOIN_MIN_HOLDERS=50        # Mínimo 50 holders
MEMECOIN_MAX_AGE_HOURS=24      # Máximo 24h de idade
```

### Timing Otimizado
```env
DISCOVERY_INTERVAL=1           # Descoberta a cada 1s
MEMPOOL_MONITOR_INTERVAL=0.2   # Mempool a cada 200ms
EXIT_POLL_INTERVAL=3           # Verificação de saída a cada 3s
```

## 🛠️ Instalação e Configuração

### 1. Clone o Repositório
```bash
git clone https://github.com/Luisqbd/sniperbot.git
cd sniperbot
```

### 2. Configure as Variáveis de Ambiente
```bash
cp .env.example .env
# Edite o arquivo .env com suas credenciais
```

### Variáveis Obrigatórias:
```env
# Blockchain
PRIVATE_KEY=sua_chave_privada
WALLET_ADDRESS=seu_endereco_carteira
RPC_URL=https://mainnet.base.org

# Telegram
TELEGRAM_TOKEN=seu_token_bot_telegram
TELEGRAM_CHAT_ID=seu_chat_id

# Modo
DRY_RUN=false  # true para testes, false para trading real
```

### 3. Instale as Dependências
```bash
pip install -r requirements.txt
```

### 4. Execute os Testes
```bash
# Testes unitários
pytest tests/unit/ -v

# Testes de integração
pytest tests/integration/ -v

# Todos os testes com cobertura
pytest --cov=. --cov-report=html
```

### 5. Execute o Bot
```bash
# Modo de teste (DRY_RUN=true)
python main_updated.py --dry-run

# Modo de produção
python main_updated.py

# Com log detalhado
python main_updated.py --log-level DEBUG
```

## 📱 Comandos do Telegram

### Comandos Básicos
- `/start` - Inicia o bot e mostra menu principal
- `/status` - Status atual do bot e estatísticas
- `/saldo` - Saldo da carteira e posições ativas
- `/posicoes` - Lista detalhada de todas as posições

### Comandos Avançados
- `/analisar <endereço_token>` - Análise completa de segurança
- `/config` - Configurações atuais do bot
- `/stats` - Estatísticas detalhadas de performance
- `/emergencia` - Parada de emergência do bot

### Botões Interativos
- **🚀 Iniciar Sniper** - Ativa o modo de detecção
- **⏸️ Pausar Bot** - Pausa temporariamente
- **💰 Ver Saldo** - Saldo atual e histórico
- **📊 Estatísticas** - Performance detalhada
- **⚙️ Configurações** - Ajustar parâmetros

## 🔧 Deploy no Render

### 1. Conecte o Repositório
- Acesse [Render.com](https://render.com)
- Conecte seu repositório GitHub
- Selecione "Web Service"

### 2. Configure as Variáveis
No painel do Render, adicione todas as variáveis do `.env`:
```
PRIVATE_KEY=sua_chave_privada
TELEGRAM_TOKEN=seu_token_telegram
TELEGRAM_CHAT_ID=seu_chat_id
RPC_URL=https://mainnet.base.org
DRY_RUN=false
```

### 3. Deploy Automático
O deploy será automático via GitHub Actions sempre que houver push na branch `main`.

## 📊 Monitoramento e Métricas

### Health Checks
- `GET /health` - Status básico do bot
- `GET /status` - Status detalhado dos componentes
- `GET /metrics` - Métricas de trading e sistema

### Métricas Prometheus
- Disponível na porta 8000
- Métricas de performance, trades e sistema
- Dashboards Grafana compatíveis

### Logs
```bash
# Ver logs em tempo real
tail -f sniper_bot.log

# Filtrar por nível
grep "ERROR" sniper_bot.log
grep "TRADE" sniper_bot.log
```

## 🧪 Testes

### Estrutura de Testes
```
tests/
├── unit/                    # Testes unitários
│   ├── test_security_checker.py
│   ├── test_dex_aggregator.py
│   └── test_advanced_sniper_strategy.py
├── integration/             # Testes de integração
│   └── test_full_workflow.py
└── performance/             # Testes de performance
    └── test_benchmarks.py
```

### Executar Testes
```bash
# Todos os testes
pytest

# Com cobertura
pytest --cov=. --cov-report=html

# Apenas testes rápidos
pytest -m "not slow"

# Testes de performance
pytest tests/performance/ --benchmark-only
```

## 🔐 Segurança

### Proteções Implementadas
- ✅ Verificação de honeypots via múltiplas APIs
- ✅ Análise de padrões maliciosos em contratos
- ✅ Verificação de liquidez e estabilidade
- ✅ Limite de risco por posição
- ✅ Stop loss obrigatório em todas as posições

### Boas Práticas
- Nunca compartilhe sua `PRIVATE_KEY`
- Use `DRY_RUN=true` para testes
- Monitore regularmente os logs
- Configure alertas de segurança
- Mantenha o bot atualizado

## 📈 Estratégias de Lucro

### Para Memecoins
1. **Detecção Rápida**: Monitoramento de mempool em 200ms
2. **Entrada Agressiva**: Investimento de 0.0008 ETH por token
3. **Saída Inteligente**: Take profit em 2x ou stop loss em 30%
4. **Timeout**: Saída automática após 24h se < 50% lucro

### Para Altcoins
1. **Análise Fundamentalista**: Tokens DeFi com liquidez estável
2. **Swing Trading**: Entradas em suportes, saídas em resistências
3. **Rebalanceamento**: Reinvestimento de 50% dos lucros
4. **Diversificação**: Máximo 2 posições simultâneas

## 🚨 Troubleshooting

### Problemas Comuns

**Bot não inicia:**
```bash
# Verifique as variáveis de ambiente
python -c "from config import config; print(config)"

# Teste a conexão RPC
python -c "from web3 import Web3; w3 = Web3(Web3.HTTPProvider('https://mainnet.base.org')); print(w3.is_connected())"
```

**Telegram não funciona:**
```bash
# Teste o token
curl "https://api.telegram.org/bot<SEU_TOKEN>/getMe"

# Verifique o chat ID
curl "https://api.telegram.org/bot<SEU_TOKEN>/getUpdates"
```

**Trades não executam:**
- Verifique se `DRY_RUN=false`
- Confirme saldo suficiente na carteira
- Verifique se a rede Base está funcionando

### Logs de Debug
```bash
# Ativar logs detalhados
export LOG_LEVEL=DEBUG
python main_updated.py --log-level DEBUG
```

## 🤝 Contribuição

### Como Contribuir
1. Fork o repositório
2. Crie uma branch para sua feature
3. Implemente os testes
4. Faça commit das mudanças
5. Abra um Pull Request

### Padrões de Código
- Use Black para formatação
- Siga PEP 8
- Documente todas as funções
- Escreva testes para novas funcionalidades

## 📄 Licença

Este projeto está sob a licença MIT. Veja o arquivo [LICENSE](LICENSE) para detalhes.

## ⚠️ Disclaimer

Este bot é para fins educacionais e de pesquisa. Trading de criptomoedas envolve riscos significativos. Use por sua própria conta e risco. Os desenvolvedores não se responsabilizam por perdas financeiras.

## 📞 Suporte

- **Issues**: [GitHub Issues](https://github.com/Luisqbd/sniperbot/issues)
- **Discussões**: [GitHub Discussions](https://github.com/Luisqbd/sniperbot/discussions)
- **Telegram**: Entre em contato via bot configurado

---

**🎯 Happy Trading! 🚀**