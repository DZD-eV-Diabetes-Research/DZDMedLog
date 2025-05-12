import inspect

import types

frame = inspect.stack()[1].frame
globals_in_caller = frame.f_globals
print("--------")
for index, frame_info in enumerate(inspect.stack()):
    print(index, frame_info.frame)
print(globals_in_caller.get("__name__"))


def run_all_tests_from_caller():
    # Get the caller's frame
    frame = inspect.stack()[1].frame
    globals_in_caller = frame.f_globals

    # Only run if the caller is __main__
    if globals_in_caller.get("__name__") != "__main__":
        return

    # Find all functions starting with "test_"
    test_functions = [
        func
        for name, func in globals_in_caller.items()
        if name.startswith("test_") and isinstance(func, types.FunctionType)
    ]

    for test in test_functions:
        print(f"Running {test.__name__}...")
        try:
            test()
            print(f"{test.__name__} passed.")
        except Exception as e:
            print(f"{test.__name__} failed with error: {e}")
