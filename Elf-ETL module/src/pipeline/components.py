"""
Pipeline Components for Elf-ETL.
Defines atomic processing steps as Datapizza PipelineComponents.
"""
from typing import List, Tuple, Any
from pathlib import Path
from datetime import datetime
import logging
import os

from datapizza.core.models import PipelineComponent
from datapizza.clients.google import GoogleClient

from core.models import Child, Letter, CountryEnum, GenderEnum
from core.schemas import LetterExtraction, ChildData

# Setup Logger for Components
logger = logging.getLogger("ElfPipeline")
logger.setLevel(logging.INFO)
if not logger.handlers:
    os.makedirs("logs", exist_ok=True)
    fh = logging.FileHandler("logs/pipeline.log")
    fh.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
    logger.addHandler(fh)


class FileScanner(PipelineComponent):
    """Scans a directory for text files."""
    def _run(self, directory: str, pattern: str = "*.txt") -> List[Path]:
        path = Path(directory)
        files = list(path.glob(pattern))
        logger.info(f"Scanned {len(files)} files in {directory}")
        return files


class FileReader(PipelineComponent):
    """Reads content from a file path."""
    def _run(self, file_path: Path) -> dict:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
        return {"file_path": file_path, "content": content}


class GrinchFilter(PipelineComponent):
    """
    Heuristic Anti-Grinch Filter.
    Returns a dict with 'is_spam' flag and reason.
    """
    def _run(self, data: dict) -> dict:
        text = data["content"]
        text_lower = text.lower()
        spam_keywords = ["grinch", "i hate christmas", "stole christmas", "non mi piace il natale"]
        
        for keyword in spam_keywords:
            if keyword in text_lower:
                logger.warning(f"SPAM detected in {data['file_path'].name}: {keyword}")
                data["is_spam"] = True
                data["spam_reason"] = f"Keyword match: '{keyword}'"
                return data
        
        data["is_spam"] = False
        data["spam_reason"] = None
        return data


class GrinchLogger(PipelineComponent):
    """
    Logs spam letters to file.
    Branch Endpoint for Spam letters.
    """
    def _run(self, data: dict):
        # SKIPPING LOGIC: If not spam, do nothing
        if not data.get("is_spam", False):
            return data
            
        file_name = data["file_path"].name
        reason = data["spam_reason"]
        
        # Log to dedicated spam log
        spam_logger = logging.getLogger("GrinchLog")
        if not spam_logger.handlers:
             os.makedirs("logs", exist_ok=True)
             fh = logging.FileHandler("logs/grinch_blocked.log")
             fh.setFormatter(logging.Formatter('%(asctime)s - SPAM - %(message)s'))
             spam_logger.addHandler(fh)
             spam_logger.setLevel(logging.INFO)
        
        spam_logger.info(f"BLOCKED: {file_name} -> {reason}")
        return data


class LLMExtractor(PipelineComponent):
    """
    Wraps the Gemini extraction logic.
    Only runs on valid letters.
    """
    def __init__(self, model_name: str = "gemini-1.5-flash"):
        super().__init__()
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
             # In a real app we might handle this gracefully or fail fast
             pass
        self.client = GoogleClient(api_key=api_key, model=model_name)

    def _build_prompt(self, letter_text: str) -> str:
        return f"""Analyze this letter to Santa Claus and extract structured information.
        RULES:
        1. Country: [italy, usa, china, russia, brazil, australia, unknown]
        2. Goodness: 0.1-1.0 based on behavior
        3. Extract GIFTS
        4. Infer GENDER
        
        LETTER:
        {letter_text}
        """

    def _run(self, *args, **kwargs) -> dict:
        """
        Expects 'data' dictionary from previous step.
        """
        # Unwrap data (robustness)
        if "data" in kwargs:
             data = kwargs["data"]
        elif args:
             data = args[0]
        else:
             # If completely empty, we can't do anything.
             # In linear pipeline, assuming dependency holds, we should get args[0]
             raise ValueError("Missing input data")
        
        # SKIPPING LOGIC: If spam, skip extraction
        if data.get("is_spam", False):
            return data

        text = data["content"]
        file_path = data["file_path"]
        
        prompt = self._build_prompt(text)
        try:
            response = self.client.structured_response(
                input=prompt,
                output_cls=LetterExtraction
            )
            extraction = response.structured_data[0]
            
            # Enrich data dict
            data["extraction"] = extraction
            return data
        except Exception as e:
            logger.error(f"LLM Error on {file_path}: {e}")
            raise e


class DatabaseLoader(PipelineComponent):
    """
    Saves extracted data to DB.
    Requires a DB session factory or similar injection.
    """
    def __init__(self, session_factory):
        super().__init__()
        self.session_factory = session_factory

    def _run(self, data: dict):
        extraction = data["extraction"]
        text = data["content"]
        
        # Logic adapted from original loader
        from sqlmodel import Session
        
        with self.session_factory() as session:
            # Create Child
            child = Child(
                name=extraction.child.name,
                age=extraction.child.age,
                city=extraction.child.city,
                country=extraction.child.country,
                gender=extraction.child.gender
            )
            session.add(child)
            session.commit()
            session.refresh(child)
            
            # Create Letter
            letter = Letter(
                content=text,
                is_spam=False, # We know it's valid if we are here
                received_at=datetime.utcnow(),
                goodness_score=extraction.goodness_score,
                gift_request=extraction.gift_request,
                child_id=child.id
            )
            session.add(letter)
            session.commit()
            session.refresh(letter)
            
            logger.info(f"SAVED: {child.name} (Letter ID: {letter.id})")
            return letter
