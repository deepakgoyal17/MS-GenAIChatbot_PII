#!/usr/bin/env python3
"""
Configuration system for PII Protection Chatbot
Allows enabling/disabling features with simple flags
"""

import os
from dataclasses import dataclass
from typing import Dict, Any
import streamlit as st

@dataclass
class PIIProtectionConfig:
    """Configuration class for PII protection methods"""
    
    # Core Features
    enable_real_names: bool = False          # Baseline - always enabled for comparison
    enable_fake_names: bool = False          # Fake NER replacement
    enable_xxxx_masking: bool = False        # XXXX masking
    enable_llm_pii_removal: bool = True     # LLM-based PII removal
    
    # Evaluation Features
    enable_deepeval: bool = True            # DeepEval relevancy metrics
    enable_semantic_similarity: bool = True # Semantic similarity analysis
    enable_pii_leakage_detection: bool = True # PII leakage scoring
    enable_performance_timing: bool = True  # Processing time measurement
    
    # Export Features
    enable_excel_export: bool = True        # Excel export functionality
    auto_export: bool = True               # Automatically export after each query
    
    # Advanced Features
    enable_smart_org_replacement: bool = True    # Use smart org replacement vs simple faker
    enable_capitalization: bool = True           # Smart capitalization preprocessing
    enable_regex_fallback: bool = True           # Regex-based entity detection fallback
    
    # UI Features
    show_mappings: bool = True              # Show PII mapping information
    show_debug_info: bool = False           # Show debug information in UI
    show_processing_times: bool = True      # Display processing times
    
    # Performance Settings
    max_queries_in_memory: int = 100        # Maximum queries to keep in memory
    export_batch_size: int = 50             # Auto-export every N queries
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert config to dictionary"""
        return {
            field.name: getattr(self, field.name)
            for field in self.__dataclass_fields__.values()
        }
    
    @classmethod
    def from_dict(cls, config_dict: Dict[str, Any]) -> 'PIIProtectionConfig':
        """Create config from dictionary"""
        return cls(**{
            key: value for key, value in config_dict.items()
            if key in cls.__dataclass_fields__
        })
    
    def save_to_session_state(self) -> None:
        """Save configuration to Streamlit session state"""
        st.session_state.pii_config = self.to_dict()
    
    @classmethod
    def load_from_session_state(cls) -> 'PIIProtectionConfig':
        """Load configuration from Streamlit session state"""
        if 'pii_config' in st.session_state:
            return cls.from_dict(st.session_state.pii_config)
        return cls()  # Return default config

def create_config_sidebar() -> PIIProtectionConfig:
    """Create Streamlit sidebar for configuration"""
    
    st.sidebar.title("🔧 Configuration")
    st.sidebar.markdown("---")
    
    # Load current config
    config = PIIProtectionConfig.load_from_session_state()
    
    # PII Protection Methods
    st.sidebar.subheader("🔒 PII Protection Methods")

    config.enable_real_names = st.sidebar.checkbox(
        "Real Names (Baseline)",
        value=config.enable_real_names,
        help="Original text without PII protection - useful for comparison"
    )
    
    config.enable_fake_names = st.sidebar.checkbox(
        "Fake Names Replacement", 
        value=config.enable_fake_names,
        help="Replace PII with fake but realistic data"
    )
    
    config.enable_xxxx_masking = st.sidebar.checkbox(
        "XXXX Masking", 
        value=config.enable_xxxx_masking,
        help="Replace PII with generic XXXX placeholders"
    )
    
    config.enable_llm_pii_removal = st.sidebar.checkbox(
        "LLM-based PII Removal", 
        value=config.enable_llm_pii_removal,
        help="Use LLM to intelligently remove PII"
    )
    
    # Evaluation Features
    st.sidebar.subheader("📊 Evaluation Features")
    
    config.enable_deepeval = st.sidebar.checkbox(
        "DeepEval Relevancy", 
        value=config.enable_deepeval,
        help="Answer relevancy scoring using DeepEval"
    )
    
    config.enable_semantic_similarity = st.sidebar.checkbox(
        "Semantic Similarity", 
        value=config.enable_semantic_similarity,
        help="Cosine similarity analysis using SentenceTransformers"
    )
    
    config.enable_pii_leakage_detection = st.sidebar.checkbox(
        "PII Leakage Detection", 
        value=config.enable_pii_leakage_detection,
        help="Detect if original PII appears in responses"
    )
    
    config.enable_performance_timing = st.sidebar.checkbox(
        "Performance Timing", 
        value=config.enable_performance_timing,
        help="Measure and display processing times"
    )
    
    # Advanced Features
    st.sidebar.subheader("⚙️ Advanced Features")
    
    config.enable_smart_org_replacement = st.sidebar.checkbox(
        "Smart Org Replacement", 
        value=config.enable_smart_org_replacement,
        help="Use intelligent organization replacement vs simple faker"
    )
    
    config.enable_capitalization = st.sidebar.checkbox(
        "Smart Capitalization", 
        value=config.enable_capitalization,
        help="Apply intelligent capitalization preprocessing"
    )
    
    config.enable_regex_fallback = st.sidebar.checkbox(
        "Regex Fallback", 
        value=config.enable_regex_fallback,
        help="Use regex patterns for entities missed by spaCy"
    )
    
    # Export Features
    st.sidebar.subheader("📊 Export Features")
    
    config.enable_excel_export = st.sidebar.checkbox(
        "Excel Export", 
        value=config.enable_excel_export,
        help="Enable Excel export functionality"
    )
    
    config.auto_export = st.sidebar.checkbox(
        "Auto Export", 
        value=config.auto_export,
        help="Automatically export data periodically"
    )
    
    if config.auto_export:
        config.export_batch_size = st.sidebar.slider(
            "Auto Export Batch Size", 
            min_value=10, 
            max_value=100, 
            value=config.export_batch_size,
            help="Export data every N queries"
        )
    
    # UI Features
    st.sidebar.subheader("🖥️ UI Features")
    
    config.show_mappings = st.sidebar.checkbox(
        "Show PII Mappings", 
        value=config.show_mappings,
        help="Display PII transformation mappings"
    )
    
    config.show_debug_info = st.sidebar.checkbox(
        "Show Debug Info", 
        value=config.show_debug_info,
        help="Display debug information in UI"
    )
    
    config.show_processing_times = st.sidebar.checkbox(
        "Show Processing Times", 
        value=config.show_processing_times,
        help="Display processing time metrics"
    )
    
    # Performance Settings
    st.sidebar.subheader("⚡ Performance Settings")
    
    config.max_queries_in_memory = st.sidebar.slider(
        "Max Queries in Memory", 
        min_value=10, 
        max_value=500, 
        value=config.max_queries_in_memory,
        help="Maximum number of queries to keep in memory"
    )
    
    # Save configuration
    config.save_to_session_state()
    
    # Configuration summary
    st.sidebar.markdown("---")
    st.sidebar.subheader("📋 Active Features")
    
    active_methods = []
    if config.enable_real_names: active_methods.append("Real Names")
    if config.enable_fake_names: active_methods.append("Fake Names")
    if config.enable_xxxx_masking: active_methods.append("XXXX Masking")
    if config.enable_llm_pii_removal: active_methods.append("LLM PII Removal")
    
    st.sidebar.write(f"**Methods:** {len(active_methods)}/4 enabled")
    for method in active_methods:
        st.sidebar.write(f"✅ {method}")
    
    # Reset to defaults button
    if st.sidebar.button("🔄 Reset to Defaults"):
        default_config = PIIProtectionConfig()
        default_config.save_to_session_state()
        st.rerun()
    
    return config

# Preset configurations
PRESET_CONFIGS = {
    "Full Research Mode": PIIProtectionConfig(
        enable_real_names=True,      # Include baseline for comparison
        enable_fake_names=True,
        enable_xxxx_masking=True,
        enable_llm_pii_removal=True,
        enable_deepeval=True,
        enable_semantic_similarity=True,
        enable_pii_leakage_detection=True,
        enable_performance_timing=True,
        enable_excel_export=True,
        show_mappings=True,
        show_processing_times=True
    ),

    "Privacy Focus": PIIProtectionConfig(
        enable_real_names=False,     # Skip baseline for pure privacy testing
        enable_fake_names=True,
        enable_xxxx_masking=True,
        enable_llm_pii_removal=True,
        enable_deepeval=False,
        enable_semantic_similarity=False,
        enable_pii_leakage_detection=True,
        enable_performance_timing=False,
        enable_excel_export=True,
        show_mappings=True,
        show_processing_times=False
    ),

    "Performance Testing": PIIProtectionConfig(
        enable_real_names=True,      # Include baseline for timing comparison
        enable_fake_names=True,
        enable_xxxx_masking=False,
        enable_llm_pii_removal=False,
        enable_deepeval=False,
        enable_semantic_similarity=True,
        enable_pii_leakage_detection=False,
        enable_performance_timing=True,
        enable_excel_export=True,
        show_mappings=False,
        show_processing_times=True
    ),

    "Minimal Demo": PIIProtectionConfig(
        enable_real_names=False,     # Skip baseline for simple demo
        enable_fake_names=True,
        enable_xxxx_masking=False,
        enable_llm_pii_removal=False,
        enable_deepeval=False,
        enable_semantic_similarity=False,
        enable_pii_leakage_detection=False,
        enable_performance_timing=False,
        enable_excel_export=False,
        show_mappings=True,
        show_processing_times=False
    ),

    "Baseline Only": PIIProtectionConfig(
        enable_real_names=True,      # Only baseline for reference
        enable_fake_names=False,
        enable_xxxx_masking=False,
        enable_llm_pii_removal=False,
        enable_deepeval=True,
        enable_semantic_similarity=False,
        enable_pii_leakage_detection=False,
        enable_performance_timing=True,
        enable_excel_export=True,
        show_mappings=False,
        show_processing_times=True
    )
}

def load_preset_config(preset_name: str) -> PIIProtectionConfig:
    """Load a preset configuration"""
    if preset_name in PRESET_CONFIGS:
        config = PRESET_CONFIGS[preset_name]
        config.save_to_session_state()
        return config
    return PIIProtectionConfig()

def create_preset_selector() -> None:
    """Create preset configuration selector"""
    st.sidebar.subheader("🎛️ Quick Presets")

    preset_options = ["Custom"] + list(PRESET_CONFIGS.keys())
    selected_preset = st.sidebar.selectbox(
        "Choose Configuration Preset",
        options=preset_options,
        help="Quick configuration presets for different use cases"
    )

    if selected_preset != "Custom":
        # Show preset description
        descriptions = {
            "Full Research Mode": "Complete analysis with all methods and metrics",
            "Privacy Focus": "Optimized for privacy testing (no baseline)",
            "Performance Testing": "Focus on timing and efficiency",
            "Minimal Demo": "Simple demonstration (no baseline)",
            "Baseline Only": "Only baseline for reference testing"
        }

        if selected_preset in descriptions:
            st.sidebar.caption(f"📋 {descriptions[selected_preset]}")

        if st.sidebar.button(f"Apply {selected_preset}"):
            load_preset_config(selected_preset)
            st.rerun()