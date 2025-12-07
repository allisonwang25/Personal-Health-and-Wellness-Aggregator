
from argparse import ArgumentParser
import json
from datetime import datetime, timedelta
import random
from zoneinfo import ZoneInfo
NUM_SLEEP_ENTRIES = 5
NUM_WORKOUT_ENTRIES = 5

# helper functions for data generation
def random_datetime(start_date, end_date, tz):
    """Return a random datetime between two dates in the given timezone."""
    delta = end_date - start_date
    random_seconds = random.randint(0, int(delta.total_seconds()))
    naive_dt = start_date + timedelta(seconds=random_seconds)
    return naive_dt.replace(tzinfo=tz)  # attach timezone


def random_sleep_duration():
    """Random sleep duration in hours."""
    return round(random.uniform(5, 9), 1)  # between 5 and 9 hours

def random_workout_duration():
    """Random workout duration in minutes."""
    return random.randint(20, 90)  # 20 to 90 min

def calories_for_workout(workout_type, duration_minutes):
    """
    Very rough calories-per-minute estimate by workout type.
    These are toy values for demo purposes, not real physiology :)
    """
    cals_per_min = {
        "Running": 11,   # kcal / min
        "Cycling": 8,
        "Swimming": 10,
        "Yoga": 4,
        "HIIT": 12,
        "Weights": 6,
    }
    rate = cals_per_min.get(workout_type, 6)  # default rate
    return int(rate * duration_minutes)


def parse_arguments():
    parser = ArgumentParser()
    parser.add_argument("--sleep-data", "-s",
                        help="Generate sleep data file",
                        action='store_true')
    parser.add_argument("--activity-data", "-a",
                        help="Generate activity data file",
                        action='store_true')
    args = parser.parse_args()
    plan = []
    if args.sleep_data:
        plan.append("sleep")
    if args.activity_data:
        plan.append("activity")

    if not plan:
        parser.error("No generation option provided. Use --sleep-data and/or --activity-data.")
    return plan



def generate_sleep_data(date_start, date_end):
    print("Generating sleep data file...")

    utc = ZoneInfo("UTC")
    sleep_data = []

    for i in range(NUM_SLEEP_ENTRIES):
        start = random_datetime(date_start, date_end, utc)
        duration_hours = random_sleep_duration()
        end = start + timedelta(hours=duration_hours)

        sleep_data.append({
            "sleep_id": i + 1,
            "start": start.isoformat().replace("+00:00", "Z"),
            "end": end.isoformat().replace("+00:00", "Z"),
            "duration_hours": duration_hours
        })

    with open("sleep.json", "w") as f:
        json.dump(sleep_data, f, indent=2)


def generate_activity_data(date_start, date_end):
    print("Generating activity data file...")

    pst = ZoneInfo("America/Los_Angeles")
    workout_types = ["Running", "Cycling", "Swimming", "Yoga", "HIIT", "Weights"]
    workout_entries = []

    for i in range(NUM_WORKOUT_ENTRIES):
        t = random_datetime(date_start, date_end, pst)
        wtype = random.choice(workout_types)
        duration = random_workout_duration()
        calories = calories_for_workout(wtype, duration)

        workout_entries.append({
            "id": i + 1,
            "type": wtype,
            "timestamp_local": t.strftime("%Y-%m-%d %H:%M:%S %Z"),
            "duration_minutes": duration,
            "calories_burned": calories
        })

    workouts_json = {"workouts": workout_entries}

    with open("workouts.json", "w") as f:
        json.dump(workouts_json, f, indent=2)



def main():
    plan = parse_arguments()
    date_start = datetime(2023, 10, 1)
    date_end   = datetime(2023, 10, 31)
    for item in plan:
        if item == "sleep":
            generate_sleep_data(date_start, date_end)
            print("Sleep data file generated.")
        elif item == "activity":
            generate_activity_data(date_start, date_end)
            print("Activity data file generated.")

if __name__ == "__main__":
    main()