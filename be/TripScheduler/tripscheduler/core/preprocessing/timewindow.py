from tripscheduler.utils.time import time_to_minutes, adjust_for_midnight
from tripscheduler.utils.window_utils import intersect_interval, subtract_intervals


def compute_meal_intervals(meal_preferences: dict, global_start: int, global_end: int) -> dict:
    intervals = {}
    for meal, times in meal_preferences.items():
        if not times or len(times) != 2:
            continue
        meal_start = time_to_minutes(times[0])
        meal_end = time_to_minutes(times[1])
        meal_start, meal_end = adjust_for_midnight(meal_start, meal_end)

        adjusted_start = max(global_start, meal_start - 60)
        adjusted_end = min(global_end, meal_end + 60)

        if adjusted_start < adjusted_end:
            intervals[meal] = (adjusted_start, adjusted_end)
    return intervals

def compute_effective_window(place: dict, global_start: int, global_end: int) -> tuple:
    place_open = time_to_minutes(place["open_time"])
    place_close = time_to_minutes(place["close_time"])

    # open_time 또는 close_time이 None인 경우 24시간 운영으로 간주
    if place_open is None:
        place_open = 0  # 00:00
    if place_close is None:
        place_close = 1440  # 24:00 (다음날 00:00)

    place_open, place_close = adjust_for_midnight(place_open, place_close)

    effective_open = max(place_open, global_start)
    effective_close = min(place_close, global_end)
    return effective_open, effective_close

def compute_operational_windows(place: dict, global_start: int, global_end: int) -> list:
    effective_open, effective_close = compute_effective_window(place, global_start, global_end)
    main_interval = (effective_open, effective_close)

    break_intervals = []
    if "break_time" in place and place["break_time"]:
        bt = place["break_time"]
        if len(bt) % 2 == 0:
            for i in range(0, len(bt), 2):
                try:
                    b_start = time_to_minutes(bt[i])
                    b_end = time_to_minutes(bt[i+1])
                    b_start, b_end = adjust_for_midnight(b_start, b_end)
                    inter = intersect_interval(effective_open, effective_close, b_start, b_end)
                    if inter:
                        break_intervals.append(inter)
                except Exception as e:
                    pass

    if break_intervals:
        segments = subtract_intervals(main_interval, break_intervals)
        return segments
    else:
        return [main_interval]

def compute_restaurant_windows(effective_open: int, effective_close: int, meal_intervals: dict, place_name: str):
    valid_windows = []
    for meal, (meal_start, meal_end) in meal_intervals.items():
        inter = intersect_interval(effective_open, effective_close, meal_start, meal_end)
        if inter:
            valid_windows.append((inter[0], inter[1], meal))
    if not valid_windows:
        raise ValueError(f"식당 {place_name}은(는) 식사 선호 시간에 부합하는 윈도우가 없습니다.")
    return valid_windows

def calculate_effective_time_windows(places: list, user: dict) -> dict:
    effective_windows = {}

    global_start = time_to_minutes(user["start_time"])
    global_end = time_to_minutes(user["end_time"])
    global_start, global_end = adjust_for_midnight(global_start, global_end)

    meal_preferences = user.get("meal_time_preferences", {})
    meal_intervals = compute_meal_intervals(meal_preferences, global_start, global_end)

    for place in places:
        operational_segments = compute_operational_windows(place, global_start, global_end)

        if place.get("category") == "restaurant":
            restaurant_windows = []
            for segment in operational_segments:
                seg_start, seg_end = segment
                try:
                    windows = compute_restaurant_windows(seg_start, seg_end, meal_intervals, place["name"])
                    restaurant_windows.extend(windows)
                except ValueError:
                    continue
            if not restaurant_windows:
                raise ValueError(f"식당 {place['name']}은(는) 식사 선호 시간에 부합하는 윈도우가 없습니다.")
            effective_windows[place["id"]] = restaurant_windows
        else:
            effective_windows[place["id"]] = [(start, end, None) for (start, end) in operational_segments]

    return effective_windows
