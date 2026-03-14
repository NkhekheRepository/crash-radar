# Crash Radar v1.0

Crypto crash detection system with Telegram alerts.

## Quick Start

```bash
# 1. Copy environment template
cp .env.template .env

# 2. Edit .env with your credentials
nano .env

# 3. Start Docker services
docker-compose up -d

# 4. Install Python dependencies
pip install -r requirements.txt

# 5. Run pipeline once
python main.py --once
```

## Configuration

Edit `settings.json` to adjust thresholds:

| Parameter | Default | Description |
|-----------|---------|-------------|
| rsi_oversold | 30 | RSI below this = +1 point |
| oi_drop_critical | 10 | OI drop % below this = +1 |
| fear_greed_critical | 25 | Fear index below this = +1 |
| alert_score | 5 | Score >= this triggers alert |

## Running

```bash
# Run once
python main.py --once

# Run scheduled (3× daily)
python main.py

# Validate Airbyte sync only
python main.py --validate-only
```

## Testing

```bash
pytest tests/
```

## Architecture

```
Docker: PostgreSQL + Airbyte + Superset
    ↓
Python: normalize → score → alert
    ↓
Telegram: Risk Off alerts
```

## License

MIT
