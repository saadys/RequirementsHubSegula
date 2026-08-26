# 🧪 Segula AI Requirement Hub — Comprehensive 20 Test Cases (Suite V2)

This test suite is designed to rigorously evaluate the full end-to-end pipeline logic of the **AI Requirement Hub**, covering:
1. **Department Scope Vetoes (`UNRELATED` vs `PARTIALLY_RELEVANT` vs `RELEVANT`)**
2. **5-Pillar Deterministic Rubrics (AI Viability, Data Readiness, Problem Clarity, Integration, Governance)**
3. **Circuit Breaker Vetoes (`NOT_AI`, `CRITICAL_RISK`, `CONTRADICTORY`, `NO_DATA`)**
4. **Multi-Turn Clarification Loops & Fast-Track Prior Art Matching**

---

## 📋 Summary Matrix of All 20 Test Cases

| Case | Title | Department / Function | Expected Decision | Expected Score | Key Validation Point |
| :---: | :--- | :--- | :---: | :---: | :--- |
| **1** | Supplier Invoice OCR & Line-Item Matcher | Finance & Procurement | 🟢 **GO** | 90 - 95 | Clean RAG + Vision Extraction |
| **2** | New Hire Onboarding & Policy Assistant | HR & Training | 🟢 **GO / FAST-TRACK** | 90 - 95 | High similarity to `IRFANE Chatbot` |
| **3** | Automotive Chassis Structural Optimization | **Automotive Engineering** | 🔴 **NO_GO (VETO)** | ≤ 10 | **Department Scope VETO** (`UNRELATED`) |
| **4** | Medical MRI Cancer Lesion Detector | **Healthcare / Medical** | 🔴 **NO_GO (VETO)** | ≤ 10 | **Department Scope VETO** (`UNRELATED`) |
| **5** | Mechanical Engineering Candidate Matcher | HR & Recruitment | 🟢 **GO** | 88 - 94 | **`PARTIALLY_RELEVANT`** (In-scope HR handling eng data) |
| **6** | Automotive Part Supplier Price Anomaly Radar | Procurement & Achats | 🟢 **GO** | 85 - 92 | **`PARTIALLY_RELEVANT`** (In-scope Procurement handling auto data) |
| **7** | Employee Burnout & Daily Email Surveillance | HR & Management | 🔴 **NO_GO (VETO)** | ≤ 10 | **Ethical/Security VETO** (GDPR Critical Risk) |
| **8** | Excel Macro to CSV Date Formatter | General Administration | 🔴 **NO_GO (VETO)** | ≤ 18 | **AI Viability VETO** (`NOT_AI`) |
| **9** | ECU Firmware CAN-Bus Real-Time Tester | **Embedded Systems** | 🔴 **NO_GO (VETO)** | ≤ 10 | **Department Scope VETO** (`UNRELATED`) |
| **10** | Legal Contract Liability Clause Reviewer | Legal & Compliance | 🟡 **CLARIFY** | 45 - 55 | `data_readiness` is `UNLABELED_OR_MESSY` |
| **11** | IT L1 Helpdesk Ticket Triage & Resolver | IT Support & Infrastructure | 🟢 **GO** | 88 - 95 | Standard Tool-Calling & IT Service Management |
| **12** | Virtual Crash Simulation Mesh Generator | **Simulation & Testing** | 🔴 **NO_GO (VETO)** | ≤ 10 | **Department Scope VETO** (`UNRELATED`) |
| **13** | Autonomous 0-Error Legal Redlining System | Legal & Compliance | 🔴 **NO_GO (VETO)** | ≤ 45 | **Contradiction VETO** (100% autonomous + zero errors) |
| **14** | Company Knowledge Base Document Indexer | Document Eng. & KM | 🟢 **GO** | 88 - 95 | Vector Search + Document RAG |
| **15** | Internal IT Security Phishing Campaign Bot | IT / Rogue Request | 🔴 **NO_GO (VETO)** | ≤ 10 | **Ethical/Security VETO** (Malicious tool) |
| **16** | Corporate Travel & Expense Fraud Detector | Finance & Controlling | 🟢 **GO** | 85 - 92 | Tabular Anomaly Detection & ERP Integration |
| **17** | Global Stock Market & Crypto Crystal Ball | Finance & Investment | 🔴 **NO_GO (VETO)** | ≤ 15 | **AI Viability VETO** (`IMPOSSIBLE` / Chaos theory) |
| **18** | Multi-Site Facility Energy & HVAC Optimizer | General Administration | 🟢 **GO** | 80 - 90 | IoT Time-Series Forecasting & Building Management |
| **19** | Generic "Smart AI Innovation Strategy" | General Administration | 🟡 **CLARIFY** | 20 - 35 | `problem_clarity` is `VAGUE` (Buzzword proposal) |
| **20** | Internal Comms Newsletter & Speech Draft Bot | Corporate Communication | 🟢 **GO** | 85 - 95 | Generative Copywriting with Human Approval |

