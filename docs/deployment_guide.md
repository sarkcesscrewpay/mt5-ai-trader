# Deployment Guide: AI-Powered MT5 Trading System

## Overview

This guide covers deployment options for the AI-powered trading system including VPS, Docker, and cloud deployment.

## ⚠️ Important Warnings

**BEFORE DEPLOYING:**
1. Always test in paper trading mode first
2. Start with minimal capital
3. Monitor system behavior closely
4. This system does NOT guarantee profits
5. Trading financial markets carries inherent risks

---

## Folder Structure

```
trading_system/
├── src/
│   └── mcp_mt5/
│       └── trading/
│           ├── data_collection.py    # Data fetching
│           ├── feature_engineering.py # Technical indicators
│           ├── ai_model.py           # ML models
│           ├── strategy.py           # Trading logic
│           ├── risk_management.py    # Risk controls
│           ├── execution.py          # MT5 execution
│           ├── logging.py            # Performance tracking
│           ├── backtesting.py        # Historical testing
│           ├── safety.py             # Safety features
│           └── starter_example.py    # Main entry point
├── models/                           # Trained ML models
├── logs/                             # Trading logs
├── config/
│   └── trading_config.yaml          # Configuration
├── requirements.txt                  # Python dependencies
└── docker-compose.yml               # Docker configuration
```

---

## 1. Requirements

### Python Dependencies

```txt
# requirements.txt
MetaTrader5>=5.0.45
numpy>=1.24.0
pandas>=2.0.0
scikit-learn>=1.3.0
xgboost>=2.0.0
lightgbm>=4.0.0
pyyaml>=6.0
python-dotenv>=1.0.0
```

### Install Dependencies

```bash
pip install -r requirements.txt
```

---

## 2. Local Deployment

### Quick Start

```bash
# 1. Clone the repository
git clone <repository-url>
cd mcp-metatrader5-server-main

# 2. Install dependencies
pip install -r requirements.txt

# 3. Configure environment
cp .env.example .env
# Edit .env with your MT5 credentials

# 4. Run starter example
python src/mcp_mt5/trading/starter_example.py
```

### Configuration

Create `config/trading_config.yaml`:

```yaml
system:
  mode: paper_trading  # or live
  symbols:
    - EURUSD
    - GBPUSD
    - USDJPY
  max_concurrent_trades: 5

data:
  timeframe: H1
  lookback_periods: 1000
  update_interval: 300  # seconds

ai_model:
  model_type: xgboost
  min_confidence: 0.65
  retrain_frequency: weekly

risk:
  max_risk_per_trade: 0.02  # 2%
  max_daily_drawdown: 0.05   # 5%
  max_open_positions: 5
  atr_multiplier_sl: 2.0
  atr_multiplier_tp: 4.0

execution:
  slippage_protection: true
  max_slippage_pips: 2

safety:
  kill_switch_enabled: true
  capital_protection_mode: true
```

---

## 3. Docker Deployment

### Dockerfile

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY src/ ./src/
COPY config/ ./config/
COPY models/ ./models/
COPY logs/ ./logs/

# Create non-root user
RUN useradd -m -u 1000 trader
USER trader

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV MT5_LOGIN=${MT5_LOGIN}
ENV MT5_SERVER=${MT5_SERVER}
ENV MT5_PASSWORD=${MT5_PASSWORD}

# Run application
CMD ["python", "src/mcp_mt5/trading/starter_example.py"]
```

### docker-compose.yml

```yaml
version: '3.8'

services:
  trading-bot:
    build: .
    container_name: mt5-trading-bot
    restart: unless-stopped
    environment:
      - MT5_LOGIN=${MT5_LOGIN}
      - MT5_SERVER=${MT5_SERVER}
      - MT5_PASSWORD=${MT5_PASSWORD}
      - TRADING_MODE=${TRADING_MODE:-paper}
    volumes:
      - ./logs:/app/logs
      - ./models:/app/models
      - ./config:/app/config
    network_mode: host
    depends_on:
      - mt5-terminal

  # Optional: MT5 Terminal (if running on same host)
  # mt5-terminal:
  #   image: metatrader5-terminal:latest
  #   container_name: mt5-terminal
  #   restart: unless-stopped
```

### Build and Run

```bash
# Build container
docker build -t mt5-trading-bot .

# Run with docker-compose
docker-compose up -d

# View logs
docker-compose logs -f trading-bot

