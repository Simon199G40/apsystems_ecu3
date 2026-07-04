"""Sensor platform for APSystems ECU-3."""

from __future__ import annotations

from dataclasses import dataclass

from homeassistant.components.sensor import (
    DOMAIN as SENSOR_DOMAIN,
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    UnitOfElectricPotential,
    UnitOfFrequency,
    UnitOfPower,
    UnitOfTemperature,
)

from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import (
    CoordinatorEntity,
)

from .const import (
    CONF_CUSTOM_MODEL,
    CONF_INVERTER_MODEL,
    DATA_HOME,
    DATA_INVERTERS,
    DEFAULT_INVERTER_MODEL,
    DOMAIN,
    MANUFACTURER,
    MODEL,
)

from .coordinator import APSystemsECU3Coordinator


@dataclass(frozen=True, kw_only=True)
class ECU3SensorDescription(
    SensorEntityDescription,
):
    """ECU sensor description."""

    value_key: str


ECU_SENSORS = (
    ECU3SensorDescription(
        key="lifetime_generation",
        translation_key="lifetime_generation",
        value_key="lifetime_generation",
        native_unit_of_measurement="kWh",
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL_INCREASING,
    ),
    ECU3SensorDescription(
        key="today_generation",
        translation_key="today_generation",
        value_key="today_generation",
        native_unit_of_measurement="kWh",
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL,
    ),
    ECU3SensorDescription(
        key="system_power",
        translation_key="system_power",
        value_key="system_power",
        native_unit_of_measurement=UnitOfPower.WATT,
        device_class=SensorDeviceClass.POWER,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    ECU3SensorDescription(
        key="inverters_online",
        translation_key="inverters_online",
        value_key="inverters_online",
        icon="mdi:access-point-check",
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up sensors."""

    coordinator: APSystemsECU3Coordinator = (
        entry.runtime_data
    )

    entities: list[SensorEntity] = []

    home = coordinator.data.get(
        DATA_HOME,
        {},
    )

    ecu_id = home.get(
        "ecu_id",
        "unknown",
    )

    for description in ECU_SENSORS:
        entities.append(
            ECU3HomeSensor(
                coordinator,
                description,
                ecu_id,
            )
        )

    inverter_model = (
        entry.options.get(
            CONF_INVERTER_MODEL,
            entry.data.get(
                CONF_INVERTER_MODEL,
                DEFAULT_INVERTER_MODEL,
            ),
        )
    )

    if inverter_model == "Custom":
        inverter_model = (
            entry.options.get(
                CONF_CUSTOM_MODEL,
                entry.data.get(
                    CONF_CUSTOM_MODEL,
                    "Custom",
                ),
            )
        )

    for inverter_serial, channels in (
        coordinator.data.get(
            DATA_INVERTERS,
            {},
        ).items()
    ):

        for channel in channels:

            entities.extend(
                [
                    InverterChannelSensor(
                        coordinator,
                        ecu_id,
                        inverter_serial,
                        inverter_model,
                        channel,
                        "power",
                    ),
                    InverterChannelSensor(
                        coordinator,
                        ecu_id,
                        inverter_serial,
                        inverter_model,
                        channel,
                        "voltage",
                    ),
                    InverterChannelSensor(
                        coordinator,
                        ecu_id,
                        inverter_serial,
                        inverter_model,
                        channel,
                        "frequency",
                    ),
                    InverterChannelSensor(
                        coordinator,
                        ecu_id,
                        inverter_serial,
                        inverter_model,
                        channel,
                        "temperature",
                    ),
                ]
            )

    async_add_entities(
        entities,
    )


class ECU3HomeSensor(
    CoordinatorEntity,
    SensorEntity,
):
    """ECU-level sensor."""

    entity_description: ECU3SensorDescription
    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator,
        description,
        ecu_id,
    ) -> None:

        super().__init__(
            coordinator,
        )

        self.entity_description = (
            description
        )

        self._attr_unique_id = (
            f"{ecu_id}_{description.key}"
        )

        self.entity_id = (
            f"{SENSOR_DOMAIN}."
            f"{DOMAIN}_{ecu_id}_{description.key}"
        )

        self._attr_device_info = DeviceInfo(
            identifiers={
                (
                    DOMAIN,
                    ecu_id,
                )
            },
            manufacturer=MANUFACTURER,
            model=MODEL,
            serial_number=ecu_id,
            sw_version=coordinator.data[
                DATA_HOME
            ].get(
                "software_version",
            ),
            name=f"APSystems ECU-3 {ecu_id}",
        )

    @property
    def native_value(
        self,
    ):
        """Return state."""

        return self.coordinator.data[
            DATA_HOME
        ].get(
            self.entity_description.value_key,
        )


class InverterChannelSensor(
    CoordinatorEntity,
    SensorEntity,
):
    """Micro-inverter channel sensor."""

    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator,
        ecu_id,
        inverter_serial,
        inverter_model,
        channel,
        metric,
    ) -> None:

        super().__init__(
            coordinator,
        )

        self._ecu_id = ecu_id
        self._serial = inverter_serial
        self._channel = channel
        self._metric = metric

        self._attr_unique_id = (
            f"{inverter_serial}_{channel}_{metric}"
        )

        self.entity_id = (
            f"{SENSOR_DOMAIN}."
            f"{inverter_serial}_{metric}_{channel.lower()}"
        )

        self._attr_translation_key = metric

        self._attr_translation_placeholders = {
            "channel": channel,
        }

        self._attr_device_info = DeviceInfo(
            identifiers={
                (
                    DOMAIN,
                    inverter_serial,
                )
            },
            manufacturer=MANUFACTURER,
            model=inverter_model,
            serial_number=inverter_serial,
            via_device=(
                DOMAIN,
                ecu_id,
            ),
            name=(
                f"{inverter_model} "
                f"{inverter_serial}"
            ),
        )

        if metric == "power":
            self._attr_native_unit_of_measurement = (
                UnitOfPower.WATT
            )
            self._attr_device_class = (
                SensorDeviceClass.POWER
            )
            self._attr_state_class = (
                SensorStateClass.MEASUREMENT
            )

        elif metric == "voltage":
            self._attr_native_unit_of_measurement = (
                UnitOfElectricPotential.VOLT
            )
            self._attr_device_class = (
                SensorDeviceClass.VOLTAGE
            )
            self._attr_state_class = (
                SensorStateClass.MEASUREMENT
            )

        elif metric == "frequency":
            self._attr_native_unit_of_measurement = (
                UnitOfFrequency.HERTZ
            )
            self._attr_state_class = (
                SensorStateClass.MEASUREMENT
            )

        elif metric == "temperature":
            self._attr_native_unit_of_measurement = (
                UnitOfTemperature.CELSIUS
            )
            self._attr_device_class = (
                SensorDeviceClass.TEMPERATURE
            )
            self._attr_state_class = (
                SensorStateClass.MEASUREMENT
            )

    @property
    def native_value(
        self,
    ):
        """Return sensor state."""

        return (
            self.coordinator.data[
                DATA_INVERTERS
            ]
            .get(
                self._serial,
                {},
            )
            .get(
                self._channel,
                {},
            )
            .get(
                self._metric,
            )
        )