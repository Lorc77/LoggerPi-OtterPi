from queue import BatchQueue

from atmoweb import AtmoWebReader
from batch_factory import SequenceStore
from composer import compose_batch
from delivery import BatchDelivery


class LoggerRuntime:
    """Orchestrates one LoggerPi collection and delivery cycle."""

    def __init__(
        self,
        *,
        logger_id: str,
        readers: dict[str, AtmoWebReader],
        sequence_store: SequenceStore,
        delivery: BatchDelivery,
        queue: BatchQueue,
    ) -> None:
        self.logger_id = logger_id
        self.readers = readers
        self.sequence_store = sequence_store
        self.delivery = delivery
        self.queue = queue

    def run_once(self):
        for queued_batch in self.queue.pending():
            if self.delivery.send(queued_batch):
                self.queue.remove(queued_batch)
            else:
                break

        measurements = {}

        for source, reader in self.readers.items():
            for name, measurement in reader.read_measurements().items():
                measurements[f"{source}.{name}"] = measurement

        batch = compose_batch(
            logger_id=self.logger_id,
            sequence_store=self.sequence_store,
            measurements=measurements,
        )

        if not self.delivery.send(batch):
            self.queue.enqueue(batch)

        return batch
