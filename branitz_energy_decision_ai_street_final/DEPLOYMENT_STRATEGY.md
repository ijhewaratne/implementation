# 🚀 CHA Intelligent Pipe Sizing System - Deployment Strategy

## 🎯 **Executive Summary**

This document outlines a comprehensive deployment strategy for the CHA Intelligent Pipe Sizing System, focusing on gradual rollout, A/B testing, performance monitoring, and user feedback collection. The strategy ensures safe, controlled deployment while maximizing system performance and user satisfaction.

---

## 📋 **Deployment Strategy Overview**

### **Deployment Phases**

The deployment strategy is organized into four main phases:

1. **Phase 1: Gradual Rollout with Feature Flags** - Controlled feature activation
2. **Phase 2: A/B Testing with Existing vs. New Sizing** - Comparative performance evaluation
3. **Phase 3: Performance Monitoring and Optimization** - Real-time monitoring and optimization
4. **Phase 4: User Feedback Collection and Iteration** - Continuous improvement based on user feedback

### **Deployment Timeline**

```
Week 1-2: Feature Flag Setup and Initial Rollout
Week 3-4: A/B Testing Implementation
Week 5-6: Performance Monitoring Deployment
Week 7-8: User Feedback System Integration
Week 9-12: Full Production Deployment
Week 13+: Continuous Monitoring and Optimization
```

---

## 🔧 **Phase 1: Gradual Rollout with Feature Flags**

### **Feature Flag System**

The feature flag system provides controlled activation of new features, enabling:
- **Gradual Rollout**: Incremental feature activation
- **Risk Mitigation**: Quick rollback capabilities
- **User Segmentation**: Targeted feature delivery
- **Performance Control**: Load management

#### **Feature Flag Configuration**

```yaml
# configs/feature_flags.yml
feature_flags:
  intelligent_pipe_sizing:
    description: "Enable intelligent pipe sizing engine"
    type: "percentage"
    status: "rolling_out"
    enabled: true
    rollout_percentage: 25.0
    user_groups: ["beta_users", "power_users"]
    
  enhanced_flow_calculation:
    description: "Enable enhanced flow calculation with safety factors"
    type: "boolean"
    status: "enabled"
    enabled: true
    
  network_hierarchy_analysis:
    description: "Enable network hierarchy analysis"
    type: "user_group"
    status: "rolling_out"
    enabled: true
    user_groups: ["beta_users"]
    
  standards_compliance:
    description: "Enable engineering standards compliance checking"
    type: "boolean"
    status: "enabled"
    enabled: true
    
  performance_optimization:
    description: "Enable performance optimization features"
    type: "percentage"
    status: "rolling_out"
    enabled: true
    rollout_percentage: 50.0
    
  cost_benefit_analysis:
    description: "Enable cost-benefit analysis"
    type: "boolean"
    status: "enabled"
    enabled: true
    
  advanced_validation:
    description: "Enable advanced validation features"
    type: "boolean"
    status: "enabled"
    enabled: true
    
  pandapipes_integration:
    description: "Enable enhanced pandapipes integration"
    type: "percentage"
    status: "rolling_out"
    enabled: true
    rollout_percentage: 75.0
```

#### **Rollout Strategy**

**Week 1: Internal Testing (5% rollout)**
- Enable features for internal team and beta users
- Monitor system performance and stability
- Collect initial feedback and identify issues

**Week 2: Beta User Rollout (25% rollout)**
- Expand to beta user group
- Monitor performance metrics
- Collect detailed feedback

**Week 3: Gradual Expansion (50% rollout)**
- Increase rollout percentage
- Monitor system load and performance
- Validate scalability

**Week 4: Full Rollout (100% rollout)**
- Complete feature activation
- Monitor for any issues
- Prepare for A/B testing phase

#### **Feature Flag Management**

```python
# Example usage of feature flags
from src.cha_feature_flags import CHAFeatureFlags

# Initialize feature flags
feature_flags = CHAFeatureFlags()

# Check if feature is enabled for user
evaluation = feature_flags.is_enabled(
    'intelligent_pipe_sizing',
    user_id='user123',
    user_groups=['beta_users']
)

if evaluation.enabled:
    # Use intelligent pipe sizing
    sizing_engine = IntelligentPipeSizingEngine()
else:
    # Use traditional sizing
    sizing_engine = TraditionalPipeSizingEngine()
```

