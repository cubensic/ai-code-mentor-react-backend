from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.models.file import File
from app.models.project import Project
from uuid import UUID

# Template definitions - initial files for each template type
TEMPLATE_FILES = {
    "portfolio_website": [
        {
            "name": "index.html",
            "file_type": "html",
            "content": """<!DOCTYPE html>
<html>
<head>
  <title>My Portfolio</title>
  <link rel="stylesheet" href="style.css">
</head>
<body>
  <!-- Your code here -->
</body>
</html>"""
        },
        {
            "name": "style.css",
            "file_type": "css",
            "content": """/* Your styles here */
body {
  margin: 0;
  font-family: Arial, sans-serif;
}"""
        }
    ],
    "todo_app": [
        {
            "name": "index.html",
            "file_type": "html",
            "content": """<!DOCTYPE html>
<html>
<head>
  <title>Todo App</title>
  <link rel="stylesheet" href="style.css">
</head>
<body>
  <div id="app"></div>
  <script src="script.js"></script>
</body>
</html>"""
        },
        {
            "name": "style.css",
            "file_type": "css",
            "content": "/* Todo app styles */\n"
        },
        {
            "name": "script.js",
            "file_type": "js",
            "content": "// Your JavaScript code here\n"
        }
    ],
    "calculator": [
        {
            "name": "index.html",
            "file_type": "html",
            "content": """<!DOCTYPE html>
<html>
<head>
  <title>Calculator</title>
  <link rel="stylesheet" href="style.css">
</head>
<body>
  <div class="calculator"></div>
  <script src="script.js"></script>
</body>
</html>"""
        },
        {
            "name": "style.css",
            "file_type": "css",
            "content": ".calculator {\n  /* Your calculator styles */\n}"
        },
        {
            "name": "script.js",
            "file_type": "js",
            "content": "// Calculator logic\n"
        }
    ]
}

async def create_initial_files(
    db: AsyncSession,
    project_id: UUID,
    template_type: str
):
    """Create initial files for a project based on template type"""
    if template_type not in TEMPLATE_FILES:
        raise ValueError(f"Unknown template type: {template_type}")
    
    files_data = TEMPLATE_FILES[template_type]
    
    for file_data in files_data:
        file = File(
            project_id=project_id,
            name=file_data["name"],
            file_type=file_data["file_type"],
            content=file_data["content"]
        )
        db.add(file)
    
    await db.commit()

async def check_max_projects(
    db: AsyncSession,
    user_id: UUID,
    max_projects: int = 10
) -> bool:
    """Check if user has reached max projects limit"""
    query = select(func.count(Project.id)).where(Project.user_id == user_id)
    result = await db.execute(query)
    count = result.scalar_one()
    
    return count < max_projects