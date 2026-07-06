"""Pipeline package - orchestrates the full AI request flow."""

__version__ = "0.1.0"

from pipeline.service import PipelineResult, PipelineService

__all__ = ["PipelineResult", "PipelineService"]
