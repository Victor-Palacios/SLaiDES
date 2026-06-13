"""IR schema package — parse, validate, and export slidekit deck IR."""

from slidekit.ir.models import DeckIR
from slidekit.ir.parse import load, loads
from slidekit.ir.schema import get_schema, write_schema

__all__ = ["DeckIR", "load", "loads", "get_schema", "write_schema"]
