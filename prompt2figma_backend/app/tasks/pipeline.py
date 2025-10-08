import os
import json
import logging
import google.generativeai as genai
import subprocess
from .celery_app import celery_app

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Configure the Gemini API key
try:
    genai.configure(api_key=os.environ["GEMINI_API_KEY"])
except KeyError:
    logging.error("GEMINI_API_KEY environment variable not set.")
    raise

def validate_component_structure(node: dict, path: str = "root") -> list:
    """
    Validates component structure and returns a list of issues found.
    
    Checks:
    1. Text components don't have strings in children
    2. Children arrays only contain objects
    3. All children have required fields (componentName, type, props)
    """
    issues = []
    
    if not isinstance(node, dict):
        return [f"{path}: Node is not a dictionary"]
    
    node_type = node.get("type", "")
    
    # Check if Text component has strings in children
    if node_type.lower() == "text" and "children" in node:
        if isinstance(node["children"], list):
            for i, child in enumerate(node["children"]):
                if isinstance(child, str):
                    issues.append(f"{path}.children[{i}]: Text component has string in children array: '{child}'")
                elif not isinstance(child, dict):
                    issues.append(f"{path}.children[{i}]: Children array contains non-object value")
    
    # Check all children are valid objects
    if "children" in node and isinstance(node["children"], list):
        for i, child in enumerate(node["children"]):
            if isinstance(child, str):
                issues.append(f"{path}.children[{i}]: Children array contains string: '{child}'")
            elif isinstance(child, dict):
                # Recursively validate children
                child_path = f"{path}.children[{i}]({child.get('componentName', 'unnamed')})"
                issues.extend(validate_component_structure(child, child_path))
            elif child is not None:
                issues.append(f"{path}.children[{i}]: Children array contains invalid type: {type(child)}")
    
    return issues


def sanitize_text_components(node: dict) -> dict:
    """
    Recursively sanitizes Text components to ensure text content is in props.text,
    not in the children array. Also ensures children is always an array.
    
    Rules:
    1. Text components should have text content in props.text (or props.content/props.title)
    2. Text components should NOT have string values in children array
    3. All children arrays must only contain component objects, never primitives
    """
    if not isinstance(node, dict):
        return node
    
    node_type = node.get("type", "").lower()
    
    # Handle Text components specifically
    if node_type == "text":
        # Ensure props exists
        if "props" not in node:
            node["props"] = {}
        
        # Check if children contains string values (incorrect format)
        if "children" in node and isinstance(node["children"], list):
            text_content = []
            valid_children = []
            
            for child in node["children"]:
                if isinstance(child, str):
                    # String found in children - this is incorrect
                    text_content.append(child)
                elif isinstance(child, dict):
                    # Valid component object
                    valid_children.append(sanitize_text_components(child))
            
            # Move string content to props.text if found
            if text_content:
                combined_text = " ".join(text_content)
                # Only set props.text if it doesn't already exist
                if "text" not in node["props"] and "content" not in node["props"]:
                    node["props"]["text"] = combined_text
            
            # Update children to only contain valid component objects
            node["children"] = valid_children
        
        # Ensure children is an empty array if not present or empty
        if "children" not in node or not node["children"]:
            node["children"] = []
    
    else:
        # For non-Text components, recursively sanitize children
        if "children" in node:
            if not isinstance(node["children"], list):
                # Convert null, undefined, or other types to empty array
                node["children"] = []
            else:
                # Filter out any primitive values and recursively sanitize
                valid_children = []
                for child in node["children"]:
                    if isinstance(child, dict):
                        valid_children.append(sanitize_text_components(child))
                    # Silently skip primitive values (strings, numbers, etc.)
                
                node["children"] = valid_children
    
    return node


def normalize_children_fields(node: dict) -> dict:
    """
    Recursively ensures all 'children' fields in the node tree are arrays.
    This is critical for Figma compatibility - Figma requires children to be arrays, not null/undefined.
    
    Note: This is now a wrapper around sanitize_text_components for backward compatibility.
    """
    return sanitize_text_components(node)


