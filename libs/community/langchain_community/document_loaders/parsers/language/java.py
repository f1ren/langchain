from typing import List

import javalang
from javalang.parser import JavaSyntaxError
from javalang.tokenizer import Position

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
        braces_counter = 1
        for i, c in enumerate(code_tail[block_start:]):
            if c == '{':
                braces_counter += 1
            elif c == '}':
                braces_counter -= 1
            if braces_counter == 0:
                break
        return code_tail[:block_start + i + 1]

    def extract_functions_classes(self) -> List[str]:
        tree = javalang.parse.parse(self.code)
        segments = []
        for child_list in tree.children:
            if child_list is None:
                continue
            for child in child_list:
                segments.append(self._extract_segment_by_braces(child.position))

        return segments

    def simplify_code(self) -> str:
        simplified_lines: List[str] = []
        inside_relevant_section = False
        omitted_code_added = (
            False  # To track if "* OMITTED CODE *" has been added after the last header
        )

        for line in self.source_lines:
            is_header = (
                "PROCEDURE DIVISION" in line
                or "DATA DIVISION" in line
                or "IDENTIFICATION DIVISION" in line
                or self.PARAGRAPH_PATTERN.match(line.strip().split(" ")[0])
                or self.SECTION_PATTERN.match(line.strip())
            )

            if is_header:
                inside_relevant_section = True
                # Reset the flag since we're entering a new section/division or
                # paragraph
                omitted_code_added = False

            if inside_relevant_section:
                if is_header:
                    # Add header and reset the omitted code added flag
                    simplified_lines.append(line)
                elif not omitted_code_added:
                    # Add omitted code comment only if it hasn't been added directly
                    # after the last header
                    simplified_lines.append("* OMITTED CODE *")
                    omitted_code_added = True

        return "\n".join(simplified_lines)
