"""Provider-specific response parsers for unified data extraction."""

from typing import Optional, Dict, Any, List, Tuple
from .instrumentation import ResponseParser


class OpenAIResponseParser(ResponseParser):
    """Parser for OpenAI API responses."""
    
    def extract_token_usage(self, response_data: Any) -> Tuple[Optional[int], Optional[int], Optional[int]]:
        """Extract token usage from OpenAI response."""
        if hasattr(response_data, 'usage') and response_data.usage:
            return (
                getattr(response_data.usage, 'prompt_tokens', None),
                getattr(response_data.usage, 'completion_tokens', None),
                getattr(response_data.usage, 'total_tokens', None)
            )
        return None, None, None
    
    def extract_model_name(self, request_data: Dict[str, Any], response_data: Any) -> Optional[str]:
        """Extract model name from OpenAI request or response."""
        if hasattr(response_data, 'model'):
            return response_data.model
        return request_data.get('model')
    
    def extract_input_messages(self, request_data: Dict[str, Any]) -> Optional[List[Dict[str, Any]]]:
        """Extract input messages from OpenAI request."""
        messages = request_data.get('messages')
        if not messages:
            return None
        
        result = []
        for msg in messages:
            if isinstance(msg, dict):
                result.append(msg)
            elif hasattr(msg, 'role') and hasattr(msg, 'content'):
                result.append({"role": msg.role, "content": msg.content})
        return result if result else None
    
    def extract_output_content(self, response_data: Any) -> Optional[str]:
        """Extract output content from OpenAI response."""
        if hasattr(response_data, 'choices') and response_data.choices:
            choice = response_data.choices[0]
            if hasattr(choice, 'message') and hasattr(choice.message, 'content'):
                return choice.message.content
        return None
    
    def extract_finish_reason(self, response_data: Any) -> Optional[str]:
        """Extract finish reason from OpenAI response."""
        if hasattr(response_data, 'choices') and response_data.choices:
            choice = response_data.choices[0]
            if hasattr(choice, 'finish_reason'):
                return choice.finish_reason
        return None
    
    def extract_tool_calls(self, response_data: Any) -> List[Dict[str, Any]]:
        """Extract tool calls from OpenAI response."""
        tool_calls = []
        
        if hasattr(response_data, 'choices') and response_data.choices:
            choice = response_data.choices[0]
            if (hasattr(choice, 'message') and 
                hasattr(choice.message, 'tool_calls') and 
                choice.message.tool_calls):
                
                for tool_call in choice.message.tool_calls:
                    if hasattr(tool_call, 'function'):
                        tool_calls.append({
                            'name': tool_call.function.name,
                            'parameters': tool_call.function.arguments
                        })
        
        return tool_calls


class AnthropicResponseParser(ResponseParser):
    """Parser for Anthropic API responses."""
    
    def extract_token_usage(self, response_data: Any) -> Tuple[Optional[int], Optional[int], Optional[int]]:
        """Extract token usage from Anthropic response."""
        if hasattr(response_data, 'usage') and response_data.usage:
            input_tokens = getattr(response_data.usage, 'input_tokens', None)
            output_tokens = getattr(response_data.usage, 'output_tokens', None)
            total_tokens = None
            if input_tokens is not None and output_tokens is not None:
                total_tokens = input_tokens + output_tokens
            return input_tokens, output_tokens, total_tokens
        return None, None, None
    
    def extract_model_name(self, request_data: Dict[str, Any], response_data: Any) -> Optional[str]:
        """Extract model name from Anthropic request or response."""
        if hasattr(response_data, 'model'):
            return response_data.model
        return request_data.get('model')
    
    def extract_input_messages(self, request_data: Dict[str, Any]) -> Optional[List[Dict[str, Any]]]:
        """Extract input messages from Anthropic request."""
        messages = request_data.get('messages')
        if not messages:
            return None
        
        result = []
        for msg in messages:
            if isinstance(msg, dict):
                result.append(msg)
            elif hasattr(msg, 'role') and hasattr(msg, 'content'):
                content = msg.content
                if isinstance(content, list):
                    # Handle structured content
                    content_items = []
                    for item in content:
                        if isinstance(item, dict):
                            content_items.append(item)
                        elif hasattr(item, 'type') and hasattr(item, 'text'):
                            content_items.append({"type": item.type, "text": item.text})
                    content = content_items
                result.append({"role": msg.role, "content": content})
        return result if result else None
    
    def extract_output_content(self, response_data: Any) -> Optional[str]:
        """Extract output content from Anthropic response."""
        if hasattr(response_data, 'content') and response_data.content:
            content_parts = []
            for content_block in response_data.content:
                if hasattr(content_block, 'text'):
                    content_parts.append(content_block.text)
                elif isinstance(content_block, dict) and 'text' in content_block:
                    content_parts.append(content_block['text'])
            return ' '.join(content_parts) if content_parts else None
        return None
    
    def extract_finish_reason(self, response_data: Any) -> Optional[str]:
        """Extract finish reason from Anthropic response."""
        if hasattr(response_data, 'stop_reason'):
            return response_data.stop_reason
        return None
    
    def extract_tool_calls(self, response_data: Any) -> List[Dict[str, Any]]:
        """Extract tool calls from Anthropic response."""
        tool_calls = []
        
        if hasattr(response_data, 'content') and response_data.content:
            for content_block in response_data.content:
                if (hasattr(content_block, 'type') and 
                    content_block.type == 'tool_use'):
                    tool_calls.append({
                        'name': getattr(content_block, 'name', 'unknown'),
                        'parameters': getattr(content_block, 'input', None)
                    })
        
        return tool_calls


