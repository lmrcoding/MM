from utils.dlp import redact_sensitive_data

def prepare_training_example(input_text: str, response_text: str) -> dict:
    clean_input = redact_sensitive_data(input_text)
    clean_output = redact_sensitive_data(response_text)

    return {
        "input": clean_input,
        "output": clean_output
    }
