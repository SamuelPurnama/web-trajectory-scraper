import asyncio
import datetime
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

from annotated_types import Interval
from gymnasium import Env

from agent.actions import SendMsgToUser
from agent.utils import AgentBase


@dataclass
class Interaction:
    state: dict[str, Any]
    action: dict[str, Any] | None = None
    next_state: dict[str, Any] | None = None
    error: dict[str, str] | None = None
    action_timestamp: float | None = None


class Episode:
    def __init__(
        self, env: Env, agent: AgentBase, eps_name: str, goal: str | None = None
    ):
        self.env = env
        self.agent = agent
        self.eps_name = eps_name
        self.goal = goal
        self.interactions: list[Interaction] = []

    def run_episode(self, max_steps=30):
        obs, info = self.env.reset()

        self.agent.reset()
        if self.goal is None:
            self.goal = obs["goal"]

        state = {
            "obs": obs,
            "reward": 0,
            "terminated": False,
            "truncated": False,
            "info": info,
        }

        metadata = {"goal": self.goal, "eps_name": self.eps_name}
        for i in range(max_steps):
            print(f"eps_name: {self.eps_name} | step: {i+1}")

            action_timestamp = datetime.now(timezone.utc).timestamp()

            # predict action for the current observation using agent
            try:
                action: dict[str, Any] = self.agent.predict_action(state["obs"])
                state["agent_inputs"] = self.agent.get_last_model_inputs()
            except Exception as e:
                error = {"ACTION_PREDICTION_ERROR": str(e)}
                self.interactions.append(Interaction(state=state, error=error))
                print(f"Ending episode {self.eps_name} due to error:\n{error}")
                return self.interactions, metadata

            print(action)

            # basic validation of predicted action
            if not isinstance(action, dict) or "action_str" not in action:
                error = {
                    "ACTION_FORMAT_ERROR": f"action_str not found in predicted action: {action}"
                }
                self.interactions.append(
                    Interaction(
                        state=state,
                        action=action,
                        error=error,
                        action_timestamp=action_timestamp,
                    )
                )
                print(f"Ending episode {self.eps_name} due to error:\n{error}")
                return self.interactions, metadata

            # take step in the environment using the predicted action
            try:
                obs, reward, terminated, truncated, info = self.env.step(
                    action["action_str"]
                )
                next_state = {
                    "obs": obs,
                    "reward": reward,
                    "terminated": terminated,
                    "truncated": truncated,
                    "info": info,
                }

            except Exception as e:
                error = {"ENV_STEP_ERROR": str(e)}
                self.interactions.append(
                    Interaction(
                        state=state,
                        action=action,
                        error=error,
                        action_timestamp=action_timestamp,
                    )
                )
                print(f"Ending episode {self.eps_name} due to error:\n{error}")
                return self.interactions, metadata

            after_step_timestamp = datetime.now(timezone.utc).timestamp()
            self.interactions.append(
                Interaction(
                    state=state,
                    action=action,
                    next_state=next_state,
                    action_timestamp=action_timestamp,
                )
            )

            state = next_state
            action_params = action["action_output"].action
            if terminated or (
                isinstance(action_params, SendMsgToUser)
                and action_params.msg == "[EXIT]"
            ):
                break

        return self.interactions, metadata
