"""gr.FileExplorer() component"""

from __future__ import annotations

import itertools
import os
import re
from glob import glob as glob_func
from pathlib import Path
from typing import Callable, Literal

from gradio_client.documentation import document, set_documentation_group
from gradio_client.serializing import JSONSerializable

from gradio.components.base import IOComponent, server
from gradio.events import (
    Changeable,
    EventListenerMethod,
)

set_documentation_group("component")


@document()
class FileExplorer(Changeable, IOComponent, JSONSerializable):
    """
    Creates a file component that allows uploading generic file (when used as an input) and or displaying generic files (output).
    Preprocessing: passes the selected file or directory as a {str} path (relative to root) or {list[str}} depending on `file_count`
    Postprocessing: expects function to return a {str} path to a file, or {List[str]} consisting of paths to files.
    Examples-format: a {str} path to a local file that populates the component.
    Demos: zip_to_json, zip_files
    """

    def __init__(
        self,
        glob: str = "**/*.*",
        *,
        value: str | list[str] | Callable | None = None,
        file_count: Literal["single", "multiple"] = "multiple",
        root: str | Path = ".",
        ignore_glob: str | None = None,
        label: str | None = None,
        every: float | None = None,
        show_label: bool | None = None,
        container: bool = True,
        scale: int | None = None,
        min_width: int = 160,
        height: int | float | None = None,
        interactive: bool | None = None,
        visible: bool = True,
        elem_id: str | None = None,
        elem_classes: list[str] | str | None = None,
        **kwargs,
    ):
        """
        Parameters:
            glob: The glob-style pattern used to select which files to display, e.g. "*" to match all files, "*.png" to match all .png files, "**/*.txt" to match any .txt file in any subdirectory, etc. The default value matches all files and folders recursively. See the Python glob documentation at https://docs.python.org/3/library/glob.html for more information.
            value: The file (or list of files, depending on the `file_count` parameter) to show as "selected" when the component is first loaded. If a callable is provided, it will be called when the app loads to set the initial value of the component. If not provided, no files are shown as selected.
            file_count: Whether to allow single or multiple files to be selected. If "single", the component will return a single absolute file path as a string. If "multiple", the component will return a list of absolute file paths as a list of strings.
            root: Path to root directory to select files from. If not provided, defaults to current working directory.
            ignore_glob: The glob-tyle pattern that will be used to exclude files from the list. For example, "*.py" will exclude all .py files from the list. See the Python glob documentation at https://docs.python.org/3/library/glob.html for more information.
            label: Component name in interface.
            every: If `value` is a callable, run the function 'every' number of seconds while the client connection is open. Has no effect otherwise. Queue must be enabled. The event can be accessed (e.g. to cancel it) via this component's .load_event attribute.
            show_label: if True, will display label.
            container: If True, will place the component in a container - providing some extra padding around the border.
            scale: relative width compared to adjacent Components in a Row. For example, if Component A has scale=2, and Component B has scale=1, A will be twice as wide as B. Should be an integer.
            min_width: minimum pixel width, will wrap if not sufficient screen space to satisfy this value. If a certain scale value results in this Component being narrower than min_width, the min_width parameter will be respected first.
            height: The maximum height of the file component, in pixels. If more files are uploaded than can fit in the height, a scrollbar will appear.
            interactive: if True, will allow users to upload a file; if False, can only be used to display files. If not provided, this is inferred based on whether the component is used as an input or output.
            visible: If False, component will be hidden.
            elem_id: An optional string that is assigned as the id of this component in the HTML DOM. Can be used for targeting CSS styles.
            elem_classes: An optional list of strings that are assigned as the classes of this component in the HTML DOM. Can be used for targeting CSS styles.
        """
        self.root = os.path.abspath(root)
        self.glob = glob
        self.ignore_glob = ignore_glob
        valid_file_count = ["single", "multiple", "directory"]
        if file_count not in valid_file_count:
            raise ValueError(
                f"Invalid value for parameter `type`: {type}. Please choose from one of: {valid_file_count}"
            )
        self.file_count = file_count
        self.height = height
        self.select: EventListenerMethod
        """
        Event listener for when the user selects file from list.
        Uses event data gradio.SelectData to carry `value` referring to name of selected file, and `index` to refer to index.
        See EventData documentation on how to use this event data.
        """
        IOComponent.__init__(
            self,
            label=label,
            every=every,
            show_label=show_label,
            container=container,
            scale=scale,
            min_width=min_width,
            interactive=interactive,
            visible=visible,
            elem_id=elem_id,
            elem_classes=elem_classes,
            value=value,
            **kwargs,
        )

    def preprocess(self, x: list[list[str]] | None) -> list[str] | str | None:
        """
        Parameters:
            x: File path segments as a list of list of strings for each file relative to the root.
        Returns:
            File path selected, as an absolute path.
        """
        if x is None:
            return None

        if self.file_count == "single":
            if len(x) > 1:
                raise ValueError(f"Expected only one file, but {len(x)} were selected.")
            return self._safe_join(x[0])

        return [self._safe_join(file) for file in (x)]

    def _strip_root(self, path):
        if path.startswith(self.root):
            return path[len(self.root) + 1 :]
        return path

    def postprocess(self, y: str | list[str] | None) -> list[list[str]] | None:
        """
        Parameters:
            y: file path
        Returns:
            list representing filepath, where each string is a directory level relative to the root.
        """
        if y is None:
            return None

        files = [y] if isinstance(y, str) else y

        return [self._strip_root(file).split(os.path.sep) for file in (files)]

    @server
    def ls(self, y=None) -> list[dict[str, str]] | None:
        """
        Parameters:
            y: file path as a list of strings for each directory level relative to the root.
        Returns:
            tuple of list of files in directory, then list of folders in directory
        """

        def expand_braces(text, seen=None):
            if seen is None:
                seen = set()

            spans = [m.span() for m in re.finditer("{[^{}]*}", text)][::-1]
            alts = [text[start + 1 : stop - 1].split(",") for start, stop in spans]

            if len(spans) == 0:
                if text not in seen:
                    yield text
                seen.add(text)

            else:
                for combo in itertools.product(*alts):
                    replaced = list(text)
                    for (start, stop), replacement in zip(spans, combo):
                        replaced[start:stop] = replacement

                    yield from expand_braces("".join(replaced), seen)

        def make_tree(files):
            tree = []
            for file in files:
                parts = file.split("/")
                make_node(parts, tree)
            return tree

        def make_node(parts, tree):
            _tree = tree
            for i in range(len(parts)):
                if _tree is None:
                    continue
                if i == len(parts) - 1:
                    type = "file"
                    _tree.append({"path": parts[i], "type": type, "children": None})
                    continue
                type = "folder"
                j = next(
                    (index for (index, v) in enumerate(_tree) if v["path"] == parts[i]),
                    None,
                )
                if j is not None:
                    _tree = _tree[j]["children"]
                else:
                    _tree.append({"path": parts[i], "type": type, "children": []})
                    _tree = _tree[-1]["children"]

        files = []
        for result in expand_braces(self.glob):
            files += glob_func(result, recursive=True, root_dir=self.root)  # type: ignore

        ignore_files = []
        if self.ignore_glob:
            for result in expand_braces(self.ignore_glob):
                ignore_files += glob_func(result, recursive=True, root_dir=self.root)  # type: ignore
            files = list(set(files) - set(ignore_files))

        tree = make_tree(files)

        return tree

    def _safe_join(self, folders):
        combined_path = os.path.join(self.root, *folders)
        absolute_path = os.path.abspath(combined_path)
        if os.path.commonprefix([self.root, absolute_path]) != os.path.abspath(
            self.root
        ):
            raise ValueError("Attempted to navigate outside of root directory")
        return absolute_path
