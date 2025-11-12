# 🚀 CHA Intelligent Pipe Sizing System - Deployment Guide

## 🎯 **Overview**

This deployment guide provides comprehensive instructions for deploying the CHA (Centralized Heating Agent) Intelligent Pipe Sizing System in various environments, from development to production.

---

## 📋 **Prerequisites**

### **System Requirements**

- **Operating System**: Linux (Ubuntu 20.04+), macOS (10.15+), or Windows 10+
- **Python**: 3.8 or higher
- **Memory**: Minimum 8GB RAM (16GB+ recommended for large networks with hydraulic simulation)
- **Storage**: Minimum 5GB free space (increased for Pandapipes and thermal simulation data)
- **CPU**: Multi-core processor recommended (4+ cores for optimal performance)
- **Additional Requirements**: Pandapipes library for hydraulic simulation

### **Software Dependencies**

- Python 3.8+
- pip (Python package manager)
- Git (for version control)
- Virtual environment (recommended)
- Pandapipes (for hydraulic simulation)
- NumPy, Pandas, SciPy (for numerical computations)
- Matplotlib, Plotly (for visualization)
- PyYAML (for configuration management)
- jsonschema (for validation)

---

## ⚡ **Enhanced Hydraulic Simulation Deployment**

### **Pandapipes Installation**

The CHA system now requires Pandapipes for hydraulic simulation:

```bash
# Install Pandapipes with dependencies
pip install pandapipes

# Or install with specific version
pip install pandapipes==0.8.0

# Install additional dependencies for thermal simulation
pip install scipy matplotlib plotly

# Verify installation
python -c "import pandapipes; print(f'Pandapipes version: {pandapipes.__version__}')"
```

### **Enhanced Configuration Setup**

Create enhanced configuration for hydraulic simulation:

```yaml
# configs/cha.yml
# Basic settings
supply_temperature_c: 80
return_temperature_c: 50
supply_pressure_bar: 6.0
return_pressure_bar: 2.0

# Enhanced hydraulic simulation
thermal_simulation_enabled: true
ground_temperature_c: 10
pipe_sections: 8
heat_transfer_coefficient: 0.6
pump_efficiency: 0.75
water_density_kg_m3: 977.8

# Auto-resize settings
max_resize_iterations: 5
velocity_tolerance: 0.1
pressure_tolerance: 50

# Validation settings
validation_tolerance:
  kpi_accuracy: 0.01
  thermal_accuracy: 0.02
  schema_validation: true
```

### **Schema Files Setup**

Ensure schema validation files are properly deployed:

```bash
# Verify schema files exist
ls -la schemas/
# Should include:
# - cha_output.schema.json
# - kpi_summary.schema.json

# Validate schema files
python -c "
import json
with open('schemas/cha_output.schema.json', 'r') as f:
    schema = json.load(f)
    print('✅ CHA output schema is valid')
"
```

---

## 🔧 **Installation Methods**

### **Method 1: Direct Installation**

#### **Step 1: Clone Repository**

```bash
# Clone the repository
git clone <repository-url>
cd branitz_energy_decision_ai_street_final

# Verify repository structure
ls -la
```

#### **Step 2: Create Virtual Environment**

```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Linux/macOS:
source venv/bin/activate
# On Windows:
venv\Scripts\activate
```

#### **Step 3: Install Dependencies**

```bash
# Upgrade pip
pip install --upgrade pip

# Install requirements
pip install -r requirements.txt

# Verify installation
python -c "import cha_pipe_sizing; print('CHA installed successfully!')"
```

### **Method 2: Docker Installation**

#### **Step 1: Create Dockerfile**

```dockerfile
# Dockerfile
FROM python:3.9-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY src/ ./src/
COPY configs/ ./configs/
COPY tests/ ./tests/

# Set environment variables
ENV PYTHONPATH=/app/src

# Expose port (if needed)
EXPOSE 8000

# Default command
CMD ["python", "-m", "pytest", "tests/", "-v"]
```

#### **Step 2: Build and Run Docker Container**

```bash
# Build Docker image
docker build -t cha-pipe-sizing .

# Run Docker container
docker run -it cha-pipe-sizing

# Run with volume mount for data
docker run -it -v $(pwd)/data:/app/data cha-pipe-sizing
```

### **Method 3: Conda Installation**

#### **Step 1: Create Conda Environment**

