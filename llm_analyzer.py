import os
import json
import importlib

class LLMAnalyzer:
    """
    Analyzes code diffs using various LLM APIs
    """
    
    def __init__(self, api_key):
        """
        Initialize with API key and provider
        
        Args:
            api_key (str): API key for the LLM provider
        """
        self.api_key = api_key
        self.provider = os.getenv('LLM_PROVIDER', 'openai').lower()
        self.model = os.getenv('LLM_MODEL', 'gpt-4-turbo')
        
        # Initialize the appropriate client based on the provider
        if self.provider == 'openai':
            from openai import OpenAI
            self.client = OpenAI(api_key=api_key)
        elif self.provider == 'anthropic':
            try:
                from anthropic import Anthropic
                self.client = Anthropic(api_key=api_key)
            except ImportError:
                raise ImportError("Anthropic package not installed. Install with 'pip install anthropic'")
        elif self.provider == 'google':
            try:
                import google.generativeai as genai
                genai.configure(api_key=api_key)
                self.client = genai
            except ImportError:
                raise ImportError("Google Generative AI package not installed. Install with 'pip install google-generativeai'")
        elif self.provider == 'azure_openai':
            from openai import AzureOpenAI
            azure_endpoint = os.getenv('AZURE_OPENAI_ENDPOINT')
            if not azure_endpoint:
                raise ValueError("AZURE_OPENAI_ENDPOINT environment variable is required for Azure OpenAI")
            self.client = AzureOpenAI(
                api_key=api_key,
                api_version=os.getenv('AZURE_OPENAI_API_VERSION', '2023-05-15'),
                azure_endpoint=azure_endpoint
            )
        else:
            raise ValueError(f"Unsupported LLM provider: {self.provider}")
    
    def analyze_diffs(self, diffs):
        """
        Analyze diffs using OpenAI's API
        
        Args:
            diffs (dict): Dictionary with file paths as keys and diff content as values
            
        Returns:
            dict: Dictionary with file paths as keys and analysis results as values
        """
        results = {}
        
        for file_path, diff_info in diffs.items():
            # Skip binary files or files without changes
            if not diff_info.get('changes'):
                continue
            
            # Analyze each file's changes
            file_analysis = self._analyze_file_diff(file_path, diff_info)
            
            if file_analysis:
                results[file_path] = file_analysis
        
        return results
    
    def _analyze_file_diff(self, file_path, diff_info):
        """
        Analyze a single file's diff
        
        Args:
            file_path (str): Path to the file
            diff_info (dict): Diff information for the file
            
        Returns:
            list: List of comments for the file
        """
        # Extract only the additions for analysis
        additions = [change for change in diff_info.get('changes', []) 
                    if change.get('type') == 'addition']
        
        if not additions:
            return []
        
        # Get file extension to determine language
        _, ext = os.path.splitext(file_path)
        language = self._get_language_from_extension(ext)
        
        # Prepare the prompt for the LLM
        prompt = self._create_analysis_prompt(file_path, language, additions, diff_info['content'])
        system_prompt = "You are a helpful code reviewer. Analyze the code changes and provide constructive feedback."
        
        # Call the appropriate LLM API based on the provider
        try:
            if self.provider == 'openai':
                return self._call_openai(system_prompt, prompt)
            elif self.provider == 'anthropic':
                return self._call_anthropic(system_prompt, prompt)
            elif self.provider == 'google':
                return self._call_google(system_prompt, prompt)
            elif self.provider == 'azure_openai':
                return self._call_azure_openai(system_prompt, prompt)
            else:
                raise ValueError(f"Unsupported LLM provider: {self.provider}")
        except Exception as e:
            print(f"Error analyzing file {file_path} with {self.provider}: {str(e)}")
            return []
    
    def _call_openai(self, system_prompt, user_prompt):
        """Call OpenAI API"""
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.3,
            max_tokens=2000
        )
        
        analysis_text = response.choices[0].message.content
        return self._parse_analysis_response(analysis_text, [])
    
    def _call_anthropic(self, system_prompt, user_prompt):
        """Call Anthropic API"""
        combined_prompt = f"{system_prompt}\n\n{user_prompt}"
        response = self.client.messages.create(
            model=self.model,
            max_tokens=2000,
            temperature=0.3,
            system=system_prompt,
            messages=[
                {"role": "user", "content": user_prompt}
            ]
        )
        
        analysis_text = response.content[0].text
        return self._parse_analysis_response(analysis_text, [])
    
    def _call_google(self, system_prompt, user_prompt):
        """Call Google Generative AI API"""
        combined_prompt = f"{system_prompt}\n\n{user_prompt}"
        response = self.client.generate_text(
            model=self.model,
            prompt=combined_prompt,
            temperature=0.3,
            max_output_tokens=2000,
        )
        
        analysis_text = response.text
        return self._parse_analysis_response(analysis_text, [])
    
    def _call_azure_openai(self, system_prompt, user_prompt):
        """Call Azure OpenAI API"""
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.3,
            max_tokens=2000
        )
        
        analysis_text = response.choices[0].message.content
        return self._parse_analysis_response(analysis_text, [])
    
    def _create_analysis_prompt(self, file_path, language, additions, full_diff):
        """
        Create a prompt for the LLM to analyze the diff
        
        Args:
            file_path (str): Path to the file
            language (str): Programming language of the file
            additions (list): List of added lines
            full_diff (str): Full diff content
            
        Returns:
            str: Prompt for the LLM
        """
        prompt = f"""
Analyze the following code changes in the file `{file_path}` ({language}).

Here's the full diff:
```diff
{full_diff}
```

Focus on the added lines and provide specific, actionable feedback on:
1. Code quality issues
2. Potential bugs or edge cases
3. Performance concerns
4. Security vulnerabilities
5. Best practices and style improvements

For each issue, specify:
1. The line number
2. A clear description of the issue
3. A suggested improvement

Format your response as a JSON array of objects with the following structure:
[
  {{
    "line": <line_number>,
    "content": "Your comment here"
  }},
  ...
]

Only include comments that are valuable and actionable. If there are no issues to report, return an empty array [].
"""
        return prompt
    
    def _parse_analysis_response(self, analysis_text, additions):
        """
        Parse the LLM's response into a structured format
        
        Args:
            analysis_text (str): Raw response from the LLM
            additions (list): List of added lines
            
        Returns:
            list: List of comments
        """
        try:
            # Extract JSON from the response
            # The LLM might include explanatory text before or after the JSON
            json_start = analysis_text.find('[')
            json_end = analysis_text.rfind(']') + 1
            
            if json_start >= 0 and json_end > json_start:
                json_str = analysis_text[json_start:json_end]
                comments = json.loads(json_str)
                
                # Validate the structure
                valid_comments = []
                for comment in comments:
                    if isinstance(comment, dict) and 'line' in comment and 'content' in comment:
                        valid_comments.append(comment)
                
                return valid_comments
            
            return []
            
        except json.JSONDecodeError:
            # If JSON parsing fails, try to extract comments in a different way
            # This is a fallback in case the LLM doesn't format the response as requested
            print(f"Failed to parse JSON response: {analysis_text}")
            return []
    
    def _get_language_from_extension(self, extension):
        """
        Get programming language from file extension
        
        Args:
            extension (str): File extension
            
        Returns:
            str: Programming language name
        """
        extension_map = {
            '.py': 'Python',
            '.js': 'JavaScript',
            '.ts': 'TypeScript',
            '.jsx': 'React JSX',
            '.tsx': 'React TSX',
            '.java': 'Java',
            '.c': 'C',
            '.cpp': 'C++',
            '.cs': 'C#',
            '.go': 'Go',
            '.rb': 'Ruby',
            '.php': 'PHP',
            '.swift': 'Swift',
            '.kt': 'Kotlin',
            '.rs': 'Rust',
            '.html': 'HTML',
            '.css': 'CSS',
            '.scss': 'SCSS',
            '.md': 'Markdown',
            '.json': 'JSON',
            '.yml': 'YAML',
            '.yaml': 'YAML',
            '.xml': 'XML',
            '.sh': 'Shell',
            '.bat': 'Batch',
            '.ps1': 'PowerShell'
        }
        
        return extension_map.get(extension.lower(), 'Unknown')
