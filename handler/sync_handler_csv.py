
from DAO.output_schema_dao import OutputSchemaDAO
from handler.sync_handler import SyncHandlerExcel
from config.logger import log_errors

class SyncHandlerCSV:
    def __init__(self, session):
        self.session = session
        self.output_schema_dao = OutputSchemaDAO(self.session)

    @log_errors
    def handle(self, sync_metadata, files):
        output_schemas_dict = self.get_output_schemas(sync_metadata=sync_metadata)

        for file in files:
            filename = file.filename

            print(filename)

    @log_errors
    def get_output_schemas(self, sync_metadata):
        output_schemas_dict = {}
        output_schemas = self.output_schema_dao.get_output_schemas_by_user_uuid(user_uuid=sync_metadata["user_uuid"])
        for output_schema in output_schemas:
            output_schemas_dict[output_schema["schema_uuid"]] = output_schema["schema"]
        return output_schema