---

### 🟢 Case 1: Supplier Invoice OCR & Purchase Order Reconciliation
* **Domain:** Finance & Controlling (In-Scope)
* **Goal:** Test a high-value, data-ready document extraction task.

```json
{
  "project_name": "Supplier Invoice OCR & Purchase Order Reconciliation",
  "department": "corporate_support",
  "team_contact_name": "Sarah Miller",
  "team_contact_email": "s.miller@segula.fr",
  "problem_description": "Accounts payable receives 1,200 PDF invoices monthly. Two accountants manually compare invoice line items against SAP ERP purchase orders, taking ~35 hours per week with a 4% human error rate.",
  "current_process": "Accountants manually open each PDF, check vendor VAT, match line items with SAP table ME23N, and flag discrepancies by email.",
  "expected_outcome": "Automated OCR extraction and fuzzy line-item matching against SAP POs, automatically validating invoices under 5,000€ and flagging mismatches for human review.",
  "data_description": "3 years of historical PDF invoices (36,000 files) with corresponding SAP ERP transactional settlement logs and discrepancy tags in SQL database.",
  "deadline_urgency": "high",
  "department_specific": {
    "service_area": "finance",
    "target_users": "employees",
    "estimated_user_count": "10-50",
    "has_existing_system": true
  }
}
```
* **Expected AI Hub Output:**
  * **Department Relevance:** `RELEVANT`
  * **Decision:** `GO`
  * **Score:** `88 - 95 / 100`
  * **Technique:** `OCR + Vision/LLM Document Parsing + Fuzzy Entity Matching`

---

### 🟢 Case 2: New Hire Onboarding & HR Policy Assistant (Prior Art Match)
* **Domain:** HR & Training (In-Scope)
* **Goal:** Test semantic match against `IRFANE Chatbot` historical repository.

```json
{
  "project_name": "Segula Knowledge Hub & Onboarding Assistant",
  "department": "corporate_support",
  "team_contact_name": "Karim Bennani",
  "team_contact_email": "k.bennani@segula.fr",
  "problem_description": "New engineers and support staff spend over 2 hours a day searching through scattered internal PDF onboarding guides, technical standards, and HR policies across SharePoint folders.",
  "current_process": "Employees ask senior colleagues or manually navigate complex SharePoint folder hierarchies.",
  "expected_outcome": "A conversational RAG assistant that answers HR and company operational questions with direct source citations from verified internal PDF documents.",
  "data_description": "350 structured PDF and Markdown documents from internal HR and engineering onboarding repositories.",
  "deadline_urgency": "medium",
  "department_specific": {
    "service_area": "hr",
    "target_users": "employees",
    "estimated_user_count": "200+",
    "has_existing_system": false
  }
}
```
* **Expected AI Hub Output:**
  * **Department Relevance:** `RELEVANT`
  * **Decision:** `GO` or `FAST_TRACK`
  * **Score:** `90 - 95 / 100`
  * **RAG Prior Art:** Matches `IRFANE Chatbot` (>75% similarity)

---

### 🔴 Case 3: Automotive Chassis Structural FEA Optimization (Scope Veto)
* **Domain:** Automotive Engineering (Out-of-Scope for Corporate Support)
* **Goal:** Test that pure vehicle engineering requests are vetoed immediately under Corporate Support.

