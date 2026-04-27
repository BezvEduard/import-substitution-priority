# Project Context: Import Substitution Prioritization System

## 1. Project Overview
This project is a bachelor thesis (ВКР) focused on developing an information system for prioritizing product categories for import substitution based on foreign trade statistics of Russia.

The system processes statistical data (import/export) and calculates a priority ranking of product groups.

Core output:
- Priority score (S_i)
- Ranked list of product groups (TNVED)

---

## 2. Problem Statement
Government resources for import substitution are limited.
A data-driven method is required to:
- objectively compare product groups
- identify high-priority categories for import substitution

---

## 3. Data Description

Input dataset fields:
- Import_Export: ["Import", "Export"]
- Year: integer (2022–2025)
- Month: string
- TNVED: product code
- Country: string
- US_dollars: float

Data is aggregated to yearly level before calculations.

---

## 4. Model Description (MAIN LOGIC)

The system uses a multi-criteria decision model:

Method:
- AHP → for weights
- Weighted Sum Model (WSM) → for aggregation

Final score:

S_i = Σ (w_j * C'_ij)

Where:
- w_j = weight of criterion j
- C'_ij = normalized value of criterion j for product i

All criteria are:
- normalized to [0, 1]
- direction: "higher = higher priority"

---

## 5. Criteria (MODEL 2 — CURRENT VERSION)

### C1: Import Share (scale of dependency)
C1_i = I_i / I_total

### C2: Import Growth (dynamics)
C2_i = ln((I_i + ε) / (I_i_prev + ε))

### C3: Import vs Trade Ratio
C3_i = I_i / (I_i + E_i + ε)

### C4: Supplier Concentration (HHI)
C4_i = Σ_k (s_ik^2)

Where:
- s_ik = I_ik / I_i

---

## 6. Data Processing Pipeline

1. Load data
2. Aggregate by:
   - TNVED
   - Year
3. Calculate:
   - Import (I_i)
   - Export (E_i)

4. Compute criteria C1–C4

5. Clipping (optional):
   - none
   - 1–99 percentile
   - 5–95 percentile

6. Normalization:
   - Min-Max scaling → [0,1]

7. Apply weights (AHP or manual)

8. Compute final score S_i

9. Rank product groups

---

## 7. System Architecture

Type:
- Desktop analytical application

Modules:
- Data Loader (CSV/Excel)
- Data Processing
- Criteria Calculation
- Normalization & Clipping
- Model Calculation
- Visualization
- Export (Excel)

No database required (in-memory processing).

---

## 8. Tech Stack

- Python
- pandas
- numpy
- matplotlib
- tkinter (UI)

---

## 9. Functional Requirements

- Load dataset
- Calculate criteria
- Configure:
  - weights
  - clipping mode
- Compute ranking
- Visualize results
- Export results to Excel

---

## 10. Non-Functional Requirements

- Response time < 2 seconds
- Stable execution (no crashes)
- Clear and reproducible calculations

---

## 11. Coding Guidelines for AI

IMPORTANT:

- Do NOT invent new criteria
- Do NOT change formulas
- Always follow Model 2
- Keep functions modular:
  - compute_import_share()
  - compute_growth()
  - compute_ratio()
  - compute_hhi()

- Use pandas DataFrame as main structure
- Avoid over-engineering

---

## 12. Expected Output Format

DataFrame columns:

- TNVED
- Year
- C1, C2, C3, C4
- normalized_C1 ... normalized_C4
- Score
- Rank

---

## 13. Key Constraints

- Work only with available data (no external sources)
- No ML models required
- Focus on interpretability

---

## 14. Goal for AI Assistant (Codex)

When generating code:
- prioritize clarity over complexity
- ensure formulas are correct
- produce reproducible calculations
- keep code aligned with this document

If something is unclear — ask, do NOT assume
