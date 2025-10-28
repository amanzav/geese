"""
FastAPI server for WaterlooWorks Automator
Provides endpoints for folder sync and job data retrieval
"""

import os
import json
from typing import Dict, List, Optional
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from .supabase_client import SupabaseClient
from .folder_sync import FolderSync


# Initialize FastAPI app
app = FastAPI(
    title="WaterlooWorks Automator API",
    description="API for syncing folders and managing job applications",
    version="1.0.0"
)

# Add CORS middleware for frontend communication
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Next.js default port
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global state
sync_status = {
    "is_syncing": False,
    "last_sync": None,
    "error": None
}


# Response models
class FoldersResponse(BaseModel):
    folders: Dict[str, List[str]]
    total_folders: int
    total_jobs: int


class SyncResponse(BaseModel):
    status: str
    message: str


class SyncStatusResponse(BaseModel):
    is_syncing: bool
    last_sync: Optional[str]
    error: Optional[str]


# ============================================
# ENDPOINTS
# ============================================

@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "status": "ok",
        "message": "WaterlooWorks Automator API",
        "version": "1.0.0"
    }


@app.get("/api/folders", response_model=FoldersResponse)
async def get_folders():
    """
    Get all folders with their job IDs from local storage.
    
    Returns:
        FoldersResponse with folder names and job IDs
    """
    try:
        folders_file = os.path.join("data", "user_folders.json")
        
        if not os.path.exists(folders_file):
            return FoldersResponse(
                folders={},
                total_folders=0,
                total_jobs=0
            )
        
        with open(folders_file, 'r', encoding='utf-8') as f:
            folders = json.load(f)
        
        total_jobs = sum(len(job_ids) for job_ids in folders.values())
        
        return FoldersResponse(
            folders=folders,
            total_folders=len(folders),
            total_jobs=total_jobs
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error loading folders: {str(e)}")


@app.post("/api/folders/sync", response_model=SyncResponse)
async def sync_folders(background_tasks: BackgroundTasks):
    """
    Trigger folder sync process.
    This will scrape all folders and sync jobs to Supabase.
    
    Note: This requires an active Selenium session. In production,
    you would need to handle driver management differently.
    """
    global sync_status
    
    if sync_status["is_syncing"]:
        return SyncResponse(
            status="already_running",
            message="Sync is already in progress"
        )
    
    # In a real implementation, you would need to:
    # 1. Get the active driver instance
    # 2. Get the scraper instance
    # 3. Run the sync
    
    # For now, return a message indicating this needs to be called from the main app
    return SyncResponse(
        status="error",
        message="Sync must be triggered from the main application with an active browser session"
    )


@app.get("/api/folders/sync/status", response_model=SyncStatusResponse)
async def get_sync_status():
    """
    Get the current sync status.
    """
    return SyncStatusResponse(
        is_syncing=sync_status["is_syncing"],
        last_sync=sync_status["last_sync"],
        error=sync_status["error"]
    )


@app.get("/api/folders/{folder_name}")
async def get_folder_jobs(folder_name: str):
    """
    Get all job IDs for a specific folder.
    
    Args:
        folder_name: Name of the folder
        
    Returns:
        Dict with folder name and list of job IDs
    """
    try:
        folders_file = os.path.join("data", "user_folders.json")
        
        if not os.path.exists(folders_file):
            raise HTTPException(status_code=404, detail="No folders found. Please sync first.")
        
        with open(folders_file, 'r', encoding='utf-8') as f:
            folders = json.load(f)
        
        if folder_name not in folders:
            raise HTTPException(status_code=404, detail=f"Folder '{folder_name}' not found")
        
        return {
            "folder_name": folder_name,
            "job_ids": folders[folder_name],
            "job_count": len(folders[folder_name])
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error loading folder: {str(e)}")


@app.get("/api/jobs/{job_id}")
async def get_job(job_id: str):
    """
    Get job details from Supabase by job ID.
    
    Args:
        job_id: WaterlooWorks job ID
        
    Returns:
        Job details from Supabase
    """
    try:
        supabase = SupabaseClient()
        job = supabase.get_job_by_id(job_id)
        
        if not job:
            raise HTTPException(status_code=404, detail=f"Job {job_id} not found")
        
        return job
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching job: {str(e)}")


@app.get("/api/jobs")
async def get_jobs(job_ids: str):
    """
    Get multiple jobs from Supabase by comma-separated job IDs.
    
    Args:
        job_ids: Comma-separated list of job IDs (e.g., "12345,67890,11111")
        
    Returns:
        List of job details
    """
    try:
        ids = [id.strip() for id in job_ids.split(",") if id.strip()]
        
        if not ids:
            return []
        
        supabase = SupabaseClient()
        jobs = supabase.get_jobs_by_ids(ids)
        
        return jobs
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching jobs: {str(e)}")


# ============================================
# HELPER FUNCTION FOR SYNC (to be called from main app)
# ============================================

def trigger_sync(driver, scraper):
    """
    Helper function to trigger sync from the main application.
    This should be called when you have an active driver and scraper instance.
    
    Args:
        driver: Selenium WebDriver instance
        scraper: WaterlooWorksScraper instance
    """
    global sync_status
    
    try:
        sync_status["is_syncing"] = True
        sync_status["error"] = None
        
        folder_sync = FolderSync(driver, scraper, use_supabase=True)
        folders = folder_sync.sync_all_folders()
        
        from datetime import datetime
        sync_status["is_syncing"] = False
        sync_status["last_sync"] = datetime.now().isoformat()
        
        return {"status": "success", "folders": folders}
        
    except Exception as e:
        sync_status["is_syncing"] = False
        sync_status["error"] = str(e)
        return {"status": "error", "message": str(e)}


# ============================================
# RUN SERVER
# ============================================

if __name__ == "__main__":
    import uvicorn
    
    print("🚀 Starting WaterlooWorks Automator API...")
    print("📍 API will be available at: http://localhost:8000")
    print("📚 API docs available at: http://localhost:8000/docs")
    
    uvicorn.run(
        "modules.api:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )
