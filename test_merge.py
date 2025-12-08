import pytest
from main import norm_and_merge  # adjust this import to your code


def test_late_night_workout_and_sleep_same_local_day():
    """
    A workout at 11:30 PM local time and a sleep session starting at
    6:30 AM UTC (which is 11:30 PM local the previous day) should both
    be grouped under the SAME local calendar day.
    """

    # Sleep data in UTC (as in sleep.json)
    # 2023-10-02T06:30:00Z = 2023-10-01 23:30:00 PDT
    sleep_data = [
        {
            "start": "2023-10-02T06:30:00Z",
            "end": "2023-10-02T14:30:00Z",
            "duration_hours": 8,
        }
    ]

    # Workout data in LOCAL time (as in workouts.json)
    # 2023-10-01 23:00 local = same local day key as above (2023-10-01)
    activity_data = {
        "workouts":[
            {
                "timestamp_local": "2023-10-01 23:00:00 PDT",
                "duration_minutes": 45,
                "calories_burned": 300,
                "type": "Running",
            }
        ]
    }

    merged = norm_and_merge(sleep_data, activity_data)

    # We expect everything to show up on the local date "2023-10-01"
    assert set(merged.keys()) == {"2023-10-01"}
    day = merged["2023-10-01"]

    # Should have both a sleep event and a workout event
    event_types = {e["event_type"] for e in day["events"]}
    assert event_types == {"sleep", "workout"}

    # Basic sanity checks on aggregation
    assert day["total_workout_minutes"] == 45
    assert day["total_calories"] == 300
    assert day["total_sleep_hours"] == 8

def test_early_morning_utc_belongs_to_previous_local_day():
    """
    A sleep record starting at 2023-10-02T05:00:00Z should appear
    as 2023-10-01 local date (PDT), so the day key must be 2023-10-01.
    """

    sleep_data = [
        {
            "start": "2023-10-02T05:00:00Z",  # 22:00 on 2023-10-01 PDT
            "end": "2023-10-02T13:00:00Z",
            "duration_hours": 8,
        }
    ]
    activity_data = {}  # no workouts for simplicity

    merged = norm_and_merge(sleep_data, activity_data)

    assert set(merged.keys()) == {"2023-10-01"}
    day = merged["2023-10-01"]

    # Only a sleep event
    assert len(day["events"]) == 1
    assert day["events"][0]["event_type"] == "sleep"

def test_midday_and_evening_workouts_same_local_day():
    """
    Two workouts on the same local calendar day should both land
    under the same day key, regardless of UTC offset.
    """

    sleep_data = []

    activity_data = {
        "workouts": [
            {
                "timestamp_local": "2023-10-10 12:00:00 PDT",  # noon
                "duration_minutes": 30,
                "calories_burned": 200,
                "type": "Cycling",
            },
            {
                "timestamp_local": "2023-10-10 21:30:00 PDT",  # 9:30 pm
                "duration_minutes": 60,
                "calories_burned": 400,
                "type": "Weights",
            },
        ]
    }

    merged = norm_and_merge(sleep_data, activity_data)

    assert set(merged.keys()) == {"2023-10-10"}
    day = merged["2023-10-10"]

    assert len(day["events"]) == 2
    assert day["total_workout_minutes"] == 30 + 60
    assert day["total_calories"] == 200 + 400

    # training_types should be deduplicated but JSON-friendly (list)
    assert set(day["training_types"]) == {"Cycling", "Weights"}



def test_day_with_only_sleep():
    sleep_data = [
        {
            "start": "2023-10-01T08:00:00Z",
            "end": "2023-10-01T16:00:00Z",
            "duration_hours": 8,
        }
    ]

    activity_data = {}  # no workouts

    merged = norm_and_merge(sleep_data, activity_data)

    # Should produce exactly 1 day
    assert list(merged.keys()) == ["2023-10-01"]

    day = merged[list(merged.keys())[0]]
    event_types = {e["event_type"] for e in day["events"]}
    assert event_types == {"sleep"}
    assert "total_calories" not in day or day["total_calories"] == 0



