# 🚀 ADK Deployment Guide - Enhanced Multi-Agent System with Google ADK

## 📋 **Overview**

This comprehensive deployment guide provides step-by-step instructions for deploying the Enhanced Multi-Agent System with Google ADK across different environments (development, staging, production) using various deployment methods.

---

## 🎯 **Deployment Options**

### **1. Interactive Deployment**
- **Command**: `make deploy-adk`
- **Description**: Interactive deployment with user prompts and environment selection
- **Best for**: First-time setup, development environments

### **2. Environment-Specific Deployment**
- **Development**: `make deploy-dev`
- **Staging**: `make deploy-staging`
- **Production**: `make deploy-prod`
- **Best for**: Automated deployments, CI/CD pipelines

### **3. Docker Deployment**
- **Build**: `make docker-build`
- **Start**: `make docker-up`
- **Stop**: `make docker-down`
- **Best for**: Containerized deployments, production environments

---

## 🔧 **Prerequisites**

### **System Requirements**
- **Operating System**: Linux (Ubuntu 20.04+), macOS (10.15+), or Windows 10+
- **Python**: 3.8 or higher (3.9+ recommended)
- **Memory**: Minimum 4GB RAM (8GB+ recommended for large networks)
- **Storage**: Minimum 2GB free space
- **CPU**: Multi-core processor recommended

### **Software Dependencies**
- Python 3.8+
- pip (Python package manager)
- Git (for version control)
- Docker (optional, for containerized deployment)
- Docker Compose (optional, for multi-service deployment)

### **API Requirements**
- **Google Gemini API Key**: Required for ADK functionality
- **Google Cloud Platform Account**: Optional, for advanced ADK features

---

## 🚀 **Quick Start Deployment**

### **Step 1: Clone Repository**
```bash
# Clone the repository
git clone <repository-url>
cd branitz_energy_decision_ai_street_final

# Verify repository structure
ls -la
```

### **Step 2: Interactive Deployment**
```bash
# Run interactive deployment
make deploy-adk

# Follow the prompts:
# 1. Select environment (development/staging/production)
# 2. Configure API keys
# 3. Install dependencies
# 4. Run tests
# 5. Setup ADK environment
```

### **Step 3: Start System**
```bash
# Start the ADK system
make start-adk

# Or use the generated start script
python start_adk_system.py
```

### **Step 4: Test System**
```bash
# Test the ADK system
make test-adk

# Or use the generated test script
python test_adk_system.py
```

---

## 🔧 **Environment-Specific Deployment**

### **Development Environment**

#### **Deploy Development Environment**
```bash
# Deploy for development
make deploy-dev

# This will:
# 1. Create development environment
# 2. Install development dependencies
# 3. Setup development configuration
# 4. Run development tests
# 5. Start development services
```

#### **Development Features**
- **Debug Mode**: Enabled for detailed logging
- **Hot Reload**: Automatic code reloading
- **Development Tools**: Jupyter, IPython, debugging tools
- **Test Coverage**: Comprehensive test execution
- **Interactive Mode**: Enhanced user interaction

#### **Start Development Environment**
```bash
# Start development environment
cd dev
python start_dev.py

# Or use the development virtual environment
source dev/venv/bin/activate  # Linux/macOS
# or
dev\venv\Scripts\activate     # Windows
python start_adk_system.py
```

### **Staging Environment**

#### **Deploy Staging Environment**
```bash
# Deploy for staging
make deploy-staging

# This will:
# 1. Create staging environment
# 2. Install staging dependencies
# 3. Setup staging configuration
# 4. Run staging tests
# 5. Deploy staging services
```

#### **Staging Features**
- **Production-like**: Similar to production environment
- **Performance Testing**: Comprehensive performance validation
- **Monitoring**: Basic monitoring and alerting
- **Load Testing**: System load testing capabilities
- **Integration Testing**: Full integration test suite

#### **Start Staging Environment**
```bash
# Start staging environment
cd staging
python start_adk_system.py

# Or use Docker Compose
docker-compose --profile staging up -d
```

### **Production Environment**

#### **Deploy Production Environment**
```bash
# Deploy for production
make deploy-prod

# This will:
# 1. Create production environment
# 2. Install production dependencies
# 3. Setup production configuration
# 4. Run production tests
# 5. Deploy production services
# 6. Setup production monitoring
```

#### **Production Features**
- **High Performance**: Optimized for production workloads
- **Monitoring**: Comprehensive monitoring and alerting
- **Security**: Enhanced security configurations
- **Scalability**: Horizontal and vertical scaling support
- **Reliability**: High availability and fault tolerance

#### **Start Production Environment**
```bash
# Start production environment
cd prod
python start_adk_system.py

# Or use Docker Compose
docker-compose --profile prod up -d

# Or use supervisor
supervisord -c prod/supervisor.conf
```

---

## 🐳 **Docker Deployment**

