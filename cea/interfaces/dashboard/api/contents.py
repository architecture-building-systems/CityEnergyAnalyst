import os.path
import tempfile
import zipfile
from dataclasses import dataclass, asdict
from enum import Enum
from io import BytesIO
from pathlib import Path
from typing import Optional, List

from fastapi import APIRouter, HTTPException, status, Form, UploadFile
from pydantic import BaseModel
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
        with tempfile.TemporaryDirectory() as tmpdir:
            with zipfile.ZipFile(BytesIO(await form.file.read())) as zf:
                paths = zf.namelist()

                def is_zone_path(path: str):
                    return path.endswith("/zone.shp")

                # TODO: Improve valid scenario detection
                # Determine valid scenarios using zone files
                zone_files = list(filter(is_zone_path, paths))
                if len(zone_files) == 0:
                    raise ValueError("No valid scenarios found")

                # Case 1: Scenario in root and name is zip name e.g. inputs/
                if len(zone_files) == 1 and zone_files[0].startswith("inputs"):
                    scenario_name = form.file.filename[:-4]
                    logger.info(f"One scenario found in root, using name {scenario_name}")
                    # Check if scenario names already exist and rename
                    if os.path.exists(scenario_name):
                        scenario_name = f"{scenario_name} copy"

                    new_scenario_path = os.path.join(project_path, scenario_name)
                    os.makedirs(new_scenario_path, exist_ok=True)
                    logger.info(f"Extracting to {new_scenario_path}")
                    for path in filter_valid_files(paths):
                        zf.extract(path, new_scenario_path)

                # Case 2: Scenario names are the first level folder names e.g. scenario/inputs/..
                # Case 3: Project name is the first level folder name e.g. project/scenario/inputs/..
                def get_zone_paths(path: str):
                    parts = path.split("/")
                    return parts[1] == "inputs" or parts[2] == "inputs"

                scenarios = list(filter(get_zone_paths, zone_files))

                print(scenarios)
                zf.extractall(tmpdir)

    except Exception as e:
        logger.error(e)
        raise HTTPException(status_code=500, detail=str(e))

    # Return success response
    return {
        "status": "success",
        "message": "File uploaded and processed successfully",
        "project": project_name
    }
