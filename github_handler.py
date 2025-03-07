import os
import requests
from github import Github
from github.GithubException import GithubException

class GithubHandler:
    """
    Handles interactions with GitHub API to fetch PR details and diffs
    """
    
    def __init__(self, github_token):
        """
        Initialize with GitHub token
        
        Args:
            github_token (str): GitHub personal access token
        """
        self.github_token = github_token
        self.github = Github(github_token)
    
    def get_pr_details(self, repo_name, pr_number):
        """
        Get pull request details
        
        Args:
            repo_name (str): Repository name in format 'owner/repo'
            pr_number (int): Pull request number
            
        Returns:
            github.PullRequest.PullRequest: Pull request object
        """
        try:
            repo = self.github.get_repo(repo_name)
            pull_request = repo.get_pull(pr_number)
            return pull_request
        except GithubException as e:
            raise Exception(f"Failed to get PR details: {str(e)}")
    
    def get_pr_diffs(self, repo_name, pr_number):
        """
        Get pull request diffs
        
        Args:
            repo_name (str): Repository name in format 'owner/repo'
            pr_number (int): Pull request number
            
        Returns:
            dict: Dictionary with file paths as keys and diff content as values
        """
        try:
            # Get PR details
            pull_request = self.get_pr_details(repo_name, pr_number)
            
            # Get diff content using the diff_url
            diff_url = pull_request.diff_url
            headers = {'Authorization': f'token {self.github_token}'}
            response = requests.get(diff_url, headers=headers)
            
            if response.status_code != 200:
                raise Exception(f"Failed to get PR diff: {response.status_code}")
            
            # Parse the diff content
            diff_content = response.text
            
            # Process the diff to extract per-file changes
            return self._parse_diff_content(diff_content)
            
        except Exception as e:
            raise Exception(f"Failed to get PR diffs: {str(e)}")
    
    def _parse_diff_content(self, diff_content):
        """
        Parse the raw diff content into a structured format
        
        Args:
            diff_content (str): Raw diff content from GitHub
            
        Returns:
            dict: Dictionary with file paths as keys and structured diff info as values
        """
        diffs = {}
        current_file = None
        current_diff_lines = []
        
        # Split the diff content by lines
        lines = diff_content.split('\n')
        
        for line in lines:
            # Check if this is a new file diff
            if line.startswith('diff --git'):
                # Save the previous file diff if exists
                if current_file and current_diff_lines:
                    diffs[current_file] = {
                        'content': '\n'.join(current_diff_lines),
                        'changes': self._extract_line_changes(current_diff_lines)
                    }
                
                # Extract the new file path
                # The format is typically: diff --git a/path/to/file b/path/to/file
                parts = line.split(' ')
                if len(parts) >= 4:
                    # Use the b/path/to/file and remove the b/ prefix
                    current_file = parts[3][2:]
                    current_diff_lines = [line]
            elif current_file:
                current_diff_lines.append(line)
        
        # Add the last file diff
        if current_file and current_diff_lines:
            diffs[current_file] = {
                'content': '\n'.join(current_diff_lines),
                'changes': self._extract_line_changes(current_diff_lines)
            }
        
        return diffs
    
    def _extract_line_changes(self, diff_lines):
        """
        Extract line-by-line changes from diff content
        
        Args:
            diff_lines (list): List of diff content lines
            
        Returns:
            list: List of dictionaries with line numbers and change types
        """
        changes = []
        in_hunk = False
        old_line_num = 0
        new_line_num = 0
        
        for line in diff_lines:
            # Check if this is a hunk header
            if line.startswith('@@'):
                in_hunk = True
                # Extract line numbers from hunk header
                # Format: @@ -old_start,old_count +new_start,new_count @@
                parts = line.split(' ')
                if len(parts) >= 3:
                    old_info = parts[1]
                    new_info = parts[2]
                    
                    # Extract old line number
                    if ',' in old_info:
                        old_line_num = int(old_info[1:].split(',')[0])
                    else:
                        old_line_num = int(old_info[1:])
                    
                    # Extract new line number
                    if ',' in new_info:
                        new_line_num = int(new_info[1:].split(',')[0])
                    else:
                        new_line_num = int(new_info[1:])
            
            # Process lines in a hunk
            elif in_hunk:
                if line.startswith('+'):
                    # Added line
                    changes.append({
                        'type': 'addition',
                        'line_num': new_line_num,
                        'content': line[1:]
                    })
                    new_line_num += 1
                elif line.startswith('-'):
                    # Removed line
                    changes.append({
                        'type': 'deletion',
                        'line_num': old_line_num,
                        'content': line[1:]
                    })
                    old_line_num += 1
                elif not line.startswith('\\'):  # Ignore "\ No newline at end of file"
                    # Context line
                    changes.append({
                        'type': 'context',
                        'old_line_num': old_line_num,
                        'new_line_num': new_line_num,
                        'content': line[1:]
                    })
                    old_line_num += 1
                    new_line_num += 1
        
        return changes