```json
{
  "project_name": "AI-Driven Vehicle Chassis Topology Optimization",
  "department": "corporate_support",
  "team_contact_name": "Antoine Dupont",
  "team_contact_email": "a.dupont@segula.fr",
  "problem_description": "Mechanical engineers want a deep learning surrogate model to predict structural stress and deformation in automotive chassis frames instead of running 6-hour finite element simulations (FEA).",
  "current_process": "Engineers run ANSYS/Abaqus mesh solvers on high-performance compute clusters.",
  "expected_outcome": "3D Graph Neural Network that estimates Von Mises stress in 30 seconds for CAD iterations.",
  "data_description": "10,000 previous ANSYS simulation mesh files (.cdb) and CAD STEP models stored on high-performance NAS.",
  "deadline_urgency": "medium",
  "department_specific": {
    "service_area": "other",
    "target_users": "employees",
    "estimated_user_count": "10-50",
    "has_existing_system": true
  }
}
```
* **Expected AI Hub Output:**
  * **Department Relevance:** `UNRELATED`
  * **Decision:** `NO_GO`
  * **Score:** `≤ 10 / 100`
  * **Veto Alert:** `Department Scope VETO: This request does not belong to Corporate & Support Services. Please select the Automotive Engineering department.`

---

### 🔴 Case 4: Medical MRI Brain Lesion Classification (Domain Scope Veto)
* **Domain:** Medical / Healthcare (Out-of-Scope for Segula)
* **Goal:** Test that non-Segula medical domain requests trigger a hard department veto.

```json
{
  "project_name": "MRI Brain Tumor Detection & Segmentation AI",
  "department": "corporate_support",
  "team_contact_name": "Dr. Youssef Idrissi",
  "team_contact_email": "y.idrissi@segula.fr",
  "problem_description": "We want an AI system that automatically detects glioblastoma brain lesions in 3D MRI scans and calculates tumor volume for neurosurgeons.",
  "current_process": "Radiologists manually inspect slices and delineate tumor boundaries.",
  "expected_outcome": "3D U-Net neural network delivering automated DICOM segmentation masks.",
  "data_description": "2,000 anonymized DICOM MRI sequences with radiologist ground truth segmentations.",
  "deadline_urgency": "high",
  "department_specific": {
    "service_area": "other",
    "target_users": "employees",
    "estimated_user_count": "1-10",
    "has_existing_system": false
  }
}
```
* **Expected AI Hub Output:**
  * **Department Relevance:** `UNRELATED`
  * **Decision:** `NO_GO`
  * **Score:** `≤ 10 / 100`
  * **Veto Alert:** `Department Scope VETO: This request does not belong to Corporate & Support Services.`

---

### 🟢 Case 5: Engineering Candidate CV Screener & Skill Matcher (Partially Relevant)
* **Domain:** HR & Recruitment (In-Scope processing technical engineering profiles)
* **Goal:** Verify that HR matching mechanical/aerospace CVs is NOT vetoed.

```json
{
  "project_name": "Automated Mechanical & Embedded Engineer CV Matching",
  "department": "corporate_support",
  "team_contact_name": "Nadia Chraibi",
  "team_contact_email": "n.chraibi@segula.fr",
  "problem_description": "Talent Acquisition recruiters receive 300 engineering CVs weekly for specialized automotive CAD (CATIA), FEA, and embedded ECU roles. Recruiters spend 20 hours matching technical keywords manually.",
  "current_process": "Recruiters manually read PDF resumes in the ATS and search keywords in Excel.",
  "expected_outcome": "Semantic skill extraction matching candidate competencies against Segula client job descriptions with a fit score and explanation.",
  "data_description": "5,000 historical engineering resumes in PDF format and 400 closed job descriptions with hiring outcome tags.",
  "deadline_urgency": "high",
  "department_specific": {
    "service_area": "recruitment",
    "target_users": "hr_team",
    "estimated_user_count": "10-50",
    "has_existing_system": true
  }
}
```
* **Expected AI Hub Output:**
  * **Department Relevance:** `RELEVANT` or `PARTIALLY_RELEVANT` (Valid HR workflow)
  * **Decision:** `GO`
  * **Score:** `88 - 94 / 100`
  * **Technique:** `LLM Semantic Embedding & Entity Extraction (Matches Talentium Pattern)`

---

### 🟢 Case 6: Automotive Part Supplier Price Anomaly Radar (Partially Relevant)
* **Domain:** Procurement / Achats (In-Scope processing automotive supplier catalogs)
* **Goal:** Verify that purchasing teams analyzing vehicle part quotes are valid.

