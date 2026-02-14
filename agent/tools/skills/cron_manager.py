"""CRON job manager for TestAIAgent.

Manages scheduled tasks stored in a JSON file.
"""

import json
import uuid
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path
from typing import Optional


@dataclass
class CronJob:
    """A scheduled cron job."""
    
    job_id: str
    name: str
    schedule: str
    schedule_description: str
    message: str
    created_at: str
    
    @classmethod
    def create(
        cls,
        name: str,
        schedule: str,
        schedule_description: str,
        message: str,
    ) -> "CronJob":
        """Create a new cron job with generated ID."""
        return cls(
            job_id=f"cron_{uuid.uuid4().hex[:8]}",
            name=name,
            schedule=schedule,
            schedule_description=schedule_description,
            message=message,
            created_at=datetime.now().isoformat(),
        )


class CronManager:
    """Manages cron jobs stored in a JSON file."""
    
    def __init__(self, storage_path: str | Path = "./data/cron_jobs.json"):
        """Initialize the cron manager.
        
        Args:
            storage_path: Path to the JSON file for storing jobs
        """
        self.storage_path = Path(storage_path)
        self._ensure_storage()
    
    def _ensure_storage(self) -> None:
        """Ensure storage directory and file exist."""
        self.storage_path.parent.mkdir(parents=True, exist_ok=True)
        if not self.storage_path.exists():
            self._save_jobs([])
    
    def _load_jobs(self) -> list[CronJob]:
        """Load jobs from storage."""
        try:
            with open(self.storage_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return [CronJob(**job) for job in data]
        except (json.JSONDecodeError, FileNotFoundError):
            return []
    
    def _save_jobs(self, jobs: list[CronJob]) -> None:
        """Save jobs to storage."""
        with open(self.storage_path, 'w', encoding='utf-8') as f:
            json.dump([asdict(job) for job in jobs], f, ensure_ascii=False, indent=2)
    
    def list_jobs(self) -> str:
        """List all scheduled jobs.
        
        Returns:
            Formatted string of all jobs or "No scheduled tasks" message
        """
        jobs = self._load_jobs()
        
        if not jobs:
            return "No scheduled tasks."
        
        lines = ["Current scheduled tasks:"]
        for job in jobs:
            lines.append(f"- [{job.job_id}] {job.name}")
            lines.append(f"  Schedule: {job.schedule} ({job.schedule_description})")
            lines.append(f"  Message: {job.message}")
            lines.append(f"  Created: {job.created_at}")
        
        return "\n".join(lines)
    
    def create_job(
        self,
        name: str,
        schedule: str,
        schedule_description: str,
        message: str,
    ) -> str:
        """Create a new scheduled job.
        
        Args:
            name: Job name
            schedule: Cron expression
            schedule_description: Human-readable schedule description
            message: Message to send when triggered
            
        Returns:
            Success message with job ID
        """
        jobs = self._load_jobs()
        
        new_job = CronJob.create(
            name=name,
            schedule=schedule,
            schedule_description=schedule_description,
            message=message,
        )
        
        jobs.append(new_job)
        self._save_jobs(jobs)
        
        return f"Scheduled task created successfully!\n- Job ID: {new_job.job_id}\n- Name: {new_job.name}\n- Schedule: {new_job.schedule} ({new_job.schedule_description})\n- Message: {new_job.message}"
    
    def delete_job(self, job_id: str) -> str:
        """Delete a scheduled job.
        
        Args:
            job_id: ID of the job to delete
            
        Returns:
            Success or error message
        """
        jobs = self._load_jobs()
        original_count = len(jobs)
        
        jobs = [job for job in jobs if job.job_id != job_id]
        
        if len(jobs) == original_count:
            return f"Error: Job with ID '{job_id}' not found."
        
        self._save_jobs(jobs)
        return f"Scheduled task '{job_id}' deleted successfully."
    
    def get_job(self, job_id: str) -> Optional[CronJob]:
        """Get a job by ID.
        
        Args:
            job_id: Job ID to look up
            
        Returns:
            CronJob if found, None otherwise
        """
        jobs = self._load_jobs()
        for job in jobs:
            if job.job_id == job_id:
                return job
        return None


# Global cron manager instance
cron_manager = CronManager()
