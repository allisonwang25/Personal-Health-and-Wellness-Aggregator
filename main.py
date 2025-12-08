from argparse import ArgumentParser
from collections import defaultdict
from datetime import datetime
from dateutil import parser
import json
from zoneinfo import ZoneInfo


HEALTHY_SLEEP_HOUR = 7
HEALTH_ACTIVITY_MIN = 30

UTC = ZoneInfo("UTC")

# Helper Functions
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
def parse_time(ts):
    return parser.parse(ts)


# Normalize Data
def norm_sleep_day(sleep_data): 
    sleep_data_by_day = defaultdict(dict)
    for rec in sleep_data:
        start_utc = parse_time(rec["start"])

        duration = rec["duration_hours"]

        start_utc = start_utc.astimezone(UTC)
        day_str = start_utc.date().isoformat()
        
        if day_str not in sleep_data_by_day:
            sleep_data_by_day[day_str]["events"] = []
            sleep_data_by_day[day_str]["total_sleep_hours"] = 0
        sleep_data_by_day[day_str]["events"].append(
            {k: v for k, v in rec.items() if k != "sleep_id"} | {"event_type": "sleep"} | {"utc_time": start_utc.isoformat()}
        )
        sleep_data_by_day[day_str]["total_sleep_hours"] += duration

    return sleep_data_by_day
def norm_activity_day(activity_data):
    act_data_by_day = defaultdict(dict)
    for rec in activity_data:
        time = parse_time(rec["timestamp_local"])
        calories = rec["calories_burned"]
        training_type = rec["type"]
        training_time = rec["duration_minutes"]

        time_utc = time.astimezone(UTC)
        day_str = time_utc.date().isoformat()
        
        if day_str not in act_data_by_day:
            act_data_by_day[day_str]["events"] = []
            act_data_by_day[day_str]["total_calories"] = 0
            act_data_by_day[day_str]["training_types"] = set()
            act_data_by_day[day_str]["total_workout_minutes"] = 0
        act_data_by_day[day_str]["events"].append(
            {k: v for k, v in rec.items() if k != "id"} | {"event_type": "workout"} | {"utc_time": time_utc.isoformat()}
        )
        act_data_by_day[day_str]["total_calories"] += calories
        act_data_by_day[day_str]["training_types"].add(training_type)
        act_data_by_day[day_str]["total_workout_minutes"] += training_time
    act_data_by_day = {
        day: {**vals, "training_types": list(vals["training_types"])}
        for day, vals in act_data_by_day.items()
    }
    return act_data_by_day
def merge(sleep_by_day, act_by_day):
    if not sleep_by_day:
        print("no sleep data")
        with open("merged.json", "w") as f:
            json.dump(act_by_day, f, indent=4)
        return act_by_day
    elif not act_by_day:
        print("no activity data")
        with open("merged.json", "w") as f:
            json.dump(sleep_by_day, f, indent=4)
        return sleep_by_day
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
        return combined

def norm_and_merge(sleep_data, activity_data):
    if activity_data:
        activity_data = activity_data.get("workouts", [])
        print(f"Loaded {len(activity_data)} activity entries.")
    norm_sleep = norm_sleep_day(sleep_data) if sleep_data else {}
    norm_activity = norm_activity_day(activity_data) if activity_data else {}
    return merge(norm_sleep, norm_activity)


# Statistic Calculations
def sleep_stat(merged):
    max_day = None
    max_time = 0
    min_time = float('inf')
    min_day = None
    for day in merged:
        time = merged[day].get("total_sleep_hours", 0)
        if max_time < time:
            max_day = day
            max_time = time
        if min_time > time:
            min_day = day
            min_time = time
    return max_day, max_time, min_day, min_time
def activity_stat(merged):
    max_day = None
    max_cal = 0
    min_cal = float('inf')
    min_day = None
    for day in merged:
        cal = merged[day].get("total_calories", 0)
        if max_cal < cal:
            max_day = day
            max_cal = cal
        if min_cal > cal:
            min_day = day
            min_cal = cal
    return max_day, max_cal, min_day, min_cal
def is_healthy(day):
    sleep = day.get("total_sleep_hours", 0)
    activity_stat = day.get("total_calories", 0)
    return sleep >= HEALTHY_SLEEP_HOUR and activity_stat >= HEALTH_ACTIVITY_MIN
def longest_streak_of_health(merged):
    cur_streak = 0
    max_streak = 0
    start_streak = end_streak = None
    cur_streak_start = None
    first = True
    for day in merged:
        cur_day = merged[day]

        if is_healthy(cur_day):
            cur_streak+=1
            if first:
                cur_streak_start = day
                first = False
        else:
            if cur_streak > max_streak:
                max_streak = cur_streak
                start_streak = cur_streak_start
                end_streak = day
            cur_streak = 0
            first = True

    return max_streak, start_streak, end_streak
def average_calories_days_sleep_6_hour(merged):
    total = 0
    days = 0
    for day in merged:
        cur_day = merged[day]
        calories = cur_day.get("total_calories", 0)
        sleep = cur_day.get("total_sleep_hours", 0)
        if sleep < 6:
            total += calories
            days += 1
    return total / days


def summary(merged):
    print("="*50)
    print("SUMMARY OF HEALTH DATA:")
    print(f"- {len(merged)} days of health data recorded")
    max_day, max_time, min_day, min_time = sleep_stat(merged)
    sleep_stat_str = "- "
    if max_day:
        sleep_stat_str += f"Max Time Slept: {max_time} (on {max_day})"
    if min_day:
        sleep_stat_str += f"; Min Time Slept: {min_time} (on {min_day})"
    print(sleep_stat_str)

    max_day, max_cal, min_day, min_cal = activity_stat(merged)
    activity_stat_str = "- "
    if max_day:
        activity_stat_str += f"Max Calories Burnt: {max_cal} (on {max_day})"
    if min_day:
        activity_stat_str += f"; Min Calories Burnt: {min_cal} (on {min_day})"
    print(activity_stat_str)

    streak, start, end = longest_streak_of_health(merged)
    streak_str = f"- Longest streak of Healthy Days (7+ hours of sleep and 30 minutes of exercise): {streak} days"
    if start and end:
        streak_str += f"({start} - {end})"
    print(streak_str)

    average_cal = average_calories_days_sleep_6_hour(merged)
    print(f"- Average calories on Days with < 6 hours of sleep: {round(average_cal,2)} calories")
    
    print("="*50)



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
    
    merged = norm_and_merge(sleep, activity)
    summary(merged)



if __name__ == "__main__":
    main()