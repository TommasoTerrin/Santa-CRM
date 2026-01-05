from pydantic import BaseModel, Field
from typing import Optional
try:
    from .models import CountryEnum, GenderEnum
except ImportError:
    from core.models import CountryEnum, GenderEnum


class ChildData(BaseModel):
    """Pydantic model for child identity data extraction."""
    name: str = Field(description="Child's first name")
    age: int = Field(ge=1, description="Child's age")
    city: Optional[str] = Field(default=None, description="City if mentioned")
    country: CountryEnum = Field(
        description="Country (lowercase). Use 'unknown' if not in the list."
    )
    gender: GenderEnum = Field(
        description="Gender inferred from name or context"
    )


class LetterExtraction(BaseModel):
    """
    Composite model for extracting all information from a letter.
    Contains child identity + this year's behavior/requests.
    """
    child: ChildData = Field(description="Child identity information")
    
    # Per-letter data (behavior and requests for THIS year)
    goodness_score: float = Field(
        ge=0.1, le=1.0,
        description="Score 0.1-1.0 based on behavior described in letter. 1.0=very good, 0.1=very naughty"
    )
    gift_request: list[str] = Field(
        description="List of gifts requested in this letter"
    )
    
    # Spam detection
    is_spam: bool = Field(
        default=False,
        description="True if letter appears to be from the Grinch (spam)"
    )
    spam_reason: Optional[str] = Field(
        default=None,
        description="Reason for spam classification (e.g., 'Signed by Grinch', 'Threatening content')"
    )
    letter_summary: str = Field(
        description="Brief 1-2 sentence summary of the letter content"
    )

