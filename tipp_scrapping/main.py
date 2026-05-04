import os
import subprocess
import logging
from typing import Dict, Optional, List
from datetime import datetime
from fastapi import FastAPI, BackgroundTasks, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import csv

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("tipp-api")

app = FastAPI(title="TIPP Scraper API", version="1.0.0")

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global state for background tasks
# In a real app, this would be in a DB or Redis
tasks_status: Dict[str, Dict] = {
    "full_scrape": {"status": "idle", "last_run": None, "pid": None},
    "products_scrape": {"status": "idle", "last_run": None, "pid": None},
    "details_scrape": {"status": "idle", "last_run": None, "pid": None},
    "combine_data": {"status": "idle", "last_run": None, "pid": None},
}

DATA_DIR = "data"

class ScrapeStats(BaseModel):
    master_codes: int
    tariffs: int
    cess: int
    exemptions: int
    antidump: int
    measures: int
    procedures: int
    products: int
    failed: int

def count_csv_rows(filename: str) -> int:
    path = os.path.join(DATA_DIR, filename)
    if not os.path.exists(path):
        return 0
    try:
        with open(path, "r", encoding="utf-8") as f:
            return sum(1 for _ in f) - 1  # Subtract header
    except Exception:
        return 0

def run_script(script_name: str, task_key: str):
    tasks_status[task_key]["status"] = "running"
    tasks_status[task_key]["last_run"] = datetime.now().isoformat()
    
    try:
        # Run using the venv python
        python_path = os.path.join(".venv", "bin", "python")
        if not os.path.exists(python_path):
            python_path = "python" # Fallback
            
        process = subprocess.Popen(
            [python_path, script_name],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        tasks_status[task_key]["pid"] = process.pid
        
        # We don't wait here because it's a background task, 
        # but the subprocess will run independently.
        # To actually track completion, we'd need a more robust worker system.
        # For now, we'll just check if the PID is still alive in the status endpoint.
        
    except Exception as e:
        logger.error(f"Failed to start {script_name}: {e}")
        tasks_status[task_key]["status"] = "failed"
        tasks_status[task_key]["error"] = str(e)

@app.get("/")
def read_root():
    return {"message": "TIPP Scraper API is running"}

@app.get("/stats", response_model=ScrapeStats)
def get_stats():
    return ScrapeStats(
        master_codes=count_csv_rows("hs_codes_master.csv"),
        tariffs=count_csv_rows("tariffs.csv"),
        cess=count_csv_rows("cess_collection.csv"),
        exemptions=count_csv_rows("exemption_concessions.csv"),
        antidump=count_csv_rows("anti_dump_tariffs.csv"),
        measures=count_csv_rows("measures.csv"),
        procedures=count_csv_rows("procedures.csv"),
        products=count_csv_rows("products.csv"),
        failed=count_csv_rows("failed.csv")
    )

@app.get("/tasks")
def get_tasks():
    # Update status based on PID
    for key, info in tasks_status.items():
        if info["status"] == "running" and info["pid"]:
            try:
                os.kill(info["pid"], 0) # Check if process is alive
            except OSError:
                info["status"] = "completed" # Or failed, we don't know easily without polling
                info["pid"] = None
                
    return tasks_status

@app.post("/tasks/full-scrape")
def trigger_full_scrape(background_tasks: BackgroundTasks):
    if tasks_status["full_scrape"]["status"] == "running":
        raise HTTPException(status_code=400, detail="Task already running")
    background_tasks.add_task(run_script, "tipp_scraper.py", "full_scrape")
    return {"message": "Full scrape started"}

@app.post("/tasks/products-scrape")
def trigger_products_scrape(background_tasks: BackgroundTasks):
    if tasks_status["products_scrape"]["status"] == "running":
        raise HTTPException(status_code=400, detail="Task already running")
    background_tasks.add_task(run_script, "scrape_products.py", "products_scrape")
    return {"message": "Products scrape started"}

@app.post("/tasks/details-scrape")
def trigger_details_scrape(background_tasks: BackgroundTasks):
    if tasks_status["details_scrape"]["status"] == "running":
        raise HTTPException(status_code=400, detail="Task already running")
    background_tasks.add_task(run_script, "scrape_details.py", "details_scrape")
    return {"message": "Details scrape started"}

@app.post("/tasks/combine")
def trigger_combine(background_tasks: BackgroundTasks):
    background_tasks.add_task(run_script, "combine_output.py", "combine_data")
    return {"message": "Data combination started"}

@app.post("/tasks/full-pipeline")
def trigger_full_pipeline(background_tasks: BackgroundTasks):
    """
    Run the complete scraping pipeline in sequence:
      1. tipp_scraper.py   — tariffs, cess, exemptions, anti-dump, measures, procedures
                             + generates pct codes with hierarchy.csv automatically
      2. scrape_products.py — products table (reads hierarchy file produced in step 1)
      3. combine_output.py  — merges everything into combined_tariffs.csv

    Safe to re-run: each script resumes from its checkpoint and skips already-done work.
    """
    for key in ("full_scrape", "products_scrape", "combine_data"):
        if tasks_status[key]["status"] == "running":
            raise HTTPException(
                status_code=400,
                detail=f"Task '{key}' is already running — wait for it to finish first."
            )

    def pipeline():
        import subprocess, time

        python_path = ".venv/bin/python" if os.path.exists(".venv/bin/python") else "python"

        steps = [
            ("tipp_scraper.py",   "full_scrape"),
            ("scrape_products.py","products_scrape"),
            ("combine_output.py", "combine_data"),
        ]

        for script, task_key in steps:
            tasks_status[task_key]["status"]   = "running"
            tasks_status[task_key]["last_run"] = datetime.now().isoformat()
            logger.info(f"[pipeline] Starting {script}…")
            result = subprocess.run(
                [python_path, script],
                capture_output=True, text=True
            )
            if result.returncode == 0:
                tasks_status[task_key]["status"] = "completed"
                logger.info(f"[pipeline] {script} completed.")
            else:
                tasks_status[task_key]["status"] = "failed"
                logger.error(f"[pipeline] {script} failed:\n{result.stderr[-2000:]}")
                break   # stop pipeline on first failure

    background_tasks.add_task(pipeline)
    return {"message": "Full pipeline started: tipp_scraper → scrape_products → combine_output"}

@app.get("/logs")
def get_logs(lines: int = 100):
    log_path = os.path.join(DATA_DIR, "scraper.log")
    if not os.path.exists(log_path):
        return {"logs": []}
    
    try:
        with open(log_path, "r") as f:
            all_lines = f.readlines()
            return {"logs": all_lines[-lines:]}
    except Exception as e:
        return {"error": str(e)}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8003)
