# Import necessary libraries
import json
import requests
import time

# Global variable to keep track of the total number of tokens
total_tokens = 0


# Function to load input file
def load_input_file(file_path):
    with open(file_path, 'r') as file:
        data = json.load(file)
    return data


# Function to generate SQL statements
def generate_sqls(data):
    """
    Generate SQL statements from the NL queries.

    :param data: List of NL queries
    :return: List of SQL statements
    """
    sql_statements = []
    # TODO: Implement logic to generate SQL statements

    api_key = "<API_KEY>"  # Replace with your actual API key
    model = "llama-3.3-70b-versatile"

    # Add rate limiting to stay within RPM limits
    requests_this_minute = 0
    minute_start_time = time.time()

    for index, item in enumerate(data):
        nl_query = item.get('NL', '')

        # Skip if NL query is empty
        if not nl_query:
            sql_statements.append({"NL": nl_query, "Query": ""})
            continue

        # Rate limiting check
        current_time = time.time()
        if current_time - minute_start_time >= 60:
            # Reset counter for new minute
            requests_this_minute = 0
            minute_start_time = current_time

        if requests_this_minute >= 29:  # Keep one below limit for safety
            # Wait until next minute begins
            sleep_time = 60 - (current_time - minute_start_time) + 1
            print(f"Rate limit approaching. Waiting {sleep_time} seconds...")
            time.sleep(sleep_time)
            requests_this_minute = 0
            minute_start_time = time.time()

        # Prepare PostgreSQL-specific prompt
        messages = [
            {
                "role": "system",
                "content": "You are a PostgreSQL expert. Convert natural language to PostgreSQL-compliant SQL. Output only the SQL query with no explanations or markdown. Use PostgreSQL syntax and features."
            },
            {
                "role": "user",
                "content": f"Convert the following request to PostgreSQL SQL syntax: {nl_query}"
            }
        ]

        try:
            # Call the API with proper error handling
            try:
                # First verify if our API call function is working correctly
                temp_msg = [{"role": "user", "content": "Write SELECT 1"}]
                test_response, _ = call_groq_api(api_key, model, temp_msg, max_tokens=50)
                if 'choices' not in test_response:
                    print(f"API call function is not working correctly. Response: {test_response}")
                    print("Please check your call_groq_api function implementation and API key.")
                    raise Exception("API call function not working properly")

                # If test succeeded, proceed with the actual query
                response, tokens_used = call_groq_api(api_key, model, messages, max_tokens=500)
                requests_this_minute += 1
            except Exception as api_error:
                print(f"API call error for query '{nl_query}': {str(api_error)}")
                # If we get an API error, add empty result and continue
                sql_statements.append({"NL": nl_query, "Query": ""})
                continue

            # Check if response contains expected keys
            if not response or 'choices' not in response or not response['choices']:
                print(f"Invalid API response for query '{nl_query}': {response}")
                sql_statements.append({"NL": nl_query, "Query": ""})
                continue

            # Extract the SQL query from the response
            try:
                sql_query = response['choices'][0]['message']['content'].strip()
            except (KeyError, IndexError) as e:
                print(f"Failed to extract SQL from response for query '{nl_query}': {str(e)}")
                print(f"Response structure: {response}")
                sql_statements.append({"NL": nl_query, "Query": ""})
                continue

            # Clean up the SQL (remove any markdown formatting if present)
            if "```" in sql_query:
                # Extract content between SQL code blocks
                import re
                sql_match = re.search(r"```(?:sql)?(.*?)```", sql_query, re.DOTALL)
                if sql_match:
                    sql_query = sql_match.group(1).strip()
                else:
                    # If regex fails, use simple string splitting
                    sql_query = sql_query.replace("```sql", "").replace("```", "").strip()

            # Ensure PostgreSQL compatibility
            sql_query = ensure_postgresql_compatibility(sql_query)

            # Add to results
            sql_statements.append({"NL": nl_query, "Query": sql_query})

            # Progress tracking
            if (index + 1) % 10 == 0:
                print(f"Generated {index + 1}/{len(data)} SQL queries, Total tokens used: {total_tokens}")

        except Exception as e:
            print(f"Unexpected error for query '{nl_query}': {str(e)}")
            sql_statements.append({"NL": nl_query, "Query": ""})

            # If error is related to rate limiting, wait and then retry
            if "rate limit" in str(e).lower():
                print("Rate limit exceeded. Waiting 60 seconds...")
                time.sleep(60)
                requests_this_minute = 0
                minute_start_time = time.time()

    return sql_statements


