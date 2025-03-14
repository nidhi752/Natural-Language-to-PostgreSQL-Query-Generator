# Natural Language to PostgreSQL Query Generator

This project provides a robust framework for converting natural language queries into executable PostgreSQL statements using the Groq API with the LLaMA-3.3-70B model. It also features SQL query correction for improperly formatted statements, ensuring accuracy and reliability.

## Overview

This system enables users to input natural language descriptions of data queries and receive corresponding SQL statements that can be executed against a PostgreSQL database. Additionally, it includes functionality to correct syntactically incorrect SQL queries.

## Features

- Convert natural language queries into executable PostgreSQL statements.
- Correct malformed or syntactically incorrect SQL queries.
- Track token usage and processing time for API calls.
- Support batch processing for multiple queries.

## Requirements

- Python 3.6+
- `requests` library
- Groq API key (register at [Groq](https://groq.com))

## Installation

1. Clone this repository:
   ```sh
   git clone https://github.com/your-username/nl-to-sql.git
   cd nl-to-sql
   ```
2. Install dependencies:
   ```sh
   pip install requests
   ```
3. Configure your API key in the code:
   ```python
   api_key = "your_actual_api_key"  # Replace with your actual Groq API key
   ```

## Usage

### Input Format

The system accepts input in JSON format:

- **SQL Generation:**
  ```json
  [
    { "NL": "Find all customers who made purchases over $500 in the last month" },
    { "NL": "Get the top 10 products by sales volume" }
  ]
  ```
- **SQL Correction:**
  ```json
  [
    {
      "IncorrectQuery": "SELECT customer_name FROM customers WERE total_purchases > 1000",
      "NL": "Find customers with purchases exceeding $1000"
    }
  ]
  ```

### Running the Program

Execute the script to process input files and generate or correct SQL statements:

```sh
python main.py
```

### Output Format

- **SQL Generation:**
  ```json
  [
    {
      "NL": "Find all customers who made purchases over $500 in the last month",
      "Query": "SELECT c.customer_id, c.name, c.email FROM customers c JOIN orders o ON c.customer_id = o.customer_id WHERE o.total_amount > 500 AND o.order_date >= NOW() - INTERVAL '1 month' GROUP BY c.customer_id, c.name, c.email;"
    }
  ]
  ```
- **SQL Correction:**
  ```json
  [
    {
      "IncorrectQuery": "SELECT customer_name FROM customers WERE total_purchases > 1000",
      "CorrectQuery": "SELECT customer_name FROM customers WHERE total_purchases > 1000"
    }
  ]
  ```

## Prompt Engineering

The system leverages carefully engineered prompts to ensure optimal SQL generation:

```
You are a PostgreSQL expert tasked with converting natural language queries into precise, executable PostgreSQL statements.

Given the following database schema:
[DATABASE SCHEMA DETAILS]

Convert this natural language request into a PostgreSQL query:
"[NATURAL LANGUAGE QUERY]"

Requirements:
- Generate only the executable PostgreSQL code without explanations.
- Use proper PostgreSQL syntax and features.
- Include appropriate joins when relationships between tables are implied.
- Apply proper filtering based on query conditions.
- Format the query with proper indentation for readability.
- Use table aliases where applicable.
- Include necessary `CAST` operations for data type compatibility.
- Optimize queries for performance, considering indexing and large datasets.
- Output only the PostgreSQL query, with no additional commentary.
```

## Fine-Tuning for Accuracy

To improve SQL generation accuracy, consider:

- Providing detailed database schema information in prompts.
- Adjusting the temperature parameter (lower for more predictable outputs).
- Increasing `max_tokens` for complex queries.
- Adding sample expected outputs to standardize results.

## Performance Tracking

The system tracks key metrics to monitor efficiency:

- Total tokens used per API call.
- Execution time for SQL generation.
- Execution time for SQL correction.

## Limitations

- The quality of SQL generation depends on the clarity of natural language inputs.
- Complex or ambiguous queries may require manual refinement.
- Schema details should be updated as database structures evolve.

## License

This project is licensed under the MIT License. See the `LICENSE` file for details.

## Contributing

Contributions are welcome! Feel free to submit issues and pull requests to enhance functionality and improve performance.
