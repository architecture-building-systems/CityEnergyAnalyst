import aiofiles
import os.path
import shutil
import tempfile
import zipfile
from dataclasses import dataclass, asdict
from enum import Enum
from io import BytesIO
from pathlib import Path
from typing import Optional, List

from fastapi import APIRouter, HTTPException, status, Form, UploadFile
from pydantic import BaseModel
from starlette.responses import StreamingResponse
from typing_extensions import Annotated, Literal

from cea.interfaces.dashboard.api.project import get_project_choices
from cea.interfaces.dashboard.dependencies import CEAProjectRoot
from cea.interfaces.dashboard.lib.logs import getCEAServerLogger
from cea.interfaces.dashboard.utils import secure_path, OutsideProjectRootError

logger = getCEAServerLogger("cea-server-contents")

router = APIRouter()


class ContentType(Enum):
    directory = 'directory'
    file = 'file'


class ContentPathNotFound(Exception):
    pass


class ContentTypeInvalid(Exception):
    pass


@dataclass
class ContentInfo:
    name: str
    path: str
    last_modified: float
    contents: Optional[List["ContentInfo"]]
    size: Optional[int]
    type: ContentType

    @staticmethod
    def _dict_factory(data):
        return {
            field: value.value if isinstance(value, Enum) else value
            for field, value in data
        }

    def as_dict(self):
        return asdict(self, dict_factory=self._dict_factory)


def get_content_info(content_path: str, content_type: ContentType,
                     depth: int = 1, show_hidden: bool = False) -> ContentInfo:
    full_path = os.path.realpath(content_path)
    if not os.path.exists(full_path):
        raise ContentPathNotFound

    if not ((content_type == ContentType.file and os.path.isfile(full_path))
            or (content_type == ContentType.directory and os.path.isdir(full_path))):
        raise ContentTypeInvalid

    contents = None
    # continue recursively up to depth
    if depth > 0 and content_type == ContentType.directory:
        _contents = [
            (item, ContentType.file if os.path.isfile(os.path.join(full_path, item)) else ContentType.directory)
            # ignore "hidden" items that start with "."
            for item in os.listdir(full_path) if not item.startswith(".") or show_hidden
        ]
        contents = [get_content_info(os.path.join(content_path, _path).replace("\\", "/"), _type,
                                     depth - 1, show_hidden)
                    for _path, _type in _contents]

    size = None
    if content_type == ContentType.file:
        size = os.path.getsize(full_path)

    return ContentInfo(
        name=os.path.basename(content_path),
        path=content_path,
        last_modified=os.path.getmtime(full_path),
        contents=contents,
        size=size,
        type=content_type
    )

@router.get('/')
@router.get("")
async def get_contents(project_root: CEAProjectRoot, content_type: ContentType,
                       content_path: str = "", show_hidden: bool = False):
    """
    Get information of the content path provided
    """
    try:
        _content_path = content_path
        if project_root is not None:
            _content_path = os.path.join(project_root, content_path)
        
        full_path = secure_path(_content_path)
        content_info = get_content_info(full_path, content_type, show_hidden=show_hidden)
        return content_info.as_dict()
    except ContentPathNotFound:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Path `{content_path}` does not exist",
        )
    except ContentTypeInvalid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Path `{content_path}` is not of type `{content_type.value}`",
        )
    except OutsideProjectRootError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


class UploadScenario(BaseModel):
    file: UploadFile
    type: Literal["current", "existing", "new"]
    project: str


VALID_EXTENSIONS = {".shp", ".dbf", ".prj", ".cpg", ".shx",
                    ".csv", ".xls", ".xlsx",
                    ".epw", ".tiff", ".tif", ".txt",
                    ".feather"}

def filter_valid_files(file_list: List[str]) -> List[str]:
    return list(filter(lambda f: Path(f).suffix in VALID_EXTENSIONS, file_list))