# Function to correct SQL statements
def correct_sqls(sql_statements):
    """
    Correct SQL statements if necessary.

    :param sql_statements: List of Dict with incorrect SQL statements and NL query
    :return: List of corrected SQL statements
    """
    corrected_sqls = []
    # TODO: Implement logic to correct SQL statements

    api_key = "<API_KEY>"  # Replace with your actual API key
    model = "llama-3.3-70b-versatile"

    # Add rate limiting to stay within RPM limits
    requests_this_minute = 0
    minute_start_time = time.time()

    for index, item in enumerate(sql_statements):
        nl_query = item.get('NL', '')
        incorrect_query = item.get('IncorrectQuery', '')

        # Skip if incorrect query is empty
        if not incorrect_query:
            corrected_sqls.append({"IncorrectQuery": incorrect_query, "CorrectQuery": ""})
            continue

        # Rate limiting check
        current_time = time.time()
        if current_time - minute_start_time >= 60:
            # Reset counter for new minute
            requests_this_minute = 0
            minute_start_time = current_time

        if requests_this_minute >= 29:  # Keep one below limit for safety
            # Wait until next minute begins
            sleep_time = 60 - (current_time - minute_start_time) + 1
            print(f"Rate limit approaching. Waiting {sleep_time} seconds...")
            time.sleep(sleep_time)
            requests_this_minute = 0
            minute_start_time = time.time()

        # First, check for common PostgreSQL syntax errors and fix them without API call if possible
        fixed_query = attempt_quick_postgresql_fix(incorrect_query)

        # If simple fixes didn't change it or if NL context is needed, use the API
        if fixed_query == incorrect_query:
            # Prepare PostgreSQL-specific prompt
            messages = [
                {
                    "role": "system",
                    "content": "You are a PostgreSQL expert. Fix the incorrect SQL query to make it valid PostgreSQL syntax. Output only the corrected SQL with no explanations or markdown."
                },
                {
                    "role": "user",
                    "content": f"Natural language: {nl_query}\nIncorrect PostgreSQL query: {incorrect_query}\nProvide only the corrected PostgreSQL query:"
                }
            ]

            try:
                # Call the API with proper error handling
                try:
                    response, tokens_used = call_groq_api(api_key, model, messages, max_tokens=500)
                    requests_this_minute += 1
                except Exception as api_error:
                    print(f"API call error for correction: {str(api_error)}")
                    corrected_sqls.append({"IncorrectQuery": incorrect_query, "CorrectQuery": fixed_query})
                    continue

                # Check if response contains expected keys
                if not response or 'choices' not in response or not response['choices']:
                    print(f"Invalid API response for correction: {response}")
                    corrected_sqls.append({"IncorrectQuery": incorrect_query, "CorrectQuery": fixed_query})
                    continue

                # Extract the corrected SQL query from the response
                try:
                    corrected_query = response['choices'][0]['message']['content'].strip()
                except (KeyError, IndexError) as e:
                    print(f"Failed to extract SQL from correction response: {str(e)}")
                    print(f"Response structure: {response}")
                    corrected_sqls.append({"IncorrectQuery": incorrect_query, "CorrectQuery": fixed_query})
                    continue

                # Clean up the SQL (remove any markdown formatting if present)
                if "```" in corrected_query:
                    # Extract content between SQL code blocks
                    import re
                    sql_match = re.search(r"```(?:sql)?(.*?)```", corrected_query, re.DOTALL)
                    if sql_match:
                        corrected_query = sql_match.group(1).strip()
                    else:
                        # If regex fails, use simple string splitting
                        corrected_query = corrected_query.replace("```sql", "").replace("```", "").strip()

                # Ensure PostgreSQL compatibility
                corrected_query = ensure_postgresql_compatibility(corrected_query)

                # Add to results
                corrected_sqls.append({"IncorrectQuery": incorrect_query, "CorrectQuery": corrected_query})

                # Progress tracking
                if (index + 1) % 10 == 0:
                    print(f"Corrected {index + 1}/{len(sql_statements)} SQL queries, Total tokens used: {total_tokens}")

            except Exception as e:
                print(f"Unexpected error for correction: {str(e)}")
                corrected_sqls.append({"IncorrectQuery": incorrect_query, "CorrectQuery": fixed_query})

                # If error is related to rate limiting, wait and then retry
                if "rate limit" in str(e).lower():
                    print("Rate limit exceeded. Waiting 60 seconds...")
                    time.sleep(60)
                    requests_this_minute = 0
                    minute_start_time = time.time()
        else:
            # Use our local fix instead of calling the API
            corrected_sqls.append({"IncorrectQuery": incorrect_query, "CorrectQuery": fixed_query})

    return corrected_sqls