### **Build Docker Images**
```bash
# Build all Docker images
make docker-build

# This will build:
# - branitz-adk-base: Base Python environment
# - branitz-adk-dev: Development environment
# - branitz-adk-prod: Production environment
# - branitz-adk-system: ADK production system
```

### **Start Docker Services**
```bash
# Start all services
make docker-up

# Start specific profiles
docker-compose --profile dev up -d      # Development
docker-compose --profile staging up -d  # Staging
docker-compose --profile prod up -d     # Production
docker-compose --profile monitoring up -d  # Monitoring
```

### **Docker Service Management**
```bash
# View service status
docker-compose ps

# View logs
make docker-logs

# Stop services
make docker-down

# Restart services
docker-compose restart
```

### **Docker Configuration**
The Docker setup includes:
- **Multi-stage builds**: Optimized for different environments
- **Health checks**: Automatic health monitoring
- **Volume mounts**: Persistent data storage
- **Network isolation**: Secure service communication
- **Resource limits**: Memory and CPU constraints

---

## ⚙️ **Configuration Management**

### **Configuration Files**
- **`configs/deployment_config.yml`**: Main deployment configuration
- **`configs/gemini_config.yml`**: Gemini API configuration
- **`configs/cha.yml`**: CHA agent configuration
- **`configs/cha_intelligent_sizing.yml`**: Intelligent sizing configuration

### **Environment Variables**
```bash
# Required environment variables
export GEMINI_API_KEY="your_gemini_api_key_here"
export ADK_ENABLED="true"
export FALLBACK_ENABLED="true"

# Optional environment variables
export PYTHONPATH="/app"
export LOG_LEVEL="INFO"
export MAX_RETRIES="3"
export QUOTA_RETRY_DELAY="60"
```

### **Configuration Validation**
```bash
# Validate configuration
python scripts/validate_config.py

# Validate specific environment
python scripts/validate_config.py --environment production
```

---

## 🧪 **Testing and Validation**

### **Test Commands**
```bash
# Run all tests
make test-adk

# Run specific test suites
python -m pytest tests/test_adk_agents_unit.py -v
python -m pytest tests/test_adk_tools_unit.py -v
python -m pytest tests/test_adk_integration.py -v
python -m pytest tests/test_adk_performance.py -v

# Run tests for specific environment
cd dev && python -m pytest tests/ -v
cd staging && python -m pytest tests/ -v
cd prod && python -m pytest tests/ -v
```

### **Health Checks**
```bash
# System health check
make health-check

# ADK system health check
python -c "from agents.copy.run_enhanced_agent_system import ADKAgentRunner; runner = ADKAgentRunner(); print('✅ ADK System Healthy')"

# Docker health check
docker-compose ps
```

### **Performance Testing**
```bash
# Run performance tests
python -m pytest tests/test_adk_performance.py -v

# Run system stability tests
python -m pytest tests/test_adk_system_stability.py -v

# Run performance comparison tests
python -m pytest tests/test_adk_vs_simpleagent_performance.py -v
```

---

## 📊 **Monitoring and Logging**

### **System Monitoring**
```bash
# Check system status
make status

# View deployment report
cat deployment_report.json | python -m json.tool

# Monitor system resources
python -c "import psutil; print(f'CPU: {psutil.cpu_percent()}%, Memory: {psutil.virtual_memory().percent}%')"
```

### **Log Management**
```bash
# View deployment logs
tail -f deployment.log

# View environment-specific logs
tail -f dev/logs/dev.log
tail -f staging/logs/staging.log
tail -f prod/logs/prod.log

# View Docker logs
docker-compose logs -f adk-system
```

### **Performance Monitoring**
```bash
# Monitor ADK system performance
python -c "
from src.cha_performance_monitoring import CHAPerformanceMonitor
monitor = CHAPerformanceMonitor()
monitor.start_monitoring()
# ... run operations ...
monitor.stop_monitoring()
print(monitor.get_metrics_summary())
"
```

---

## 🔧 **Troubleshooting**

### **Common Issues**

#### **1. ADK Import Error**
```bash
# Error: ModuleNotFoundError: No module named 'adk'
# Solution: Install ADK package
pip install adk>=0.1.0

# Or use fallback mode
export ADK_ENABLED="false"
export FALLBACK_ENABLED="true"
```

#### **2. API Key Issues**
```bash
# Error: API key not configured
# Solution: Set API key
export GEMINI_API_KEY="your_api_key_here"

# Or update configuration file
echo "api_key: your_api_key_here" >> configs/gemini_config.yml
```

#### **3. Docker Issues**
```bash
# Error: Docker service not starting
# Solution: Check Docker status
docker --version
docker-compose --version

# Restart Docker services
sudo systemctl restart docker  # Linux
# or restart Docker Desktop  # Windows/macOS
```

