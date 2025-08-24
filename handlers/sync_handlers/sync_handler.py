from DAO.output_schema_dao import OutputSchemaDAO
from handlers.sync_handlers.sync_handler_excel import SyncHandlerExcel
from handlers.sync_handlers.sync_handler_csv import SyncHandlerCSV
from config.logger import log_errors, logger

class SyncHandler:
    def __init__(self, session):
        self.session = session
        self.output_schema_dao = OutputSchemaDAO(self.session)
        self.sync_handler_csv = SyncHandlerCSV()
        self.sync_handler_excel = SyncHandlerExcel()

    @log_errors
    async def handle(self, sync_metadata, files):
        processed_files = []
        output_schemas_dict = self.get_output_schemas(sync_metadata=sync_metadata)

        for file in files:
            filename = file.filename
            logger.info(f"processing file : {filename}")
            file_metadata = sync_metadata["file_metadatas"].get(filename, None)
            if file_metadata is None:
                continue
            output_schema = output_schemas_dict.get(file_metadata.get("schema_uuid"), None)
            file_extension = filename.split('.')[-1]
            processed_file = None
            if file_extension == 'csv' and output_schema is not None:
                processed_file = await self.sync_handler_csv.handle(output_schema, file)
            elif file_extension in ['xlsx', 'xls'] and output_schema is not None:
                processed_file = await self.sync_handler_excel.handle(output_schema, file)
            if processed_file is not None:
                processed_files.append(processed_file)
        return processed_files

    @log_errors
    def get_output_schemas(self, sync_metadata):
        output_schemas_dict = {}
        output_schemas = self.output_schema_dao.get_output_schemas_by_user_uuid(user_uuid=sync_metadata["user_uuid"])
        for output_schema in output_schemas:
            output_schemas_dict[output_schema["schema_uuid"]] = output_schema["schema"]
        return output_schemas_dict