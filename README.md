# Personal Health & Wellness Aggregator

This project is a tiny data-engineering exercise:
merge fragmented sleep and workout data from different timezones into a single, normalized daily view.

It:

- Reads sleep data in UTC (sleep.json)
- Reads workout data in local time (workouts.json, e.g. PDT / PST)
- Normalizes everything to UTC
- Aggregates by day (UTC date)
- Writes a combined merged.json file with daily totals and event lists
- Prints out summary statistics to terminal


## 1. Data Format
### 1.1 Sleep Data (sleep.json)
Timestamps are in UTC ISO 8601 with Z.
Example:
```json
[
  {
    "sleep_id": 1,
    "start": "2023-10-01T06:30:00Z",
    "end": "2023-10-01T14:30:00Z",
    "duration_hours": 8.0
  }
]
```
### 1.2 Activity Data (workouts.json)

Local timestamps, with timezone abbreviation (e.g. PDT / PST).
Wrapped in a workouts array.
```json
{
  "workouts": [
    {
      "id": 1,
      "type": "Cycling",
      "timestamp_local": "2023-10-01 18:00:00 PDT",
      "duration_minutes": 60,
      "calories_burned": 600
    }
  ]
}
```
## 2. Output Format (merged.json)
The script writes a merged.json file that groups all events by UTC day, keyed by "YYYY-MM-DD".
Example entry:
```json
{
  "2023-10-02": {
    "events": [
      {
        "start": "2023-10-02T23:30:00Z",
        "end": "2023-10-03T07:30:00Z",
        "duration_hours": 8.0,
        "event_type": "sleep"
      },
      {
        "type": "Cycling",
        "timestamp_local": "2023-10-01 18:00:00 PDT",
        "duration_minutes": 60,
        "calories_burned": 600,
        "event_type": "workout",
        "utc_time": "2023-10-02T01:00:00+00:00"
      }
    ],
    "total_sleep_hours": 8.0,
    "total_calories": 600,
    "training_types": ["Cycling"],
    "total_workout_minutes": 60
  }
}
```
Some notes:
- Sleep events:
  - event_type: "sleep"
  - Attributed to the UTC date of start.
- Workout events:
  - event_type: "workout"
  - Original timestamp_local kept for reference.
  - Normalized UTC time stored (e.g. "utc_time": "2023-10-02T01:00:00+00:00").
  - Attributed to the UTC date of that UTC timestamp.
- Per-day aggregates:
  - total_sleep_hours
  - total_calories
  - training_types (unique list)
  - total_workout_minutes
 
# Design Choices
- Time standard: All grouping is done by UTC date to avoid ambiguity (this can in pratical use be converted more simply to the local time of the us4er).
- Sleep attribution: Sleep is attributed to the UTC date of its start timestamp, not the end.
- Workout attribution: Workouts are parsed as local (PDT/PST) and converted to UTC before grouping.
- Libraries over manual math: Uses zoneinfo and dateutil instead of manually subtracting 7/8 hours, to avoid subtle DST bugs.
- JSON-friendly: Sets (like training_types) are converted to lists before writing to JSON.

# AI Usage
- used for developing some of the tests, making sure to check the expected behavior (made it easier to have many large sets of data)
- used for writing the regex for datetime parsing before switching to use dateutil parsing
 
# Usage

From the repo root:
```python main.py --sleep-data sleep.json --activity-data workouts.json```
or, with short flags:
```python main.py -s sleep.json -a workouts.json```


Behavior:
- Prints counts of loaded records.
- Runs normalization + merge.
- Writes merged.json to the current directory.
- Returns the merged Python dict from norm_and_merge.
- You can also run with only one dataset:
```
python main.py -s sleep.json
python main.py -a workouts.json
```
In those cases, the script just writes the normalized data for that side.