---

## 🧪 **Phase 2: A/B Testing with Existing vs. New Sizing**

### **A/B Testing Framework**

The A/B testing system enables comparative evaluation of different sizing approaches:

#### **Test Configuration**

```yaml
# configs/ab_tests.yml
ab_tests:
  pipe_sizing_comparison:
    name: "Pipe Sizing Method Comparison"
    description: "Compare traditional vs. intelligent pipe sizing methods"
    test_type: "pipe_sizing"
    status: "running"
    start_date: "2024-01-15T00:00:00"
    end_date: "2024-02-15T00:00:00"
    
    variants:
      - name: "traditional"
        description: "Traditional fixed diameter sizing"
        traffic_percentage: 50.0
        configuration:
          pipe_sizing_method: "fixed_diameter"
          default_diameter_mm: 100
          enable_intelligent_sizing: false
          
      - name: "intelligent"
        description: "Intelligent pipe sizing with flow-based calculation"
        traffic_percentage: 50.0
        configuration:
          pipe_sizing_method: "intelligent"
          enable_intelligent_sizing: true
          max_velocity_ms: 2.0
          min_velocity_ms: 0.1
    
    metrics:
      - name: "pipe_cost_efficiency"
        description: "Cost efficiency of pipe sizing"
        metric_type: "primary"
        aggregation: "mean"
        target_direction: "increase"
        minimum_detectable_effect: 0.05
        significance_level: 0.05
        power: 0.8
        
      - name: "hydraulic_performance"
        description: "Hydraulic performance metrics"
        metric_type: "primary"
        aggregation: "mean"
        target_direction: "increase"
        
      - name: "sizing_accuracy"
        description: "Accuracy of pipe sizing"
        metric_type: "secondary"
        aggregation: "mean"
        target_direction: "increase"
    
    target_sample_size: 1000
    minimum_duration_days: 7
    maximum_duration_days: 30
    
  flow_calculation_comparison:
    name: "Flow Calculation Method Comparison"
    description: "Compare basic vs. enhanced flow calculation methods"
    test_type: "flow_calculation"
    status: "running"
    
    variants:
      - name: "basic"
        description: "Basic flow calculation without safety factors"
        traffic_percentage: 50.0
        configuration:
          flow_calculation_method: "basic"
          safety_factor: 1.0
          diversity_factor: 1.0
          
      - name: "enhanced"
        description: "Enhanced flow calculation with safety and diversity factors"
        traffic_percentage: 50.0
        configuration:
          flow_calculation_method: "enhanced"
          safety_factor: 1.1
          diversity_factor: 0.8
    
    metrics:
      - name: "flow_accuracy"
        description: "Accuracy of flow calculations"
        metric_type: "primary"
        aggregation: "mean"
        target_direction: "increase"
        
      - name: "system_reliability"
        description: "System reliability metrics"
        metric_type: "primary"
        aggregation: "mean"
        target_direction: "increase"
    
    target_sample_size: 800
    minimum_duration_days: 7
    maximum_duration_days: 21
```

#### **A/B Testing Implementation**

```python
# Example A/B testing implementation
from src.cha_ab_testing import CHAABTesting

# Initialize A/B testing
ab_testing = CHAABTesting()

# Assign user to test variant
variant = ab_testing.assign_user_to_variant('pipe_sizing_comparison', 'user123')

# Record metrics based on variant
if variant == 'intelligent':
    # Use intelligent sizing
    sizing_engine = IntelligentPipeSizingEngine()
    start_time = time.time()
    result = sizing_engine.size_network(network_data)
    end_time = time.time()
    
    # Record performance metrics
    ab_testing.record_metric(
        'pipe_sizing_comparison',
        'intelligent',
        'pipe_cost_efficiency',
        result['cost_efficiency']
    )
    ab_testing.record_metric(
        'pipe_sizing_comparison',
        'intelligent',
        'hydraulic_performance',
        result['hydraulic_performance']
    )
    ab_testing.record_metric(
        'pipe_sizing_comparison',
        'intelligent',
        'sizing_accuracy',
        result['accuracy']
    )
else:
    # Use traditional sizing
    sizing_engine = TraditionalPipeSizingEngine()
    start_time = time.time()
    result = sizing_engine.size_network(network_data)
    end_time = time.time()
    
    # Record performance metrics
    ab_testing.record_metric(
        'pipe_sizing_comparison',
        'traditional',
        'pipe_cost_efficiency',
        result['cost_efficiency']
    )
    ab_testing.record_metric(
        'pipe_sizing_comparison',
        'traditional',
        'hydraulic_performance',
        result['hydraulic_performance']
    )
    ab_testing.record_metric(
        'pipe_sizing_comparison',
        'traditional',
        'sizing_accuracy',
        result['accuracy']
    )

# Analyze test results
analysis = ab_testing.analyze_test_results('pipe_sizing_comparison')
print(f"Test conclusion: {analysis['overall_conclusion']}")
print(f"Recommendations: {analysis['recommendations']}")
```