# Stop
docker-compose down
```

---

## 4. VPS Deployment

### Recommended VPS Specs

| Component | Minimum | Recommended |
|-----------|---------|-------------|
| CPU | 2 cores | 4 cores |
| RAM | 4 GB | 8 GB |
| Storage | 50 GB SSD | 100 GB SSD |
| OS | Ubuntu 22.04 | Ubuntu 22.04 |

### VPS Setup Steps

#### 1. Create VPS (e.g., DigitalOcean, AWS, Hetzner)

```bash
# Example: Hetzner Cloud
hc create mt5-trading --image ubuntu-22.04 --type cx42
```

#### 2. Connect to VPS

```bash
ssh root@<vps-ip>
```

#### 3. Install Dependencies

```bash
# Update system
apt update && apt upgrade -y

# Install Python
apt install -y python3.11 python3-pip python3-venv


curl -fsSL https# Install Docker://get.docker.com | sh
systemctl enable docker
```

#### 4. Deploy Application

```bash
# Clone repository
git clone <repository-url>
cd mcp-metatrader5-server-main

# Setup virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run with systemd
cp trading.service /etc/systemd/system/
systemctl daemon-reload
systemctl enable trading
systemctl start trading
```

#### 5. Systemd Service

Create `/etc/systemd/system/trading.service`:

```ini
[Unit]
Description=MT5 Trading Bot
After=network.target

[Service]
Type=simple
User=trader
WorkingDirectory=/home/trader/trading
Environment=PATH=/home/trader/venv/bin
ExecStart=/home/trader/venv/bin/python src/mcp_mt5/trading/starter_example.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

---

## 5. Cloud Deployment (AWS/GCP/Azure)

### AWS ECS Deployment

```yaml
# ecs-task-definition.json
{
  "family": "mt5-trading",
  "networkMode": "host",
  "containerDefinitions": [
    {
      "name": "trading-bot",
      "image": "<your-registry>/mt5-trading:latest",
      "essential": true,
      "environment": [
        {"name": "MT5_LOGIN", "value": "${MT5_LOGIN}"},
        {"name": "MT5_SERVER", "value": "${MT5_SERVER}"}
      ],
      "logConfiguration": {
        "logDriver": "awslogs",
        "options": {
          "awslogs-group": "/ecs/mt5-trading",
          "awslogs-region": "us-east-1"
        }
      }
    }
  ]
}
```

### Important Cloud Considerations

1. **MT5 Must Run Locally**: MT5 terminal cannot run in cloud containers. It must run on a local Windows machine or VPS with GUI access.

2. **Architecture**: The bot connects to MT5 via network, so MT5 terminal must be accessible.

---

## 6. Production Checklist

### Before Going Live

- [ ] Test extensively in paper trading mode
- [ ] Verify all safety features are working
- [ ] Set up monitoring and alerts
- [ ] Configure log rotation
- [ ] Test kill switch functionality
- [ ] Verify backup and recovery procedures

### Monitoring Setup

```python
# Add to your monitoring
import logging.handlers

# Email alerts
handler = logging.handlers.SMTPHandler(
    mailhost=("smtp.gmail.com", 587),
    fromaddr="trading-bot@example.com",
    toaddrs=["alerts@example.com"],
    subject="Trading Bot Alert",
    credentials=("email", "password"),
    secure=None
)

logger.addHandler(handler)
```

### Log Rotation

```bash
# /etc/logrotate.d/trading
/home/trader/logs/*.log {
    daily
    rotate 30
    compress
    delaycompress
    missingok
    notifempty
    create 0640 trader trader
}
```

---

## 7. Risk Disclaimers

**IMPORTANT:**

1. **No Guarantees**: This system does NOT guarantee profits. Past performance does not indicate future results.

2. **Capital at Risk**: You may lose your entire investment. Only trade with money you can afford to lose.

3. **Backtesting Limitations**: Backtested results often overestimate real-world performance due to overfitting and ideal assumptions.

4. **Live Trading Risks**: Always start with paper trading. Monitor system behavior closely when going live.

5. **No Financial Advice**: This is software for educational purposes. Not financial advice.

---

## 8. Support and Maintenance

### Regular Maintenance

- Monitor disk space for logs
- Review and rotate models periodically
- Update dependencies for security
- Monitor system resources
- Check MT5 terminal updates

### Troubleshooting

```bash
# Check logs
tail -f logs/trading_*.log

# Check MT5 connection
python -c "import MetaTrader5 as mt5; mt5.initialize(); print(mt5.terminal_info())"

# Restart service
systemctl restart trading
```

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0.0 | 2024-01 | Initial release |

---

**End of Deployment Guide**
