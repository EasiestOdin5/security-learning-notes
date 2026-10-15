import argparse
import json
from pathlib import Path

import pandas as pd


# ==========================================
# LOAD AND VALIDATE
# ==========================================

def load_events(filename):
    try:
        with open(filename, "r", encoding="utf-8-sig") as file:
            data = json.load(file)
        return data, "Success: JSON loaded"
    except FileNotFoundError:
        return None, "Error: File not found"
    except (json.JSONDecodeError, UnicodeError):
        return None, "Error: Invalid JSON or encoding"


def validate_cloudtrail(data):
    if not isinstance(data, dict):
        return False, "Error: Data must be a dictionary"
    if not isinstance(data.get("Records"), list):
        return False, "Error: Missing or invalid Records list"
    if not all(isinstance(event, dict) for event in data["Records"]):
        return False, "Error: Records must contain event dictionaries"
    return True, "Success: Valid CloudTrail structure"


# ==========================================
# INVESTIGATION FUNCTIONS
# ==========================================

def find_events(df, event_name=None, start_time=None, end_time=None, identity=None):
    results = df

    if event_name is not None:
        results = results[results["eventName"] == event_name]

    if start_time is not None and end_time is not None and end_time < start_time:
        raise ValueError("End time cannot be earlier than start time")

    if start_time is not None:
        results = results[results["eventTime"] >= start_time]

    if end_time is not None:
        results = results[results["eventTime"] <= end_time]

    if identity is not None:
        results = results[
            results["userIdentity.arn"].str.contains(
                identity, case=False, regex=False, na=False
            )
        ]

    return results


def build_timeline(events, descending=False):
    return events.sort_values("eventTime", ascending=not descending)


def display_timeline(events, limit=10, columns=None):
    if columns is None:
        columns = [
            "eventTime",
            "eventName",
            "userIdentity.arn",
            "sourceIPAddress",
            "awsRegion"
        ]

    available = [column for column in columns if column in events.columns]

    print(
        events.reindex(columns=available)
        .head(limit)
        .to_string(index=False)
    )


def summarize_events(events, column="eventName"):
    return events[column].value_counts()


def group_events(events, columns):
    return (
        events.groupby(columns, dropna=False)
        .size()
        .sort_values(ascending=False)
    )


# ==========================================
# DETECTION FUNCTIONS
# ==========================================

def detect_create_policy_version(df):
    events = find_events(df, event_name="CreatePolicyVersion")

    if "requestParameters.setAsDefault" not in events.columns:
        alerts = events.iloc[0:0]
    else:
        errors = events.get(
            "errorCode",
            pd.Series(index=events.index, dtype="object")
        )

        alerts = events[
            (events["requestParameters.setAsDefault"] == True)
            & errors.isna()
        ]

    return {
        "rule": "IAM_DEFAULT_POLICY_VERSION_CREATED",
        "severity": "MEDIUM",
        "reason": "New IAM policy version created and set as default",
        "alerts": alerts
    }


def detect_set_default_policy_version(df):
    events = find_events(df, event_name="SetDefaultPolicyVersion")

    errors = events.get(
        "errorCode",
        pd.Series(index=events.index, dtype="object")
    )

    alerts = events[errors.isna()]

    return {
        "rule": "IAM_DEFAULT_POLICY_VERSION_CHANGED",
        "severity": "MEDIUM",
        "reason": "An existing IAM policy version was activated",
        "alerts": alerts
    }


def detect_create_access_key(df):
    events = find_events(df, event_name="CreateAccessKey")
    alerts = events[events["errorCode"].isna()]

    return {
        "rule": "IAM_ACCESS_KEY_CREATED",
        "severity": "MEDIUM",
        "reason": "An IAM access key was successfully created",
        "alerts": alerts
    }


# ==========================================
# REPORTING
# ==========================================

def report_detections(detection):
    alerts = detection["alerts"]

    print("\n=== CLOUDTRAIL SECURITY DETECTIONS ===")
    print("Rule:", detection["rule"])

    for _, event in alerts.iterrows():
        print("\nSeverity:", detection["severity"])
        print("Time:", event.get("eventTime"))
        print("Actor:", event.get("userIdentity.arn"))
        print("Policy:", event.get("requestParameters.policyArn"))
        print("Reason:", detection["reason"])
        print("Assessment: Requires investigation")

    print(f"\nTotal alerts: {len(alerts)}")


# ==========================================
# MAIN
# ==========================================

def main():
    parser = argparse.ArgumentParser(
        description="CloudTrail JSON investigation and detection tool"
    )

    parser.add_argument(
        "filename",
        type=Path,
        help="CloudTrail JSON file containing a Records list"
    )

    parser.add_argument(
        "--detect",
        action="store_true",
        help="Run all registered security detectors"
    )

    parser.add_argument(
        "--event",
        type=str,
        help="Find CloudTrail events by API name"
    )

    args = parser.parse_args()

    data, message = load_events(args.filename)

    if data is None:
        print(message)
        return

    valid, message = validate_cloudtrail(data)

    if not valid:
        print(message)
        return

    df = pd.json_normalize(data["Records"])

    if df.empty:
        print("No CloudTrail events found")
        return

    if "eventName" not in df.columns:
        print("Error: Missing eventName field")
        return

    df["eventTime"] = pd.to_datetime(
        df.get("eventTime"),
        utc=True,
        errors="coerce"
    )

    print(f"Loaded {len(df)} CloudTrail events")

    # Registered detection rules
    detectors = [
        detect_create_policy_version,
        detect_set_default_policy_version,
        detect_create_access_key,
    ]

    # Run all detectors
    if args.detect:
        for detector in detectors:
            result = detector(df)
            report_detections(result)

    # Search for events by API name
    if args.event:
        events = find_events(df, event_name=args.event)

        print(f"\n=== EVENTS: {args.event} ===")
        print(f"Matching events: {len(events)}")

        if not events.empty:
            columns = [
                "eventTime",
                "eventName",
                "userIdentity.arn",
                "userIdentity.accessKeyId",
                "requestParameters.userName",
                "responseElements.accessKey.accessKeyId",
                "errorCode"
            ]

            display_timeline(
                build_timeline(events),
                limit=50,
                columns=columns
            )

    if not args.detect and not args.event:
        print("Use --detect to run detection rules")
        print("Use --event EVENT_NAME to investigate an API")


if __name__ == "__main__":
    main()
