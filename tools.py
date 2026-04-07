import os
from pydantic import BaseModel, Field
from crewai.tools import BaseTool


class FileWriteInput(BaseModel):
    filepath: str = Field(description="Path to write the file to")
    content: str = Field(description="Content to write to the file")


class FileWriterTool(BaseTool):
    name: str = "write_file"
    description: str = "Write content to a file on disk. Creates parent directories as needed."
    args_schema: type[BaseModel] = FileWriteInput

    def _run(self, filepath: str, content: str) -> str:
        os.makedirs(os.path.dirname(os.path.abspath(filepath)), exist_ok=True)
        with open(filepath, "w") as f:
            f.write(content)
        return f"Successfully written to {filepath}"
