from typing import List

import javalang
from javalang.parser import JavaSyntaxError
from javalang.tokenizer import Position
from javalang.tree import Import

from langchain_community.document_loaders.parsers.language.code_segmenter import (
    CodeSegmenter,
)


class JavaSegmenter(CodeSegmenter):
    """Code segmenter for `JAVA`."""

    def is_valid(self) -> bool:
        try:
            javalang.parse.parse(self.code)
        except JavaSyntaxError:
            return False

        return True

    def _find_location(self, line, column):
        lines = self.code.split('\n')
        location = 0
        for i in range(line - 1):
            location += len(lines[i]) + 1
        location += column - 1
        return location

    def _extract_segment_by_braces(self, position: Position) -> str:
        location = self._find_location(position.line, position.column)
        code_tail = self.code[location:]
        block_start = code_tail.find('{') + 1

        semicolon = code_tail.find(';')
        if 0 <= semicolon < block_start - 1:
            return code_tail[:semicolon + 1]

        braces_counter = 1
        for i, c in enumerate(code_tail[block_start:]):
            if c == '{':
                braces_counter += 1
            elif c == '}':
                braces_counter -= 1
            if braces_counter == 0:
                break

        return code_tail[:block_start + i + 1]

    def _list_children(self):
        children = []
        tree = javalang.parse.parse(self.code)
        for child_list in tree.children:
            if child_list is None:
                continue
            for child in child_list:
                if isinstance(child, Import):
                    continue
                children.append(child)

        return children

    def extract_functions_classes(self) -> List[str]:
        return [self._extract_segment_by_braces(child.position) for child in self._list_children()]

    def simplify_code(self) -> str:
        simplified_lines = self.code.splitlines()[:]

        for child in self._list_children():
            # TODO
            pass
            # simplified_lines[start] = f"// Code for: {simplified_lines[start]}"
            #
            # for line_num in range(start + 1, node.loc.end.line):
            #     simplified_lines[line_num] = None  # type: ignore

        return "\n".join(line for line in simplified_lines if line is not None)