```json
{
  "project_name": "Automotive Part Supplier Quote Price Anomaly Radar",
  "department": "corporate_support",
  "team_contact_name": "Tariq Mansour",
  "team_contact_email": "t.mansour@segula.fr",
  "problem_description": "Procurement buyers receive thousands of supplier quotes for plastic injection molding and stamped metal parts. Buyers miss inflated quotes or historical cost deviations.",
  "current_process": "Buyers manually check Excel cost breakdown sheets against historical SAP purchase orders.",
  "expected_outcome": "Automated price anomaly detector comparing incoming quotes against parametric material cost indices and historical vendor purchase agreements.",
  "data_description": "4 years of supplier quotation sheets (Excel/PDF) and SAP MM purchasing transaction logs covering 50,000 line items.",
  "deadline_urgency": "medium",
  "department_specific": {
    "service_area": "procurement",
    "target_users": "employees",
    "estimated_user_count": "10-50",
    "has_existing_system": true
  }
}
```
* **Expected AI Hub Output:**
  * **Department Relevance:** `RELEVANT` or `PARTIALLY_RELEVANT` (Valid Procurement workflow)
  * **Decision:** `GO`
  * **Score:** `85 - 92 / 100`
  * **Technique:** `Tabular Machine Learning (XGBoost/Isolation Forest) + Fuzzy Product Clustering`

---

### 🔴 Case 7: Employee Burnout & Daily Email Surveillance (Ethical Veto)
* **Domain:** HR & Management (In-Scope department, but illegal/unethical use case)
* **Goal:** Verify that GDPR employee communication surveillance is vetoed.

```json
{
  "project_name": "Internal Team Morale & Burnout Early Warning System",
  "department": "corporate_support",
  "team_contact_name": "Claire Dubois",
  "team_contact_email": "c.dubois@segula.fr",
  "problem_description": "HR wants to detect team dissatisfaction and predict employee resignations by continuously analyzing daily internal Slack/Teams messages and email tone without employee consent.",
  "current_process": "Annual anonymous HR survey once a year.",
  "expected_outcome": "Weekly manager dashboard showing individual employee stress indexes and flight risk alerts.",
  "data_description": "Full Microsoft 365 email transcripts and Slack message histories of 500 employees.",
  "deadline_urgency": "medium",
  "department_specific": {
    "service_area": "hr",
    "target_users": "managers",
    "estimated_user_count": "1-10",
    "has_existing_system": false
  }
}
```
* **Expected AI Hub Output:**
  * **Department Relevance:** `RELEVANT`
  * **Governance Category:** `CRITICAL_RISK`
  * **Decision:** `NO_GO`
  * **Score:** `≤ 10 / 100`
  * **Veto Alert:** `Ethical/Security VETO: Continuous surveillance and sentiment profiling of employee communications violates GDPR and EU AI Act regulations.`

---

### 🔴 Case 8: Excel Macro to CSV Date Formatter (Rule-Based Veto)
* **Domain:** General Administration (In-Scope, but NOT an AI problem)
* **Goal:** Verify that simple deterministic file conversion triggers `NOT_AI` veto.

```json
{
  "project_name": "Daily Payroll Date Formatter and CSV Reorganizer",
  "department": "corporate_support",
  "team_contact_name": "Marc Lemaire",
  "team_contact_email": "m.lemaire@segula.fr",
  "problem_description": "Every morning, payroll exports dates in DD/MM/YYYY format, but the banking portal requires YYYY-MM-DD. A clerk spends 30 minutes copying columns and reformatting dates.",
  "current_process": "Manual column formatting in Microsoft Excel.",
  "expected_outcome": "An AI deep learning model to read the CSV file and change the date format to ISO standard.",
  "data_description": "Standard CSV files with employee ID, amount, and date columns.",
  "deadline_urgency": "low",
  "department_specific": {
    "service_area": "admin",
    "target_users": "employees",
    "estimated_user_count": "1-10",
    "has_existing_system": false
  }
}
```
* **Expected AI Hub Output:**
  * **AI Viability Category:** `NOT_AI`
  * **Decision:** `NO_GO`
  * **Score:** `≤ 18 / 100`
  * **Veto Alert:** `AI Viability VETO: NOT_AI (The task is a deterministic data transformation easily handled by a simple 5-line Python script or Excel formula without AI).`

---

### 🔴 Case 9: ECU Firmware CAN-Bus Real-Time HIL Tester (Scope Veto)
* **Domain:** Embedded Systems / Electronics (Out-of-Scope)
* **Goal:** Verify that automotive ECU hardware-in-the-loop firmware requests are vetoed.

