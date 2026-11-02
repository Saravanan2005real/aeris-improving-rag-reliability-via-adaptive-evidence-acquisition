import json
import re
import logging
import json_repair

logger = logging.getLogger(__name__)

class JSONParsingError(Exception):
    pass

def extract_json(text: str) -> str:
    """
    Extracts a JSON object or array from text deterministically.
    Raises JSONParsingError and logs raw output if parsing fails.
    """
    if not text:
        raise JSONParsingError("Empty response")
        
    original_text = text
    text = text.strip()
    
    # 1. Strip markdown fences
    text = re.sub(r"^```(?:json)?\s*", "", text)
    text = re.sub(r"\s*```$", "", text)
    
    # 1.5 Fix trailing commas
    text = re.sub(r",\s*([\]}])", r"\1", text)
    
    # 2. Try whole text
    try:
        json.loads(text)
        return text
    except json.JSONDecodeError:
        pass
        
    # 3. Try to extract first complete object
    s_obj = text.find("{")
    e_obj = text.rfind("}")
    if s_obj != -1 and e_obj != -1 and e_obj > s_obj:
        cand = text[s_obj:e_obj+1]
        try:
            json.loads(cand)
            return cand
        except json.JSONDecodeError:
            pass
            
    # 4. Try to extract first complete array
    s_arr = text.find("[")
    e_arr = text.rfind("]")
    if s_arr != -1 and e_arr != -1 and e_arr > s_arr:
        cand = text[s_arr:e_arr+1]
        try:
            json.loads(cand)
            return cand
        except json.JSONDecodeError:
            pass
            
    # 5. Handle restarted generations
    start_indices_obj = [i for i, c in enumerate(text) if c == '{']
    if start_indices_obj and e_obj != -1:
        for s in reversed(start_indices_obj):
            if e_obj > s:
                cand = text[s:e_obj+1]
                try:
                    json.loads(cand)
                    return cand
                except json.JSONDecodeError:
                    pass

    # 6. Handle truncated extractor output
    if '"claims": [' in text and not text.endswith('}'):
        idx = text.rfind('",')
        if idx != -1:
            cand = text[:idx+1] + "]}"
            try:
                json.loads(cand)
                return cand
            except json.JSONDecodeError:
                pass

    # 7. Try robust repair
    try:
        repaired = json_repair.repair_json(original_text, return_objects=False)
        if repaired:
            # Validate that the repaired result is a valid object/array
            parsed_repaired = json.loads(repaired)
            if isinstance(parsed_repaired, (dict, list)):
                return repaired
    except Exception as e:
        pass

    # Log raw output on complete failure
    error_msg = f"JSON Parsing Error. Raw model output:\n{original_text}\n---END RAW---"
    logger.error(error_msg)
    try:
        print(error_msg)
    except UnicodeEncodeError:
        print(error_msg.encode('ascii', 'replace').decode('ascii'))
        
    raise JSONParsingError("No valid JSON object or array found in model response.")
