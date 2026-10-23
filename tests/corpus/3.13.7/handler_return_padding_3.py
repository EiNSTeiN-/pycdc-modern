# The .pyc variants insert 1, 3 or 9 NOPs before each RETURN_VALUE.
# Regenerate with the matching CPython: python tools/compile_padded_returns.py
# Jump targets and exception-table boundaries are relocated with the padding.

async def handled(read, log):
    try:
        await read()
        log("saved")
    except ValueError:
        log("locked")
        return False
    except Exception as error:
        log("failed", error)
        return False
    return True
