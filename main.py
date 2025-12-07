from argparse import ArgumentParser
from collections import defaultdict
from datetime import datetime
import json
from zoneinfo import ZoneInfo


USER_TZ = ZoneInfo("America/Los_Angeles")
UTC = ZoneInfo("UTC")

def parse_arguments():
    parser = ArgumentParser()
    parser.add_argument("--sleep-data", "-s",
                        help="Path to sleep data file",
                        required=False)
    parser.add_argument("--activity-data", "-a",
                        help="Path to activity data file",
                        required=False)
    args = parser.parse_args()
    return args

def load_data(file_path):
    with open(file_path, "r") as f:
        return json.load(f)

def norm_sleep_day(sleep_data):
    
    sleep_data_by_day = defaultdict(dict)
    for rec in sleep_data:
        start_utc = datetime.fromisoformat(rec["start"].replace("Z", "+00:00"))

        duration = rec["duration_hours"]

        start_local = start_utc.astimezone(USER_TZ)
        day_str = start_local.date().isoformat()
        
        if day_str not in sleep_data_by_day:
            sleep_data_by_day[day_str]["events"] = []
            sleep_data_by_day[day_str]["total_sleep_hours"] = 0
        sleep_data_by_day[day_str]["events"].append(
            {k: v for k, v in rec.items() if k != "sleep_id"} | {"event_type": "sleep"}
        )
        sleep_data_by_day[day_str]["total_sleep_hours"] += duration

    return sleep_data_by_day

def parse_workout_local_timestamp(ts):

    base_dt = datetime.strptime(ts, "%Y-%m-%d %H:%M:%S %Z")

    # Attach user timezone (PST/PDT logic handled by ZoneInfo)
    return base_dt


def norm_activity_day(activity_data):
    act_data_by_day = defaultdict(dict)
    for rec in activity_data:
        time = parse_workout_local_timestamp(rec["timestamp_local"])
        calories = rec["calories_burned"]
        training_type = rec["type"]
        training_time = rec["duration_minutes"]

        time_local = time.astimezone(USER_TZ)
        day_str = time_local.date().isoformat()
        
        if day_str not in act_data_by_day:
            act_data_by_day[day_str]["events"] = []
            act_data_by_day[day_str]["total_calories"] = 0
            act_data_by_day[day_str]["training_types"] = set()
            act_data_by_day[day_str]["total_workout_minutes"] = 0
        act_data_by_day[day_str]["events"].append(
            {k: v for k, v in rec.items() if k != "id"} | {"event_type": "workout"}
        )
        act_data_by_day[day_str]["total_calories"] += calories
        act_data_by_day[day_str]["training_types"].add(training_type)
        act_data_by_day[day_str]["total_workout_minutes"] += training_time
    act_data_by_day = {
        day: {**vals, "training_types": list(vals["training_types"])}
        for day, vals in act_data_by_day.items()
    }
    print(act_data_by_day)
    return act_data_by_day

def merge(sleep_by_day, act_by_day):
    if not sleep_by_day:
        print("no sleep data")
        with open("merged.json", "w") as f:
            json.dump(act_by_day, f, indent=4)
    elif not act_by_day:
        print("no activity data")
        with open("merged.json", "w") as f:
            json.dump(sleep_by_day, f, indent=4)
    else:
        combined = {}
        all_days = sorted(set(sleep_by_day.keys()) | set(act_by_day.keys()))
        for day in all_days:
            sleep = sleep_by_day.get(day, {})
            activity = act_by_day.get(day, {})
            events = sleep.get("events", [])+ (activity.get("events", []))
            combined[day] = {**sleep, **activity, "events": events}


        with open("merged.json", "w") as f:
            json.dump(combined, f, indent=4)
        



def norm_and_merge(sleep_data, activity_data):
    if activity_data:
        activity_data = activity_data.get("workouts", [])
        print(f"Loaded {len(activity_data)} activity entries.")
    norm_sleep = norm_sleep_day(sleep_data)
    norm_activity = norm_activity_day(activity_data)
    merge(norm_sleep, norm_activity)


def main():
    args = parse_arguments()
    sleep = activity = None
    if args.sleep_data:
        print(f"Sleep data file path: {args.sleep_data}")
        sleep = load_data(args.sleep_data)
        print(f"Loaded {len(sleep)} sleep entries.")
    if args.activity_data:
        print(f"Activity data file path: {args.activity_data}")
        activity = load_data(args.activity_data)
    
    norm_and_merge(sleep, activity)



if __name__ == "__main__":
    main()