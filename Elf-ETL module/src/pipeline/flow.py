"""
Pipeline Flow Definition.
Assembles the FunctionalPipeline for Single File Processing.
"""
from datapizza.pipeline import FunctionalPipeline, Dependency
from core.database import engine
from sqlmodel import Session

from pipeline.components import (
    FileReader, GrinchFilter, GrinchLogger, 
    LLMExtractor, DatabaseLoader
)

def build_single_file_pipeline():
    """
    Builds a pipeline that processes a single file.
    Flow (Linear with Skip Logic): 
    Read -> Filter -> GrinchLogger (conditional) -> LLMExtractor (conditional) -> DatabaseLoader (conditional)
    """
    
    pipeline = (
        FunctionalPipeline()
        .run("read", FileReader()) 
        .run("filter", GrinchFilter(), dependencies=[Dependency("read", target_key="data")])
        .run("log", GrinchLogger(), dependencies=[Dependency("filter", target_key="data")])
        .run("extract", LLMExtractor(model_name="gemini-1.5-flash"), dependencies=[Dependency("filter", target_key="data")])
        .run("load", DatabaseLoader(session_factory=lambda: Session(engine)), dependencies=[Dependency("extract", target_key="data")])
    )
    
    return pipeline
