#!/usr/bin/env python3
"""
Excel Exporter for PII Protection Chatbot Analysis
Comprehensive data logging and metrics comparison
"""

import pandas as pd
import os
from datetime import datetime
from typing import Dict, List, Any, Optional
import logging

class PIIAnalysisExporter:
    """
    Comprehensive Excel exporter for PII protection analysis
    Captures all prompts, responses, and metrics for research purposes
    """
    
    def __init__(self, output_dir: str = "analysis_results", logger: Optional[logging.Logger] = None):
        """
        Initialize the exporter
        
        Args:
            output_dir: Directory to save Excel files
            logger: Logger instance for debugging
        """
        self.output_dir = output_dir
        self.logger = logger or logging.getLogger(__name__)
        
        # Create output directory if it doesn't exist
        os.makedirs(output_dir, exist_ok=True)
        
        # Initialize data storage
        self.session_data = []
        self.summary_stats = {
            'total_queries': 0,
            'avg_relevancy_real': 0.0,
            'avg_relevancy_fake': 0.0,
            'avg_relevancy_masked': 0.0,
            'avg_relevancy_llm': 0.0,
            'avg_similarity_real_fake': 0.0,
            'avg_similarity_real_masked': 0.0,
            'avg_similarity_real_llm': 0.0,
            'avg_processing_time_real': 0.0,
            'avg_processing_time_fake': 0.0,
            'avg_processing_time_masked': 0.0,
            'avg_processing_time_llm': 0.0,
            'avg_pii_leakage_rate_real': 0.0,
            'avg_pii_leakage_rate_fake': 0.0,
            'avg_pii_leakage_rate_masked': 0.0,
            'avg_pii_leakage_rate_llm': 0.0,
            'avg_reidentification_risk_real': 0.0,
            'avg_reidentification_risk_fake': 0.0,
            'avg_reidentification_risk_masked': 0.0,
            'avg_reidentification_risk_llm': 0.0,
            'avg_entropy_score_real': 0.0,
            'avg_entropy_score_fake': 0.0,
            'avg_entropy_score_masked': 0.0,
            'avg_entropy_score_llm': 0.0,
            'avg_bleu_score_real': 0.0,
            'avg_bleu_score_fake': 0.0,
            'avg_bleu_score_masked': 0.0,
            'avg_bleu_score_llm': 0.0,
            'avg_rouge1_real': 0.0,
            'avg_rouge1_fake': 0.0,
            'avg_rouge1_masked': 0.0,
            'avg_rouge1_llm': 0.0,
            'avg_rouge2_real': 0.0,
            'avg_rouge2_fake': 0.0,
            'avg_rouge2_masked': 0.0,
            'avg_rouge2_llm': 0.0,
            'avg_rougel_real': 0.0,
            'avg_rougel_fake': 0.0,
            'avg_rougel_masked': 0.0,
            'avg_rougel_llm': 0.0,
            'avg_coherence_score_real': 0.0,
            'avg_coherence_score_fake': 0.0,
            'avg_coherence_score_masked': 0.0,
            'avg_coherence_score_llm': 0.0
        }
        
        self.logger.info(f"PIIAnalysisExporter initialized with output directory: {output_dir}")
    
    def add_analysis_record(self, data: Dict[str, Any]) -> None:
        """
        Add a new analysis record
        
        Args:
            data: Dictionary containing all analysis data
        """
        try:
            # Add timestamp
            record = {
                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                **data
            }
            
            self.session_data.append(record)
            self.logger.info(f"Added analysis record #{len(self.session_data)}")
            
            # Update summary statistics
            self._update_summary_stats(record)
            
        except Exception as e:
            self.logger.error(f"Error adding analysis record: {e}")
    
    def _update_summary_stats(self, record: Dict[str, Any]) -> None:
        """Update running summary statistics"""
        try:
            n = len(self.session_data)
            
            # Update averages using incremental formula
            metrics_to_update = [
                'relevancy_real', 'relevancy_fake', 'relevancy_masked', 'relevancy_llm',
                'similarity_real_fake', 'similarity_real_masked', 'similarity_real_llm',
                'processing_time_real', 'processing_time_fake', 'processing_time_masked', 'processing_time_llm',
                'pii_leakage_rate_real', 'pii_leakage_rate_fake', 'pii_leakage_rate_masked', 'pii_leakage_rate_llm',
                'reidentification_risk_real', 'reidentification_risk_fake', 'reidentification_risk_masked', 'reidentification_risk_llm',
                'entropy_score_real', 'entropy_score_fake', 'entropy_score_masked', 'entropy_score_llm',
                'bleu_score_real', 'bleu_score_fake', 'bleu_score_masked', 'bleu_score_llm',
                'rouge1_real', 'rouge1_fake', 'rouge1_masked', 'rouge1_llm',
                'rouge2_real', 'rouge2_fake', 'rouge2_masked', 'rouge2_llm',
                'rougel_real', 'rougel_fake', 'rougel_masked', 'rougel_llm',
                'coherence_score_real', 'coherence_score_fake', 'coherence_score_masked', 'coherence_score_llm'
            ]
            
            for metric in metrics_to_update:
                if metric in record and record[metric] is not None:
                    current_avg = self.summary_stats.get(f'avg_{metric}', 0.0)
                    new_value = float(record[metric])
                    self.summary_stats[f'avg_{metric}'] = ((current_avg * (n - 1)) + new_value) / n
            
            self.summary_stats['total_queries'] = n
            
        except Exception as e:
            self.logger.error(f"Error updating summary stats: {e}")
    
    def export_to_excel(self, filename: Optional[str] = None) -> str:
        """
        Export all data to Excel with multiple sheets
        
        Args:
            filename: Custom filename (optional)
            
        Returns:
            Path to the exported Excel file
        """
        try:
            if not self.session_data:
                self.logger.warning("No data to export")
                return ""
            
            # Generate filename if not provided
            if filename is None:
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                filename = f"pii_analysis_{timestamp}.xlsx"
            
            filepath = os.path.join(self.output_dir, filename)
            
            # Create Excel writer
            with pd.ExcelWriter(filepath, engine='openpyxl') as writer:
                
                # Sheet 1: Detailed Analysis
                self._create_detailed_analysis_sheet(writer)
                
                # Sheet 2: Metrics Comparison
                self._create_metrics_comparison_sheet(writer)
                
                # Sheet 3: Response Analysis
                self._create_response_analysis_sheet(writer)
                
                # Sheet 4: PII Mapping Analysis
                self._create_pii_mapping_sheet(writer)
                
                # Sheet 5: Summary Statistics
                self._create_summary_sheet(writer)
                
                # Sheet 6: Performance Analysis
                self._create_performance_sheet(writer)
            
            self.logger.info(f"Excel file exported successfully: {filepath}")
            return filepath
            
        except Exception as e:
            self.logger.error(f"Error exporting to Excel: {e}")
            return ""
    
    def _create_detailed_analysis_sheet(self, writer: pd.ExcelWriter) -> None:
        """Create detailed analysis sheet with all data"""
        try:
            # Prepare detailed data
            detailed_data = []
            
            for i, record in enumerate(self.session_data, 1):
                detailed_data.append({
                    'Query_ID': i,
                    'Timestamp': record.get('timestamp', ''),
                    'Original_Prompt': record.get('original_prompt', ''),
                    'Real_Response': record.get('real_response', ''),
                    'Fake_Prompt': record.get('fake_prompt', ''),
                    'Fake_Response': record.get('fake_response', ''),
                    'Masked_Prompt': record.get('masked_prompt', ''),
                    'Masked_Response': record.get('masked_response', ''),
                    'LLM_Anonymized_Prompt': record.get('llm_anonymized_prompt', ''),
                    'LLM_Response': record.get('llm_response', ''),
                    'NER_Mapping': str(record.get('ner_mapping', {})),
                    'Mask_Mapping': str(record.get('mask_mapping', {}))
                })
            
            df_detailed = pd.DataFrame(detailed_data)
            df_detailed.to_excel(writer, sheet_name='Detailed_Analysis', index=False)
            
            # Auto-adjust column widths
            worksheet = writer.sheets['Detailed_Analysis']
            for column in df_detailed:
                column_length = max(df_detailed[column].astype(str).map(len).max(), len(column))
                col_letter = chr(65 + df_detailed.columns.get_loc(column))
                worksheet.column_dimensions[col_letter].width = min(column_length + 2, 50)
            
        except Exception as e:
            self.logger.error(f"Error creating detailed analysis sheet: {e}")
    
    def _create_metrics_comparison_sheet(self, writer: pd.ExcelWriter) -> None:
        """Create metrics comparison sheet"""
        try:
            metrics_data = []
            
            for i, record in enumerate(self.session_data, 1):
                metrics_data.append({
                    'Query_ID': i,
                    'Timestamp': record.get('timestamp', ''),
                    'Original_Prompt_Length': len(record.get('original_prompt', '')),
                    
                    # Relevancy Scores
                    'Relevancy_Real': record.get('relevancy_real', 0.0),
                    'Relevancy_Fake': record.get('relevancy_fake', 0.0),
                    'Relevancy_Masked': record.get('relevancy_masked', 0.0),
                    'Relevancy_LLM': record.get('relevancy_llm', 0.0),
                    
                    # Semantic Similarity
                    'Similarity_Real_vs_Fake': record.get('similarity_real_fake', 0.0),
                    'Similarity_Real_vs_Masked': record.get('similarity_real_masked', 0.0),
                    'Similarity_Real_vs_LLM': record.get('similarity_real_llm', 0.0),
                    'Similarity_Fake_vs_Masked': record.get('similarity_fake_masked', 0.0),
                    'Similarity_Fake_vs_LLM': record.get('similarity_fake_llm', 0.0),
                    'Similarity_Masked_vs_LLM': record.get('similarity_mask_llm', 0.0),
                    
                    # PII Leakage Scores
                    'PII_Leakage_Real': record.get('pii_leakage_real', 0),
                    'PII_Leakage_Fake': record.get('pii_leakage_fake', 0),
                    'PII_Leakage_Masked': record.get('pii_leakage_masked', 0),
                    'PII_Leakage_LLM': record.get('pii_leakage_llm', 0),

                    # PII Leakage Rates (PLR)
                    'PII_Leakage_Rate_Real': record.get('pii_leakage_rate_real', 0.0),
                    'PII_Leakage_Rate_Fake': record.get('pii_leakage_rate_fake', 0.0),
                    'PII_Leakage_Rate_Masked': record.get('pii_leakage_rate_masked', 0.0),
                    'PII_Leakage_Rate_LLM': record.get('pii_leakage_rate_llm', 0.0),

                    # PLR Severity Levels
                    'PLR_Severity_Real': record.get('pii_leakage_severity_real', 'UNKNOWN'),
                    'PLR_Severity_Fake': record.get('pii_leakage_severity_fake', 'UNKNOWN'),
                    'PLR_Severity_Masked': record.get('pii_leakage_severity_masked', 'UNKNOWN'),
                    'PLR_Severity_LLM': record.get('pii_leakage_severity_llm', 'UNKNOWN'),

                    # F1 Scores
                    'F1_Score_Real': record.get('f1_real', 0),
                    'F1_Score_Fake': record.get('f1_fake', 0),
                    'F1_Score_Masked': record.get('f1_masked', 0),
                    'F1_Score_LLM': record.get('f1_llm', 0),
                    
                    # Processing Times
                    'Processing_Time_Real': record.get('processing_time_real', 0.0),
                    'Processing_Time_Fake': record.get('processing_time_fake', 0.0),
                    'Processing_Time_Masked': record.get('processing_time_masked', 0.0),
                    'Processing_Time_LLM': record.get('processing_time_llm', 0.0),

                    # Re-identification Risk
                    'ReID_Risk_Real': record.get('reidentification_risk_real', 0.0),
                    'ReID_Risk_Fake': record.get('reidentification_risk_fake', 0.0),
                    'ReID_Risk_Masked': record.get('reidentification_risk_masked', 0.0),
                    'ReID_Risk_LLM': record.get('reidentification_risk_llm', 0.0),

                    'ReID_Risk_Level_Real': record.get('reidentification_risk_level_real', 'UNKNOWN'),
                    'ReID_Risk_Level_Fake': record.get('reidentification_risk_level_fake', 'UNKNOWN'),
                    'ReID_Risk_Level_Masked': record.get('reidentification_risk_level_masked', 'UNKNOWN'),
                    'ReID_Risk_Level_LLM': record.get('reidentification_risk_level_llm', 'UNKNOWN'),

                    # Entropy Scores
                    'Entropy_Score_Real': record.get('entropy_score_real', 0.0),
                    'Entropy_Score_Fake': record.get('entropy_score_fake', 0.0),
                    'Entropy_Score_Masked': record.get('entropy_score_masked', 0.0),
                    'Entropy_Score_LLM': record.get('entropy_score_llm', 0.0),

                    'Entropy_Level_Real': record.get('entropy_level_real', 'UNKNOWN'),
                    'Entropy_Level_Fake': record.get('entropy_level_fake', 'UNKNOWN'),
                    'Entropy_Level_Masked': record.get('entropy_level_masked', 'UNKNOWN'),
                    'Entropy_Level_LLM': record.get('entropy_level_llm', 'UNKNOWN'),

                    # NLP Quality Metrics
                    'BLEU_Score_Real': record.get('bleu_score_real', 0.0),
                    'BLEU_Score_Fake': record.get('bleu_score_fake', 0.0),
                    'BLEU_Score_Masked': record.get('bleu_score_masked', 0.0),
                    'BLEU_Score_LLM': record.get('bleu_score_llm', 0.0),

                    'ROUGE1_Score_Real': record.get('rouge1_real', 0.0),
                    'ROUGE1_Score_Fake': record.get('rouge1_fake', 0.0),
                    'ROUGE1_Score_Masked': record.get('rouge1_masked', 0.0),
                    'ROUGE1_Score_LLM': record.get('rouge1_llm', 0.0),

                    'ROUGE2_Score_Real': record.get('rouge2_real', 0.0),
                    'ROUGE2_Score_Fake': record.get('rouge2_fake', 0.0),
                    'ROUGE2_Score_Masked': record.get('rouge2_masked', 0.0),
                    'ROUGE2_Score_LLM': record.get('rouge2_llm', 0.0),

                    'ROUGEL_Score_Real': record.get('rougel_real', 0.0),
                    'ROUGEL_Score_Fake': record.get('rougel_fake', 0.0),
                    'ROUGEL_Score_Masked': record.get('rougel_masked', 0.0),
                    'ROUGEL_Score_LLM': record.get('rougel_llm', 0.0),

                    'Perplexity_Real': record.get('perplexity_real', float('inf')),
                    'Perplexity_Fake': record.get('perplexity_fake', float('inf')),
                    'Perplexity_Masked': record.get('perplexity_masked', float('inf')),
                    'Perplexity_LLM': record.get('perplexity_llm', float('inf')),

                    'Coherence_Score_Real': record.get('coherence_score_real', 3.0),
                    'Coherence_Score_Fake': record.get('coherence_score_fake', 3.0),
                    'Coherence_Score_Masked': record.get('coherence_score_masked', 3.0),
                    'Coherence_Score_LLM': record.get('coherence_score_llm', 3.0),

                    'Coherence_Level_Real': record.get('coherence_level_real', 'FAIR'),
                    'Coherence_Level_Fake': record.get('coherence_level_fake', 'FAIR'),
                    'Coherence_Level_Masked': record.get('coherence_level_masked', 'FAIR'),
                    'Coherence_Level_LLM': record.get('coherence_level_llm', 'FAIR')
                })
            
            df_metrics = pd.DataFrame(metrics_data)
            df_metrics.to_excel(writer, sheet_name='Metrics_Comparison', index=False)
            
        except Exception as e:
            self.logger.error(f"Error creating metrics comparison sheet: {e}")
    
    def _create_response_analysis_sheet(self, writer: pd.ExcelWriter) -> None:
        """Create response analysis sheet"""
        try:
            response_data = []
            
            for i, record in enumerate(self.session_data, 1):
                response_data.append({
                    'Query_ID': i,
                    'Real_Response_Length': len(record.get('real_response', '')),
                    'Fake_Response_Length': len(record.get('fake_response', '')),
                    'Masked_Response_Length': len(record.get('masked_response', '')),
                    'LLM_Response_Length': len(record.get('llm_response', '')),
                    
                    'Real_Word_Count': len(record.get('real_response', '').split()),
                    'Fake_Word_Count': len(record.get('fake_response', '').split()),
                    'Masked_Word_Count': len(record.get('masked_response', '').split()),
                    'LLM_Word_Count': len(record.get('llm_response', '').split()),
                    
                    'Entities_Detected': record.get('entities_detected', 0),
                    'Entities_Replaced_Fake': len(record.get('ner_mapping', {})),
                    'Entities_Masked': len(record.get('mask_mapping', {}))
                })
            
            df_response = pd.DataFrame(response_data)
            df_response.to_excel(writer, sheet_name='Response_Analysis', index=False)
            
        except Exception as e:
            self.logger.error(f"Error creating response analysis sheet: {e}")
    
    def _create_pii_mapping_sheet(self, writer: pd.ExcelWriter) -> None:
        """Create PII mapping analysis sheet"""
        try:
            pii_data = []
            
            for i, record in enumerate(self.session_data, 1):
                ner_mapping = record.get('ner_mapping', {})
                mask_mapping = record.get('mask_mapping', {})
                
                # Add each mapping as a separate row
                for fake_entity, real_entity in ner_mapping.items():
                    pii_data.append({
                        'Query_ID': i,
                        'Mapping_Type': 'Fake_Replacement',
                        'Original_Entity': real_entity,
                        'Replaced_With': fake_entity,
                        'Entity_Type': 'Auto_Detected'
                    })
                
                for mask_key, real_entity in mask_mapping.items():
                    pii_data.append({
                        'Query_ID': i,
                        'Mapping_Type': 'XXXX_Masking',
                        'Original_Entity': real_entity,
                        'Replaced_With': mask_key,
                        'Entity_Type': 'Auto_Detected'
                    })
            
            if pii_data:
                df_pii = pd.DataFrame(pii_data)
                df_pii.to_excel(writer, sheet_name='PII_Mappings', index=False)
            
        except Exception as e:
            self.logger.error(f"Error creating PII mapping sheet: {e}")
    
    def _create_summary_sheet(self, writer: pd.ExcelWriter) -> None:
        """Create summary statistics sheet"""
        try:
            summary_data = [
                ['Metric', 'Value'],
                ['Total Queries Processed', self.summary_stats['total_queries']],
                ['', ''],
                ['Average Relevancy Scores', ''],
                ['Real Names', f"{self.summary_stats['avg_relevancy_real']:.3f}"],
                ['Fake Names', f"{self.summary_stats['avg_relevancy_fake']:.3f}"],
                ['XXXX Masking', f"{self.summary_stats['avg_relevancy_masked']:.3f}"],
                ['LLM-based PII Removal', f"{self.summary_stats['avg_relevancy_llm']:.3f}"],
                ['', ''],
                ['Average Semantic Similarity', ''],
                ['Real vs Fake', f"{self.summary_stats['avg_similarity_real_fake']:.3f}"],
                ['Real vs Masked', f"{self.summary_stats['avg_similarity_real_masked']:.3f}"],
                ['Real vs LLM', f"{self.summary_stats['avg_similarity_real_llm']:.3f}"],
                ['', ''],
                ['Average Processing Times (seconds)', ''],
                ['Real Names', f"{self.summary_stats['avg_processing_time_real']:.3f}"],
                ['Fake Names', f"{self.summary_stats['avg_processing_time_fake']:.3f}"],
                ['XXXX Masking', f"{self.summary_stats['avg_processing_time_masked']:.3f}"],
                ['LLM-based PII Removal', f"{self.summary_stats['avg_processing_time_llm']:.3f}"],
                ['', ''],
                ['Average PII Leakage Rate (PLR) (%)', ''],
                ['Real Names', f"{self.summary_stats['avg_pii_leakage_rate_real']:.1f}%"],
                ['Fake Names', f"{self.summary_stats['avg_pii_leakage_rate_fake']:.1f}%"],
                ['XXXX Masking', f"{self.summary_stats['avg_pii_leakage_rate_masked']:.1f}%"],
                ['LLM-based PII Removal', f"{self.summary_stats['avg_pii_leakage_rate_llm']:.1f}%"],
                ['', ''],
                ['Average Re-identification Risk (%)', ''],
                ['Real Names', f"{self.summary_stats['avg_reidentification_risk_real']:.1f}%"],
                ['Fake Names', f"{self.summary_stats['avg_reidentification_risk_fake']:.1f}%"],
                ['XXXX Masking', f"{self.summary_stats['avg_reidentification_risk_masked']:.1f}%"],
                ['LLM-based PII Removal', f"{self.summary_stats['avg_reidentification_risk_llm']:.1f}%"],
                ['', ''],
                ['Average Entropy Score (Unpredictability)', ''],
                ['Real Names', f"{self.summary_stats['avg_entropy_score_real']:.1f}"],
                ['Fake Names', f"{self.summary_stats['avg_entropy_score_fake']:.1f}"],
                ['XXXX Masking', f"{self.summary_stats['avg_entropy_score_masked']:.1f}"],
                ['LLM-based PII Removal', f"{self.summary_stats['avg_entropy_score_llm']:.1f}"],
                ['', ''],
                ['Average BLEU Score', ''],
                ['Real Names', f"{self.summary_stats['avg_bleu_score_real']:.3f}"],
                ['Fake Names', f"{self.summary_stats['avg_bleu_score_fake']:.3f}"],
                ['XXXX Masking', f"{self.summary_stats['avg_bleu_score_masked']:.3f}"],
                ['LLM-based PII Removal', f"{self.summary_stats['avg_bleu_score_llm']:.3f}"],
                ['', ''],
                ['Average ROUGE-1 Score', ''],
                ['Real Names', f"{self.summary_stats['avg_rouge1_real']:.3f}"],
                ['Fake Names', f"{self.summary_stats['avg_rouge1_fake']:.3f}"],
                ['XXXX Masking', f"{self.summary_stats['avg_rouge1_masked']:.3f}"],
                ['LLM-based PII Removal', f"{self.summary_stats['avg_rouge1_llm']:.3f}"],
                ['', ''],
                ['Average Coherence Score (1-5)', ''],
                ['Real Names', f"{self.summary_stats['avg_coherence_score_real']:.1f}"],
                ['Fake Names', f"{self.summary_stats['avg_coherence_score_fake']:.1f}"],
                ['XXXX Masking', f"{self.summary_stats['avg_coherence_score_masked']:.1f}"],
                ['LLM-based PII Removal', f"{self.summary_stats['avg_coherence_score_llm']:.1f}"],
                ['', ''],
                ['Export Information', ''],
                ['Export Date', datetime.now().strftime('%Y-%m-%d %H:%M:%S')],
                ['Total Records', len(self.session_data)]
            ]
            
            df_summary = pd.DataFrame(summary_data[1:], columns=summary_data[0])
            df_summary.to_excel(writer, sheet_name='Summary_Statistics', index=False)
            
        except Exception as e:
            self.logger.error(f"Error creating summary sheet: {e}")
    
    def _create_performance_sheet(self, writer: pd.ExcelWriter) -> None:
        """Create performance analysis sheet"""
        try:
            if not self.session_data:
                return
            
            # Calculate performance metrics
            performance_data = []
            
            for i, record in enumerate(self.session_data, 1):
                # Calculate efficiency scores (relevancy per second)
                real_efficiency = record.get('relevancy_real', 0) / max(record.get('processing_time_real', 0.001), 0.001)
                fake_efficiency = record.get('relevancy_fake', 0) / max(record.get('processing_time_fake', 0.001), 0.001)
                masked_efficiency = record.get('relevancy_masked', 0) / max(record.get('processing_time_masked', 0.001), 0.001)
                llm_efficiency = record.get('relevancy_llm', 0) / max(record.get('processing_time_llm', 0.001), 0.001)
                
                performance_data.append({
                    'Query_ID': i,
                    'Real_Efficiency_Score': real_efficiency,
                    'Fake_Efficiency_Score': fake_efficiency,
                    'Masked_Efficiency_Score': masked_efficiency,
                    'LLM_Efficiency_Score': llm_efficiency,
                    
                    'Best_Relevancy_Method': max([
                        ('Real', record.get('relevancy_real', 0)),
                        ('Fake', record.get('relevancy_fake', 0)),
                        ('Masked', record.get('relevancy_masked', 0)),
                        ('LLM', record.get('relevancy_llm', 0))
                    ], key=lambda x: x[1])[0],
                    
                    'Fastest_Method': min([
                        ('Real', record.get('processing_time_real', float('inf'))),
                        ('Fake', record.get('processing_time_fake', float('inf'))),
                        ('Masked', record.get('processing_time_masked', float('inf'))),
                        ('LLM', record.get('processing_time_llm', float('inf')))
                    ], key=lambda x: x[1])[0],
                    
                    'Privacy_Score_Fake': record.get('f1_fake', 0),
                    'Privacy_Score_Masked': record.get('f1_masked', 0),
                    'Privacy_Score_LLM': record.get('f1_llm', 0)
                })
            
            df_performance = pd.DataFrame(performance_data)
            df_performance.to_excel(writer, sheet_name='Performance_Analysis', index=False)
            
        except Exception as e:
            self.logger.error(f"Error creating performance sheet: {e}")
    
    def get_current_stats(self) -> Dict[str, Any]:
        """Get current summary statistics"""
        return self.summary_stats.copy()
    
    def clear_data(self) -> None:
        """Clear all stored data"""
        self.session_data.clear()
        self.summary_stats = {
            'total_queries': 0,
            'avg_relevancy_real': 0.0,
            'avg_relevancy_fake': 0.0,
            'avg_relevancy_masked': 0.0,
            'avg_relevancy_llm': 0.0,
            'avg_similarity_real_fake': 0.0,
            'avg_similarity_real_masked': 0.0,
            'avg_similarity_real_llm': 0.0,
            'avg_processing_time_real': 0.0,
            'avg_processing_time_fake': 0.0,
            'avg_processing_time_masked': 0.0,
            'avg_processing_time_llm': 0.0,
            'avg_pii_leakage_rate_real': 0.0,
            'avg_pii_leakage_rate_fake': 0.0,
            'avg_pii_leakage_rate_masked': 0.0,
            'avg_pii_leakage_rate_llm': 0.0,
            'avg_reidentification_risk_real': 0.0,
            'avg_reidentification_risk_fake': 0.0,
            'avg_reidentification_risk_masked': 0.0,
            'avg_reidentification_risk_llm': 0.0,
            'avg_entropy_score_real': 0.0,
            'avg_entropy_score_fake': 0.0,
            'avg_entropy_score_masked': 0.0,
            'avg_entropy_score_llm': 0.0,
            'avg_bleu_score_real': 0.0,
            'avg_bleu_score_fake': 0.0,
            'avg_bleu_score_masked': 0.0,
            'avg_bleu_score_llm': 0.0,
            'avg_rouge1_real': 0.0,
            'avg_rouge1_fake': 0.0,
            'avg_rouge1_masked': 0.0,
            'avg_rouge1_llm': 0.0,
            'avg_rouge2_real': 0.0,
            'avg_rouge2_fake': 0.0,
            'avg_rouge2_masked': 0.0,
            'avg_rouge2_llm': 0.0,
            'avg_rougel_real': 0.0,
            'avg_rougel_fake': 0.0,
            'avg_rougel_masked': 0.0,
            'avg_rougel_llm': 0.0,
            'avg_coherence_score_real': 0.0,
            'avg_coherence_score_fake': 0.0,
            'avg_coherence_score_masked': 0.0,
            'avg_coherence_score_llm': 0.0
        }
        self.logger.info("All data cleared")

