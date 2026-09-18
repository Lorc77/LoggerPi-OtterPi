from typing import Optional

from batch_factory import SequenceStore, create_batch
from model.batch import Batch
from model.measurement import Measurement
from system_info import get_system_info


def compose_batch(
    logger_id: str,
    sequence_store: SequenceStore,
    measurements: Optional[dict[str, Measurement]] = None,
) -> Batch:
    system_info = get_system_info()

    system = {
        "time": system_info["time"],
        "boot": system_info["boot"],
        "cpu": system_info["cpu"],
    }

    return create_batch(
        logger_id=logger_id,
        sequence_store=sequence_store,
        measurements=measurements,
        system=system,
        memory=system_info["memory"],
    )
