from typing import Union


def asymptotic_average_builder(new_part: Union[float, int]):
    """
    Given a percentage as a float, return an interpolation function based on it.

    Example:
       ``interpolate_builder(10)``

    The returned function will use .1 of the new value and .9 of the old value
    to calculate the current value.

    :param new_part: float
    :return: Callable[[Any, Any], Any]
    """
    new = new_part / 100.0
    old = 1 - new

    def interpolate(old_input, new_input):
        return old_input * old + new_input * new

    return interpolate


def quadratic_ease_in(run_time, start, change, duration):
    run_time /= duration
    return change*run_time*run_time + start


def quadratic_ease_out(run_time, start, change, duration):
    run_time /= duration
    return -change * run_time * (run_time - 2) + start
