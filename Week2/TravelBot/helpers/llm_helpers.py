import os
import json
import requests

from langchain.chat_models import ChatOpenAI
from langchain.output_parsers import ResponseSchema, StructuredOutputParser
from langchain.prompts import SystemMessagePromptTemplate, HumanMessagePromptTemplate
from langchain_core.prompts import ChatPromptTemplate

def get_llm(temperature=0.3, model_name="gpt-4"):
    """
    Returns a ChatOpenAI instance with the specified parameters.
    """
    openai_api_key = os.getenv("OPENAI_API_KEY")
    return ChatOpenAI(openai_api_key=openai_api_key, temperature=temperature, model_name=model_name)


def parse_location(location_string: str) -> dict:
    """
    Parse a user-supplied location into city, state, country, and clarifications.
    
    TODO: Build and send a prompt with few-shot examples.
    HINT:
        - Define the JSON schema (city, state, country, clarifications) using ResponseSchema.
        - Use a few-shot approach with example inputs and outputs.
        - Convert examples into prompt text and pass to LLM with `get_llm().predict(...)`.
        - Parse with StructuredOutputParser to enforce JSON structure.
    """
        # Example placeholder schema:
    schemas = [
        ResponseSchema(name="city", description="City name, or best guess if not explicit"),
        ResponseSchema(name="state", description="State/Province name if applicable, else null or empty"),
        #create schemea for country,
        ResponseSchema(name="country", description="Country name or best guess if not explicit"),
        ResponseSchema(name="clarifications", description="Any extra info or ambiguities")
    ]
    #https://python.langchain.com/v0.1/docs/modules/model_io/output_parsers/types/structured/
    parser = StructuredOutputParser.from_response_schemas(schemas)
    format_instructions = parser.get_format_instructions()

    # TODO: Provide a few-shot list and build your prompt.
    # Something like, add a few more and uncomment
    few_shot_examples = [
        {
            "input": "NYC, United States",
            "output": {
                "city": "New York",
                "state": "New York",
                "country": "United States",
                "clarifications": ""
            }
        },
        {
            "input": "Detroit, United States",
            "output": {
                "city": "Detroit",
                "state": "Michigan",
                "country": "United States",
                "clarifications": ""
            }
        },
        {   
            "input": "San Diego, United States",
            "output": {
                "city": "San Diego",
                "state": "California",
                "country": "United States",
                "clarifications": ""
            }
        },
        {   
            "input": "Tirana, Albania",
            "output": {
                "city": "Tirana",
                "state": "",
                "country": "Albania",
                "clarifications": "No state concept in Albania"
            }
        },
    ]
    #Uncomment after few show examples completed
    example_text = "\n".join([
        f"Input: {ex['input']}\nJSON Output: {json.dumps(ex['output'], ensure_ascii=False)}\n"
        for ex in few_shot_examples
    ])

    #TODO: Finish prompt, include role and specific instructions for recieving and output
    prompt = f"""
    You are a helpful travel assistant. You receive a location input and must produce:
        - city
        - state (or empty string if not applicable)
        - country
        - clarifications (if anything is ambiguous or missing)

        Follow these few-shot examples to see how we want the JSON output structured:

        {example_text}

        Now parse this user input:
        "{location_string}"

        Return a JSON object with keys city, state, country, clarifications.

        {format_instructions}
        """

    llm_response = get_llm().predict(prompt)
    return dict(parser.parse(llm_response))

    # For now, return a placeholder:
    return {
        "city": "",
        "state": "",
        "country": "",
        "clarifications": ":"
    }


def parse_dates(date_string: str) -> dict:
    """
    Parse user-supplied date information into start_date, end_date, and clarifications.
    
    TODO: Similar approach as parse_location, but focused on dates.
    HINT:
        - Use a JSON schema: start_date, end_date, clarifications.
        - Provide few-shot examples for date parsing in a prompt.
        - Parse the response with StructuredOutputParser.
    """
    
    # Example placeholder schema:
    schemas = [
        ResponseSchema(name="start_date", description="ISO date for start, else empty"),
        ResponseSchema(name="end_date", description="ISO date for end, else empty"),
        ResponseSchema(name="clarifications", description="Any ambiguities or notes, If none, empty")
    ]
    parser = StructuredOutputParser.from_response_schemas(schemas)
    format_instructions = parser.get_format_instructions()

    # TODO: Create few_shot_examples, build prompt, parse output.
    #few_shot_examples = 
    #example_text = 
    #prompt = 
    # Placeholder return:

    # Create few_shot_examples,
    few_shot_examples = [
        {
            "input": "June 5 to June 10, 2024",
            "output": {
                "start_date": "2024-06-05",
                "end_date": "2024-06-10",
                "clarifications": ""
            }
        },
        {
            "input": "2024-01-01",
            "output": {
                "start_date": "2024-01-01",
                "end_date": "",
                "clarifications": ""
            }
        }
    ]
    
    # 3) Convert examples to textual format
    example_text = "\n".join([
        f"Input: {ex['input']}\nJSON Output: {json.dumps(ex['output'], ensure_ascii=False)}\n"
        for ex in few_shot_examples
    ])

    # 4) Build the final prompt
    prompt = f"""
        You are a travel assistant. The user provided the following date information:
        "{date_string}"

        Below are a few-shot examples of how to parse date inputs and produce valid JSON:

        {example_text}

        Now parse the new input into JSON with keys:
        start_date, end_date, clarifications.
        If uncertain, indicate the ambiguity under 'clarifications'.

        {format_instructions}
        """
    
    # 5) Send to LLM and parse
    llm_output = get_llm().predict(prompt)
    try:
        return dict(parser.parse(llm_output))
    except Exception as e:
        # Fallback if the LLM output doesn't parse correctly
        return {
            "start_date": "",
            "end_date": "",
            "clarifications": f"Could not parse: {llm_output}\nError: {str(e)}"
        }

def process_user_input(user_text: str) -> str:
    """
    Decide which service category the user wants: vacation, flight, hotel, or activities.
    Returns one of these as a JSON snippet: {"service": "<category>"}.
    """
    system_instructions = """
    You are a travel assistant deciding which category fits the user's request.
    The categories: 'vacation', 'flight', 'hotel', 'activities'.
    You MUST return valid JSON in the form: {"service": "<category>"}.
    """

    format_instructions = """
    Return a JSON object in this exact format:
    {
        "service": "<category>"
    }
    Replace <category> with one of: 'vacation', 'flight', 'hotel', 'activities'.
    """

    prompt = ChatPromptTemplate.from_messages([
        SystemMessagePromptTemplate.from_template("{system_instructions}"),
        HumanMessagePromptTemplate.from_template(
            "User request: {user_text}\n\n{format_instructions}"
        )
    ]).format_messages(
        system_instructions=system_instructions,
        user_text=user_text,
        format_instructions=format_instructions
    )

    llm_response = get_llm(temperature=0, model_name="gpt-4")(prompt)

    try:
        return json.loads(llm_response.content).get("service", "vacation")
    except json.JSONDecodeError:
        return "vacation"
    except Exception as e:
        print(f"Error processing user input: {e}")
        return "vacation"
