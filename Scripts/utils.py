"""Small helpers shared by several modules."""


def time_to_minutes(clock_time):
    """Convert 'HH:MM:SS' into minutes since midnight (seconds are ignored): '05:07:30' -> 307."""
    hours, minutes, _seconds = clock_time.split(":")
    return int(hours) * 60 + int(minutes)


def minutes_to_hhmm(minutes):
    """Convert minutes since midnight into 'HH:MM': 307 -> '05:07'."""
    minutes = int(minutes)
    return f"{minutes // 60:02d}:{minutes % 60:02d}"
