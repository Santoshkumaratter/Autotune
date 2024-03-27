
from transformers import TrainerCallback

from api.utilies.tasks import *


class CeleryProgressCallback(TrainerCallback):
    def __init__(self, task):
        self.task = task

    def on_log(self, args, state, control, logs, **kwargs):
        self.task.update_state(state="TRAINING", meta=state.log_history)

def get_task_class(task):
    tasks = {"text_classification": TextClassification, "seq2seq": Seq2Seq}
    return tasks.get(task)
