from typing import Literal

import ell
from jinja2 import Template
from PIL import Image
from pydantic import BaseModel, Field

LLM_JUDGE_SYSTEM_PROMPT = """You will evaluate whether a web assistant was able to successfully complete a given web task. As an evaluator, you will be presented with three primary components to assist you in your role:

1. Web Task Instruction: This is a clear and specific directive provided in natural language, detailing the online activity to be carried out. These requirements may include conducting searches, verifying information, comparing prices, checking availability, or any other action relevant to the specified web service (such as Amazon, Apple, ArXiv, BBC News, Booking etc).

2. Result Screenshots: This is a visual representation of the screen showing the result or intermediate state of performing a web task. It serves as visual proof of the actions taken in response to the instruction.

3. Result Response: This is a textual response obtained after the execution of the web task. It serves as textual result in response to the instruction.

-- You DO NOT NEED to interact with web pages or perform actions such as booking flights or conducting searches on websites.
-- You SHOULD NOT make assumptions based on information not presented in the screenshot when comparing it to the instructions.
-- Your primary responsibility is to conduct a thorough assessment of the web task instruction against the outcome depicted in the screenshot and in the response, evaluating whether the actions taken align with the given instructions.
-- NOTE that the instruction may involve more than one task, for example, locating the garage and summarizing the review. Failing to complete either task, such as not providing a summary, should be considered unsuccessful.
-- NOTE that the screenshot is authentic, but the response provided by LLM is generated at the end of web browsing, and there may be discrepancies between the text and the screenshots.
-- Note the difference: 1) Result response may contradict the screenshot, then the content of the screenshot prevails, 2) The content in the Result response is not mentioned on the screenshot, choose to believe the content.

You should elaborate on how you arrived at your final evaluation and then provide a definitive verdict on whether the task has been successfully accomplished, either as 'SUCCESS' or 'FAILURE'."""


LLM_JUDGE_USER_PROMPT = Template(
    """Task: {{ task }}

Result Response: {{ answer }}

{num_screenshot} screenshots recorded during the task:
"""
)


class LLMVerdict(BaseModel):
    thought: str = Field(description="Reasoning behind the verdict")
    verdict: Literal["SUCCESS", "FAILURE"] = Field(
        description="Final verdict for whether the web assistant completed the task or not."
    )


@ell.complex(model="gpt-4o", response_format=LLMVerdict)
def llm_verdict_lmp(task: str, answer: str, screenshots: list[Image.Image]):
    user_message = [
        LLM_JUDGE_USER_PROMPT.render(
            task=task, answer=answer, num_screenshots=len(screenshots)
        )
    ]
    for i, screenshot in enumerate(screenshots):
        user_message.extend([f"Step {i+1}", screenshot])
    return [
        ell.system(LLM_JUDGE_SYSTEM_PROMPT),
        ell.user(user_message),
    ]


def get_verdict(
    task: str, answer: str, screenshots: list[Image.Image]
) -> LLMVerdict:
    return llm_verdict_lmp(task=task, answer=answer, screenshots=screenshots).parsed  # type: ignore