#### **A/B Testing Metrics**

**Primary Metrics:**
- **Pipe Cost Efficiency**: Cost per unit of performance
- **Hydraulic Performance**: System efficiency and reliability
- **Sizing Accuracy**: Accuracy of pipe diameter calculations

**Secondary Metrics:**
- **Processing Time**: Time to complete sizing calculations
- **Memory Usage**: System resource utilization
- **User Satisfaction**: User feedback and ratings

**Guardrail Metrics:**
- **System Stability**: Error rates and crashes
- **Performance Impact**: Overall system performance
- **Resource Usage**: CPU, memory, and disk usage

---

## 📊 **Phase 3: Performance Monitoring and Optimization**

### **Performance Monitoring System**

The performance monitoring system provides real-time monitoring and optimization:

#### **Monitoring Configuration**

```yaml
# configs/performance_monitoring.yml
thresholds:
  - metric_name: "pipe_sizing_time_ms"
    warning_threshold: 1000.0
    error_threshold: 5000.0
    critical_threshold: 10000.0
    comparison_operator: "greater_than"
    window_size_minutes: 5
    evaluation_interval_seconds: 60
    
  - metric_name: "network_creation_time_ms"
    warning_threshold: 2000.0
    error_threshold: 10000.0
    critical_threshold: 30000.0
    comparison_operator: "greater_than"
    window_size_minutes: 5
    evaluation_interval_seconds: 60
    
  - metric_name: "simulation_time_ms"
    warning_threshold: 5000.0
    error_threshold: 30000.0
    critical_threshold: 60000.0
    comparison_operator: "greater_than"
    window_size_minutes: 5
    evaluation_interval_seconds: 60
    
  - metric_name: "memory_usage_mb"
    warning_threshold: 1000.0
    error_threshold: 2000.0
    critical_threshold: 4000.0
    comparison_operator: "greater_than"
    window_size_minutes: 5
    evaluation_interval_seconds: 60
    
  - metric_name: "cpu_usage_percent"
    warning_threshold: 80.0
    error_threshold: 90.0
    critical_threshold: 95.0
    comparison_operator: "greater_than"
    window_size_minutes: 5
    evaluation_interval_seconds: 60
    
  - metric_name: "error_rate_percent"
    warning_threshold: 1.0
    error_threshold: 5.0
    critical_threshold: 10.0
    comparison_operator: "greater_than"
    window_size_minutes: 5
    evaluation_interval_seconds: 60
```

#### **Performance Monitoring Implementation**

```python
# Example performance monitoring implementation
from src.cha_performance_monitoring import CHAPerformanceMonitor

# Initialize performance monitoring
monitor = CHAPerformanceMonitor()

# Record performance metrics
monitor.record_timer('pipe_sizing_time_ms', duration_seconds)
monitor.record_gauge('memory_usage_mb', memory_usage)
monitor.record_counter('pipe_sizing_requests', 1)

# Add alert callback
def alert_callback(alert):
    print(f"ALERT: {alert.level.value} - {alert.message}")
    # Send notification, log to system, etc.

monitor.add_alert_callback(alert_callback)

# Generate performance report
report = monitor.generate_performance_report()
monitor.save_report(report, 'reports/performance_report.json')
```

#### **Performance Optimization Strategies**

**1. Algorithm Optimization**
- Optimize pipe sizing algorithms for better performance
- Implement caching for frequently calculated values
- Use parallel processing for large networks

**2. Memory Optimization**
- Implement memory pooling for large data structures
- Use lazy loading for non-critical data
- Optimize data structures for memory efficiency

