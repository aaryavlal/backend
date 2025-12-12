from typing import Any, Dict, List

import rustism


def get_sequential() -> List[Dict[str, Any]]:
    """
    Execute sequential task simulation from Rust component

    Returns:
        List of dictionaries containing task execution data with keys:
            - task_id: The unique ID (in sequence) for the task
            - start_ms: Start time in milliseconds
            - end_ms: End time in milliseconds
            - duration_ms: Calculated duration of the task
    """

    # Call the Rust function to get the TaskRecord object
    task_records = rustism.sequential()

    return task_records
