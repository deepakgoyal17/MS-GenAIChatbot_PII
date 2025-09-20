# 🔒 PII Protection Chatbot - Complete Research Platform

## 🎯 Overview

A comprehensive **PII (Personally Identifiable Information) Protection Research Platform** that compares different anonymization methods for conversational AI. Features modular design with feature flags, comprehensive evaluation metrics, and Excel export capabilities.

## ✨ Key Features

### **🔧 Modular Architecture**
- **Feature Flags**: Enable/disable individual PII protection methods
- **Conditional Loading**: Components load only when needed
- **Configuration Presets**: Quick setup for different use cases
- **Real-time Toggling**: Change features without restarting

### **🔒 PII Protection Methods**
- **Real Names** (Baseline): No protection for comparison *(configurable)*
- **Fake Names**: Replace PII with realistic fake data
- **XXXX Masking**: Simple placeholder masking
- **LLM-based PII Removal**: Intelligent context-aware removal

### **📊 Comprehensive Evaluation**
- **DeepEval Relevancy**: Answer quality assessment
- **Semantic Similarity**: Meaning preservation analysis
- **PII Leakage Detection**: Privacy breach monitoring
- **Performance Timing**: Computational efficiency metrics

### **📈 Research-Ready Export**
- **Excel Export**: 6-sheet comprehensive analysis
- **Real-time Statistics**: Live metrics dashboard
- **Historical Data**: Persistent analysis storage
- **Research Reports**: Publication-ready data format

## 🚀 Quick Start

### **Step 1: Installation**
```bash
# Clone or navigate to the project
cd "Codes/Deep Learning/Chatbots"

# Install dependencies
pip install -r requirements.txt

# Download spaCy model (if using NER features)
python -m spacy download en_core_web_sm
```

### **Step 2: Configuration**
```bash
# Create .env file with your API key
echo "GOOGLE-API-KEY=your_actual_api_key_here" > .env
```

### **Step 3: Launch**
```bash
# Run modular version (recommended)
python run.py modular

# Or run original version
python run.py original

# Or use Streamlit directly
streamlit run app_modular.py
```

## 🎛️ Configuration Options

### **Preset Configurations**
- **🔬 Full Research Mode**: All features for comprehensive analysis
- **🔒 Privacy Focus**: Optimized for privacy protection
- **⚡ Performance Testing**: Minimal setup for benchmarking
- **🎯 Minimal Demo**: Simple demonstration mode

### **Feature Flags**
```python
# Enable/disable individual features
config.enable_fake_names = True          # Fake NER replacement
config.enable_xxxx_masking = True        # XXXX masking
config.enable_llm_pii_removal = True     # LLM-based removal
config.enable_deepeval = True            # Relevancy evaluation
config.enable_semantic_similarity = True # Similarity analysis
config.enable_excel_export = True        # Data export
```

## 📋 Usage Examples

### **🔬 Research Mode**
```bash
python run.py modular
```
- Use sidebar to enable all evaluation features
- Export comprehensive Excel analysis
- Compare all PII protection methods
- Generate research-quality metrics

### **🏭 Production Mode**
```bash
python run.py modular
```
- Enable only required PII methods
- Disable expensive evaluation features
- Configure auto-export for monitoring
- Optimize for performance

### **🎓 Learning Mode**
```bash
python run.py modular
```
- Start with minimal configuration
- Gradually enable features to learn
- Use debug mode to understand processing
- Experiment with different methods

## 📁 Project Structure

```
PII Protection Chatbot/
├── 📄 app.py                    # Original application (all features)
├── 📄 app_modular.py           # Modular application with feature flags
├── 📄 config.py                # Configuration system
├── 📄 excel_exporter.py        # Excel export functionality
├── 📄 run.py                   # Launcher script
├── 📄 test_deepeval.py         # DeepEval testing
├── 📄 test_fixes.py            # General testing
├── 📄 requirements.txt         # Dependencies
├── 📁 analysis_results/        # Excel export directory
├── 📁 logs/                    # Application logs
└── 📁 docs/                    # Documentation
    ├── 📄 MODULAR_SYSTEM_GUIDE.md
    ├── 📄 EXCEL_EXPORT_GUIDE.md
    ├── 📄 ERROR_FIXES_README.md
    ├── 📄 APP_CODE_EXPLANATION.md
    └── 📄 DEEPEVAL_TROUBLESHOOTING.md
```

## 🔍 Feature Details

### **PII Protection Methods**

