from DAO.output_schema_dao import OutputSchemaDAO
from config.logger import log_errors

class SyncHandlerCSV:
    def __init__(self, session):
        self.session = session
        self.output_schema_dao = OutputSchemaDAO(self.session)

    @log_errors
    def handle(self, sync_metadata, file):
    