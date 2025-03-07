# PR Agent

A Flask application that automatically analyzes GitHub pull requests using an LLM and posts review comments.

## Features

- Receives GitHub webhook events for pull requests
- Extracts code diffs from pull requests
- Analyzes code changes using various LLM providers:
  - OpenAI (GPT-4, GPT-3.5)
  - Anthropic (Claude)
  - Google (Gemini)
  - Azure OpenAI
- Posts review comments back to the pull request

## Prerequisites

- Python 3.8+
- GitHub account with a personal access token
- API key from one of the supported LLM providers:
  - OpenAI
  - Anthropic
  - Google AI
  - Azure OpenAI

## Installation

### Standard Installation

1. Clone this repository:
   ```
   git clone https://github.com/langal/pr_agent.git
   cd pr_agent
   ```

2. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

3. Create a `.env` file based on the example:
   ```
   cp .env.example .env
   ```

4. Edit the `.env` file and add your GitHub token and LLM provider API key.

### Docker Installation

1. Clone this repository:
   ```
   git clone https://github.com/langal/pr_agent.git
   cd pr_agent
   ```

2. Create a `.env` file based on the example:
   ```
   cp .env.example .env
   ```

3. Edit the `.env` file and add your GitHub token and LLM provider API key.

4. Build and run the Docker container:
   ```
   docker build -t pr-agent .
   docker run -p 5000:5000 --env-file .env pr-agent
   ```

   Or using Docker Compose:
   ```
   docker-compose up -d
   ```

5. For debug mode (which runs sleep infinity instead of the application):
   ```
   docker run -p 5000:5000 --env-file .env -e DEBUG=1 pr-agent
   ```

   Or using Docker Compose:
   ```
   docker-compose --profile debug up pr-agent-debug -d
   ```

## Configuration

### GitHub Token

You need a GitHub personal access token with the `repo` scope. Generate one at [GitHub Settings > Developer settings > Personal access tokens](https://github.com/settings/tokens).

### LLM Provider API Keys

Depending on which LLM provider you choose, you'll need to obtain an API key:

- **OpenAI**: Get an API key from [OpenAI's platform](https://platform.openai.com/api-keys)
- **Anthropic**: Get an API key from [Anthropic's console](https://console.anthropic.com/)
- **Google AI**: Get an API key from [Google AI Studio](https://makersuite.google.com/app/apikey)
- **Azure OpenAI**: Get an API key and endpoint from your Azure OpenAI Service resource in the [Azure Portal](https://portal.azure.com/)

### Environment Variables

#### Required Variables
- `GITHUB_TOKEN`: Your GitHub personal access token

#### LLM Provider Configuration
- `LLM_PROVIDER` (optional): The LLM provider to use (defaults to 'openai')
  - Supported providers: 'openai', 'anthropic', 'google', 'azure_openai'
- `LLM_API_KEY`: API key for the selected LLM provider
- `LLM_MODEL` (optional): The model to use (provider-specific defaults apply)
  - Examples:
    - OpenAI: 'gpt-4-turbo', 'gpt-3.5-turbo'
    - Anthropic: 'claude-3-opus-20240229', 'claude-3-sonnet-20240229'
    - Google: 'gemini-pro'

#### OpenAI-specific Configuration
- `OPENAI_API_KEY`: For backward compatibility when using OpenAI (same as LLM_API_KEY)

#### Azure OpenAI-specific Configuration
- `AZURE_OPENAI_ENDPOINT`: Your Azure OpenAI endpoint URL
- `AZURE_OPENAI_API_VERSION` (optional): API version (defaults to '2023-05-15')

#### Server Configuration
- `PORT` (optional): The port for the Flask server (defaults to 5000)

## Usage

1. Start the Flask server:
   ```
   python app.py
   ```

2. Set up a GitHub webhook:
   - Go to your repository settings
   - Navigate to Webhooks > Add webhook
   - Set the Payload URL to your server's URL (e.g., `https://your-server.com/webhook`)
   - Set Content type to `application/json`
   - Select "Let me select individual events" and check "Pull requests"
   - Click "Add webhook"

3. Create or update a pull request in your repository, and the PR Agent will automatically:
   - Receive the webhook event
   - Analyze the code changes
   - Post review comments on the pull request

## Deployment

For production use, consider deploying the application using:

### Docker Deployment (Recommended)

The simplest way to deploy the application is using Docker:

```
docker run -d --restart unless-stopped -p 5000:5000 --env-file .env pr-agent
```

Or using Docker Compose:

```
docker-compose up -d
```

### Traditional Deployment

Alternatively, you can deploy using:

- [Gunicorn](https://gunicorn.org/) for a production-ready WSGI server
- [Nginx](https://nginx.org/) as a reverse proxy
- [Supervisor](http://supervisord.org/) for process management

Example Gunicorn command:
```
gunicorn -w 4 -b 0.0.0.0:5000 app:app
```

## Exposing Local Server

For testing with GitHub webhooks, you can use tools like [ngrok](https://ngrok.com/) to expose your local server:

```
ngrok http 5000
```

Then use the ngrok URL as your webhook URL in GitHub.

## Customization

You can customize the LLM prompts in `llm_analyzer.py` to focus on specific aspects of code review or to match your team's coding standards.

## License

MIT
