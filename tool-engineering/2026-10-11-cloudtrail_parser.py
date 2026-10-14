"""Checkpoint snapshot (2026-10-11) of the learner's CloudTrail loader/validator.

Reconstructed from code shown in chat; NOT independently executed against actual logs.
No AWS account data or CloudTrail event history is included.
"""

import json


def load_events(filename):
    try:
        with open(filename, "r") as file:
            data = json.load(file)
            return data, "Success: JSON loaded"
    except FileNotFoundError:
        return None, "Error: File not found"
    except json.JSONDecodeError:
        return None, "Error: Invalid JSON"


def validate_cloudtrail(data):
    if data is None:
        return False, "Error: Data is None"
    elif not isinstance(data, dict):
        return False, "Error: Data is not dictionary"
    elif "Records" not in data:
        return False, "Error: Invalid CloudTrail structure"
    elif not isinstance(data["Records"], list):
        return False, "Error: Invalid Records type"
    else:
        for event in data["Records"]:
            if not isinstance(event, dict):
                return False, "Error: Invalid Event type"
        return True, "Success: Valid Cloudtrail"


if __name__ == "__main__":
    data, message = load_events("event_short.json")

    if data is None:
        print(message)
        exit()

    validation, message = validate_cloudtrail(data)

    if not validation:
        print(message)
        exit()

    print(len(data["Records"]))
