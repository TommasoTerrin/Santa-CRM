"""
Loader Module for Elf-ETL.
Responsible for saving extracted data to the database.
"""
from sqlmodel import Session, select
from models import Child, Letter
from schemas import LetterExtraction
from typing import Tuple

class Loader:
    def __init__(self, session: Session):
        self.session = session

    def load_letter(self, child: Child, letter: Letter) -> Tuple[Child, Letter]:
        """
        Saves the child and letter to the database.
        """
        # TODO: Implement duplicate check for Child based on name/city/etc.
        # For now, we assume every letter comes from a new child entry or we just insert blindly.
        # Ideally: existing_child = session.exec(select(Child).where(Child.name == child.name)).first()
        
        # Add objects to session
        self.session.add(child)
        self.session.commit()
        self.session.refresh(child)
        
        # Link letter to child
        letter.child_id = child.id
        self.session.add(letter)
        self.session.commit()
        self.session.refresh(letter)
        
        return child, letter