**3. CPU Optimization**
- Implement multi-threading for CPU-intensive operations
- Use vectorized operations where possible
- Optimize numerical algorithms

**4. I/O Optimization**
- Implement asynchronous I/O operations
- Use connection pooling for database operations
- Optimize file I/O operations

---

## 💬 **Phase 4: User Feedback Collection and Iteration**

### **User Feedback System**

The user feedback system enables continuous improvement based on user input:

#### **Feedback Configuration**

```yaml
# configs/user_feedback.yml
feedback_categories:
  pipe_sizing:
    - "accuracy"
    - "performance"
    - "usability"
  flow_calculation:
    - "accuracy"
    - "performance"
    - "usability"
  network_analysis:
    - "accuracy"
    - "performance"
    - "usability"
  cost_analysis:
    - "accuracy"
    - "performance"
    - "usability"
  user_interface:
    - "usability"
    - "design"
    - "navigation"
  documentation:
    - "clarity"
    - "completeness"
    - "accuracy"
  performance:
    - "speed"
    - "memory"
    - "stability"
  integration:
    - "compatibility"
    - "ease_of_use"
    - "reliability"

sentiment_keywords:
  positive:
    - "good"
    - "great"
    - "excellent"
    - "amazing"
    - "fantastic"
    - "love"
    - "perfect"
    - "awesome"
    - "brilliant"
    - "outstanding"
  negative:
    - "bad"
    - "terrible"
    - "awful"
    - "horrible"
    - "hate"
    - "disappointing"
    - "frustrating"
    - "annoying"
    - "broken"
    - "useless"
  neutral:
    - "okay"
    - "fine"
    - "average"
    - "normal"
    - "standard"
    - "acceptable"
    - "decent"
    - "reasonable"
    - "adequate"
    - "satisfactory"

priority_keywords:
  critical:
    - "critical"
    - "urgent"
    - "emergency"
    - "broken"
    - "crash"
    - "error"
    - "fail"
    - "not working"
  high:
    - "important"
    - "major"
    - "significant"
    - "serious"
    - "problem"
    - "issue"
    - "bug"
    - "slow"
  medium:
    - "moderate"
    - "minor"
    - "small"
    - "suggestion"
    - "improvement"
    - "enhancement"
  low:
    - "nice to have"
    - "optional"
    - "future"
    - "wish"
    - "request"
    - "feature"
```

#### **Feedback Collection Implementation**

```python
# Example feedback collection implementation
from src.cha_user_feedback import CHAUserFeedback, FeedbackType

# Initialize user feedback system
feedback_system = CHAUserFeedback()

# Submit feedback
feedback_id = feedback_system.submit_feedback(
    user_id='user123',
    feedback_type=FeedbackType.BUG_REPORT,
    title='Pipe sizing calculation error',
    description='The pipe sizing calculation is returning incorrect diameters for high flow rates.',
    rating=2,
    tags=['pipe_sizing', 'calculation', 'error']
)

# Analyze feedback
analysis = feedback_system.analyze_feedback()
print(f"Total feedback: {analysis.total_feedback}")
print(f"Average rating: {analysis.average_rating}")
print(f"Top issues: {analysis.top_issues}")
print(f"Recommendations: {analysis.improvement_recommendations}")

# Generate feedback report
report_path = feedback_system.generate_feedback_report(analysis)
```

#### **Feedback Analysis and Iteration**

**1. Sentiment Analysis**
- Analyze user sentiment from feedback text
- Identify positive and negative feedback patterns
- Track sentiment trends over time

**2. Priority Classification**
- Automatically classify feedback by priority
- Identify critical issues requiring immediate attention
- Prioritize feature requests based on user demand

**3. Trend Analysis**
- Identify recurring issues and patterns
- Track user satisfaction trends
- Monitor feedback volume and types

**4. Improvement Recommendations**
- Generate actionable improvement recommendations
- Prioritize improvements based on impact and effort
- Track implementation of improvements

---

## 🔄 **Deployment Automation**

### **Deployment Scripts**

#### **Feature Flag Deployment**

```bash
#!/bin/bash
# deploy_feature_flags.sh

echo "🚀 Deploying Feature Flags..."

# Update feature flag configuration
python src/cha_feature_flags.py --action save --config configs/feature_flags.yml

# Validate configuration
python scripts/validate_config.py configs/feature_flags.yml

# Deploy to production
echo "✅ Feature flags deployed successfully"
```

