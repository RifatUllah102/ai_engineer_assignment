# 📄 Document Intelligence Pipeline

An end-to-end pipeline for processing unstructured documents, extracting key information, and generating structured legal drafts with iterative learning.

---

## 🚀 Quick Start (5 Minutes)

### 1. Navigate to Project Folder
```bash
cd D:\Downloads\Assesment
```

### 2. Create Virtual Environment
```bash
python -m venv env
```

### 3. Activate Environment
**Windows**
```bash
env\Scripts\activate
```

**Mac/Linux**
```bash
source env/bin/activate
```

### 4. Install Dependencies
```bash
pip install openai==0.28.1 python-dotenv==1.0.0 numpy==1.24.3
```

### 5. Set API Key
Create a `.env` file in the root directory:

```
OPENAI_API_KEY=your_openai_api_key_here
```

### 6. Run the Pipeline
```bash
python main.py
```

---

## 📊 What You’ll See

### Step 1: Processing Documents
- OCR cleanup and normalization  
- Extraction of liens, deadlines, and action items  

```
✓ Processed: title_search_page1 (3 liens found)
✓ Processed: servicer_email (3 action items found)
✓ Processed: court_order (2 deadlines found)
```

### Step 2: Indexing Documents
```
✓ Created 15 chunks
```

### Step 3: Generating Drafts
```
✓ Title Review Summary generated
✓ Case Status Memo generated
```

### Step 4: Learning from Edits
```
✓ Learned patterns from operator edits
```

### Step 5: Improved Drafts
```
✓ Improved drafts created
```

---

## 📂 Output Files

Generated inside the `outputs/` directory:

| File | Description |
|------|-------------|
| `initial_title_review.txt` | First draft (before learning) |
| `initial_case_status_memo.txt` | Initial memo |
| `improved_title_review.txt` | Improved draft |
| `improved_case_status_memo.txt` | Improved memo |
| `comparison_report.json` | Metrics comparing drafts |

---

## 🧪 Testing Your Setup

### Test File Integrity
```bash
python test_setup.py
```

### Test API Connectivity
```bash
python test_api.py
```

---

## ⚠️ Common Errors & Fixes

### ❌ No module named src
```bash
cd D:\Downloads\Assesment
```

### ❌ OPENAI_API_KEY not found
Ensure `.env` file contains:
```
OPENAI_API_KEY=your_key
```

### ❌ Insufficient balance
Add credits to your OpenAI account.

### ❌ Connection Error
```bash
python test_api.py
```

---

## 📁 Project Structure

```
D:\Downloads\Assesment/
├── main.py
├── test_api.py
├── test_setup.py
├── .env
├── ai_engineer_assignment_data/
│   ├── case_context.json
│   ├── sample_edits.json
│   └── sample_documents/
│       ├── court_order.txt
│       ├── servicer_email.txt
│       ├── title_search_page1.txt
│       └── title_search_page2.txt
├── src/
│   ├── config.py
│   ├── processing/
│   ├── retrieval/
│   ├── generation/
│   └── learning/
└── outputs/
```

---

## ✅ Success Checklist

- [ ] test_setup.py passes  
- [ ] test_api.py passes  
- [ ] main.py runs  
- [ ] outputs/ folder created  
- [ ] improved drafts generated  

---

## ⚡ Useful Commands

| Task | Command |
|------|--------|
| Run pipeline | python main.py |
| Test API | python test_api.py |
| Test setup | python test_setup.py |
| Clean & rerun | rmdir /s /q outputs && python main.py |

---

## 🧠 What This Pipeline Does

1. Cleans OCR errors  
2. Extracts key info  
3. Retrieves context  
4. Generates drafts  
5. Improves via learning  

---

## ⏱️ Notes

- First run: 2–3 minutes  
- Works with minimal credits  
- Designed for AI document workflows  

---

## ❓ Troubleshooting

```bash
python test_setup.py
python test_api.py
```
