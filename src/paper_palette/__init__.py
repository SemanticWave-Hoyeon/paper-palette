"""Publication-ready color palette generation."""

from ._palette import Palette
from ._presets import list_presets, preset_colors

PaperPalette = Palette

__all__ = ["Palette", "PaperPalette", "list_presets", "preset_colors"]
