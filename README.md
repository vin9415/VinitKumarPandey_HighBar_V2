# 🧠 Kasparro Agentic FB Analyst — Multi-Agent AI Marketing Analytics System

### **Author:** Vinit Kumar Pandey  
### **GitHub:** https://github.com/vin9415/kasparro-agentic-fb-analyst-vinitkumarpandey  
### **Tech Stack:** Python, Pandas, Multi-Agent Architecture, Data Analytics

---

## 🚀 Project Overview

Kasparro Agentic FB Analyst is a fully functional **Multi-Agent AI System** designed to automate Facebook Ads performance analysis. It loads real advertising data, computes important marketing KPIs, generates insights, and produces human-like recommendations.

This project demonstrates:

- Multi-Agent modular design  
- Real dataset ingestion (4500 rows)  
- Automated marketing analysis  
- Executive summary generation  
- Evaluation scoring  
- Orchestrator-driven workflow  

---

## 📂 Folder Structure

```
kasparroagenticfbanalystvinit/
│
├── run.py
├── README.md
│
├── data/
│   └── sample_ads.csv
│
└── src/
    ├── agents/
    │   ├── planner.py
    │   ├── data_agent.py
    │   ├── insight_agent.py
    │   ├── creative_agent.py
    │   └── evaluator_agent.py
    │
    ├── orchestrator/
    │   └── orchestrator.py
    │
    └── utils/
        └── logger.py
```

---

## 🧠 Agent Architecture

### **1️⃣ Planner Agent**
Breaks the user instruction into a clear plan:
- Understand task  
- Load data  
- Analyze metrics  
- Generate insights  
- Produce report  

---

### **2️⃣ Data Agent**
Loads real marketing data from:

```
data/sample_ads.csv
```

Dataset details:
- **4500 rows**
- **15 columns**
- Includes spend, revenue, ROAS, CTR, country, platform, creative type, etc.

---

### **3️⃣ Insight Agent**
Performs advanced computations:

- Total Spend  
- Total Revenue  
- Total Purchases  
- Average CTR  
- Average ROAS  
- Best Creative Type  
- Best Platform  
- Best Country  
- Highest Revenue Day  
- Highest ROAS Day  
- Best Audience Type  
- Best Adset  

---

### **4️⃣ Creative Agent**
Creates a clean, human-friendly **executive summary**, including:

- KPI overview  
- Best performers  
- Recommendations  
- Planner steps  

---

### **5️⃣ Evaluator Agent**
Scores system output based on:

- Completeness  
- Insight coverage  
- Data availability  

Final score in testing: **100/100**

---

### **6️⃣ Orchestrator**
Controls entire pipeline:

- Executes Planner → Data → Insight → Creative → Evaluation  
- Returns final output dictionary  

---

## 🏃 How to Run

### **1. Install dependencies**

```
pip install pandas
```

(optional: create requirements.txt)

### **2. Run the project**

```
cd kasparroagenticfbanalystvinit
python run.py
```

---

## 📊 Example Output (Real Analytics)

```
Total Spend: $2,105,579.9
Total Revenue: $12,265,700.71
Total Purchases: 341,144
Average CTR: 0.0131
Average ROAS: 9.6151

Top Platform: Facebook
Top Country: US
Best Creative Type: UGC
Best Audience Type: Broad
Best Adset: Adset-5 Broad

Highest Revenue Day: 2025-01-13
Highest ROAS Day: 2025-03-02
```

---

## 🎯 Recommendations (Auto-Generated)

- Scale budget on **Facebook** for highest purchase volume.  
- Increase use of **UGC creatives** for best ROAS.  
- Expand ads in **US** (highest revenue).  
- Allocate more spend to **Broad audiences**.  
- Use learnings from **Adset-5 Broad** to optimize weaker adsets.  

---

## 💡 Why This Project Is Industry-Level?

- Multi-agent design  
- Clean modular Python architecture  
- Real dataset used  
- Professional analytics output  
- Logging enabled  
- Expandable (ML, dashboards, APIs)  
- Works end-to-end automatically  

---

## 👨‍💻 Author

**Vinit Kumar Pandey**  
B.Tech CSE  
Data Science Enthusiast  
Python | Machine Learning | AI | Full Stack Learner  

GitHub: https://github.com/vin9415

---

## ⭐ Support

If you like this project, please **star the repository**!