#### **A/B Testing Deployment**

```bash
#!/bin/bash
# deploy_ab_tests.sh

echo "🧪 Deploying A/B Tests..."

# Start A/B tests
python src/cha_ab_testing.py --action start --test-id pipe_sizing_comparison
python src/cha_ab_testing.py --action start --test-id flow_calculation_comparison

# Monitor test status
python src/cha_ab_testing.py --action list

echo "✅ A/B tests deployed successfully"
```

#### **Performance Monitoring Deployment**

```bash
#!/bin/bash
# deploy_performance_monitoring.sh

echo "📊 Deploying Performance Monitoring..."

# Start performance monitoring
python src/cha_performance_monitoring.py --action start

# Configure monitoring thresholds
python src/cha_performance_monitoring.py --action save --config configs/performance_monitoring.yml

echo "✅ Performance monitoring deployed successfully"
```

#### **User Feedback Deployment**

```bash
#!/bin/bash
# deploy_user_feedback.sh

echo "💬 Deploying User Feedback System..."

# Initialize feedback system
python src/cha_user_feedback.py --action analyze

# Configure feedback collection
python src/cha_user_feedback.py --action export --output data/feedback_backup.json

echo "✅ User feedback system deployed successfully"
```

### **Deployment Pipeline**

```yaml
# .github/workflows/deploy.yml
name: Deploy CHA System

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v2
    
    - name: Set up Python
      uses: actions/setup-python@v2
      with:
        python-version: 3.9
    
    - name: Install dependencies
      run: |
        pip install -r requirements.txt
    
    - name: Run tests
      run: |
        python -m pytest tests/ -v
    
    - name: Deploy feature flags
      run: |
        bash scripts/deploy_feature_flags.sh
    
    - name: Deploy A/B tests
      run: |
        bash scripts/deploy_ab_tests.sh
    
    - name: Deploy performance monitoring
      run: |
        bash scripts/deploy_performance_monitoring.sh
    
    - name: Deploy user feedback
      run: |
        bash scripts/deploy_user_feedback.sh
    
    - name: Generate deployment report
      run: |
        python scripts/generate_deployment_report.py
```

---

## 📈 **Monitoring and Alerting**

### **Monitoring Dashboard**

The monitoring dashboard provides real-time visibility into system performance:

#### **Key Metrics**

**Performance Metrics:**
- Pipe sizing time
- Network creation time
- Simulation time
- Memory usage
- CPU usage
- Error rates

**A/B Testing Metrics:**
- Test participation rates
- Variant performance
- Statistical significance
- Conversion rates

**User Feedback Metrics:**
- Feedback volume
- Sentiment distribution
- Priority distribution
- Resolution rates

#### **Alerting Rules**

```yaml
# configs/alerting_rules.yml
alerts:
  - name: "High Pipe Sizing Time"
    condition: "pipe_sizing_time_ms > 5000"
    severity: "warning"
    action: "notify_team"
    
  - name: "Critical Memory Usage"
    condition: "memory_usage_mb > 4000"
    severity: "critical"
    action: "scale_up"
    
  - name: "High Error Rate"
    condition: "error_rate_percent > 5"
    severity: "error"
    action: "rollback"
    
  - name: "A/B Test Significance"
    condition: "ab_test_significance > 0.95"
    severity: "info"
    action: "notify_team"
```

---

## 🔄 **Rollback Strategy**

### **Rollback Procedures**

#### **Feature Flag Rollback**

```bash
#!/bin/bash
# rollback_feature_flags.sh

echo "🔄 Rolling back feature flags..."

# Disable problematic features
python src/cha_feature_flags.py --action update --flag intelligent_pipe_sizing --updates '{"enabled": false, "status": "disabled"}'

# Validate rollback
python scripts/validate_config.py configs/feature_flags.yml

echo "✅ Feature flags rolled back successfully"
```

#### **A/B Testing Rollback**

```bash
#!/bin/bash
# rollback_ab_tests.sh

echo "🔄 Rolling back A/B tests..."

# Stop problematic tests
python src/cha_ab_testing.py --action stop --test-id pipe_sizing_comparison

# Analyze results
python src/cha_ab_testing.py --action analyze --test-id pipe_sizing_comparison

echo "✅ A/B tests rolled back successfully"
```

