# 📊 Excel Export Feature Guide

## 🎯 Overview

The Excel Export feature provides comprehensive data logging and analysis capabilities for your PII Protection Chatbot research. It automatically captures all prompts, responses, and metrics for detailed analysis.

## 🏗️ Architecture

### **PIIAnalysisExporter Class** ([`excel_exporter.py`](excel_exporter.py))

A comprehensive data export system that captures:
- **All 4 response types** (Real, Fake, Masked, LLM-based)
- **Complete metrics** (Relevancy, Similarity, Performance, PII Leakage)
- **PII mappings** and transformations
- **Summary statistics** and performance analysis

## 📋 Excel File Structure

When you export data, you get a comprehensive Excel file with **6 sheets**:

### **Sheet 1: Detailed_Analysis**
| Column | Description |
|--------|-------------|
| Query_ID | Unique identifier for each query |
| Timestamp | When the query was processed |
| Original_Prompt | User's original input |
| Real_Response | LLM response with real names |
| Fake_Prompt | Input with fake PII replacements |
| Fake_Response | LLM response to fake prompt |
| Masked_Prompt | Input with XXXX masking |
| Masked_Response | LLM response to masked prompt |
| LLM_Anonymized_Prompt | LLM-processed anonymized input |
| LLM_Response | Response to LLM-anonymized input |
| NER_Mapping | JSON of fake→real mappings |
| Mask_Mapping | JSON of mask→real mappings |

### **Sheet 2: Metrics_Comparison**
| Metric Category | Columns |
|----------------|---------|
| **Relevancy Scores** | Relevancy_Real, Relevancy_Fake, Relevancy_Masked, Relevancy_LLM |
| **Semantic Similarity** | Similarity_Real_vs_Fake, Similarity_Real_vs_Masked, etc. |
| **PII Leakage** | PII_Leakage_Real, PII_Leakage_Fake, etc. |
| **F1 Scores** | F1_Score_Real, F1_Score_Fake, etc. |
| **Processing Times** | Processing_Time_Real, Processing_Time_Fake, etc. |

### **Sheet 3: Response_Analysis**
- Response lengths and word counts
- Entity detection statistics
- Content analysis metrics

### **Sheet 4: PII_Mappings**
- Detailed PII transformation records
- Entity type classification
- Mapping effectiveness analysis

### **Sheet 5: Summary_Statistics**
- Average scores across all metrics
- Overall performance summary
- Export metadata

### **Sheet 6: Performance_Analysis**
- Efficiency scores (relevancy per second)
- Best performing methods per query
- Privacy vs utility trade-offs

## 🚀 How to Use

### **In the Streamlit App:**

1. **Interact with the chatbot** - Ask questions and get responses
2. **Click "📥 Export to Excel"** - Exports all current session data
3. **Click "📈 Show Current Stats"** - View real-time statistics
4. **Click "🗑️ Clear Data"** - Reset the analysis data

### **Programmatic Usage:**

```python
from excel_exporter import PIIAnalysisExporter

# Initialize exporter
exporter = PIIAnalysisExporter(output_dir="my_analysis")

# Add analysis data
analysis_data = {
    'original_prompt': 'Hello, I am John Doe from Microsoft',
    'real_response': 'Hello John Doe! Nice to meet someone from Microsoft.',
    'fake_prompt': 'Hello, I am Jane Smith from Google',
    'fake_response': 'Hello Jane Smith! Nice to meet someone from Google.',
    # ... all other metrics
}

exporter.add_analysis_record(analysis_data)

# Export to Excel
filepath = exporter.export_to_excel('my_analysis.xlsx')
print(f"Data exported to: {filepath}")
```

## 📊 Data Analysis Examples

### **Research Questions You Can Answer:**

1. **Which PII protection method maintains highest relevancy?**
   ```excel
   =AVERAGE(Metrics_Comparison[Relevancy_Fake])
   =AVERAGE(Metrics_Comparison[Relevancy_Masked])
   =AVERAGE(Metrics_Comparison[Relevancy_LLM])
   ```

2. **What's the privacy-utility trade-off?**
   ```excel
   =CORREL(Metrics_Comparison[F1_Score_Fake], Metrics_Comparison[Relevancy_Fake])
   ```

