"""
Information Extractor Module for Elf-ETL.
Uses datapizza-ai to extract structured data from letters.
"""
import os
from pathlib import Path
from typing import List, Tuple, Optional
from datetime import datetime
from dotenv import load_dotenv
from datapizza.clients.google import GoogleClient

import logging
try:
    from schemas import LetterExtraction, ChildData
    from models import Child, Letter, CountryEnum, GenderEnum
except ImportError:
    from .schemas import LetterExtraction, ChildData
    from .models import Child, Letter, CountryEnum, GenderEnum

load_dotenv()


class LetterExtractor:
    """
    Extracts structured data from letters using Gemini LLM via datapizza-ai.
    Returns both Child and Letter objects ready for database insertion.
    """
    
    def __init__(self, model_name: str = "gemini-2.0-flash-exp"):
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("GEMINI_API_KEY not found in environment variables.")
        
        self.client = GoogleClient(
            api_key=api_key,
            model=model_name
        )
        self.letters_dir = Path("data/test_letters")
        
        # Setup Tracing / Logging
        self.logger = logging.getLogger("ElfTrace")
        self.logger.setLevel(logging.INFO)
        # Create handlers if not exist
        if not self.logger.handlers:
            # Use path relative to this file's module root (Elf-ETL module)
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            log_dir = os.path.join(base_dir, "logs")
            os.makedirs(log_dir, exist_ok=True)
            fh = logging.FileHandler(os.path.join(log_dir, "spam_tracing.log"))
            fh.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
            self.logger.addHandler(fh)

    def _build_prompt(self, letter_text: str) -> str:
        """Build the extraction prompt."""
        return f"""Analyze this letter to Santa Claus and extract structured information.

        IMPORTANT RULES:
        1. Detect if this is SPAM (from "Il Grinch", "The Grinch", etc.) - if so, set is_spam=True
        2. For country: use one of [italy, usa, china, russia, brazil, australia], or "unknown" if different
        3. For goodness_score: analyze the behavior described:
        - 0.9-1.0: Very good (helps parents, kind, polite)
        - 0.7-0.8: Good (mostly positive behavior)
        - 0.5-0.6: Neutral (mixed behavior)
        - 0.3-0.4: Somewhat naughty
        - 0.1-0.2: Very naughty
        4. Extract ALL gift requests mentioned
        5. Infer gender from the name if not explicitly stated

        LETTER TEXT:
        {letter_text}
        """

    def _is_spam_heuristic(self, text: str) -> Tuple[bool, Optional[str]]:
        """
        Fast heuristic check for spam keywords to avoid LLM costs.
        Returns (is_spam, reason).
        """
        text_lower = text.lower()
        spam_keywords = ["grinch", "i hate christmas", "stole christmas", "non mi piace il natale"]
        
        for keyword in spam_keywords:
            if keyword in text_lower:
                return True, f"Keyword match: '{keyword}'"
        return False, None

    def extract_from_text(self, letter_text: str) -> LetterExtraction:
        """Extract data from a single letter text."""
        prompt = self._build_prompt(letter_text)
        response = self.client.structured_response(
            input=prompt,
            output_cls=LetterExtraction
        )
        return response.structured_data[0]
    
    def extract_from_file(self, file_path: Path) -> Tuple[Child, Letter, LetterExtraction]:
        """
        Extract data from a letter file and return SQLModel objects and raw extraction.
        Returns (Child, Letter, LetterExtraction) tuple.
        """
        with open(file_path, "r", encoding="utf-8") as f:
            letter_text = f.read()
        
        # 1. Heuristic Check (Anti-Grinch Filter)
        is_spam_heuristic, spam_reason = self._is_spam_heuristic(letter_text)
        
        if is_spam_heuristic:
            self.logger.warning(f"SPAM DETECTED (Heuristic) in {file_path.name}: {spam_reason}")
            
            # Create a dummy extraction for spam to skip LLM cost
            extraction = LetterExtraction(
                child=ChildData(
                    name="Unknown (Spam)", 
                    age=999, 
                    city="Unknown", 
                    country=CountryEnum.UNKNOWN, # Use Enum if possible or defaults
                    gender=GenderEnum.MALE
                ),
                goodness_score=0.1,
                gift_request=[],
                is_spam=True,
                spam_reason=spam_reason,
                letter_summary="Automatically blocked by heuristic filter."
            )
            
            # For heuristic spam, we might still want to return objects, 
            # OR logic in caller should decide to skip saving "Unknown" children.
            # But method signature requires returning them.
        else:
            # 2. Extract using LLM
            extraction = self.extract_from_text(letter_text)
            self.logger.info(f"Processed valid letter: {file_path.name}")
        
        # Create Child SQLModel object (identity only)
        child = Child(
            name=extraction.child.name,
            age=extraction.child.age,
            city=extraction.child.city,
            country=extraction.child.country,
            gender=extraction.child.gender
        )
        
        # Create Letter SQLModel object (includes behavior/requests)
        letter = Letter(
            content=letter_text,
            is_spam=extraction.is_spam,
            spam_reason=extraction.spam_reason,
            received_at=datetime.utcnow(),
            goodness_score=extraction.goodness_score,
            gift_request=extraction.gift_request
        )
        
        return child, letter, extraction
    
    def extract_batch(
        self,
        limit: Optional[int] = None,
        only_valid: bool = False,
        only_spam: bool = False
    ) -> List[Tuple[Child, Letter, LetterExtraction]]:
        """
        Extract data from multiple letters.
        
        Args:
            limit: Max number of letters to process (None = all)
            only_valid: If True, only process child_*.txt files
            only_spam: If True, only process grinch_*.txt files
        
        Returns:
            List of (Child, Letter, LetterExtraction) tuples
        """
        results = []
        
        # Get files based on filters
        if only_valid:
            files = list(self.letters_dir.glob("child_*.txt"))
        elif only_spam:
            files = list(self.letters_dir.glob("grinch_*.txt"))
        else:
            files = list(self.letters_dir.glob("*.txt"))
        
        # Apply limit
        if limit:
            files = files[:limit]
        
        print(f"📬 Processing {len(files)} letters...")
        
        for i, file_path in enumerate(files):
            try:
                child, letter, extraction = self.extract_from_file(file_path)
                results.append((child, letter, extraction))
                status = "🛑 SPAM" if letter.is_spam else "✓ Valid"
                print(f"  {status} [{i+1}/{len(files)}] {file_path.name}")
            except Exception as e:
                print(f"  ✗ [{i+1}/{len(files)}] {file_path.name}: {e}")
        
        return results


# Quick test function
def test_extraction():
    """Test extraction on a single letter."""
    extractor = LetterExtractor()
    
    # Test on first valid letter
    test_file = Path("data/test_letters/child_italy_000.txt")
    if test_file.exists():
        child, letter, extraction = extractor.extract_from_file(test_file)
        print(f"\n🎄 Extracted from {test_file.name}:")
        print(f"  Child: {child.name}, {child.age}yo, {child.country}")
        print(f"  Goodness: {letter.goodness_score}, Gifts: {letter.gift_request}")
        print(f"  Coal: {letter.coal_qty_kg}kg")
        print(f"  Is Spam: {letter.is_spam}")
    else:
        print(f"Test file not found: {test_file}")


if __name__ == "__main__":
    test_extraction()