```bash
# Create conda environment
conda create -n cha-env python=3.9

# Activate environment
conda activate cha-env
```

#### **Step 2: Install Dependencies**

```bash
# Install conda packages
conda install -c conda-forge pandas numpy networkx geopandas

# Install pip packages
pip install -r requirements.txt
```

---

## ⚙️ **Configuration**

### **Environment Configuration**

#### **Development Environment**

```bash
# Set environment variables
export CHA_ENV=development
export CHA_DEBUG=true
export CHA_LOG_LEVEL=DEBUG
export CHA_DATA_PATH=./data
export CHA_CONFIG_PATH=./configs
```

#### **Production Environment**

```bash
# Set environment variables
export CHA_ENV=production
export CHA_DEBUG=false
export CHA_LOG_LEVEL=INFO
export CHA_DATA_PATH=/opt/cha/data
export CHA_CONFIG_PATH=/opt/cha/configs
```

### **Configuration Files**

#### **Main Configuration (`configs/cha.yml`)**

```yaml
# Environment settings
environment: production
debug: false
log_level: INFO

# Data paths
data_paths:
  raw: ./data/raw
  interim: ./data/interim
  processed: ./data/processed
  output: ./data/output

# Performance settings
performance:
  max_workers: 4
  memory_limit_gb: 8
  cache_size_mb: 512

# Pipe sizing configuration
pipe_sizing:
  max_velocity_ms: 2.0
  min_velocity_ms: 0.1
  max_pressure_drop_pa_per_m: 5000
  safety_factor: 1.1
  diversity_factor: 0.8
  
  standard_diameters_mm: [50, 63, 80, 100, 125, 150, 200, 250, 300, 400]
  
  cost_model:
    base_cost_eur_per_m: 100
    diameter_cost_factor: 1.5
    material_cost_factor: 1.2
    insulation_cost_factor: 1.1

# Pandapipes settings
pandapipes:
  enabled: true
  solver: "pipeflow"
  max_iterations: 100
  convergence_tolerance: 1e-6

# Logging configuration
logging:
  level: INFO
  format: "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
  file: /var/log/cha/cha.log
  max_size_mb: 100
  backup_count: 5
```

#### **Database Configuration (if applicable)**

```yaml
# Database settings
database:
  type: postgresql
  host: localhost
  port: 5432
  name: cha_db
  user: cha_user
  password: ${CHA_DB_PASSWORD}
  pool_size: 10
  max_overflow: 20
```

---

## 🏗️ **Deployment Environments**

### **Development Environment**

#### **Local Development Setup**

```bash
# 1. Clone repository
git clone <repository-url>
cd branitz_energy_decision_ai_street_final

# 2. Create virtual environment
python -m venv venv
source venv/bin/activate

# 3. Install dependencies
pip install -r requirements.txt
pip install -r requirements-dev.txt

# 4. Set up pre-commit hooks
pre-commit install

# 5. Run tests
python -m pytest tests/ -v

# 6. Start development server
python src/cha_main.py --config configs/cha.yml --debug
```

#### **Development Configuration**

```yaml
# configs/cha-dev.yml
environment: development
debug: true
log_level: DEBUG

# Use local data paths
data_paths:
  raw: ./data/raw
  interim: ./data/interim
  processed: ./data/processed
  output: ./data/output

# Development-specific settings
development:
  hot_reload: true
  auto_reload: true
  debug_toolbar: true
```

### **Staging Environment**

#### **Staging Setup**

```bash
# 1. Set up staging server
sudo apt update
sudo apt install python3.9 python3.9-venv nginx

# 2. Create application user
sudo useradd -m -s /bin/bash cha-app
sudo su - cha-app

# 3. Clone and setup application
git clone <repository-url>
cd branitz_energy_decision_ai_street_final
python3.9 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 4. Configure nginx
sudo nano /etc/nginx/sites-available/cha-staging
```

#### **Nginx Configuration**

```nginx
# /etc/nginx/sites-available/cha-staging
server {
    listen 80;
    server_name staging.cha.example.com;
    
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
    
    location /static/ {
        alias /home/cha-app/branitz_energy_decision_ai_street_final/static/;
    }
    
    location /media/ {
        alias /home/cha-app/branitz_energy_decision_ai_street_final/media/;
    }
}
```

#### **Systemd Service**