3. **Which method is most computationally efficient?**
   ```excel
   =AVERAGE(Performance_Analysis[Fake_Efficiency_Score])
   ```

### **Visualization Opportunities:**

1. **Relevancy Comparison Chart:**
   - X-axis: Query ID
   - Y-axis: Relevancy Score
   - 4 series: Real, Fake, Masked, LLM

2. **Privacy vs Utility Scatter Plot:**
   - X-axis: F1 Score (Privacy)
   - Y-axis: Relevancy Score (Utility)
   - Points: Different methods

3. **Processing Time Analysis:**
   - Bar chart comparing average processing times
   - Efficiency metrics visualization

## 🔧 Advanced Features

### **Automatic Data Collection:**
- Every user interaction is automatically logged
- No manual intervention required
- Persistent across sessions (when using file-based storage)

### **Comprehensive Metrics:**
- **Relevancy**: DeepEval Answer Relevancy scores
- **Similarity**: Semantic similarity using SentenceTransformers
- **Privacy**: PII leakage detection and F1 scores
- **Performance**: Processing time and efficiency metrics

### **Research-Ready Format:**
- Clean, structured data ready for statistical analysis
- Multiple sheets for different analysis perspectives
- Timestamp tracking for temporal analysis

## 📁 File Organization

```
analysis_results/
├── pii_analysis_20250120_143022.xlsx  # Timestamped exports
├── pii_analysis_20250120_151545.xlsx
└── custom_analysis.xlsx               # Custom named exports
```

## 🧪 Testing the Export Feature

### **Test Script:**
```bash
cd "Codes/Deep Learning/Chatbots"
python excel_exporter.py  # Runs built-in test
```

### **Manual Testing:**
1. Run the Streamlit app: `streamlit run app.py`
2. Ask a few questions with PII (names, organizations)
3. Click "📥 Export to Excel"
4. Check the `analysis_results/` folder for the Excel file

## 💡 Research Applications

### **Academic Research:**
- **Comparative Studies**: Quantitative comparison of PII protection methods
- **Performance Analysis**: Computational overhead vs privacy trade-offs
- **Effectiveness Metrics**: Privacy preservation vs conversational quality

### **Industry Applications:**
- **Compliance Reporting**: Document PII protection effectiveness
- **Method Selection**: Data-driven choice of protection strategies
- **Performance Optimization**: Identify bottlenecks and improvements

### **Data Science Projects:**
- **Feature Engineering**: Use metrics as features for ML models
- **Trend Analysis**: Temporal patterns in protection effectiveness
- **Correlation Studies**: Relationships between different metrics

## 🔍 Troubleshooting

### **Common Issues:**

1. **Permission Errors:**
   ```bash
   # Ensure write permissions
   chmod 755 analysis_results/
   ```

2. **Missing Dependencies:**
   ```bash
   pip install pandas openpyxl xlsxwriter
   ```

3. **Large File Sizes:**
   - Use `clear_data()` periodically
   - Export in batches for large datasets

### **Performance Tips:**

1. **Batch Processing:** Export every 50-100 queries
2. **Memory Management:** Clear data after export if memory is limited
3. **File Naming:** Use descriptive names for different experiments

## 📈 Sample Analysis Workflow

1. **Data Collection Phase:**
   - Run multiple test scenarios
   - Collect diverse query types
   - Ensure representative sample

2. **Export Phase:**
   - Export data to Excel
   - Verify all sheets are populated
   - Check data quality

3. **Analysis Phase:**
   - Load Excel file in analysis tool (Excel, Python, R)
   - Create visualizations
   - Calculate statistical significance
   - Draw research conclusions

## 🎯 Benefits

- **Comprehensive Data Capture**: Every aspect of the analysis is recorded
- **Research-Ready Format**: Structured data for immediate analysis
- **Multiple Perspectives**: Different sheets for different analysis needs
- **Automated Process**: No manual data entry required
- **Scalable**: Handles large datasets efficiently
- **Professional Output**: Publication-ready data format

This Excel export feature transforms your chatbot from a demo tool into a comprehensive research platform for PII protection analysis!