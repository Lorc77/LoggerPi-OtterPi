from typing import Optional

from atmoweb import AtmoWebReader
from batch_factory import SequenceStore
from batch_queue import BatchQueue
from composer import compose_batch
from delivery import BatchDelivery
from freezer import FreezerReader
from memmert import MemmertReader
from thingspeak_delivery import ThingSpeakDelivery
from weatherhub import WeatherHubReader
from weatherhub_gateway_listener import WeatherHubGatewayListener


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
        freezer_reader: Optional[FreezerReader] = None,
        memmert_readers: Optional[dict[str, MemmertReader]] = None,
        thingspeak_delivery: Optional[ThingSpeakDelivery] = None,
        weatherhub_listener: Optional[WeatherHubGatewayListener] = None,
        weatherhub_reader: Optional[WeatherHubReader] = None,
    ) -> None:
        self.logger_id = logger_id
        self.readers = readers
        self.sequence_store = sequence_store
        self.delivery = delivery
        self.queue = queue
        self.freezer_reader = freezer_reader
        self.memmert_readers = memmert_readers or {}
        self.thingspeak_delivery = thingspeak_delivery
        self.weatherhub_listener = weatherhub_listener
        self.weatherhub_reader = weatherhub_reader

        # Listener starten, wenn vorhanden
        if self.weatherhub_listener is not None:
            self.weatherhub_listener.start()

    def stop(self) -> None:
        """Stoppt den WeatherHub-Listener (sauberer Shutdown)."""
        if self.weatherhub_listener is not None:
            self.weatherhub_listener.stop()
            self.weatherhub_listener.join(timeout=5.0)

    def run_once(self):
        # 1. Queue-Replay
        for queued_batch in self.queue.pending():
            if self.delivery.send(queued_batch):
                self.queue.remove(queued_batch)
            else:
                break

        # 2. Measurements + States + Setpoints + Device-Info sammeln
        measurements = {}
        states = {}
        operation = {}
        setpoints = {}
        device = {}
        serial = None

        for source, reader in self.readers.items():
            for name, measurement in reader.read_measurements().items():
                measurements[f"{source}.{name}"] = measurement

            reader_states, reader_operation = reader.read_state()
            if reader_states:
                states[source] = reader_states
            if reader_operation:
                operation[source] = reader_operation

            reader_setpoints = reader.read_setpoints()
            if reader_setpoints:
                setpoints[source] = reader_setpoints

            reader_device = reader.read_device_info()
            if reader_device:
                device[source] = reader_device

        if self.freezer_reader is not None:
            measurements.update(self.freezer_reader.read_measurements())

            freezer_states, freezer_operation = self.freezer_reader.read_state()
            if freezer_states:
                states["freezer"] = freezer_states
            if freezer_operation:
                operation["freezer"] = freezer_operation

            serial = self.freezer_reader.serial

            freezer_device = self.freezer_reader.read_device_info()
            if freezer_device:
                device["freezer"] = freezer_device

        for source, reader in self.memmert_readers.items():
            for name, measurement in reader.read_measurements().items():
                measurements[f"{source}.{name}"] = measurement

            reader_states, reader_operation = reader.read_state()
            if reader_states:
                states[source] = reader_states
            if reader_operation:
                operation[source] = reader_operation

            reader_setpoints = reader.read_setpoints()
            if reader_setpoints:
                setpoints[source] = reader_setpoints

            reader_device = reader.read_device_info()
            if reader_device:
                device[source] = reader_device

        if self.weatherhub_reader is not None:
            measurements.update(self.weatherhub_reader.read_measurements())

            wh_states, wh_operation = self.weatherhub_reader.read_state()
            states.update(wh_states)
            if wh_operation:
                operation.update(wh_operation)

            wh_device = self.weatherhub_reader.read_device_info()
            device.update(wh_device)

        # 3. Batch erzeugen
        batch = compose_batch(
            logger_id=self.logger_id,
            sequence_store=self.sequence_store,
            measurements=measurements,
            states=states or None,
            operation=operation or None,
            serial=serial,
            setpoints=setpoints or None,
            device=device or None,
        )

        # 4. OtterPi-Delivery (oder Queue)
        if not self.delivery.send(batch):
            self.queue.enqueue(batch)

        # 5. ThingSpeak-Injektion (optional)
        if self.thingspeak_delivery is not None:
            self.thingspeak_delivery.send(batch)

        return batch