```ini
# /etc/systemd/system/cha-staging.service
[Unit]
Description=CHA Staging Application
After=network.target

[Service]
Type=simple
User=cha-app
Group=cha-app
WorkingDirectory=/home/cha-app/branitz_energy_decision_ai_street_final
Environment=PATH=/home/cha-app/branitz_energy_decision_ai_street_final/venv/bin
ExecStart=/home/cha-app/branitz_energy_decision_ai_street_final/venv/bin/python src/cha_main.py --config configs/cha-staging.yml
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

### **Production Environment**

#### **Enhanced Production Requirements**

For production deployment with hydraulic simulation capabilities:

**Hardware Requirements:**
- **CPU**: 8+ cores recommended for parallel thermal calculations
- **Memory**: 16GB+ RAM for large network simulations
- **Storage**: 10GB+ free space for simulation data and logs
- **Network**: Stable internet connection for dependency updates

**Software Stack:**
```bash
# Production software stack
Python 3.8+
Pandapipes 0.8.0+
NumPy 1.21+
Pandas 1.3+
SciPy 1.7+
Matplotlib 3.4+
Plotly 5.0+
PyYAML 5.4+
jsonschema 3.2+
```

**Performance Optimization:**
```python
# Production configuration optimizations
production_config = {
    # Optimize for performance
    'pipe_sections': 4,  # Reduce for faster thermal calculation
    'max_resize_iterations': 3,  # Reduce for faster convergence
    'convergence_tolerance': 1e-4,  # Less strict for faster convergence
    
    # Enable parallel processing
    'parallel_processing': True,
    'max_workers': 4,
    
    # Memory optimization
    'memory_optimization': True,
    'cleanup_after_simulation': True,
    
    # Logging configuration
    'log_level': 'INFO',
    'log_file': '/var/log/cha_simulation.log',
    'max_log_size': '100MB',
    'backup_count': 5
}
```

#### **Production Setup**

```bash
# 1. Set up production server
sudo apt update
sudo apt install python3.9 python3.9-venv nginx postgresql redis-server

# 2. Create application user
sudo useradd -m -s /bin/bash cha-prod
sudo su - cha-prod

# 3. Clone and setup application
git clone <repository-url>
cd branitz_energy_decision_ai_street_final
python3.9 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 4. Set up data directories
mkdir -p /opt/cha/data/{raw,interim,processed,output}
mkdir -p /var/log/cha
sudo chown -R cha-prod:cha-prod /opt/cha
sudo chown -R cha-prod:cha-prod /var/log/cha
```

#### **Production Configuration**

```yaml
# configs/cha-prod.yml
environment: production
debug: false
log_level: INFO

# Production data paths
data_paths:
  raw: /opt/cha/data/raw
  interim: /opt/cha/data/interim
  processed: /opt/cha/data/processed
  output: /opt/cha/data/output

# Production performance settings
performance:
  max_workers: 8
  memory_limit_gb: 16
  cache_size_mb: 1024

# Production logging
logging:
  level: INFO
  format: "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
  file: /var/log/cha/cha.log
  max_size_mb: 500
  backup_count: 10

# Security settings
security:
  secret_key: ${CHA_SECRET_KEY}
  allowed_hosts: ["cha.example.com"]
  csrf_protection: true
  rate_limiting: true
```

#### **Production Systemd Service**

```ini
# /etc/systemd/system/cha-prod.service
[Unit]
Description=CHA Production Application
After=network.target postgresql.service redis.service

[Service]
Type=simple
User=cha-prod
Group=cha-prod
WorkingDirectory=/home/cha-prod/branitz_energy_decision_ai_street_final
Environment=PATH=/home/cha-prod/branitz_energy_decision_ai_street_final/venv/bin
Environment=CHA_ENV=production
Environment=CHA_SECRET_KEY=${CHA_SECRET_KEY}
ExecStart=/home/cha-prod/branitz_energy_decision_ai_street_final/venv/bin/python src/cha_main.py --config configs/cha-prod.yml
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
```

---

## 🔒 **Security Configuration**

### **Application Security**

#### **Environment Variables**

```bash
# Set secure environment variables
export CHA_SECRET_KEY="your-secret-key-here"
export CHA_DB_PASSWORD="secure-database-password"
export CHA_REDIS_PASSWORD="secure-redis-password"
```

#### **File Permissions**

```bash
# Set secure file permissions
chmod 600 configs/cha-prod.yml
chmod 700 /opt/cha/data
chmod 755 /var/log/cha
```

#### **Firewall Configuration**

```bash
# Configure UFW firewall
sudo ufw enable
sudo ufw allow ssh
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw deny 8000/tcp  # Block direct access to application port
```

### **Database Security**

#### **PostgreSQL Configuration**

```bash
# Configure PostgreSQL
sudo -u postgres psql