class GoogleResponseParser(ResponseParser):
    """Parser for Google Gemini API responses."""
    
    def extract_token_usage(self, response_data: Any) -> Tuple[Optional[int], Optional[int], Optional[int]]:
        """Extract token usage from Google response."""
        if hasattr(response_data, 'usage_metadata') and response_data.usage_metadata:
            usage = response_data.usage_metadata
            input_tokens = getattr(usage, 'prompt_token_count', None)
            output_tokens = getattr(usage, 'candidates_token_count', None)
            total_tokens = getattr(usage, 'total_token_count', None)
            
            if total_tokens is None and input_tokens is not None and output_tokens is not None:
                total_tokens = input_tokens + output_tokens
                
            return input_tokens, output_tokens, total_tokens
        return None, None, None
    
    def extract_model_name(self, request_data: Dict[str, Any], response_data: Any) -> Optional[str]:
        """Extract model name from Google request."""
        return request_data.get('model')
    
    def extract_input_messages(self, request_data: Dict[str, Any]) -> Optional[List[Dict[str, Any]]]:
        """Extract input messages from Google request."""
        contents = request_data.get('contents')
        if not contents:
            return None
        
        result = []
        
        if isinstance(contents, str):
            result.append({"role": "user", "content": contents})
        elif isinstance(contents, list):
            for content in contents:
                if isinstance(content, str):
                    result.append({"role": "user", "content": content})
                elif isinstance(content, dict):
                    result.append(content)
                elif hasattr(content, 'role') and hasattr(content, 'parts'):
                    parts_text = []
                    for part in content.parts:
                        if hasattr(part, 'text'):
                            parts_text.append(part.text)
                    result.append({
                        "role": content.role,
                        "content": ' '.join(parts_text) if parts_text else str(content.parts)
                    })
        
        return result if result else None
    
    def extract_output_content(self, response_data: Any) -> Optional[str]:
        """Extract output content from Google response."""
        if hasattr(response_data, 'text'):
            return response_data.text
        
        if hasattr(response_data, 'candidates') and response_data.candidates:
            candidate = response_data.candidates[0]
            if hasattr(candidate, 'content') and hasattr(candidate.content, 'parts'):
                parts_text = []
                for part in candidate.content.parts:
                    if hasattr(part, 'text'):
                        parts_text.append(part.text)
                return ' '.join(parts_text) if parts_text else None
        
        return None
    
    def extract_finish_reason(self, response_data: Any) -> Optional[str]:
        """Extract finish reason from Google response."""
        if hasattr(response_data, 'candidates') and response_data.candidates:
            candidate = response_data.candidates[0]
            if hasattr(candidate, 'finish_reason'):
                return str(candidate.finish_reason)
        return None


class PydanticAIResponseParser(ResponseParser):
    """Parser for Pydantic AI responses."""
    
    def extract_token_usage(self, response_data: Any) -> Tuple[Optional[int], Optional[int], Optional[int]]:
        """Extract token usage from Pydantic AI response."""
        if hasattr(response_data, 'usage_cost') and response_data.usage_cost:
            usage = response_data.usage_cost
            input_tokens = (getattr(usage, 'input_tokens', None) or 
                          getattr(usage, 'prompt_tokens', None))
            output_tokens = (getattr(usage, 'output_tokens', None) or 
                           getattr(usage, 'completion_tokens', None))
            total_tokens = getattr(usage, 'total_tokens', None)
            
            if total_tokens is None and input_tokens is not None and output_tokens is not None:
                total_tokens = input_tokens + output_tokens
                
            return input_tokens, output_tokens, total_tokens
        return None, None, None
    
    def extract_model_name(self, request_data: Dict[str, Any], response_data: Any) -> Optional[str]:
        """Extract model name from Pydantic AI response."""
        if hasattr(response_data, 'model_name'):
            return response_data.model_name
        return request_data.get('model')
    
    def extract_input_messages(self, request_data: Dict[str, Any]) -> Optional[List[Dict[str, Any]]]:
        """Extract input messages from Pydantic AI request."""
        user_prompt = request_data.get('user_prompt')
        if user_prompt:
            return [{"role": "user", "content": str(user_prompt)}]
        return None
    
    def extract_output_content(self, response_data: Any) -> Optional[str]:
        """Extract output content from Pydantic AI response."""
        if hasattr(response_data, 'data'):
            data = response_data.data
            if isinstance(data, str):
                return data
            else:
                try:
                    import json
                    return json.dumps(data, default=str)
                except Exception:
                    return str(data)
        return None
    
    def extract_finish_reason(self, response_data: Any) -> Optional[str]:
        """Extract finish reason from Pydantic AI response."""
        return "completed" if hasattr(response_data, 'data') else None
    
    def extract_tool_calls(self, response_data: Any) -> List[Dict[str, Any]]:
        """Extract tool calls from Pydantic AI response."""
        tool_calls = []
        
        if hasattr(response_data, 'all_messages'):
            for message in response_data.all_messages():
                if hasattr(message, 'tool_calls') and message.tool_calls:
                    for tool_call in message.tool_calls:
                        tool_calls.append({
                            'name': getattr(tool_call, 'name', 'unknown'),
                            'parameters': getattr(tool_call, 'arguments', None)
                        })
        
        return tool_calls