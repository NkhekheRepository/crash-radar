# Crash Radar v1.0

**Automated cryptocurrency crash detection system with real-time Telegram alerts.**

Crash Radar monitors multiple market indicators across 6 risk layers to detect potential crypto market crashes before they happen. When risk levels reach critical thresholds, it sends instant alerts via Telegram.

## What It Does

Crash Radar continuously monitors:
- **Price Action** (RSI indicator)
- **Leverage Levels** (Open Interest, Funding Rates)
- **Market Sentiment** (Fear & Greed Index)
- **Market Cycle** (Accumulation/Distribution phases)
- **Regulatory Environment** (Threat detection)
- **Macro Indicators** (CPI, DXY trends)

Each layer contributes 0-1 points to a total **Crash Radar Score (0-6)**:
- **0-2**: BUY signal
- **3-4**: WATCH (caution)
- **5-6**: RISK OFF (alert triggered!)

## How It Works

```
┌─────────────────────────────────────────────────────────────┐
│                    Data Sources                             │
│  CoinGecko │ Coinglass │ Alternative.me │ FRED │ News    │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│                   Airbyte (ETL)                            │
│         Collects & loads data into PostgreSQL              │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│                Signal Engine (6 Layers)                    │
│  Price │ Leverage │ Sentiment │ Cycle │ Regulation │ Macro │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│                   Crash Radar Score                        │
│         0-6 → BUY / WATCH / RISK OFF                     │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│              Telegram Alert (Score ≥ 5)                    │
│         Instant notification with detailed metrics          │
└─────────────────────────────────────────────────────────────┘
```

## Scoring Rules

| Layer | Condition | Points |
|-------|-----------|--------|
| Price | RSI < 30 (oversold) | +1 |
| Leverage | OI drop >10% OR negative funding | +1 |
| Sentiment | Fear Index < 25 | +1 |
| Cycle | Phase = Accumulation/Run-Up | +1 |
| Regulation | No regulatory threat | +1 |
| Macro | CPI or DXY decreasing | +1 |

## Quick Start

```bash
# 1. Clone the repository
git clone https://github.com/NkhekheRepository/crash-radar
cd crash-radar

# 2. Copy environment template
cp .env.template .env

# 3. Edit .env with your credentials
nano .env

# 4. Start Docker services
docker-compose up -d

# 5. Install Python dependencies
pip install -r requirements.txt

# 6. Run pipeline once
python main.py --once
```

## Configuration

### Environment Variables (.env)

```bash
# Database
POSTGRES_PASSWORD=your_secure_password

# Telegram (get from @BotFather)
TELEGRAM_BOT_TOKEN=your_bot_token
TELEGRAM_CHAT_ID=your_chat_id

# Run times (24-hour format)
RUN_TIMES=06:00,14:00,22:00
```

### Signal Thresholds (settings.json)

| Parameter | Default | Description |
|-----------|---------|-------------|
| rsi_oversold | 30 | RSI below this = +1 point |
| oi_drop_critical | 10 | OI drop % below this = +1 |
| fear_greed_critical | 25 | Fear index below this = +1 |
| alert_score | 5 | Score >= this triggers alert |

## Running

```bash
# Run once (for testing)
python main.py --once

# Run scheduled (3× daily - default)
python main.py

# Validate Airbyte sync only
python main.py --validate-only
```

## Testing

```bash
# Run all tests
pytest tests/

# Run specific module tests
pytest tests/test_signal_engine.py
pytest tests/test_alerts.py
```

## Project Structure

```
crash_radar/
├── docker-compose.yml      # Docker services
├── settings.json           # Signal thresholds
├── main.py                 # Pipeline orchestrator
├── src/
│   ├── utils/              # Config, DB, Logger
│   ├── data_ingestion/     # Airbyte sync validation
│   ├── normalization/      # Raw → normalized data
│   ├── signal_engine/      # Crash Radar scoring
│   └── alerts/             # Telegram notifications
├── tests/                  # Unit & integration tests
└── init-scripts/           # Database schema
```

## Data Sources

| Source | Data | API |
|--------|------|-----|
| CoinGecko | Price, RSI, Market Cap | ✓ |
| Coinglass | Open Interest, Funding Rate | ✓ |
| Alternative.me | Fear & Greed Index | ✓ |
| FRED | CPI, DXY, Interest Rates | ✓ |
| Google News | Regulatory news | ✓ |

## Telegram Alert Example

```
🚨 CRASH RADAR ALERT 🚨

🔴 RISK OFF - Score: 5/6

📊 Metrics:
• BTC Price: $45,000.00
• RSI: 28.50
• OI Change: -12.50%
• Fear Index: 22

📈 Context:
• Cycle Phase: Accumulation
• Macro: neutral
• Regulation: none
```

## Superset Dashboards

Connect Superset (port 8088) to PostgreSQL for:
- Historical signal charts
- RSI/OI trends over time
- Alert frequency analytics

## Requirements

- Python 3.12+
- PostgreSQL 15+
- Docker & Docker Compose
- Telegram Bot (via @BotFather)

## License

MIT

## Author

Nkhekhe Innovations
