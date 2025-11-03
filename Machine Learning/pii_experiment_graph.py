import matplotlib.pyplot as plt
import pandas as pd

# Flags to toggle plots
plot_additional = True  # Set to False to disable additional metrics plot
plot_performance = True  # Set to False to disable performance metrics plot

# Data from the experiment
data = {
    'Experiment Conditions': [
        'Real Names (Baseline)',
        'Fake Names Replacement',
        'XXXX Masking',
        'LLM-based PII Removal(ollMA)'
    ],
    'PII Leakage Rate (%)': [87.3, 12.4, 3.2, 5.8],
    'Re-identification Risk': [0.92, 0.18, 0.05, 0.08],
    'Entropy Score': [1.2, 4.8, 6.1, 5.7],
    'BLEU Score': [1.000, 0.876, 0.623, 0.831],
    'ROUGE-1': [1.000, 0.912, 0.701, 0.864],
    'ROUGE-2': [1.000, 0.883, 0.645, 0.847],
    'ROUGE-L': [1.000, 0.895, 0.672, 0.858],
    'Perplexity': [24.3, 28.7, 45.2, 31.4],
    'Coherence(1-5)': [4.8, 4.5, 3.2, 4.2],
    'Task Completion Rate (%)': [94.8, 91.2, 76.5, 88.7],
    'Semantic Similarity': [1.000, 0.945, 0.682, 0.891],
    'Context Preservation': [1.000, 0.923, 0.714, 0.867],
    'Avg Processing Time (ms)': [152, 287, 198, 1243],
    'Token Overhead (%)': [0, 12, 3, 8],
    'API Calls per Query': [1.0, 1.0, 1.0, 2.2]
}

# Create DataFrame
df = pd.DataFrame(data)

def plot_main_metrics():
    # Create subplots for main metrics (first 9)
    fig, axes = plt.subplots(3, 3, figsize=(18, 18))

    metrics = ['PII Leakage Rate (%)', 'Re-identification Risk', 'Entropy Score', 'BLEU Score', 'ROUGE-1', 'ROUGE-2', 'ROUGE-L', 'Perplexity', 'Coherence(1-5)']

    # Add space between groups
    plt.subplots_adjust(hspace=1.8, wspace=0.6, top=0.95, bottom=0.2)

    for i, metric in enumerate(metrics):
        row = i // 3
        col = i % 3
        axes[row, col].bar(df['Experiment Conditions'], df[metric], color=['red', 'blue', 'green', 'orange'])
        axes[row, col].set_ylabel(metric, fontsize=12)
        axes[row, col].set_xticks(range(len(df['Experiment Conditions'])))
        axes[row, col].set_xticklabels(['Exp 1', 'Exp 2', 'Exp 3', 'Exp 4'], rotation=0, ha='right', fontsize=10)
        # Add value labels on bars
        for j, v in enumerate(df[metric]):
            axes[row, col].text(j, v + max(df[metric])*0.01, f'{v}', ha='center', va='bottom', fontsize=10)

    plt.tight_layout()
    plt.savefig('pii_experiment_graph_main.png', dpi=300, bbox_inches='tight')
    plt.show()

def plot_additional_metrics():
    # Create subplots for additional metrics (Task Completion, Semantic Similarity, Context Preservation)
    fig, axes = plt.subplots(1, 3, figsize=(18, 6))

    metrics = ['Task Completion Rate (%)', 'Semantic Similarity', 'Context Preservation']

    # Add space between groups
    plt.subplots_adjust(hspace=0.4, wspace=0.6, top=0.85, bottom=0.2)

    for i, metric in enumerate(metrics):
        col = i % 3
        axes[col].bar(df['Experiment Conditions'], df[metric], color=['red', 'blue', 'green', 'orange'])
        axes[col].set_ylabel(metric, fontsize=12)
        axes[col].set_xticks(range(len(df['Experiment Conditions'])))
        axes[col].set_xticklabels(['Exp 1', 'Exp 2', 'Exp 3', 'Exp 4'], rotation=0, ha='right', fontsize=10)
        # Add value labels on bars
        for j, v in enumerate(df[metric]):
            axes[col].text(j, v + max(df[metric])*0.01, f'{v}', ha='center', va='bottom', fontsize=10)

    plt.tight_layout()
    plt.savefig('pii_experiment_graph_additional.png', dpi=300, bbox_inches='tight')
    plt.show()

def plot_performance_metrics():
    # Create subplots for performance metrics (Avg Processing Time, Token Overhead, API Calls per Query)
    fig, axes = plt.subplots(1, 3, figsize=(18, 6))

    metrics = ['Avg Processing Time (ms)', 'Token Overhead (%)', 'API Calls per Query']

    # Add space between groups
    plt.subplots_adjust(hspace=0.4, wspace=0.6, top=0.85, bottom=0.2)

    for i, metric in enumerate(metrics):
        col = i % 3
        axes[col].bar(df['Experiment Conditions'], df[metric], color=['red', 'blue', 'green', 'orange'])
        axes[col].set_ylabel(metric, fontsize=12)
        axes[col].set_xticks(range(len(df['Experiment Conditions'])))
        axes[col].set_xticklabels(['Exp 1', 'Exp 2', 'Exp 3', 'Exp 4'], rotation=0, ha='right', fontsize=10)
        # Add value labels on bars
        for j, v in enumerate(df[metric]):
            axes[col].text(j, v + max(df[metric])*0.01, f'{v}', ha='center', va='bottom', fontsize=10)

    plt.tight_layout()
    plt.savefig('pii_experiment_graph_performance.png', dpi=300, bbox_inches='tight')
    plt.show()

# Plot main metrics
plot_main_metrics()

# Plot additional metrics if flag is True
if plot_additional:
    plot_additional_metrics()

# Plot performance metrics if flag is True
if plot_performance:
    plot_performance_metrics()