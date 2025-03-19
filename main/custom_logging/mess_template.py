from datetime import datetime


def def_runtime_mess(func_name: str, action: str, dt):
    """Returns a string message about the runtime of the def"""
    return f"{func_name}: RUNTIME of the {action} = {dt} sec."


def work_runtime_mess(action: str, start_t: datetime, end_t: datetime):
    """Returns a string message about the runtime of the action"""
    return f"--- RUNTIME of the {action} = {(end_t - start_t).total_seconds()}"