def attempt_quick_postgresql_fix(sql_query):
    """
    Attempt to fix common PostgreSQL syntax errors without calling the API.
    This saves tokens and time for simple errors.

    :param sql_query: Incorrect SQL query string
    :return: Fixed SQL query string or original if no fixes applied
    """
    # Make a copy of the original query
    fixed_query = sql_query

    # Common PostgreSQL syntax error fixes
    common_fixes = [
        # Missing semicolons at the end
        (r'(?<!\;)$', ';'),

        # Fix quote issues (PostgreSQL uses single quotes for strings, double quotes for identifiers)
        (r'(?<!")"([^"]*?)"(?!")', r"'\1'"),  # Replace standalone double quotes with single quotes for strings

        # PostgreSQL specific fixes
        (r'(?i)\bLIMIT\s+(\d+)\s+OFFSET\s+(\d+)', r'LIMIT \1 OFFSET \2'),  # Ensure proper LIMIT OFFSET syntax
        (r'(?i)\bILIKE\b', 'ILIKE'),  # Preserve ILIKE operator (PostgreSQL specific)
        (r'(?i)\bTEXT\(\)', 'TEXT'),  # Fix TEXT() data type to TEXT

        # Fix common typos
        (r'\bSELET\b', 'SELECT'),
        (r'\bFROM\s+FORM\b', 'FROM'),
        (r'\bWHERE\s+HWERE\b', 'WHERE'),
        (r'\bGROUP BY\s+GRUOP BY\b', 'GROUP BY'),
        (r'\bJION\b', 'JOIN'),
        (r'\bINNER JION\b', 'INNER JOIN'),
        (r'\bLEFT JION\b', 'LEFT JOIN'),

        # Fix missing spaces
        (r'(?<=\w)(?=SELECT|FROM|WHERE|GROUP|ORDER|HAVING|JOIN)', ' '),

        # Fix doubled keywords
        (r'\b(SELECT|FROM|WHERE|GROUP BY|ORDER BY|HAVING)\s+\1\b', r'\1'),

        # Replace CONCAT function with PostgreSQL's concatenation operator
        (r'CONCAT\((.*?),(.*?)\)', r'\1 || \2'),

        # Fix datetime functions to PostgreSQL syntax
        (r'(?i)DATE_FORMAT\((.*?),\s*[\'"](%[YmdHis])[\'"].*?\)', r'TO_CHAR(\1, \'YYYY-MM-DD\')'),
        (r'(?i)NOW\(\)', r'CURRENT_TIMESTAMP'),

        # Fix incorrect TOP syntax (SQL Server) to LIMIT (PostgreSQL)
        (r'(?i)SELECT\s+TOP\s+(\d+)', r'SELECT'),  # Remove TOP
        (r'(?i)SELECT\s+TOP\s+(\d+)(.*?)FROM', r'SELECT\2 FROM'),  # Remove TOP and preserve other parts
    ]

    import re
    for pattern, replacement in common_fixes:
        fixed_query = re.sub(pattern, replacement, fixed_query)

    # Add LIMIT clause at the end if TOP was removed
    top_match = re.search(r'(?i)TOP\s+(\d+)', sql_query)
    if top_match and 'LIMIT' not in fixed_query:
        if ';' in fixed_query:
            fixed_query = fixed_query[:-1] + f" LIMIT {top_match.group(1)};"
        else:
            fixed_query = fixed_query + f" LIMIT {top_match.group(1)};"

    # Balance parentheses
    open_count = fixed_query.count('(')
    close_count = fixed_query.count(')')
    if open_count > close_count:
        fixed_query += ')' * (open_count - close_count)

    return fixed_query


def ensure_postgresql_compatibility(sql_query):
    """
    Ensures the generated SQL is compatible with PostgreSQL.

    :param sql_query: SQL query to check
    :return: PostgreSQL-compatible SQL query
    """
    # Replace functions and syntax that might be incompatible with PostgreSQL
    replacements = [
        # Date functions
        (r'(?i)GETDATE\(\)', 'CURRENT_DATE'),
        (r'(?i)CURRENT_TIMESTAMP\(\)', 'CURRENT_TIMESTAMP'),

        # String functions
        (r'(?i)CHARINDEX\((.*?),(.*?)\)', r'POSITION(\1 IN \2)'),
        (r'(?i)LEN\((.*?)\)', r'LENGTH(\1)'),
        (r'(?i)SUBSTRING\((.*?),(.*?),(.*?)\)', r'SUBSTRING(\1 FROM \2 FOR \3)'),

        # Concatenation
        (r'(?i)CONCAT_WS\((.*?),(.*?)\)', r'array_to_string(ARRAY[\2], \1)'),

        # Replace LIMIT n,m syntax (MySQL) with LIMIT m OFFSET n (PostgreSQL)
        (r'(?i)LIMIT\s+(\d+)\s*,\s*(\d+)', r'LIMIT \2 OFFSET \1'),

        # Replace non-standard operators
        (r'(?i)\bRLIKE\b', '~'),  # RLIKE to ~ (regex match)

        # Handle auto-increment columns in PostgreSQL (if in CREATE TABLE)
        (r'(?i)AUTO_INCREMENT', 'SERIAL'),

        # Handle table hints (not supported in PostgreSQL)
        (r'(?i)WITH\s*\(\s*NOLOCK\s*\)', ''),

        # Fix any use of square brackets (SQL Server style) for identifiers
        (r'\[([^\]]+)\]', r'"\1"'),
    ]

    import re
    for pattern, replacement in replacements:
        sql_query = re.sub(pattern, replacement, sql_query)

    return sql_query


