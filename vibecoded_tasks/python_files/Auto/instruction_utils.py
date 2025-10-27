import random
from typing import Literal, Optional

import ell
from pydantic import BaseModel, Field


class Instructions(BaseModel):
    high_level: str = Field(
        description="Instruction to a super smart web browsing assistant with minimal details"
    )
    mid_level: str = Field(
        description="Instruction to a slightly less smart web browsing assistant with a few details"
    )
    low_level: str = Field(
        description="Instruction to an average web browsing assistant with full details but avoiding itemized list of steps."
    )


def get_instruction(website: str, steps: list[str]) -> Instructions:
    @ell.complex(model="gpt-4.1", response_format=Instructions)
    def lmp(website: str, steps: list[str]):
        return f"Below are a detailed sequence of steps for accomplish a task on {website}. Phrase the task as an instruction to various intelligent assistants with varying levels of intelligence.\n\n# Task Steps\n\n{'\n'.join(steps)}"

    return lmp(website, steps).parsed  # type: ignore
