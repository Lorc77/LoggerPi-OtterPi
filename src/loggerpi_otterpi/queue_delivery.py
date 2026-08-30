from .delivery import BatchDelivery
from .queue import BatchQueue


def deliver_pending(queue: BatchQueue, delivery: BatchDelivery) -> int:
    delivered = 0

    for batch in queue.pending():
        if not delivery.send(batch):
            continue

        queue.remove(batch)
        delivered += 1

    return delivered
