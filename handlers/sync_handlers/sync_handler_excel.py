from config.logger import log_errors, logger
import pandas as pd
from io import BytesIO
import json
from groq import Groq
import os
from dotenv import load_dotenv

load_dotenv()

class SyncHandlerExcel:
    def __init__(self):
        self.client = Groq(
            api_key=os.environ.get("GROQ_API_KEY"),
        )

    async def _get_column_mapping(self, sheeet_df, output_schema):

        prompt = f"""
            You are a data mapping expert. Your task is to map columns from an Excel sheet to a given output schema.

            ### INPUT DATA:
            First 5 rows of the Excel sheet:
            {sheeet_df}

            Output schema (list of columns in desired order):
            {output_schema}

            ### REQUIRED OUTPUT (JSON only, no extra text):
            {{
                "skip_n_rows": <integer or null>,
                "reordered_columns": <list of integers or null>,
                "error": <true|false>,
                "error_message": <string or null>
            }}

            ### RULES:
            1. Determine `skip_n_rows` is the count of rows which are not part of the actual data from top.
            2. The header row is the first non-empty row after skipping `skip_n_rows`.
            3. Use ONLY the header row (and at most the next one or two rows if needed) for understanding the column names. Ignore data rows beyond the first 2 non-empty rows to avoid confusion.
            4. For `reordered_columns`, return the column indexes (0-based) in the order that matches the output schema.
            5. Match columns using semantic similarity, including common variations and abbreviations (e.g., "first_name" ~ "fname" ~ "First Name").
            6. Do not guess; only map if you are highly confident. If any column in `output_schema` cannot be matched, return an error response (see below).

            ### EXAMPLES:
            Success:
            {{
                "skip_n_rows": 4,
                "reordered_columns": [3, 0, 1],
                "error": false,
                "error_message": null
            }}

            Failure:
            {{
                "skip_n_rows": null,
                "reordered_columns": null,
                "error": true,
                "error_message": "column tax_value not found"
            }}

            Now provide the JSON output based on the above instructions.

        """
        try:
            chat_completion = self.client.chat.completions.create(
                messages=[
                    {
                        "role": "user",
                        "content": prompt,
                    }
                ],
                model=os.environ.get("GROQ_MODEL","openai/gpt-oss-20b"),
                stream=False,
                temperature=0.1,  # Low temperature for consistent mapping
            )
            
            response_content = chat_completion.choices[0].message.content.strip()
            logger.info(f"Groq LLM response: {response_content}")
            
            # Parse the JSON response
            mapping_result = json.loads(response_content)
            return mapping_result
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse LLM response as JSON: {e}")
            logger.error(f"Response content: {response_content}")
        except Exception as e:
            logger.error(f"Error calling Groq API: {e}")


    def _create_output_dataframe(self, sheet_df, mapping_result, output_schema):
        """Create the output dataframe based on mapping results"""
        updated_columns = list(output_schema.keys())
        skip_n_rows = mapping_result.get("skip_n_rows", 0)
        
        # Determine output columns order
        if mapping_result.get("error") is True:
            logger.error("Failed to recognize the output_schema")
            return sheet_df
        
        reordered_columns = mapping_result.get("reordered_columns", None)
        
        mapped_df = sheet_df.iloc[skip_n_rows:, reordered_columns]
        mapped_df.columns = updated_columns
        return mapped_df

    @log_errors
    async def handle(self, output_schema, file, sheet_name: str):
        """Main handler method"""
        # Read file contents
        filename = file.filename
        contents = await file.read()
        file_content = BytesIO(contents)
        df = pd.read_excel(file_content, engine="openpyxl", sheet_name=None)

        excel_file = pd.ExcelFile(file_content)
        available_sheets = excel_file.sheet_names
    
        # Validate sheet exists
        if sheet_name not in available_sheets:
            logger.error(f"Sheet '{sheet_name}' not found in file '{filename}'. ")
            logger.error(f"Available sheets: {available_sheets}")
            return None
        
        sheet_df = df[sheet_name]
        rows = []
        rows.append(f"row 0 : {sheet_df.columns.to_list()}")

        # Get the actual number of rows
        num_rows = min(5, len(sheet_df))

        for i in range(num_rows):
            row_as_list = sheet_df.iloc[i].tolist()
            rows.append(f"row {i+1} : {row_as_list}")

        mapping_result = await self._get_column_mapping(rows, output_schema)
        
        processed_sheet = self._create_output_dataframe(sheet_df=sheet_df, mapping_result=mapping_result, output_schema=output_schema)
        df[sheet_name] = processed_sheet
        file_detail = {
            "filename": filename,
            "file": df
        }
        return file_detail