#### **Performance Monitoring Rollback**

```bash
#!/bin/bash
# rollback_performance_monitoring.sh

echo "🔄 Rolling back performance monitoring..."

# Stop monitoring
python src/cha_performance_monitoring.py --action stop

# Generate final report
python src/cha_performance_monitoring.py --action report --output reports/rollback_report.json

echo "✅ Performance monitoring rolled back successfully"
```

---

## 📊 **Success Metrics**

### **Deployment Success Criteria**

#### **Feature Flag Success Metrics**
- **Rollout Success Rate**: >95% successful feature activations
- **Rollback Time**: <5 minutes for emergency rollbacks
- **User Impact**: <1% of users affected by failed rollouts

#### **A/B Testing Success Metrics**
- **Statistical Significance**: >95% confidence level
- **Sample Size**: Minimum 1000 users per variant
- **Test Duration**: Minimum 7 days for reliable results
- **Performance Improvement**: >5% improvement in primary metrics

#### **Performance Monitoring Success Metrics**
- **Monitoring Coverage**: 100% of critical metrics monitored
- **Alert Response Time**: <5 minutes for critical alerts
- **False Positive Rate**: <5% false positive alerts
- **System Uptime**: >99.9% system availability

#### **User Feedback Success Metrics**
- **Feedback Collection Rate**: >10% of users provide feedback
- **Response Time**: <24 hours for feedback acknowledgment
- **Resolution Rate**: >80% of feedback resolved within 30 days
- **User Satisfaction**: >4.0 average rating

---

## 🎯 **Deployment Checklist**

### **Pre-Deployment Checklist**

- [ ] **Feature Flag Configuration**
  - [ ] Feature flags configured and tested
  - [ ] Rollout percentages set appropriately
  - [ ] User groups defined
  - [ ] Rollback procedures tested

- [ ] **A/B Testing Setup**
  - [ ] Test variants configured
  - [ ] Metrics defined and validated
  - [ ] Sample size calculations completed
  - [ ] Statistical significance thresholds set

- [ ] **Performance Monitoring**
  - [ ] Monitoring thresholds configured
  - [ ] Alerting rules set up
  - [ ] Dashboard configured
  - [ ] Notification channels established

- [ ] **User Feedback System**
  - [ ] Feedback collection configured
  - [ ] Analysis rules set up
  - [ ] Reporting system configured
  - [ ] Response procedures defined

### **Deployment Checklist**

- [ ] **Deployment Execution**
  - [ ] Feature flags deployed
  - [ ] A/B tests started
  - [ ] Performance monitoring activated
  - [ ] User feedback system enabled

- [ ] **Validation**
  - [ ] System functionality verified
  - [ ] Performance metrics within expected ranges
  - [ ] No critical errors detected
  - [ ] User experience validated

### **Post-Deployment Checklist**

- [ ] **Monitoring**
  - [ ] Real-time monitoring active
  - [ ] Alerts configured and tested
  - [ ] Performance baselines established
  - [ ] User feedback collection active

- [ ] **Documentation**
  - [ ] Deployment procedures documented
  - [ ] Rollback procedures documented
  - [ ] Monitoring procedures documented
  - [ ] User feedback procedures documented

---

## 🚀 **Conclusion**

The comprehensive deployment strategy for the CHA Intelligent Pipe Sizing System provides:

✅ **Gradual Rollout**: Controlled feature activation with feature flags  
✅ **A/B Testing**: Comparative evaluation of different approaches  
✅ **Performance Monitoring**: Real-time monitoring and optimization  
✅ **User Feedback**: Continuous improvement based on user input  
✅ **Automation**: Automated deployment and rollback procedures  
✅ **Monitoring**: Comprehensive monitoring and alerting  
✅ **Documentation**: Complete deployment documentation  

This strategy ensures safe, controlled deployment while maximizing system performance and user satisfaction. The phased approach allows for continuous learning and improvement throughout the deployment process.

**The deployment strategy is ready for implementation and will ensure successful deployment of the CHA Intelligent Pipe Sizing System!** 🎯

---

*This deployment strategy is part of the Branitz Energy Decision AI project. For more information, see the main project documentation.*
