from enum import Enum
from datetime import datetime
from sqlmodel import Field, SQLModel, Relationship, Column, JSON
from pydantic import field_validator, model_validator
from typing import Optional


class CountryEnum(str, Enum):
    ITALY = "italy"
    USA = "usa"
    CHINA = "china"
    RUSSIA = "russia"
    BRAZIL = "brazil"
    AUSTRALIA = "australia"
    UNKNOWN = "unknown"


class GenderEnum(str, Enum):
    MALE = "male"
    FEMALE = "female"


class Child(SQLModel, table=True):
    """
    Represents a child who wrote a letter to Santa.
    Contains identity information.
    """
    id: int | None = Field(default=None, primary_key=True)
    name: str = Field(index=True, max_length=100)
    age: int = Field(ge=1)
    city: str | None = Field(default=None, max_length=100)
    country: CountryEnum = Field(
        description="Country name (normalized to lowercase)."
    )
    gender: GenderEnum = Field(
        description="Gender inferred from name"
    )
    
    letters: list["Letter"] = Relationship(back_populates="child")
    
    @field_validator('city')
    @classmethod
    def normalize_city(cls, v: str | None) -> str | None:
        return v.strip() if v else None


class Letter(SQLModel, table=True):
    """
    Represents a letter received from a child.
    """
    id: int | None = Field(default=None, primary_key=True)
    content: str = Field(description="Full text content")
    is_spam: bool = Field(default=False)
    spam_reason: str | None = Field(default=None)
    received_at: datetime = Field(default_factory=datetime.utcnow)
    
    goodness_score: float = Field(ge=0.1, le=1.0)
    # Using sa_column=Column(JSON) for both SQLite and Postgres
    gift_request: list[str] = Field(sa_column=Column(JSON), default_factory=list)
    coal_qty_kg: int = Field(default=0)
    
    child_id: int | None = Field(default=None, foreign_key="child.id")
    child: Child | None = Relationship(back_populates="letters")
    
    @model_validator(mode='after')
    def validate_goodness_logic(self):
        score = self.goodness_score
        
        if score <= 0.4:
            self.coal_qty_kg = int(1 / score)
        else:
            self.coal_qty_kg = 0
        
        if 0.5 <= score <= 0.6:
            self.gift_request = self.gift_request[:1]
        elif 0.7 <= score <= 0.8:
            self.gift_request = self.gift_request[:2]
        elif 0.9 <= score <= 1.0:
            self.gift_request = self.gift_request[:3]
        
        return self

