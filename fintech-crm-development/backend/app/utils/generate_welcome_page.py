from fastapi.responses import HTMLResponse

def generate_welcome_page() -> HTMLResponse:
    """
    Generates a welcome page for the Saral Backend application.
    Returns an HTMLResponse with styled content.
    """
    html_content = """
    <!DOCTYPE html>
    <html>
        <head>
            <title>Saral Backend</title>
            <style>
                :root {
                    --primary-color: #333;
                    --secondary-color: #666;
                    --background-color: #f5f5f5;
                    --card-background: white;
                    --shadow-color: rgba(0,0,0,0.1);
                }

                body {
                    font-family: Arial, sans-serif;
                    display: flex;
                    justify-content: center;
                    align-items: center;
                    height: 100vh;
                    margin: 0;
                    background-color: var(--background-color);
                }

                .welcome-container {
                    text-align: center;
                    padding: 3rem;
                    background-color: var(--card-background);
                    border-radius: 12px;
                    box-shadow: 0 4px 6px var(--shadow-color);
                    transition: transform 0.2s ease;
                }

                .welcome-container:hover {
                    transform: translateY(-2px);
                }

                .welcome-text {
                    font-size: 2.5em;
                    color: var(--primary-color);
                    margin-bottom: 1.5rem;
                    font-weight: bold;
                }

                .api-info {
                    color: var(--secondary-color);
                    font-size: 1.2em;
                    line-height: 1.5;
                }

                .api-link {
                    color: #007bff;
                    text-decoration: none;
                    transition: color 0.2s ease;
                }

                .api-link:hover {
                    color: #0056b3;
                    text-decoration: underline;
                }

                @media (max-width: 768px) {
                    .welcome-container {
                        padding: 2rem;
                        margin: 1rem;
                    }

                    .welcome-text {
                        font-size: 2em;
                    }

                    .api-info {
                        font-size: 1em;
                    }
                }
            </style>
        </head>
        <body>
            <div class="welcome-container">
                <div class="welcome-text">
                    Welcome to Saral Backend
                </div>
                <div class="api-info">
                    API Documentation available at <a href="/docs" class="api-link">docs</a>
                </div>
            </div>
        </body>
    </html>
    """
    return HTMLResponse(content=html_content)