@celery_app.task(bind=True, max_retries=3, default_retry_delay=5)
def generate_wireframe_json(self, prompt: str) -> dict:
    """
    Task 1: Takes a text prompt and calls the Gemini API to generate a structured JSON output
    for a Figma wireframe.
    """
    logging.info(f"TASK 1 [generate_wireframe_json]: Received prompt - '{prompt}'")
    try:
        system_prompt = (
            "You are an expert UI/UX designer and a Figma specialist. Your task is to translate a user's "
            "natural language description into a detailed, structured JSON object that represents a Figma wireframe. "
            "This JSON will be used to programmatically generate the design, so precision is key."
            "\n\n"
            "IMPORTANT: Your response must be a SINGLE JSON object representing the root component, not an array of components."
            "\n\n"
            "The JSON structure must strictly adhere to the following schema:\n"
            "{\n"
            "  \"componentName\": \"string\",  // Name for the Figma layer, e.g., 'AppContainer' or 'MainLayout'.\n"
            "  \"type\": \"string\",            // The type of UI element. Use standard names like 'Frame', 'Rectangle', 'Text', 'Vector', 'Button', 'Input'.\n"
            "  \"props\": {                   // Properties for styling and layout, mimicking Figma's properties.\n"
            "    \"layoutMode\": \"string\",      // 'HORIZONTAL' or 'VERTICAL' for auto-layout frames.\n"
            "    \"padding\": \"string\",         // e.g., '16px' or '8px 16px'.\n"
            "    \"backgroundColor\": \"string\", // Hex code, e.g., '#FFFFFF'.\n"
            "    \"borderRadius\": \"string\",    // e.g., '8px'.\n"
            "    \"color\": \"string\",           // For text elements, e.g., '#000000'.\n"
            "    \"fontSize\": \"string\",        // e.g., '16px'.\n"
            "    \"fontWeight\": \"number\",      // e.g., 400 for regular, 700 for bold.\n"
            "    \"placeholder\": \"string\",     // For input fields.\n"
            "    \"iconName\": \"string\"         // Suggest an icon name from Material Icons if applicable, e.g., 'search' or 'arrow_forward'.\n"
            "  },\n"
            "  \"children\": []               // REQUIRED: An array of nested component objects. MUST be an array, even if empty.\n"
            "}\n\n"
            "CRITICAL RULES:\n"
            "1. Always start with a single root Frame component that contains all other elements as children.\n"
            "2. EVERY node that has children MUST have 'children' as an array (never null or missing).\n"
            "3. If a node has no children, use an empty array: \"children\": []\n"
            "4. Your output MUST be only the raw JSON object (not an array).\n"
            "5. Do not include any other text, explanations, or markdown formatting.\n"
            "\n"
            "TEXT COMPONENT RULES (CRITICAL):\n"
            "- For Text components (type: 'Text'), text content MUST be in props.text, NOT in children array\n"
            "- CORRECT: {\"type\": \"Text\", \"props\": {\"text\": \"Hello World\"}, \"children\": []}\n"
            "- INCORRECT: {\"type\": \"Text\", \"props\": {}, \"children\": [\"Hello World\"]}\n"
            "- The children array should ONLY contain component objects, NEVER strings or primitive values\n"
            "- Text components should have empty children arrays or omit children entirely\n"
            "\n"
            "Think about logical grouping of elements using 'Frame' components with 'HORIZONTAL' or 'VERTICAL' layout modes to ensure a well-structured and responsive design."
        )


        model = genai.GenerativeModel(
            'gemini-2.5-flash',
            system_instruction=system_prompt,
            generation_config=genai.types.GenerationConfig(
                response_mime_type="application/json"
            )
        )
        
        logging.info("TASK 1: Calling Gemini API for enhanced wireframe generation...")
        response = model.generate_content(prompt)
        
        model_output_str = response.text
        logging.info(f"TASK 1: Received raw model output: {model_output_str}")
        
        json_output = json.loads(model_output_str)
        
        # Ensure we have a single root object, not an array
        if isinstance(json_output, list):
            logging.warning("TASK 1: Model returned an array, wrapping in root container")
            json_output = {
                "componentName": "AppContainer",
                "type": "Frame",
                "props": {
                    "layoutMode": "VERTICAL",
                    "backgroundColor": "#FFFFFF",
                    "padding": "0px"
                },
                "children": json_output
            }
        
        # Ensure required fields exist
        if not isinstance(json_output, dict):
            raise ValueError("Generated JSON must be an object")
        
        if "componentName" not in json_output:
            json_output["componentName"] = "AppContainer"
        if "type" not in json_output:
            json_output["type"] = "Frame"
        if "props" not in json_output:
            json_output["props"] = {}
        if "children" not in json_output:
            json_output["children"] = []
        
        # CRITICAL: Recursively normalize all children fields to be arrays
        # and sanitize Text components to ensure proper format
        json_output = normalize_children_fields(json_output)
        
        # Validate the sanitization worked
        validation_issues = validate_component_structure(json_output)
        if validation_issues:
            logging.warning(f"TASK 1: Component structure issues detected after sanitization: {validation_issues}")
        else:
            logging.info("TASK 1: Component structure validation passed.")
        
        logging.info("TASK 1: Successfully generated and normalized wireframe JSON for Figma compatibility.")
        return json_output
    except Exception as e:
        logging.error(f"TASK 1: An error occurred with the Gemini API: {e}. Retrying...")
        raise self.retry(exc=e)


