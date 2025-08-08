import pandas as pd
from datetime import datetime, timedelta

# Start date for Week 1
start_date = datetime(2025, 7, 21)

# Task schedule: (Task Name, Week Offset, Duration in Weeks)
schedule = [
    ("Milestone 1: Research Proposal", 0, 4),
    ("Week 1", 0, 1),
    ("Week 2", 1, 1),
    ("Week 3", 2, 1),
    ("Week 4", 3, 1),
    ("Milestone 2: Interim Report", 5, 6),
    ("Week 6", 5, 1),
    ("Week 7", 6, 1),
    ("Week 8", 7, 1),
    ("Week 9", 8, 1),
    ("Week 10", 9, 1),
    ("Week 11", 10, 1),
    ("Milestone 3: Final Thesis & Video", 12, 8),
    ("Week 13", 12, 1),
    ("Week 14", 13, 1),
    ("Week 15", 14, 1),
    ("Week 16", 15, 1),
    ("Week 17", 16, 1),
    ("Week 18", 17, 1),
    ("Week 19", 18, 1),
    ("Week 20", 19, 1),
]

# Build DataFrame
data = []
for task, offset, duration in schedule:
    start = start_date + timedelta(weeks=offset)
    data.append({
        "Task": task,
        "Start Date": start,
        "Duration (Days)": duration * 7,
        "Start Offset (Days)": (start - start_date).days
    })

df = pd.DataFrame(data)

# Export to Excel with Gantt chart
with pd.ExcelWriter("Gantt_Chart_Template.xlsx", engine="xlsxwriter") as writer:
    df.to_excel(writer, sheet_name="Gantt Data", index=False)
    workbook = writer.book
    worksheet = writer.sheets["Gantt Data"]

    # Create stacked bar chart
    chart = workbook.add_chart({'type': 'bar', 'subtype': 'stacked'})
    chart.add_series({
        'name': 'Start Offset',
        'categories': ['Gantt Data', 1, 0, len(df), 0],
        'values':     ['Gantt Data', 1, 3, len(df), 3],
        'fill':       {'none': True}
    })
    chart.add_series({
        'name': 'Duration',
        'categories': ['Gantt Data', 1, 0, len(df), 0],
        'values':     ['Gantt Data', 1, 2, len(df), 2],
        'fill':       {'color': '#4F81BD'}
    })
    chart.set_title({'name': 'Gantt Chart'})
    chart.set_x_axis({'name': 'Days'})
    chart.set_y_axis({'reverse': True})
    worksheet.insert_chart('F2', chart)