# Function to properly test the Groq API call before using it in main functions
def verify_groq_api_connection(api_key, model):
    """
    Test the Groq API connection to ensure it's working properly.

    :param api_key: API key for authentication
    :param model: Model name to use
    :return: True if connection works, False otherwise
    """
    print("Verifying Groq API connection...")
    url = "https://api.groq.com/openai/v1/chat/completions"

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}",
    }
    data = {
        "model": model,
        "messages": [{"role": "user", "content": "Say 'Connection successful'"}],
        'temperature': 0.0,
        'max_tokens': 20,
        'n': 1
    }

    try:
        response = requests.post(url, headers=headers, json=data)

        # Check if we get a successful response
        if response.status_code == 200:
            response_json = response.json()
            if 'choices' in response_json and response_json['choices']:
                content = response_json['choices'][0]['message']['content']
                print(f"API Connection verified. Response: {content}")
                return True

        print(f"API connection failed. Status code: {response.status_code}")
        print(f"Response: {response.text}")
        return False

    except Exception as e:
        print(f"API connection error: {str(e)}")
        return False


# Function to call the Groq API
def call_groq_api(api_key, model, messages, temperature=0.0, max_tokens=1000, n=1):
    """
    NOTE: DO NOT CHANGE/REMOVE THE TOKEN COUNT CALCULATION
    Call the Groq API to get a response from the language model.
    :param api_key: API key for authentication
    :param model: Model name to use
    :param messages: List of message dictionaries
    :param temperature: Temperature for the model
    :param max_tokens: Maximum number of tokens to generate (these are max new tokens)
    :param n: Number of responses to generate
    :return: Response from the API
    """
    global total_tokens
    url = "https://api.groq.com/openai/v1/chat/completions"

    api_key = "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"
    model = "llama-3.3-70b-versatile"
    messages = [
        {
            "role": "user",
            "content": "Explain the importance of fast language models"
        }
    ]

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}",
    }
    data = {
        "model": model,
        "messages": messages,
        'temperature': temperature,
        'max_tokens': max_tokens,
        'n': n
    }

    response = requests.post(url, headers=headers, json=data)
    response_json = response.json()

    # Update the global token count
    total_tokens += response_json.get('usage', {}).get('completion_tokens', 0)

    # You can get the completion from response_json['choices'][0]['message']['content']
    return response_json, total_tokens


# Main function
def main():
    # TODO: Specify the path to your input file
    input_file_path_1 = '/train_generate_task.json'
    input_file_path_2 = '/train_query_coorection_task.json'

    # Load data from input file
    data_1 = load_input_file(input_file_path_1)
    data_2 = load_input_file(input_file_path_2)

    start = time.time()
    # Generate SQL statements
    sql_statements = generate_sqls(data_1)
    generate_sqls_time = time.time() - start

    start = time.time()
    # Correct SQL statements
    corrected_sqls = correct_sqls(data_2)
    correct_sqls_time = time.time() - start

    assert len(data_2) == len(corrected_sqls)  # If no answer, leave blank
    assert len(data_1) == len(sql_statements)  # If no answer, leave blank

    # TODO: Process the outputs

    # Get the outputs as a list of dicts with keys 'IncorrectQuery' and 'CorrectQuery'
    with open('output_sql_correction_task.json', 'w') as f:
        json.dump(corrected_sqls, f)

        # Get the outputs as a list of dicts with keys 'NL' and 'Query'
    with open('output_sql_generation_task.json', 'w') as f:
        json.dump(sql_statements, f)

    return generate_sqls_time, correct_sqls_time


if __name__ == "__main__":
    generate_sqls_time, correct_sqls_time = main()
    print(f"Time taken to generate SQLs: {generate_sqls_time} seconds")
    print(f"Time taken to correct SQLs: {correct_sqls_time} seconds")
    print(f"Total tokens: {total_tokens}")

