import os
from langchain_core.pydantic_v1 import BaseModel, Field
from langchain_openai import ChatOpenAI
from sqlalchemy import create_engine, inspect
from sqlalchemy.engine.url import URL
from schemex1 import schemex

SF_USER = 'Naveen'
SF_PASSWORD = 'Naveen@1234'
SF_ACCOUNT = 'kc68443.ap-southeast-1'
SF_WAREHOUSE = 'COMPUTE_WH'
SF_DATABASE = 'MEC'
SF_SCHEMA = 'BIKE_SALE'
SF_ROLE = 'ACCOUNTADMIN'

# Function to create SQLAlchemy engine for Snowflake
def connect_to_snowflake(user, password, account, warehouse, database, schema, role):
    try:
        connection_string = URL.create(
            drivername='snowflake',
            username=user,
            password=password,
            host=f'{account}',  # Use account name without .snowflakecomputing.com
            database=database,
            query={
                'warehouse': warehouse,
                'schema': schema,
                'role': role
            }
        )
        engine = create_engine(connection_string)
        return engine
    except Exception as e:
        print(f"Error creating Snowflake engine: {e}")
        raise

# Setup the Snowflake connection
engine = connect_to_snowflake(SF_USER, SF_PASSWORD, SF_ACCOUNT, SF_WAREHOUSE, SF_DATABASE, SF_SCHEMA, SF_ROLE)
inspector = inspect(engine)

# Define the Table and Column classes
class Table(BaseModel):
    name: str = Field(description="Name of table in SQL database.")

class Column(BaseModel):
    name: str = Field(description="Name of column in SQL table.")
    type: str = Field(description="Data type of the column.")

# Function to generate examples
def generate_examples(table, columns):
    examples = []
    column_list = ", ".join(columns) if columns else "*"
    column_condition = columns[0] if columns else "column_name"

    examples.append(f"""EXAMPLE

Conversation history:
User: Please show me the {table} table
AI: SELECT * FROM {table};
Last line:
User: Show me the {table} with {column_condition} = 'example_value'.
Output: SELECT {column_list}
FROM {table}
WHERE {column_condition} = 'example_value';

""")

    examples.append(f"""EXAMPLE

Conversation history:
User: provide me the database name
AI: SELECT CURRENT_DATABASE();
User: list the tables in our database
AI: SHOW TABLES;

Last line:
User:
Output: SHOW COLUMNS IN TABLE {table};

""")

    examples.append(f"""EXAMPLE

Conversation history:
User: list the {table} details
AI: SELECT {column_list}
FROM {table};

Last line:
User: list the {table} details of only {column_condition}
Output: SELECT *
FROM {table}
WHERE LOWER({column_condition}) LIKE '%example_value%';

""")
    
    return examples

# Function to get table names from Snowflake
def get_table_names():
    return inspector.get_table_names(schema=SF_SCHEMA)

# Function to get column names from Snowflake
def get_column_names(table_name):
    columns = inspector.get_columns(table_name, schema=SF_SCHEMA)
    return [column['name'] for column in columns]

# Extract column names for each table and generate examples
all_examples = []
examples = []
schema = schemex()

# Add initial schema and examples to the list

examples.append("""Instructions:
                
                When the user asks a question analyse the database and give the sql query

Schema-Restricted Queries: Only generate SQL queries using tables and columns that exist within the provided database schema. If a requested table or column is not found in the schema, return an error message or ask the user to clarify their query.

Month Handling: When a user specifies a month, use its numerical value instead of the LIKE % pattern.

Join Requests: If the user mentions "along" in their query, interpret it as a request to join the requested tables with the help of the table and column names present in the database schema. Refrain from generating queries with table or column names which aren't in the database schema

Validation: If a table or column is requested that does not exist in the schema, respond with: "The requested table/column does not exist in the database schema."

Enhanced Error Handling: When a user's query references a non-existent table or column, return an error message: "The requested table/column does not exist in the database schema. Please specify a valid table or column."
""")
examples.append(f"{schema}")
all_examples.append("\n\n".join(examples))

for table in get_table_names():
    column_names = get_column_names(table)
    if column_names:
        examples1 = generate_examples(table, column_names)
        all_examples.append("\n\n".join(examples1))
    else:
        print(f"No columns found for table {table}.")

# Append the context block at the end
context_block = """
Conversation history (for reference only):
{history}
Last line of conversation (for extraction):
User: {input}

Context:
{entities}

Current conversation:

Last line:
Human: {input}

You:"""

all_examples.append(context_block)

# Print or save the combined examples and context block
final_output = "\n\n".join(all_examples)
with open("sample.txt", "w") as file:
    # Write the text to the file
    file.write(final_output)

# Function to get column names and types from Snowflake
def get_columns_info(table_name):
    columns = inspector.get_columns(table_name, schema=SF_SCHEMA)
    return [(column['name'], column['type']) for column in columns]

# Function to generate schema string for the database
def generate_schema_string():
    schema_strings = []
    for table in get_table_names():
        columns_info = get_columns_info(table)
        if columns_info:
            columns_str = "<ul>" + "".join([f"<li><b>{col_name}</b> ({col_type})</li>" for col_name, col_type in columns_info]) + "</ul>"
            schema_strings.append(f"<h3>{table}</h3>{columns_str}")
        else:
            print(f"No columns found for table {table}.")
    return "".join(schema_strings)

def schema_venum():
    schema_string = generate_schema_string()
    return schema_string