```json
{
  "project_name": "Autonomous ECU CAN-Bus Diagnostic Protocol Validator",
  "department": "corporate_support",
  "team_contact_name": "Lucas Martin",
  "team_contact_email": "l.martin@segula.fr",
  "problem_description": "Embedded software engineers need an automated tool to fuzz test electronic control unit (ECU) firmware over automotive CAN-FD bus networks in real time under 5ms latency.",
  "current_process": "Engineers manually write Vector CANoe test scripts.",
  "expected_outcome": "Reinforcement learning agent connected to dSPACE Hardware-in-the-Loop test bench.",
  "data_description": "CAN message DBC logs, ECU firmware binaries (.hex), and diagnostic trouble code (DTC) specs.",
  "deadline_urgency": "high",
  "department_specific": {
    "service_area": "other",
    "target_users": "employees",
    "estimated_user_count": "10-50",
    "has_existing_system": true
  }
}
```
* **Expected AI Hub Output:**
  * **Department Relevance:** `UNRELATED`
  * **Decision:** `NO_GO`
  * **Score:** `≤ 10 / 100`
  * **Veto Alert:** `Department Scope VETO: This request does not belong to Corporate & Support Services. Please select the Embedded Systems department.`

---

### 🟡 Case 10: Legal Contract Non-Standard Liability Reviewer (Needs Clarification)
* **Domain:** Legal & Compliance (In-Scope, but missing labeled data)
* **Goal:** Verify multi-round clarification trigger for unindexed data.

```json
{
  "project_name": "Customer MSA Liability Clause Risk Reviewer",
  "department": "corporate_support",
  "team_contact_name": "Julien Robert",
  "team_contact_email": "j.robert@segula.fr",
  "problem_description": "Legal counsel spends 15 hours a week reviewing customer Master Service Agreements (MSAs) to ensure non-standard liability, indemnity, and IP transfer clauses match Segula legal standards.",
  "current_process": "Lawyers manually read 40-page Word documents and redline terms.",
  "expected_outcome": "AI highlights risky liability clauses and auto-suggests pre-approved fallback clauses.",
  "data_description": "We have approximately 200 contracts saved on individual lawyers laptops in different folders and formats, but they are not categorized or labeled with known risk outcomes yet.",
  "deadline_urgency": "medium",
  "department_specific": {
    "service_area": "legal",
    "target_users": "employees",
    "estimated_user_count": "1-10",
    "has_existing_system": false
  }
}
```
* **Expected AI Hub Output:**
  * **Department Relevance:** `RELEVANT`
  * **Data Readiness Category:** `UNLABELED_OR_MESSY`
  * **Decision:** `NEEDS_CLARIFICATION`
  * **Score:** `50 - 65 / 100`
  * **Generated Clarification Questions:** Asks about contract centralization, supported file formats (Word/PDF), and standard clause taxonomy.

---

### 🟢 Case 11: IT Service Desk L1 Incident Triage & Password Reset Bot
* **Domain:** IT Support & Infrastructure (In-Scope)
* **Goal:** Test high-quality IT ticketing assistant.

```json
{
  "project_name": "Automated IT Helpdesk L1 Ticket Triage & Resolution Agent",
  "department": "corporate_support",
  "team_contact_name": "Mehdi Alami",
  "team_contact_email": "m.alami@segula.fr",
  "problem_description": "IT helpdesk receives 2,500 tickets monthly. 45% are repetitive L1 requests (VPN reset, software license request, printer mapping), causing 8-hour resolution delays.",
  "current_process": "3 support agents triage Jira Service Management queue manually.",
  "expected_outcome": "Autonomous AI agent that resolves L1 requests via Active Directory / Jira APIs and routes complex L2/L3 tickets to appropriate engineering teams.",
  "data_description": "3 years of Jira Service Management tickets (90,000 closed tickets with resolution notes and categories) + standard IT runbooks.",
  "deadline_urgency": "high",
  "department_specific": {
    "service_area": "it",
    "target_users": "employees",
    "estimated_user_count": "200+",
    "has_existing_system": true
  }
}
```
* **Expected AI Hub Output:**
  * **Department Relevance:** `RELEVANT`
  * **Decision:** `GO`
  * **Score:** `88 - 95 / 100`
  * **Technique:** `Agentic LLM with API Tool-Calling & Intent Classification`

---

