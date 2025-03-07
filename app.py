import os
import json
from flask import Flask, request, jsonify
from dotenv import load_dotenv
from github_handler import GithubHandler
from llm_analyzer import LLMAnalyzer
from github_commenter import GithubCommenter

# Load environment variables
load_dotenv()

app = Flask(__name__)

@app.route('/')
def index():
    return "PR Agent is running! Send GitHub webhooks to /webhook"

@app.route('/webhook', methods=['POST'])
def webhook():
    # Verify webhook signature if needed
    # GitHub sends a X-Hub-Signature header that you can verify
    
    if request.method == 'POST':
        payload = request.json
        
        # Check if this is a pull request event
        if 'pull_request' in payload and payload.get('action') in ['opened', 'synchronize']:
            try:
                # Extract PR information
                pr_number = payload['pull_request']['number']
                repo_name = payload['repository']['full_name']
                
                # Process the pull request
                process_pull_request(repo_name, pr_number)
                
                return jsonify({'status': 'success', 'message': f'Processing PR #{pr_number}'})
            except Exception as e:
                app.logger.error(f"Error processing webhook: {str(e)}")
                return jsonify({'status': 'error', 'message': str(e)}), 500
        
        return jsonify({'status': 'ignored', 'message': 'Not a relevant PR event'})

def process_pull_request(repo_name, pr_number):
    """
    Process a pull request by:
    1. Fetching the PR details and diffs
    2. Analyzing the diffs with an LLM
    3. Posting comments back to GitHub
    """
    # Initialize components
    github_handler = GithubHandler(os.getenv('GITHUB_TOKEN'))
    
    # Get the appropriate API key based on the LLM provider
    llm_provider = os.getenv('LLM_PROVIDER', 'openai').lower()
    if llm_provider == 'openai':
        api_key = os.getenv('OPENAI_API_KEY') or os.getenv('LLM_API_KEY')
    else:
        api_key = os.getenv('LLM_API_KEY')
    
    if not api_key:
        raise ValueError(f"API key for {llm_provider} not provided. Set LLM_API_KEY environment variable.")
    
    llm_analyzer = LLMAnalyzer(api_key)
    github_commenter = GithubCommenter(os.getenv('GITHUB_TOKEN'))
    
    # Get PR diffs
    diffs = github_handler.get_pr_diffs(repo_name, pr_number)
    
    # Analyze diffs with LLM
    analysis_results = llm_analyzer.analyze_diffs(diffs)
    
    # Post comments back to GitHub
    for file_path, comments in analysis_results.items():
        for comment in comments:
            github_commenter.post_comment(
                repo_name, 
                pr_number, 
                file_path, 
                comment['line'], 
                comment['content']
            )

if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
