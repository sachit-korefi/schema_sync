from config.logger import log_errors

class SyncHandlerExcel:
    def __init__(self):
        pass

    @log_errors
    async def handle(self, sync_metadata, files):
        print(sync_metadata)
        print("-"*40)
        pass