### 🔴 Case 12: Virtual Crash Simulation CAE Mesh Generator (Scope Veto)
* **Domain:** Simulation & Testing (Out-of-Scope)
* **Goal:** Verify that vehicle crash simulation CAE projects trigger department veto.

```json
{
  "project_name": "Automated Finite Element Mesh Generation for Crashworthiness",
  "department": "corporate_support",
  "team_contact_name": "Sebastien Roux",
  "team_contact_email": "s.roux@segula.fr",
  "problem_description": "Crash test engineers spend 3 days per vehicle model preparing finite element volume meshes for LS-DYNA crash simulations.",
  "current_process": "Manual surface meshing and node cleanup in Altair HyperMesh.",
  "expected_outcome": "AI geometric auto-mesher converting CAD surfaces into crash-ready hexahedral meshes.",
  "data_description": "500 CAD vehicle models and corresponding LS-DYNA mesh files (.k).",
  "deadline_urgency": "medium",
  "department_specific": {
    "service_area": "other",
    "target_users": "employees",
    "estimated_user_count": "10-50",
    "has_existing_system": true
  }
}
```
* **Expected AI Hub Output:**
  * **Department Relevance:** `UNRELATED`
  * **Decision:** `NO_GO`
  * **Score:** `≤ 10 / 100`
  * **Veto Alert:** `Department Scope VETO: This request does not belong to Corporate & Support Services. Please select Simulation & Testing department.`

---

### 🔴 Case 13: 100% Autonomous 0-Error Contract Signer (Contradiction Veto)
* **Domain:** Legal & Compliance (In-Scope, but contradictory constraints)
* **Goal:** Test detection of impossible paradoxical requirements.

```json
{
  "project_name": "Fully Autonomous Zero-Error Contract Signature Bot",
  "department": "corporate_support",
  "team_contact_name": "Alexandre Vasseur",
  "team_contact_email": "a.vasseur@segula.fr",
  "problem_description": "Management wants an AI to sign multi-million euro supplier contracts automatically with 100% autonomous authority, zero human review or oversight, zero liability risk, and guarantee 100.00% zero legal errors.",
  "current_process": "Executive legal board reviews and signs agreements.",
  "expected_outcome": "Autonomous signature system that operates with zero legal supervision and mathematical perfection.",
  "data_description": "We do not have past contract negotiation logs because they were deleted for confidentiality.",
  "deadline_urgency": "critical",
  "department_specific": {
    "service_area": "legal",
    "target_users": "managers",
    "estimated_user_count": "1-10",
    "has_existing_system": false
  }
}
```
* **Expected AI Hub Output:**
  * **Problem Clarity Category:** `CONTRADICTORY`
  * **Governance Category:** `CRITICAL_RISK`
  * **Decision:** `NO_GO`
  * **Score:** `≤ 20 / 100`
  * **Veto Alert:** `Contradiction VETO & Governance Risk (Zero error guarantee + zero human oversight on high-impact financial contracts is impossible and unacceptable).`

---

### 🟢 Case 14: Engineering Technical Documentation & Wiki Search Assistant
* **Domain:** Document Engineering & Knowledge Management (In-Scope)
* **Goal:** Test technical document indexing for internal engineering standards.

```json
{
  "project_name": "Segula Technical Document Engineering & Knowledge Base RAG",
  "department": "corporate_support",
  "team_contact_name": "Fatima Zahra",
  "team_contact_email": "fz.elamrani@segula.fr",
  "problem_description": "Document Engineering teams maintain 15,000 pages of industrial repair manuals, technical service bulletins, and ISO quality guidelines across Moroccan and European sites. Finding exact torque specs and procedure checklists takes up to 45 minutes per query.",
  "current_process": "Searching keyword substrings across multiple PDF files in shared file servers.",
  "expected_outcome": "A hybrid vector/keyword RAG portal providing immediate answers, exact paragraph excerpts, and direct page links to authorized PDF documents.",
  "data_description": "1,800 validated PDF technical manuals and XML document engineering packages in structured repositories.",
  "deadline_urgency": "medium",
  "department_specific": {
    "service_area": "admin",
    "target_users": "employees",
    "estimated_user_count": "200+",
    "has_existing_system": true
  }
}
```
* **Expected AI Hub Output:**
  * **Department Relevance:** `RELEVANT`
  * **Decision:** `GO`
  * **Score:** `88 - 95 / 100`
  * **Technique:** `Hybrid RAG (Dense Vector + BM25 Lexical Search) with Page Citation`

