import pandas as pd

# Create data for the enhanced decision matrix
data = {
    "Activity": [
        "ETL Monitoring",
        "Infrastructure Monitoring",
        "User Query Resolution",
        "Incident Management",
        "Change Management / Deployments",
        "Report Validation / QA",
        "Business Communication",
        "Risk & Compliance Checks",
        "Shift Handover & Coordination"
    ],
    "India Shift": [
        "✅ High",
        "✅ High",
        "⚠️ Medium",
        "✅ High",
        "⚠️ Medium",
        "⚠️ Early hours",
        "❌ Low",
        "✅ High",
        "✅ Shared"
    ],
    "UK Shift": [
        "❌ Low",
        "✅ High",
        "✅ High",
        "✅ High",
        "✅ High",
        "✅ Core hours",
        "✅ High",
        "⚠️ Low",
        "✅ Shared"
    ],
    "Workload Impact": [
        "🔴 High",
        "🟠 Medium",
        "🔴 High",
        "🔴 High",
        "🟡 Low–Medium",
        "🟠 Medium",
        "🟡 Low–Medium",
        "🟢 Low",
        "🟢 Low"
    ],
    "Recommended Staffing Basis": [
        "2 people in India shift for overnight batch & job monitoring",
        "1 person per shift for system alerts, dashboards",
        "2–3 in UK shift (depending on query volume); 1 in India for follow-ups",
        "2 per shift, with one experienced incident owner in each",
        "1 in India (for pre-checks), 1–2 in UK for deployment coordination",
        "1 in India (early QA), 1–2 in UK (for user-facing validation)",
        "1–2 in UK shift to interface with business users",
        "1 in India shift (e.g., checklist, backup validation)",
        "0.5 FTE in each shift for 30-min overlap and documentation"
    ]
}

# Create DataFrame
df = pd.DataFrame(data)

# Save to Excel
df.to_excel("Production_Support_Shift_Staffing_Matrix.xlsx", index=False)