@router.post("/scenario/upload")
async def upload_scenario(form: Annotated[UploadScenario, Form()], project_root: CEAProjectRoot):
    # Validate file is a zip
    if not form.file.filename.endswith('.zip'):
        raise HTTPException(status_code=400, detail="File must be a ZIP archive")

    # TODO: Catch HTTPException(s) at app level to logger errors
    # Ensure project root
    if project_root is None or project_root == "":
        logger.error("Unable to determine project path")
        raise HTTPException(
            status_code=400,
            detail="Project root not defined",
        )

    project_name = form.project
    project_path = Path(project_root, project_name)

    # Check for existing projects
    if form.type == "current" or form.type == "existing":
        project_choices = await get_project_choices(project_root)
        if project_name not in project_choices:
            logger.error("Project not found")
            raise HTTPException(status_code=400, detail="Project not found")

    # Create new project
    elif form.type == "new":
        if project_path.exists():
            logger.error("Project already exists")
            raise HTTPException(status_code=400, detail="Project already exists")
        os.makedirs(project_path, exist_ok=True)
    else:
        logger.error("Unable to determine operation")
        raise HTTPException(status_code=400, detail="Unknown operation type")

    try:
        with zipfile.ZipFile(BytesIO(await form.file.read())) as zf:
            paths = zf.namelist()

            def is_zone_path(path: str):
                return path.endswith("inputs/building-geometry/zone.shp")

            # TODO: Improve valid scenario detection
            # Determine valid scenarios using zone files
            zone_files = list(filter(is_zone_path, paths))
            if len(zone_files) == 0:
                raise ValueError("No valid scenarios found")

            # Case 1: Scenario in root and name is zip name e.g. inputs/
            if len(zone_files) == 1 and zone_files[0].startswith("inputs"):
                scenario_name = form.file.filename[:-4]
                logger.info(f"Scenario found as root, using name `{scenario_name}`")
                # Check if scenario names already exist and rename
                if os.path.exists(os.path.join(project_path, scenario_name)):
                    # TODO: Find way to rename new scenario and extract
                    raise HTTPException(status_code=400, detail=f"Scenario `{scenario_name}` already exists in project")
                # Create scenario directory
                new_scenario_path = os.path.join(project_path, scenario_name)
                os.makedirs(new_scenario_path, exist_ok=True)

                logger.info(f"Extracting to {new_scenario_path}")
                # Extract only valid files with extensions
                for path in filter_valid_files(paths):
                    zf.extract(path, new_scenario_path)

            # Case 2: More than 1 scenario in zip
            scenario_names = []
            existing_scenario_names = []
            # Check for existing scenario names
            for zone_file in zone_files:
                parts = zone_file.split("/")

                # Case 2a: Scenario names are the first level folder names e.g. scenario/inputs/..
                if parts[1] == "inputs":
                    scenario_name = parts[0]
                # Case 2b: Project name is the first level folder name e.g. project/scenario/inputs/..
                elif parts[2] == "inputs":
                    scenario_name = parts[1]
                else:
                    continue

                scenario_names.append(scenario_name)
                if os.path.exists(os.path.join(project_path, scenario_name)):
                    existing_scenario_names.append(scenario_name)

            logger.info(f"Scenario found: {scenario_names}")
            if len(existing_scenario_names):
                # TODO: Find way to rename new scenario and extract
                raise HTTPException(status_code=400,
                                    detail=f"Scenarios {existing_scenario_names} already exists in project")


            for zone_file in zone_files:
                parts = zone_file.split("/")

                # Case 2: Scenario names are the first level folder names e.g. scenario/inputs/..
                if parts[1] == "inputs":
                    scenario_name = parts[0]
                    logger.info(f"Scenario found in root, using name `{scenario_name}`")
                    scenario_files = list(filter(lambda x: x.startswith(f"{scenario_name}/"), paths))

                    logger.info(f"Extracting to {project_path}")
                    for path in filter_valid_files(scenario_files):
                        zf.extract(path, project_path)

                # Case 3: Project name is the first level folder name e.g. project/scenario/inputs/..
                if parts[2] == "inputs":
                    project_name = parts[0]
                    scenario_name = parts[1]
                    logger.info(f"Scenario found in a project folder, using name `{scenario_name}`")
                    scenario_files = list(filter(lambda x: x.startswith("/".join(parts[:1])), paths))

                    # Extract to temp first
                    with tempfile.TemporaryDirectory() as tmpdir:
                        logger.info(f"Extracting to {tmpdir}")
                        for path in filter_valid_files(scenario_files):
                            zf.extract(path, tmpdir)
                        # Move scenario from temp to project
                        temp_scenario_path = os.path.join(tmpdir, project_name, scenario_name)
                        logger.info(f"Moving {temp_scenario_path} to {project_path}")
                        shutil.move(temp_scenario_path, project_path)

    except Exception as e:
        logger.error(e)
        raise HTTPException(status_code=500, detail=str(e))

    # Return success response
    return {
        "status": "success",
        "message": "File uploaded and processed successfully",
        "project": project_name
    }


class DownloadScenario(BaseModel):
    project: str
    scenarios: List[str]
    input_files: bool


@router.post("/scenario/download")
async def download_scenario(form: DownloadScenario, project_root: CEAProjectRoot):
    if not form.project or not form.scenarios:
        raise HTTPException(status_code=400, detail="Missing project or scenarios")

    # Ensure project root
    if project_root is None or project_root == "":
        logger.error("Unable to determine project path")
        raise HTTPException(
            status_code=400,
            detail="Project root not defined",
        )

    project = form.project.strip()
    scenarios = form.scenarios
    input_files_only = form.input_files

    filename = f"{project}_scenarios.zip" if len(scenarios) > 1 else f"{project}_{scenarios[0]}.zip"

    temp_file_path = None
    try:
        with tempfile.NamedTemporaryFile(delete=False) as temp_file:
            temp_file_path = temp_file.name
            with zipfile.ZipFile(temp_file, 'w', zipfile.ZIP_DEFLATED) as zip_file:
                base_path = Path(project_root) / project
                
                for scenario in scenarios:
                    scenario_path = base_path / scenario
                    if not scenario_path.exists():
                        continue
                        
                    target_path = (scenario_path / "inputs") if input_files_only else scenario_path
                    prefix = f"{scenario}/inputs" if input_files_only else scenario
                    
                    for item_path in target_path.rglob('*'):
                        if item_path.is_file() and item_path.suffix in VALID_EXTENSIONS:
                            relative_path = str(Path(prefix) / item_path.relative_to(target_path))
                            zip_file.write(item_path, arcname=relative_path)
        
        # Get the file size for Content-Length header
        file_size = os.path.getsize(temp_file_path)
        
        # Define the streaming function
        async def file_streamer():
            try:
                async with aiofiles.open(temp_file_path, 'rb') as f:
                    while True:
                        chunk = await f.read(1024 * 1024)  # 1MB chunks
                        if not chunk:
                            break
                        yield chunk
            finally:
                # Clean up the temporary file
                if os.path.exists(temp_file_path):
                    os.unlink(temp_file_path)
        
        return StreamingResponse(
            file_streamer(),
            media_type="application/zip",
            headers={
                "Content-Disposition": f'attachment; filename="{filename}"',
                "Content-Length": str(file_size),  # Add Content-Length header
                "Access-Control-Expose-Headers": "Content-Disposition, Content-Length"
            }
        )
    
    except Exception as e:
        # Clean up the temporary file if there was an error
        if temp_file_path and os.path.exists(temp_file_path):
            os.unlink(temp_file_path)
        logger.error(f"Error creating zip: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))