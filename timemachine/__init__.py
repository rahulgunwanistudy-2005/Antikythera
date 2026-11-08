"""Antikythera temporal, matched-cohort analysis (standard library only)."""
from .engine import analyze, era_ablation, validate_dataset, wilson_interval, calibration, file_drawer_sensitivity, analysis_slices

__all__ = ['analyze', 'era_ablation', 'validate_dataset', 'wilson_interval', 'calibration', 'file_drawer_sensitivity', 'analysis_slices']
