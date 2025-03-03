from enum import Enum

class AppState(Enum):
    FILE_SELECTION = "file_selection"
    PROCESSING = "processing"
    RESULTS = "results"
    COMPLETE = "complete"
    ERROR = "error"