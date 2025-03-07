import os
from github import Github
from github.GithubException import GithubException

class GithubCommenter:
    """
    Posts comments to GitHub pull requests
    """
    
    def __init__(self, github_token):
        """
        Initialize with GitHub token
        
        Args:
            github_token (str): GitHub personal access token
        """
        self.github_token = github_token
        self.github = Github(github_token)
    
    def post_comment(self, repo_name, pr_number, file_path, line_number, comment_text):
        """
        Post a comment on a specific line in a pull request
        
        Args:
            repo_name (str): Repository name in format 'owner/repo'
            pr_number (int): Pull request number
            file_path (str): Path to the file
            line_number (int): Line number to comment on
            comment_text (str): Comment text
            
        Returns:
            bool: True if comment was posted successfully, False otherwise
        """
        try:
            # Get repository and pull request
            repo = self.github.get_repo(repo_name)
            pull_request = repo.get_pull(pr_number)
            
            # Create a review comment
            # Note: This requires the PR to have been created with a diff
            # and the line number must be in the diff
            pull_request.create_review_comment(
                body=comment_text,
                commit=pull_request.get_commits().get_page(0)[-1],  # Last commit in the PR
                path=file_path,
                position=self._get_position_in_diff(pull_request, file_path, line_number)
            )
            
            return True
            
        except GithubException as e:
            print(f"Failed to post comment: {str(e)}")
            
            # Fallback: Post a regular PR comment if review comment fails
            try:
                self._post_fallback_comment(repo_name, pr_number, file_path, line_number, comment_text)
                return True
            except Exception as e2:
                print(f"Failed to post fallback comment: {str(e2)}")
                return False
    
    def _get_position_in_diff(self, pull_request, file_path, line_number):
        """
        Get the position in the diff for a specific line number
        
        Args:
            pull_request: GitHub pull request object
            file_path (str): Path to the file
            line_number (int): Line number in the file
            
        Returns:
            int: Position in the diff
        """
        # Get the diff for the file
        files = pull_request.get_files()
        for file in files:
            if file.filename == file_path:
                # Parse the patch to find the position
                patch_lines = file.patch.split('\n')
                position = 0
                current_line = 0
                
                for patch_line in patch_lines:
                    position += 1
                    
                    # Skip diff headers
                    if patch_line.startswith('@@'):
                        # Extract the starting line number
                        # Format: @@ -old_start,old_count +new_start,new_count @@
                        parts = patch_line.split(' ')
                        if len(parts) >= 3:
                            new_info = parts[2]
                            if ',' in new_info:
                                current_line = int(new_info[1:].split(',')[0])
                            else:
                                current_line = int(new_info[1:])
                        continue
                    
                    # Track line numbers for additions and context lines
                    if patch_line.startswith('+') or not patch_line.startswith('-'):
                        if current_line == line_number:
                            return position
                        if not patch_line.startswith('\\'):  # Ignore "\ No newline at end of file"
                            current_line += 1
                
                # If we couldn't find the exact line, return the position at the end of the file
                return position
        
        # If we couldn't find the file, raise an exception
        raise Exception(f"File {file_path} not found in the pull request")
    
    def _post_fallback_comment(self, repo_name, pr_number, file_path, line_number, comment_text):
        """
        Post a regular comment on the pull request as a fallback
        
        Args:
            repo_name (str): Repository name in format 'owner/repo'
            pr_number (int): Pull request number
            file_path (str): Path to the file
            line_number (int): Line number to comment on
            comment_text (str): Comment text
        """
        repo = self.github.get_repo(repo_name)
        pull_request = repo.get_pull(pr_number)
        
        # Format the comment to include file and line information
        formatted_comment = f"**{file_path}:{line_number}**\n\n{comment_text}"
        
        # Post a regular comment on the PR
        pull_request.create_issue_comment(formatted_comment)
    
    def post_summary_comment(self, repo_name, pr_number, summary_text):
        """
        Post a summary comment on the pull request
        
        Args:
            repo_name (str): Repository name in format 'owner/repo'
            pr_number (int): Pull request number
            summary_text (str): Summary text
            
        Returns:
            bool: True if comment was posted successfully, False otherwise
        """
        try:
            repo = self.github.get_repo(repo_name)
            pull_request = repo.get_pull(pr_number)
            
            # Post a regular comment on the PR
            pull_request.create_issue_comment(summary_text)
            
            return True
            
        except GithubException as e:
            print(f"Failed to post summary comment: {str(e)}")
            return False
