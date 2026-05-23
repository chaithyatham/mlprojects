# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Environment

The repo uses a local `.venv` at the project root. Always run scripts with:
```bash
python3 <script.py>
```
The venv is activated automatically by the shell. If a package is missing, install it into the venv with `python3 -m pip install <package>`.

All matplotlib scripts must use `matplotlib.use("Agg")` before any other matplotlib import — the environment has no display server, so interactive backends will block indefinitely.

## Projects

This is a collection of independent ML and web projects. Each lives in its own folder and is run from within that folder.

### `fraud_detection/`
Binary classification (fraud vs. non-fraud) on the Kaggle credit card dataset.

**Pipeline — run in order:**
```bash
cd fraud_detection
python3 preprocess.py    # produces X_train.npy, y_train.npy, X_test.npy, y_test.npy
python3 fraud_pytorch.py # trains FraudNet, prints metrics, saves fraud_net_weights.pt
python3 eda.py           # saves eda_report.png (run any time, independent of training)
```

**Architecture:**  
`preprocess.py` scales `Amount`/`Time` with `StandardScaler`, performs an 80/20 stratified split, then applies SMOTE **only to the training set** (test set stays raw to reflect real-world distribution). Outputs are float32 `.npy` arrays.

`fraud_pytorch.py` is the canonical model file. It defines `FraudDataset` (wraps `.npy` arrays), `FraudNet` (4-layer MLP: 256→128→64→32 with BatchNorm + Dropout), and a manual training loop using `BCEWithLogitsLoss` + Adam. Evaluation uses sklearn metrics (precision, recall, F1, ROC-AUC). `train.py` is an earlier version of the same model; prefer `fraud_pytorch.py`.

**Key constraint:** Never apply SMOTE to the test set. The imbalance (0.17% fraud) must be preserved in test data for metrics to reflect production conditions.

**Saved artefacts:** `creditcard.csv` and `*.npy` files are gitignored (see `fraud_detection/.gitignore`).

---

### `fundraiser/`
Flask web app for fundraising request management.

```bash
cd fundraiser
python3 app.py           # runs on http://localhost:5050
```

SQLite database at `fundraiser/fundraiser.db` (auto-created on first run via `init_db()`). Uploaded images go to `fundraiser/static/uploads/`.

**Routes:** `/` home, `/submit` public request form, `/status` email-based status lookup, `/admin` review dashboard with approve/deny actions.

---

### `tax_rag.py`
CLI RAG tool for querying personal tax PDFs using Claude + ChromaDB.

```bash
python3 tax_rag.py ingest path/to/pdfs/   # index PDFs (persisted to ~/.tax_rag_db)
python3 tax_rag.py ask "your question"
python3 tax_rag.py list                   # show indexed documents
python3 tax_rag.py clear                  # wipe the index
```

Uses `all-MiniLM-L6-v2` for embeddings (via `sentence-transformers`), ChromaDB as the vector store, and `claude-opus-4-6` with adaptive thinking for answers. The index persists at `~/.tax_rag_db` across runs. Requires `ANTHROPIC_API_KEY` set in the environment.

---

## Dependencies

Top-level `requirements.txt` covers the web/RAG stack: `anthropic`, `chromadb`, `sentence-transformers`, `pypdf`, `flask`.

ML stack (torch, pandas, numpy, scikit-learn, imbalanced-learn, matplotlib, seaborn) is installed directly into the venv and not in `requirements.txt`.

## Git

Remote: `https://github.com/chaithyatham/mlprojects.git` (branch: `main`).  
Large data files (`*.npy`, `creditcard.csv`) are gitignored and must not be committed.