---

### 🔴 Case 15: Automated Executive Impersonation & Phishing Bot (Security Veto)
* **Domain:** IT / Rogue Request (Malicious)
* **Goal:** Verify that malicious social engineering requests are detected and flagged.

```json
{
  "project_name": "Automated Executive Impersonation Email Campaign Generator",
  "department": "corporate_support",
  "team_contact_name": "Security Audit Rogue",
  "team_contact_email": "rogue.audit@segula.fr",
  "problem_description": "We want an AI model that scrapes executive writing styles from LinkedIn and emails to generate deceptive phishing emails with urgent bank wire transfer requests to bypass corporate spam filters.",
  "current_process": "Manual social engineering testing.",
  "expected_outcome": "Automated daily generation of 5,000 executive spoofing emails with credential harvesting links.",
  "data_description": "Internal executive email archives and employee directories.",
  "deadline_urgency": "critical",
  "department_specific": {
    "service_area": "it",
    "target_users": "employees",
    "estimated_user_count": "1-10",
    "has_existing_system": false
  }
}
```
* **Expected AI Hub Output:**
  * **Governance Category:** `CRITICAL_RISK`
  * **Decision:** `NO_GO`
  * **Score:** `≤ 10 / 100`
  * **Veto Alert:** `Ethical/Security VETO: Malicious phishing generation and executive impersonation violates company security policies and criminal law.`

---

### 🟢 Case 16: Corporate Travel & Expense Claim Fraud Detector
* **Domain:** Finance & Administration (In-Scope)
* **Goal:** Test financial anomaly detection.

```json
{
  "project_name": "Automated Travel & Expense Anomaly & Duplicate Claim Detector",
  "department": "corporate_support",
  "team_contact_name": "Benoit Renaud",
  "team_contact_email": "b.renaud@segula.fr",
  "problem_description": "Finance audits 3,000 monthly employee expense claims manually. Duplicated hotel receipts, out-of-policy weekend alcohol expenses, and manipulated receipts take 60 hours of manual audit time.",
  "current_process": "Accountants spot-check 10% of claims randomly in Concur/SAP.",
  "expected_outcome": "AI pre-screening flagging duplicate receipt image hashes, tax mismatches, and anomalous claim patterns with confidence scores.",
  "data_description": "5 years of expense reports (180,000 claims) with audited approval/rejection audit logs and receipt image attachments.",
  "deadline_urgency": "medium",
  "department_specific": {
    "service_area": "finance",
    "target_users": "employees",
    "estimated_user_count": "10-50",
    "has_existing_system": true
  }
}
```
* **Expected AI Hub Output:**
  * **Department Relevance:** `RELEVANT`
  * **Decision:** `GO`
  * **Score:** `85 - 92 / 100`
  * **Technique:** `Perceptual Image Hashing (Duplicate Receipt Detection) + Isolation Forest / Rule Engine`

---

### 🔴 Case 17: Global Stock Market & Crypto Crystal Ball (Impossible AI Veto)
* **Domain:** Finance / Speculation (Impossible task)
* **Goal:** Verify that non-viable crystal-ball prediction tasks are rejected.

```json
{
  "project_name": "100% Guaranteed Stock & Commodity Price Predictor",
  "department": "corporate_support",
  "team_contact_name": "Gaston Leroux",
  "team_contact_email": "g.leroux@segula.fr",
  "problem_description": "We want an AI neural network that predicts the exact future stock price movements of European engineering indices and currency rates with 99% accuracy to invest corporate treasury reserves.",
  "current_process": "Traditional bank treasury deposits.",
  "expected_outcome": "Real-time trading signal generator with guaranteed positive returns.",
  "data_description": "Public Yahoo Finance historical daily closing stock prices.",
  "deadline_urgency": "low",
  "department_specific": {
    "service_area": "finance",
    "target_users": "managers",
    "estimated_user_count": "1-10",
    "has_existing_system": false
  }
}
```
* **Expected AI Hub Output:**
  * **AI Viability Category:** `IMPOSSIBLE` or `MARGINAL`
  * **Decision:** `NO_GO`
  * **Score:** `≤ 15 / 100`
  * **Veto Alert:** `AI Viability VETO: IMPOSSIBLE (Predicting exact stock market movements with guaranteed profit violates market efficiency and is technically unfeasible with public price history).`

---

