from config.logger import log_errors, logger
import pandas as pd
import io
import json
from groq import Groq
import os
from dotenv import load_dotenv

load_dotenv()

class SyncHandlerCSV:
    def __init__(self):
        self.client = Groq(
            api_key=os.environ.get("GROQ_API_KEY"),
        )

    async def _get_column_mapping(self, csv_columns, output_schema):
        prompt = f"""
            You are a data mapping expert. I have a CSV with these columns:
            {csv_columns}

            I need to map them to this output schema:
            {output_schema}

            Please provide a 
            {{
                "reordered_columns": [3, 0, 1],
                "error": false,
                "error_message": null
            }}

            info:
            reordered_columns: List of column indexes to map in the desired order

            Rules:
            1. Match columns based on semantic meaning, not just exact names
            2. Consider common variations (e.g., "first_name" matches "fname", "First Name")
            3. If no good match exists, include it in unmapped_output_columns
            4. Only include exact matches or very high confidence matches
            5. Return valid JSON only, no explanation text

            If not able to match then return with following JSON response with the following structure: 
            {{
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
            # Fallback to exact matching
            return self._fallback_exact_matching(csv_columns, output_schema)
        except Exception as e:
            logger.error(f"Error calling Groq API: {e}")
            # Fallback to exact matching
            return self._fallback_exact_matching(csv_columns, output_schema)


    def _create_output_dataframe(self, df, mapping_result, output_schema):
        """Create the output dataframe based on mapping results"""
        updated_columns = list(output_schema.keys())
        
        # Determine output columns order
        if mapping_result.get("error") is True:
            logger.error("Invalid output_schema format. Expected list or dict.")
            return df
        
        reordered_columns = mapping_result.get("reordered_columns", None)
        
        mapped_df = df.iloc[:, reordered_columns]
        return mapped_df

    @log_errors
    async def handle(self, output_schema, file):
        """Main handler method"""
        # Read file contents
        filename = file.filename
        contents = await file.read()
        df = pd.read_csv(io.BytesIO(contents))
        
        # Get intelligent column mapping using Groq LLM
        mapping_result = await self._get_column_mapping(list(df.columns), output_schema)
        
        processed_file = self._create_output_dataframe(df=df, mapping_result=mapping_result, output_schema=output_schema)
        file_detail = {
            "filename": filename,
            "file": processed_file
        }
        return file_detail