-- Create database and user
CREATE DATABASE cha_db;
CREATE USER cha_user WITH PASSWORD 'secure-password';
GRANT ALL PRIVILEGES ON DATABASE cha_db TO cha_user;

-- Configure authentication
sudo nano /etc/postgresql/13/main/pg_hba.conf
```

#### **Redis Security**

```bash
# Configure Redis
sudo nano /etc/redis/redis.conf

# Set password
requirepass secure-redis-password

# Bind to localhost only
bind 127.0.0.1

# Restart Redis
sudo systemctl restart redis
```

---

## 📊 **Monitoring and Logging**

### **Application Monitoring**

#### **Health Check Endpoint**

```python
# src/health_check.py
from flask import Flask, jsonify
import psutil
import os

app = Flask(__name__)

@app.route('/health')
def health_check():
    """Health check endpoint."""
    try:
        # Check system resources
        cpu_percent = psutil.cpu_percent()
        memory_percent = psutil.virtual_memory().percent
        disk_percent = psutil.disk_usage('/').percent
        
        # Check application status
        status = "healthy" if all([
            cpu_percent < 80,
            memory_percent < 80,
            disk_percent < 90
        ]) else "unhealthy"
        
        return jsonify({
            "status": status,
            "cpu_percent": cpu_percent,
            "memory_percent": memory_percent,
            "disk_percent": disk_percent,
            "timestamp": datetime.utcnow().isoformat()
        })
    except Exception as e:
        return jsonify({
            "status": "error",
            "error": str(e)
        }), 500
```

#### **Prometheus Metrics**

```python
# src/metrics.py
from prometheus_client import Counter, Histogram, Gauge, start_http_server

# Define metrics
pipe_sizing_requests = Counter('cha_pipe_sizing_requests_total', 'Total pipe sizing requests')
pipe_sizing_duration = Histogram('cha_pipe_sizing_duration_seconds', 'Pipe sizing duration')
active_connections = Gauge('cha_active_connections', 'Active connections')

def start_metrics_server(port=9090):
    """Start Prometheus metrics server."""
    start_http_server(port)
```

### **Logging Configuration**

#### **Structured Logging**

```python
# src/logging_config.py
import logging
import logging.config
import json
from datetime import datetime

class JSONFormatter(logging.Formatter):
    """JSON formatter for structured logging."""
    
    def format(self, record):
        log_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno
        }
        
        if record.exc_info:
            log_entry["exception"] = self.formatException(record.exc_info)
        
        return json.dumps(log_entry)

# Configure logging
logging_config = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "json": {
            "()": JSONFormatter
        },
        "standard": {
            "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        }
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "level": "INFO",
            "formatter": "standard",
            "stream": "ext://sys.stdout"
        },
        "file": {
            "class": "logging.handlers.RotatingFileHandler",
            "level": "INFO",
            "formatter": "json",
            "filename": "/var/log/cha/cha.log",
            "maxBytes": 10485760,  # 10MB
            "backupCount": 5
        }
    },
    "loggers": {
        "": {
            "handlers": ["console", "file"],
            "level": "INFO",
            "propagate": False
        }
    }
}

logging.config.dictConfig(logging_config)
```

### **System Monitoring**

#### **Systemd Service Monitoring**

```bash
# Check service status
sudo systemctl status cha-prod

# View service logs
sudo journalctl -u cha-prod -f

# Restart service
sudo systemctl restart cha-prod
```

#### **Log Rotation**

```bash
# Configure logrotate
sudo nano /etc/logrotate.d/cha

