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
            You are a data mapping expert. I have a Excel sheet with following first 10 rows of the excel sheet:
            {sheeet_df}

            I need to map them to this output schema:
            {output_schema}

            Please provide a JSON response with the following structure: 
            {{
                "skip_n_rows": 4,
                "reordered_columns": [3, 0, 1],
                "error": false,
                "error_message": null
            }}

            Info:
            skip_n_rows: count of rows containing no data or empty rows before header(treat NaN values as empty values)
            reordered_columns: List of column indexes to map in the desired order of columns

            Rules:
            1. Match columns based on semantic meaning, not just exact names
            2. Consider common variations (e.g., "first_name" matches "fname", "First Name")
            3. If no good match exists, include it in unmapped_output_columns
            4. Only include exact matches or very high confidence matches
            5. Return valid JSON only, no explanation text

            If not able to match then return with following JSON response with the following structure:
            {{
                "skip_n_rows": null,
                "reordered_columns": null,
                "error": true,
                "error_message": "column tax_value not found"
            }}
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
        
        # Get intelligent column mapping using Groq LLM
        sheet_df = df[sheet_name]
        first_10_rows = sheet_df.head(10)
        first_10_rows.columns = ["NaN" if col.startswith("Unnamed") else col for col in first_10_rows.columns]
        mapping_result = await self._get_column_mapping(first_10_rows, output_schema)
        
        processed_sheet = self._create_output_dataframe(sheet_df=sheet_df, mapping_result=mapping_result, output_schema=output_schema)
        df[sheet_name] = processed_sheet
        file_detail = {
            "filename": filename,
            "file": df
        }
        return file_detail