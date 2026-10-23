async def handled(read, log):
    try:
        await read()
        log('saved')
    except ValueError:
        log('locked')
        return False
    except Exception as error:
        log('failed', error)
        return False
    return True

