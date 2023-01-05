import os.path
from dataclasses import dataclass, asdict
from enum import Enum
from pathlib import Path
from typing import Optional, List

from flask import current_app
from flask_restx import Namespace, Resource

api = Namespace('Contents', description='Local path file contents')


class ContentType(Enum):
    directory = 'directory'
    file = 'file'


contents_parser = api.parser()
contents_parser.add_argument('type', type=ContentType, required=True, location='args')
contents_parser.add_argument('show_hidden', type=bool, default=False, location='args')
contents_parser.add_argument('root', type=str, default=None, location='args')


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


def get_content_info(root_path: str, content_path: str, content_type: ContentType,
                     depth: int = 1, show_hidden: bool = False) -> ContentInfo:
    full_path = os.path.join(root_path, content_path)
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
        contents = [get_content_info(root_path, os.path.join(content_path, _path).replace("\\", "/"), _type,
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


@api.route('/', defaults={'content_path': ''})
@api.route('/<path:content_path>')
@api.expect(contents_parser)
class Contents(Resource):
    def get(self, content_path: str):
        """
        Get information of the content path provided
        """
        args = contents_parser.parse_args()
        content_type: ContentType = args["type"]
        show_hidden: bool = args["show_hidden"]
        root: Path = args["root"]

        if root is None:
            config = current_app.cea_config
            root_path = config.server.project_root
        else:
            root_path = root

        try:
            content_info = get_content_info(root_path, content_path, content_type, show_hidden=show_hidden)
            return content_info.as_dict()
        except ContentPathNotFound:
            return {"message": f"Path `{content_path}` does not exist"}, 404
        except ContentTypeInvalid:
            return {"message": f"Path `{content_path}` is not of type `{content_type.value}`"}, 400