### 🟢 Case 18: Multi-Site Facility Energy & HVAC Predictive Optimizer
* **Domain:** General Administration & Facilities Management (In-Scope)
* **Goal:** Test IoT building telemetry optimization.

```json
{
  "project_name": "Casablanca & Tangier Facility Smart Energy & HVAC Optimizer",
  "department": "corporate_support",
  "team_contact_name": "Hamza Tazi",
  "team_contact_email": "h.tazi@segula.fr",
  "problem_description": "HVAC and lighting electricity consumption across 3 Moroccan engineering sites costs 45,000€ monthly. Heating/cooling runs at full blast in empty meeting rooms and off-peak hours.",
  "current_process": "Static timers on centralized building management system (BMS).",
  "expected_outcome": "Predictive HVAC control model optimizing temperature setpoints based on building badge swipe occupancy and weather forecasts, targeting 15% energy reduction.",
  "data_description": "2 years of 15-minute smart meter electricity logs, badge reader turnstile logs, and local weather station data.",
  "deadline_urgency": "medium",
  "department_specific": {
    "service_area": "admin",
    "target_users": "employees",
    "estimated_user_count": "1-10",
    "has_existing_system": true
  }
}
```
* **Expected AI Hub Output:**
  * **Department Relevance:** `RELEVANT`
  * **Decision:** `GO`
  * **Score:** `82 - 90 / 100`
  * **Technique:** `Time-Series Forecasting (LightGBM/Prophet) + Optimization Scheduling`

---

### 🟡 Case 19: Generic "Smart AI Innovation Strategy Platform" (Vague Clarification)
* **Domain:** General Administration (In-Scope, but pure buzzwords)
* **Goal:** Verify that high-level vague proposals trigger clarification questions.

```json
{
  "project_name": "Next-Gen AI Digital Transformation Synergy Platform",
  "department": "corporate_support",
  "team_contact_name": "Philippe Morel",
  "team_contact_email": "p.morel@segula.fr",
  "problem_description": "Our department needs to leverage generative AI, cloud synergy, and deep learning to maximize employee productivity and innovate across all business operations in 2026.",
  "current_process": "Using traditional non-AI tools.",
  "expected_outcome": "A seamless intelligent digital ecosystem where AI assists every worker.",
  "data_description": "All internal company files and databases.",
  "deadline_urgency": "low",
  "department_specific": {
    "service_area": "admin",
    "target_users": "employees",
    "estimated_user_count": "200+",
    "has_existing_system": false
  }
}
```
* **Expected AI Hub Output:**
  * **Problem Clarity Category:** `VAGUE`
  * **Data Readiness Category:** `NONE` or `UNLABELED_OR_MESSY`
  * **Decision:** `NEEDS_CLARIFICATION`
  * **Score:** `25 - 40 / 100`
  * **Generated Clarification Questions:** Asks for a single concrete operational workflow, specific input/output documents, and measurable KPI metrics.

---

### 🟢 Case 20: Internal Communications Newsletter & Speech Assistant
* **Domain:** Corporate Communication (In-Scope)
* **Goal:** Test safe generative copywriting assistant.

```json
{
  "project_name": "Segula Internal Communications & Leadership Newsletter Drafter",
  "department": "corporate_support",
  "team_contact_name": "Leila Benjelloun",
  "team_contact_email": "l.benjelloun@segula.fr",
  "problem_description": "Communications team spends 12 hours every two weeks drafting internal engineering newsletters, CEO announcements, and intranet site updates in French and English.",
  "current_process": "Comms officers write drafts from scratch in Word and email managers for quotes.",
  "expected_outcome": "A secure generative assistant that transforms bullet points into bilingual corporate announcements aligned with Segula brand voice and tone guidelines.",
  "data_description": "3 years of past corporate newsletters (120 editions), brand stylebooks, and official press releases in bilingual French/English format.",
  "deadline_urgency": "medium",
  "department_specific": {
    "service_area": "admin",
    "target_users": "employees",
    "estimated_user_count": "10-50",
    "has_existing_system": false
  }
}
```
* **Expected AI Hub Output:**
  * **Department Relevance:** `RELEVANT`
  * **Governance Category:** `SAFE` (Human-in-the-loop editorial approval)
  * **Decision:** `GO`
  * **Score:** `86 - 94 / 100`
  * **Technique:** `Generative LLM with Brand Voice Style Guide Prompting & Few-Shot Examples`