@celery_app.task(bind=True, max_retries=3, default_retry_delay=5)
def generate_react_code(self, wireframe_json: dict) -> str:
    """
    Task 2: Takes a detailed JSON structure and calls the Gemini API to convert it into a
    production-quality React component.
    """
    logging.info(f"TASK 2 [generate_react_code]: Received detailed wireframe JSON.")
    try:
        json_input_str = json.dumps(wireframe_json, indent=2)
        system_prompt = (
            "You are a senior frontend developer specializing in React and Tailwind CSS. Your task is to convert the "
            "following JSON UI structure into a single, production-ready, and well-documented React functional component."
            "\n\n"
            "GUIDELINES:\n"
            "1.  **Code Quality**: Write clean, readable, and maintainable code. Use ES6+ features.\n"
            "2.  **Styling**: Use Tailwind CSS exclusively for all styling. Do not use custom CSS or inline styles.\n"
            "3.  **Responsiveness**: Implement a mobile-first responsive design. Use Tailwind's responsive prefixes (e.g., `md:`, `lg:`) where appropriate.\n"
            "4.  **Component Structure**: The output must be a single self-contained React functional component.\n"
            "5.  **Icons**: If an `iconName` is provided, assume you have an `<Icon>` component available and use it like `<Icon name={iconName} />`.\n"
            "6.  **Interactivity**: Add subtle hover effects to interactive elements like buttons for better UX.\n"
            "7.  **Output Format**: You MUST ONLY output the raw React component code. Do not include any explanatory text, markdown formatting (like ```jsx), or anything else."
        )
        
        model = genai.GenerativeModel('gemini-2.5-flash', system_instruction=system_prompt)
        
        logging.info("TASK 2: Calling Gemini API for high-quality code generation...")
        
        response = model.generate_content(f"Here is the detailed JSON UI structure:\n{json_input_str}")

        react_code = response.text
        logging.info(f"TASK 2: Received React code from model.")
        
        # Basic cleaning to remove potential markdown fences
        react_code = react_code.replace("```jsx", "").replace("```", "").strip()
        
        return react_code
    except Exception as e:
        logging.error(f"TASK 2: An error occurred with the Gemini API: {e}. Retrying...")
        raise self.retry(exc=e)


# This task remains the same
@celery_app.task(bind=True)
def validate_code_ast(self, react_code: str) -> dict:
    """
    Task 3: Validates the generated React code by piping it to a Node.js script
    that uses @babel/parser.
    """
    logging.info(f"TASK 3 [validate_code_ast]: Received React code to validate.")

    try:
        script_path = "app/tasks/ast_validation.js"
        code_bytes = react_code.encode('utf-8')

        process = subprocess.run(
            ["node", script_path],
            input=code_bytes,
            capture_output=True,
            check=False,
            timeout=15
        )

        result_json_str = process.stdout.decode('utf-8')
        logging.info(f"TASK 3 [validate_code_ast]: Raw output from validator: '{result_json_str}'")

        if process.stderr:
            stderr_output = process.stderr.decode('utf-8')
            if stderr_output.strip():
                logging.error(f"AST validation script produced an error: {stderr_output}")

        if not result_json_str.strip():
            logging.error("AST validation script returned empty output.")
            return {"code": react_code, "validation_status": "FAILURE", "errors": ["Validator returned empty output."]}

        try:
            validation_result = json.loads(result_json_str)
        except Exception as e:
            logging.error(f"Failed to parse validator output as JSON: {e}")
            return {"code": react_code, "validation_status": "FAILURE", "errors": [f"Invalid JSON from validator: {e}"]}

        logging.info(f"TASK 3 [validate_code_ast]: Validation complete. Status: {validation_result.get('validation_status')}")
        return validation_result

    except FileNotFoundError:
        logging.error("AST validation script not found or 'node' command is not available.")
        return {"code": react_code, "validation_status": "FAILURE", "errors": ["Validation script not found."]}
    except Exception as e:
        logging.error(f"An unexpected error occurred during AST validation: {e}")
        return {"code": react_code, "validation_status": "FAILURE", "errors": [str(e)]}