from fastapi import APIRouter

import cea.interfaces.dashboard.api.inputs as inputs
import cea.interfaces.dashboard.api.contents as contents
import cea.interfaces.dashboard.api.dashboards as dashboards
import cea.interfaces.dashboard.api.databases as databases
import cea.interfaces.dashboard.api.downloads as downloads
import cea.interfaces.dashboard.api.glossary as glossary
import cea.interfaces.dashboard.api.project as project
import cea.interfaces.dashboard.api.tools as tools
import cea.interfaces.dashboard.api.weather as weather
import cea.interfaces.dashboard.api.geometry as geometry
import cea.interfaces.dashboard.api.map_layers as map_layers
import cea.interfaces.dashboard.api.user as user

router = APIRouter()

router.include_router(inputs.router, prefix="/inputs")
router.include_router(contents.router, prefix="/contents")
router.include_router(dashboards.router, prefix="/dashboards")
router.include_router(databases.router, prefix="/databases")
router.include_router(downloads.router, prefix="/downloads")
router.include_router(glossary.router, prefix="/glossary")
router.include_router(project.router, prefix="/project")
router.include_router(tools.router, prefix="/tools")
router.include_router(weather.router, prefix="/weather")
router.include_router(geometry.router, prefix="/geometry")
router.include_router(map_layers.router, prefix="/map_layers")
router.include_router(user.router, prefix="/user")