# Logrotate configuration
/var/log/cha/*.log {
    daily
    missingok
    rotate 30
    compress
    delaycompress
    notifempty
    create 644 cha-prod cha-prod
    postrotate
        systemctl reload cha-prod
    endscript
}
```

---

## 🔄 **Deployment Automation**

### **CI/CD Pipeline**

#### **GitHub Actions Workflow**

```yaml
# .github/workflows/deploy.yml
name: Deploy CHA

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      
      - name: Set up Python
        uses: actions/setup-python@v2
        with:
          python-version: 3.9
      
      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install -r requirements.txt
          pip install -r requirements-dev.txt
      
      - name: Run tests
        run: |
          python -m pytest tests/ -v --cov=src
      
      - name: Run linting
        run: |
          flake8 src/ tests/
          black --check src/ tests/
          mypy src/

  deploy-staging:
    needs: test
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main'
    steps:
      - uses: actions/checkout@v2
      
      - name: Deploy to staging
        run: |
          # Deploy to staging server
          ssh user@staging-server "cd /path/to/app && git pull && systemctl restart cha-staging"

  deploy-production:
    needs: test
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main'
    steps:
      - uses: actions/checkout@v2
      
      - name: Deploy to production
        run: |
          # Deploy to production server
          ssh user@production-server "cd /path/to/app && git pull && systemctl restart cha-prod"
```

### **Docker Compose**

#### **Development Environment**

```yaml
# docker-compose.yml
version: '3.8'

services:
  cha-app:
    build: .
    ports:
      - "8000:8000"
    volumes:
      - ./data:/app/data
      - ./configs:/app/configs
    environment:
      - CHA_ENV=development
      - CHA_DEBUG=true
    depends_on:
      - postgres
      - redis

  postgres:
    image: postgres:13
    environment:
      POSTGRES_DB: cha_db
      POSTGRES_USER: cha_user
      POSTGRES_PASSWORD: password
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"

  redis:
    image: redis:6-alpine
    ports:
      - "6379:6379"

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
    depends_on:
      - cha-app

volumes:
  postgres_data:
```

#### **Production Environment**

```yaml
# docker-compose.prod.yml
version: '3.8'

services:
  cha-app:
    build: .
    restart: unless-stopped
    volumes:
      - /opt/cha/data:/app/data
      - /var/log/cha:/app/logs
    environment:
      - CHA_ENV=production
      - CHA_DEBUG=false
      - CHA_SECRET_KEY=${CHA_SECRET_KEY}
    depends_on:
      - postgres
      - redis

  postgres:
    image: postgres:13
    restart: unless-stopped
    environment:
      POSTGRES_DB: cha_db
      POSTGRES_USER: cha_user
      POSTGRES_PASSWORD: ${CHA_DB_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "127.0.0.1:5432:5432"

  redis:
    image: redis:6-alpine
    restart: unless-stopped
    command: redis-server --requirepass ${CHA_REDIS_PASSWORD}
    ports:
      - "127.0.0.1:6379:6379"

  nginx:
    image: nginx:alpine
    restart: unless-stopped
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.prod.conf:/etc/nginx/nginx.conf
      - ./ssl:/etc/nginx/ssl
    depends_on:
      - cha-app

volumes:
  postgres_data:
```

---

## 🔧 **Maintenance and Updates**

### **Application Updates**

#### **Update Process**

```bash
# 1. Backup current version
sudo systemctl stop cha-prod
cp -r /home/cha-prod/branitz_energy_decision_ai_street_final /home/cha-prod/backup-$(date +%Y%m%d)

# 2. Update application
cd /home/cha-prod/branitz_energy_decision_ai_street_final
git pull origin main

# 3. Update dependencies
source venv/bin/activate
pip install -r requirements.txt

# 4. Run migrations (if applicable)
python src/migrate.py

# 5. Restart application
sudo systemctl start cha-prod

# 6. Verify deployment
curl http://localhost:8000/health
```

#### **Rollback Process**

```bash
# 1. Stop current version
sudo systemctl stop cha-prod

# 2. Restore backup
rm -rf /home/cha-prod/branitz_energy_decision_ai_street_final
mv /home/cha-prod/backup-$(date +%Y%m%d) /home/cha-prod/branitz_energy_decision_ai_street_final

# 3. Restart application
sudo systemctl start cha-prod
```

### **Database Maintenance**

#### **Backup Database**

```bash
# Create database backup
pg_dump -h localhost -U cha_user cha_db > /opt/cha/backups/cha_db_$(date +%Y%m%d_%H%M%S).sql

# Compress backup
gzip /opt/cha/backups/cha_db_$(date +%Y%m%d_%H%M%S).sql
```

#### **Restore Database**

```bash
# Restore database from backup
gunzip -c /opt/cha/backups/cha_db_20231201_120000.sql.gz | psql -h localhost -U cha_user cha_db
```

### **Log Management**

#### **Log Cleanup**

```bash
# Clean old logs
find /var/log/cha -name "*.log.*" -mtime +30 -delete

# Compress old logs
find /var/log/cha -name "*.log.*" -mtime +7 -exec gzip {} \;
```

---

## 🚨 **Troubleshooting**

### **Common Issues**

#### **1. Application Won't Start**

**Symptoms**: Service fails to start, error in logs

**Diagnosis**:
```bash
# Check service status
sudo systemctl status cha-prod

# Check logs
sudo journalctl -u cha-prod -f

# Check configuration
python -c "import yaml; print(yaml.safe_load(open('configs/cha-prod.yml')))"
```

**Solutions**:
- Check configuration file syntax
- Verify environment variables
- Check file permissions
- Verify dependencies are installed

#### **2. Database Connection Issues**

**Symptoms**: Database connection errors, timeout errors

**Diagnosis**:
```bash
# Test database connection
psql -h localhost -U cha_user -d cha_db -c "SELECT 1;"

# Check PostgreSQL status
sudo systemctl status postgresql

# Check database logs
sudo tail -f /var/log/postgresql/postgresql-13-main.log
```

**Solutions**:
- Check database service status
- Verify connection parameters
- Check firewall settings
- Verify user permissions

#### **3. Performance Issues**

**Symptoms**: Slow response times, high memory usage

**Diagnosis**:
```bash
# Check system resources
htop
iostat -x 1
free -h

# Check application metrics
curl http://localhost:8000/metrics
```

**Solutions**:
- Optimize configuration parameters
- Increase system resources
- Implement caching
- Optimize database queries

#### **4. Memory Issues**

**Symptoms**: Out of memory errors, application crashes

**Diagnosis**:
```bash
# Check memory usage
free -h
ps aux --sort=-%mem | head

# Check application memory
curl http://localhost:8000/health
```

**Solutions**:
- Increase system memory
- Optimize memory usage in code
- Implement memory monitoring
- Use memory profiling tools

### **Emergency Procedures**

#### **Service Recovery**

```bash
# Emergency restart
sudo systemctl restart cha-prod

# Check service status
sudo systemctl status cha-prod

# If service fails, check logs
sudo journalctl -u cha-prod --since "10 minutes ago"
```

#### **Data Recovery**

```bash
# Restore from latest backup
sudo systemctl stop cha-prod
gunzip -c /opt/cha/backups/cha_db_latest.sql.gz | psql -h localhost -U cha_user cha_db
sudo systemctl start cha-prod
```

---

## 📊 **Performance Optimization**

### **System Optimization**

#### **OS Tuning**

```bash
# Optimize system parameters
echo 'vm.swappiness=10' >> /etc/sysctl.conf
echo 'vm.dirty_ratio=15' >> /etc/sysctl.conf
echo 'vm.dirty_background_ratio=5' >> /etc/sysctl.conf
sysctl -p
```

#### **Application Optimization**

```yaml
# configs/cha-prod.yml
performance:
  max_workers: 8
  memory_limit_gb: 16
  cache_size_mb: 1024
  enable_compression: true
  enable_caching: true
```

### **Database Optimization**

#### **PostgreSQL Tuning**

```bash
# Optimize PostgreSQL configuration
sudo nano /etc/postgresql/13/main/postgresql.conf

# Key parameters
shared_buffers = 256MB
effective_cache_size = 1GB
work_mem = 4MB
maintenance_work_mem = 64MB
```

---

## 🎯 **Conclusion**

This deployment guide provides comprehensive instructions for deploying the CHA Intelligent Pipe Sizing System in various environments. By following these guidelines, you can ensure a successful deployment with proper security, monitoring, and maintenance procedures.

Key takeaways:

1. **Plan Deployment**: Choose appropriate deployment method for your environment
2. **Secure Configuration**: Implement proper security measures
3. **Monitor Performance**: Set up monitoring and logging
4. **Automate Processes**: Use CI/CD pipelines for automated deployments
5. **Maintain System**: Regular maintenance and updates
6. **Troubleshoot Issues**: Know how to diagnose and fix common problems

The system is designed to be robust and scalable, with proper deployment practices ensuring reliable operation in production environments.

**Happy deploying!** 🚀

---

*This deployment guide is part of the Branitz Energy Decision AI project. For more information, see the main project documentation.*
