from enum import Enum

class AppState(Enum):
    """Enum for the AppState."""
    FILE_SELECTION = "file_selection"
    PROCESSING = "processing"
    RESULTS = "results"
    COMPLETE = "complete"
    ERROR = "error"