#### **4. Permission Issues**
```bash
# Error: Permission denied
# Solution: Fix permissions
chmod +x scripts/deploy_adk_system.py
chmod +x scripts/deploy_environment.py
chmod +x start_adk_system.py
chmod +x test_adk_system.py
```

### **Debug Mode**
```bash
# Enable debug mode
export DEBUG="true"
export LOG_LEVEL="DEBUG"

# Run with debug output
python -u scripts/deploy_adk_system.py --debug
```

### **Log Analysis**
```bash
# Analyze deployment logs
grep "ERROR" deployment.log
grep "WARNING" deployment.log
grep "SUCCESS" deployment.log

# Analyze test results
grep "FAILED" test_results.log
grep "PASSED" test_results.log
```

---

## 🔄 **Maintenance and Updates**

### **System Updates**
```bash
# Update dependencies
pip install -r requirements.txt --upgrade

# Update ADK package
pip install adk --upgrade

# Update configuration
python scripts/update_config.py
```

### **Backup and Recovery**
```bash
# Backup configuration
cp -r configs/ configs_backup_$(date +%Y%m%d_%H%M%S)/

# Backup processed data
cp -r processed/ processed_backup_$(date +%Y%m%d_%H%M%S)/

# Restore from backup
cp -r configs_backup_20240101_120000/* configs/
```

### **Cleanup**
```bash
# Clean old deployments
make clean

# Clean Docker resources
docker system prune -a

# Clean old logs
find . -name "*.log" -mtime +30 -delete
```

---

## 📋 **Deployment Checklist**

### **Pre-Deployment**
- [ ] System requirements met
- [ ] API keys configured
- [ ] Configuration files validated
- [ ] Dependencies installed
- [ ] Tests passing

### **Deployment**
- [ ] Environment selected
- [ ] Deployment script executed
- [ ] Services started
- [ ] Health checks passed
- [ ] Monitoring enabled

### **Post-Deployment**
- [ ] System functionality verified
- [ ] Performance metrics acceptable
- [ ] Logs monitored
- [ ] Backup procedures tested
- [ ] Documentation updated

---

## 🚀 **Advanced Deployment**

### **CI/CD Integration**
```yaml
# Example GitHub Actions workflow
name: Deploy ADK System
on:
  push:
    branches: [main]
jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Deploy Development
        run: make deploy-dev
      - name: Deploy Staging
        run: make deploy-staging
      - name: Deploy Production
        run: make deploy-prod
```

### **Kubernetes Deployment**
```yaml
# Example Kubernetes deployment
apiVersion: apps/v1
kind: Deployment
metadata:
  name: branitz-adk-system
spec:
  replicas: 3
  selector:
    matchLabels:
      app: branitz-adk-system
  template:
    metadata:
      labels:
        app: branitz-adk-system
    spec:
      containers:
      - name: adk-system
        image: branitz-adk-system:latest
        ports:
        - containerPort: 8000
        env:
        - name: GEMINI_API_KEY
          valueFrom:
            secretKeyRef:
              name: gemini-secret
              key: api-key
```

### **Load Balancing**
```bash
# Use nginx for load balancing
upstream adk_backend {
    server localhost:8001;
    server localhost:8002;
    server localhost:8003;
}

server {
    listen 80;
    location / {
        proxy_pass http://adk_backend;
    }
}
```

---

## 📚 **Additional Resources**

### **Documentation**
- [System Architecture - ADK Integration](SYSTEM_ARCHITECTURE_ADK_INTEGRATION.md)
- [API Documentation - ADK Agents](API_DOCUMENTATION_ADK_AGENTS.md)
- [ADK Integration Changes](ADK_INTEGRATION_CHANGES.md)
- [Configuration Migration Guide](CONFIGURATION_MIGRATION_GUIDE.md)

### **Support**
- **Issues**: Report issues in the project repository
- **Documentation**: Check the comprehensive documentation
- **Community**: Join the project community discussions
- **Updates**: Follow project updates and releases

### **Best Practices**
- **Security**: Keep API keys secure and rotate regularly
- **Monitoring**: Monitor system health and performance continuously
- **Backup**: Regular backup of configuration and data
- **Testing**: Run tests before and after deployments
- **Documentation**: Keep deployment documentation updated

---

## 🎉 **Conclusion**

This deployment guide provides comprehensive instructions for deploying the Enhanced Multi-Agent System with Google ADK across different environments. The system supports multiple deployment methods, from simple interactive deployment to advanced containerized and orchestrated deployments.

**Key Benefits:**
- **Flexible Deployment**: Multiple deployment options for different needs
- **Environment Support**: Development, staging, and production environments
- **Docker Integration**: Full containerization support
- **Comprehensive Testing**: Extensive testing and validation
- **Monitoring**: Built-in monitoring and logging
- **Troubleshooting**: Detailed troubleshooting guides
- **Maintenance**: Easy maintenance and update procedures

**Ready to deploy your Enhanced Multi-Agent System with Google ADK!** 🚀