| Method | Description | Use Case | Complexity |
|--------|-------------|----------|------------|
| **Real Names** | No protection | Baseline comparison | None |
| **Fake Names** | Realistic replacement | Context preservation | Medium |
| **XXXX Masking** | Simple masking | Basic privacy | Low |
| **LLM PII Removal** | Intelligent removal | Advanced protection | High |

### **Evaluation Metrics**

| Metric | Description | Scale | Purpose |
|--------|-------------|-------|---------|
| **Relevancy** | Answer quality | 0.0 - 1.0 | Quality assessment |
| **Similarity** | Meaning preservation | 0.0 - 1.0 | Context retention |
| **PII Leakage** | Privacy breaches | 0 - N | Security monitoring |
| **Processing Time** | Computational cost | Seconds | Performance analysis |

## 📊 Excel Export Features

### **6 Comprehensive Sheets**
1. **Detailed_Analysis**: All prompts and responses
2. **Metrics_Comparison**: Complete evaluation metrics
3. **Response_Analysis**: Content and length analysis
4. **PII_Mappings**: Transformation mappings
5. **Summary_Statistics**: Aggregated insights
6. **Performance_Analysis**: Efficiency metrics

### **Export Controls**
- **📥 Export to Excel**: Manual export with timestamp
- **📈 Show Current Stats**: Real-time statistics view
- **🗑️ Clear Data**: Reset analysis data
- **Auto Export**: Periodic automatic export

## 🛠️ Troubleshooting

### **Common Issues**

#### **API Key Missing**
```bash
# Check .env file
cat .env

# Should contain:
GOOGLE-API-KEY=your_actual_api_key_here
```

#### **Dependencies Missing**
```bash
# Install all requirements
pip install -r requirements.txt

# Check specific packages
pip list | grep pandas
```

#### **Model Loading Issues**
```bash
# Pre-download models
python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('all-MiniLM-L6-v2')"
```

#### **DeepEval Issues**
```bash
# Test DeepEval separately
python test_deepeval.py
```

### **Performance Optimization**
- Disable unused features in configuration
- Use minimal presets for production
- Enable auto-export for periodic data collection
- Monitor memory usage with large datasets

## 🎯 Research Applications

### **Academic Research**
- **Comparative Analysis**: Quantitative method comparison
- **Privacy-Utility Trade-offs**: Balance assessment
- **Semantic Preservation**: Context retention studies
- **Performance Evaluation**: Computational efficiency analysis

### **Industry Applications**
- **Compliance Monitoring**: PII protection validation
- **Method Selection**: Data-driven approach selection
- **Quality Assurance**: Automated testing and validation
- **Performance Optimization**: Resource usage optimization

## 📚 Documentation

| Document | Purpose |
|----------|---------|
| [`MODULAR_SYSTEM_GUIDE.md`](MODULAR_SYSTEM_GUIDE.md) | Feature flag system guide |
| [`EXCEL_EXPORT_GUIDE.md`](EXCEL_EXPORT_GUIDE.md) | Excel export documentation |
| [`ERROR_FIXES_README.md`](ERROR_FIXES_README.md) | Error resolution guide |
| [`APP_CODE_EXPLANATION.md`](APP_CODE_EXPLANATION.md) | Code structure explanation |
| [`DEEPEVAL_TROUBLESHOOTING.md`](DEEPEVAL_TROUBLESHOOTING.md) | DeepEval debugging guide |

## 🤝 Contributing

### **Adding New PII Methods**
```python
# 1. Add to config.py
enable_new_method: bool = False

# 2. Add to app_modular.py
if config.enable_new_method:
    result = new_pii_method(text)

# 3. Add to Excel export
'new_method_response': result
```

### **Adding New Metrics**
```python
# 1. Add calculation function
def calculate_new_metric(data):
    # Implementation
    return score

# 2. Add to processing pipeline
new_metric_score = calculate_new_metric(analysis_data)

# 3. Add to Excel export
'new_metric': new_metric_score
```

## 📄 License & Attribution

This project is designed for **PII protection research** and **privacy-preserving AI development**. All components are implemented with research and educational purposes in mind.

## 🎉 Getting Started

1. **📦 Install dependencies**
2. **🔑 Configure API key**
3. **🚀 Launch application**
4. **🎛️ Configure features**
5. **🔬 Start experimenting**

```bash
# Complete setup in one command
pip install -r requirements.txt && python run.py modular
```

**Happy researching! 🔬✨**

---

*Built for the PII Protection Research Community*