# Example usage and testing
if __name__ == "__main__":
    # Test the exporter
    exporter = PIIAnalysisExporter()
    
    # Add sample data
    sample_data = {
        'original_prompt': 'Hello, my name is John Doe and I work at Microsoft.',
        'real_response': 'Hello John Doe! It\'s nice to meet someone from Microsoft.',
        'fake_prompt': 'Hello, my name is Jane Smith and I work at Google.',
        'fake_response': 'Hello Jane Smith! It\'s nice to meet someone from Google.',
        'masked_prompt': 'Hello, my name is XXXX and I work at XXXX.',
        'masked_response': 'Hello! It\'s nice to meet you.',
        'llm_anonymized_prompt': 'Hello, my name is [PERSON] and I work at [ORGANIZATION].',
        'llm_response': 'Hello! It\'s nice to meet you.',
        'ner_mapping': {'Jane Smith': 'John Doe', 'Google': 'Microsoft'},
        'mask_mapping': {'XXXX': 'John Doe, Microsoft'},
        'relevancy_real': 0.85,
        'relevancy_fake': 0.82,
        'relevancy_masked': 0.65,
        'relevancy_llm': 0.78,
        'similarity_real_fake': 0.92,
        'similarity_real_masked': 0.75,
        'similarity_real_llm': 0.88,
        'similarity_fake_masked': 0.73,
        'similarity_fake_llm': 0.86,
        'similarity_mask_llm': 0.82,
        'processing_time_real': 1.2,
        'processing_time_fake': 2.8,
        'processing_time_masked': 1.5,
        'processing_time_llm': 3.1,
        'pii_leakage_real': 2,
        'pii_leakage_fake': 0,
        'pii_leakage_masked': 0,
        'pii_leakage_llm': 0,
        'f1_real': 0,
        'f1_fake': 1,
        'f1_masked': 1,
        'f1_llm': 1,
        'entities_detected': 2
    }
    
    exporter.add_analysis_record(sample_data)
    
    # Export to Excel
    filepath = exporter.export_to_excel('test_export.xlsx')
    print(f"Test export created: {filepath}")