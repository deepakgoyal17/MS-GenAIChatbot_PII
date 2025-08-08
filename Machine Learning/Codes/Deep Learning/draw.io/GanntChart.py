from datetime import datetime, timedelta
import pandas as pd

# Start date for Week 1
start_date = datetime(2025, 7, 21)

# Task list (task name, description, week offset, duration in weeks)
schedule = [
    ("Milestone 1: Research Proposal", "Background, Problem Statement, Literature review, etc.", 0, 4),
    ("Week 1", "Background, Problem Statement, Literature review, Hypothesis formulation, Clarifications", 0, 1),
    ("Week 2", "Finalize research questions, Aims and Objectives, Significance, Scope, Clarifications", 1, 1),
    ("Week 3", "Research Methodology, Resources, Evaluation metrics, Clarifications", 2, 1),
    ("Week 4", "Title, Research plan, References, Proposal template, Supervisor sign-off, Submit", 3, 1),
    ("Milestone 2: Interim Report", "Design, Data collection, Model setup, Architecture, Reporting", 5, 6),
    ("Week 6", "Literature review, Design & Data collection", 5, 1),
    ("Week 7", "NER model decision, Define PII categories, Setup, Pre-processing", 6, 1),
    ("Week 8", "Plan architecture integration, Create diagrams", 7, 1),
    ("Week 9", "Code setup, LLM subscriptions, Key component experiments", 8, 1),
    ("Week 10", "Experimental results, Write Interim report, Supervisor review", 9, 1),
    ("Week 11", "Refine and submit Interim report", 10, 1),
    ("Milestone 3: Final Thesis & Video", "Analysis, Modeling, Evaluation, Writing, Submission", 12, 8),
    ("Week 13", "Literature review, Data analysis and interpretation", 12, 1),
    ("Week 14", "Train/fine-tune NER model, Impact statement, Refine results, Supervisor clarifications", 13, 1),
    ("Week 15", "Refine evaluation metrics, Propose best architecture", 14, 1),
    ("Week 16", "Write and disseminate findings, Supervisor clarifications", 15, 1),
    ("Week 17", "Write and disseminate findings", 16, 1),
    ("Week 18", "Discussion, Future work, Writing, Supervisor clarifications", 17, 1),
    ("Week 19", "Review final report, Prepare video", 18, 1),
    ("Week 20", "Refine final report, Supervisor sign-off, Submit final report and video", 19, 1),
]

# Build the Gantt chart data
gantt_data = []

for task_name, description, week_offset, duration_weeks in schedule:
    task_start = start_date + timedelta(weeks=week_offset)
    task_end = task_start + timedelta(weeks=duration_weeks) - timedelta(days=1)
    gantt_data.append({
        "Task": task_name,
        "Description": description,
        "Start": task_start.strftime("%Y-%m-%d"),
        "End": task_end.strftime("%Y-%m-%d"),
        "Duration (weeks)": duration_weeks
    })

# Convert to DataFrame
df_gantt = pd.DataFrame(gantt_data)

# Save to Excel
df_gantt.to_excel("Gantt_Schedule.xlsx", index=False)
