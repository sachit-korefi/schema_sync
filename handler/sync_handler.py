from DAO.output_schema_dao import OutputSchemaDAO
from handler.sync_handler import SyncHandlerExcel
from handler.sync_handler import SyncHandlerCSV
from config.logger import log_errors

class SyncHandler:
    def __init__(self, session):
        self.session = session
        self.output_schema_dao = OutputSchemaDAO(self.session)
        self.sync_handler_csv = SyncHandlerCSV()
        self.sync_handler_excel = SyncHandlerExcel()

    @log_errors
    def handle(self, sync_metadata, files):
        processed_files = []
        output_schemas_dict = self.get_output_schemas(sync_metadata=sync_metadata)

        for file in files:
            filename = file.filename
            file_metadata = sync_metadata["file_metadatas"].get(filename, None)
            if file_metadata is None:
                processed_files.append({
                    "file_name": filename,
                    "file": None,
                    "error": True,
                    "error_message": "Schema not found"
                })
                continue
            file_extension = filename.split('.')[-1]
            processed_file = None
            if file_extension == 'csv':
                processed_file = self.sync_handler_csv.handle(file_metadata, file)
            elif file_extension in ['xlsx', 'xls']:
                processed_file = self.sync_handler_excel.handle(file_metadata, file)
            if processed_file is not None:
                processed_files.append({
                    "file_name": filename,
                    "file": processed_file,
                    "error": False,
                    "error_message": None
                })
        return processed_files

    @log_errors
    def get_output_schemas(self, sync_metadata):
        output_schemas_dict = {}
        output_schemas = self.output_schema_dao.get_output_schemas_by_user_uuid(user_uuid=sync_metadata["user_uuid"])
        for output_schema in output_schemas:
            output_schemas_dict[output_schema["schema_uuid"]] = output_schema["schema"]
        return output_schemas_dict