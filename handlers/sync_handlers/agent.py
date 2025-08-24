import os
import operator
import pandas as pd
from langchain_core.tools import tool
from dotenv import load_dotenv
from langgraph.graph import StateGraph, START, END
from langchain_core.messages import SystemMessage, HumanMessage, AnyMessage, ToolMessage
from typing import Annotated, TypedDict, Dict, Any

load_dotenv()

class AgentState(TypedDict):
    messages: Annotated[list[AnyMessage], operator.add]



@tool
def read_excel_file(no_of_rows_to_read: int = 5):
    """
    Reads an Excel file and returns the first few rows
    Args:
        no_of_rows_to_read: Number of rows to read (default: 5)
    """
    file_path = "Book1.xlsx"
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File not found: {file_path}")

    df = pd.read_excel(file_path)
    
    # Get the specified number of rows
    sample_data = df.head(no_of_rows_to_read).to_dict(orient='records')
    
    result = {
        "sample_data": sample_data
    }
    
    print(f"Read {no_of_rows_to_read} rows from Excel file")
    return str(result)  # Convert to string for LLM processing

@tool
def column_mapper(skip_first_n_rows:int, reordered_columns: list[int]):
    """
    Maps the specified columns from the Excel data and writes the data to output excel.
    Args:
        skip_first_n_rows: Number of rows to skip at the start of the file
        reordered_columns: List of column indexes to map in the desired order
    """
    input_file_path = "Book1.xlsx"  # Read from input file
    output_file_path = "Book1_output.xlsx"  # Write to output file
    
    if not os.path.exists(input_file_path):
        raise FileNotFoundError(f"Input file not found: {input_file_path}")
    
    print(f"Mapping columns with indexes: {reordered_columns}")
    
    # Read the input Excel file
    df = pd.read_excel(input_file_path, skiprows=skip_first_n_rows)
    
    # Standard column names in order
    standard_columns = [
        'Date', 'Vendor Name', 'Inv. Number', 'Taxable Value', 
        'Total Value', 'GST no.', 'Tax Percentage', 'Total GST'
    ]
    
    # Select and reorder columns
    try:
        mapped_df = df.iloc[:, reordered_columns]
        standard_columns = mapped_df.columns.tolist()
        # Rename columns to standard names
        if len(reordered_columns) <= len(standard_columns):
            mapped_df.columns = standard_columns[:len(reordered_columns)]
        else:
            # If more columns than standard, keep original names for extras
            new_columns = standard_columns + [f"Extra_Col_{i}" for i in range(len(standard_columns), len(reordered_columns))]
            mapped_df.columns = new_columns[:len(reordered_columns)]
        
        # Save to output Excel file
        mapped_df.to_excel(output_file_path, index=False)
        
        print(f"Successfully mapped and saved data to {output_file_path}")
        print(f"Mapped {len(mapped_df)} rows and {len(reordered_columns)} columns")
        
        return f"Successfully created output file: {output_file_path} with {len(mapped_df)} rows and columns: {list(mapped_df.columns)}"
        
    except Exception as e:
        error_msg = f"Error during column mapping: {str(e)}"
        print(error_msg)
        return error_msg

class ExcelColumnMapper:
    def __init__(self, model_name: str = "claude-3-haiku-20240307"):
        self.model = ChatAnthropic(
            model_name=model_name,
            timeout=30,
            api_key=os.getenv("ANTHROPIC_API_KEY")
        )
        
        # Define tools first
        self.tools = [
            read_excel_file,
            column_mapper
        ]
        
        # Bind tools to model
        self.model_with_tools = self.model.bind_tools(self.tools)
        
        # Build graph
        graph = StateGraph(AgentState)
        graph.add_node("llm", self.call_llm)
        graph.add_node("tools", self.tool_node)
        
        # Set entry point
        graph.set_entry_point("llm")
        
        # Add conditional edges
        graph.add_conditional_edges(
            "llm",
            self.should_continue,
            {
                "continue": "tools",
                "end": END
            }
        )
        graph.add_edge("tools", "llm")
        
        self.graph = graph.compile()

    def should_continue(self, state: AgentState):
        """Determine if we should continue to tools or end."""
        messages = state["messages"]
        last_message = messages[-1]
        
        # If the last message has tool calls, continue to tools
        if hasattr(last_message, 'tool_calls') and last_message.tool_calls:
            return "continue"
        else:
            return "end"
    
    def call_llm(self, state: AgentState):
        """Call the LLM with tools."""
        messages = state["messages"]
        response = self.model_with_tools.invoke(messages)
        return {"messages": [response]}
    
    def tool_node(self, state: AgentState):
        """Execute tools and return results."""
        messages = state["messages"]
        last_message = messages[-1]
        print("="*30)
        print("tool_calls: ", last_message)
        print("="*30)
        tool_calls = last_message.tool_calls
        tool_messages = []
        
        # Use self.tools as a dict of tool objects
        tool_dict = {t.name: t for t in self.tools}
        for tool_call in tool_calls:
            tool_name = tool_call["name"]
            tool_args = tool_call["args"]
            tool_id = tool_call["id"]
            
            # Find and execute the tool using the tool object
            tool_result = None
            print(tool_name, tool_args)
            print(type(tool_name), type(tool_args))
            if tool_name in tool_dict:
                tool_result = tool_dict[tool_name].invoke(tool_args)
            else:
                tool_result = f"Tool {tool_name} not found."
            
            # Create tool message
            tool_message = ToolMessage(
                content=str(tool_result),
                tool_call_id=tool_id
            )
            tool_messages.append(tool_message)
        
        # Return the updated messages list
        return {"messages": tool_messages}

# Create an instance of the ExcelColumnMapper
excel_mapper = ExcelColumnMapper()

# Create the system prompt as a SystemMessage
system_prompt = SystemMessage(content="""
You are an intelligent Excel processing agent designed to read Excel files and map their columns to a standardized format. Your primary goal is to identify, map, and extract data using column detection.

Required Standard Columns (Truth Data)
Your task is to map input Excel columns to these exact standard column names along with their order:

1. Date - Date of transaction/invoice
2. Vendor Name - Name of the vendor/supplier  
3. Inv. Number - Invoice number or reference
4. Taxable Value - Taxable amount before tax
5. Total Value - Total amount including all taxes
6. GST no. - GST registration number
7. Tax Percentage - Tax rate percentage
8. Total GST - Total GST amount

Processing Workflow:
Step 1: Use read_excel_file tool to read first 5 rows and analyze column headers
Step 2: Map available columns to required standard columns using fuzzy matching
Step 3: If mapping confidence is low, try reading 10 rows instead
Step 4: Use column_mapper tool with the correct the skip rows and correct column indexes in standard order

Start by reading the Excel file to see what columns are available.
""")

# Create the human message asking to start the process
human_message = HumanMessage(content="Please start processing the Excel file. Read the file first to see what columns are available, then map them to the required standard format.")

# Start with the proper initial state
initial_state = {
    "messages": [system_prompt, human_message]
}

# Run the workflow
result = excel_mapper.graph.invoke(initial_state)
