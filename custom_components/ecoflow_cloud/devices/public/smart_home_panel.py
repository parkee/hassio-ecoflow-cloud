"""
Smart Home Panel (SHP) device implementation for EcoFlow Cloud integration.

Based on the official EcoFlow IoT Developer Platform documentation for Smart Home Panel.
Implements both HTTP and MQTT communication modes with comprehensive sensor, switch,
number, select, and button entities.

API Reference:
- HTTP API: PUT/GET /iot-open/sign/device/quota
- MQTT Topics: /open/${certificateAccount}/${sn}/{set|set_reply|quota|status}
"""
import logging
from typing import Any

from homeassistant.components.binary_sensor import BinarySensorEntity
from homeassistant.components.button import ButtonEntity
from homeassistant.components.number import NumberEntity
from homeassistant.components.select import SelectEntity
from homeassistant.components.sensor import SensorEntity
from homeassistant.components.switch import SwitchEntity
from homeassistant.helpers.entity import EntityCategory

from custom_components.ecoflow_cloud.api import EcoflowApiClient
from custom_components.ecoflow_cloud.binary_sensor import MiscBinarySensorEntity
from custom_components.ecoflow_cloud.button import EnabledButtonEntity
from custom_components.ecoflow_cloud.devices import BaseDevice, const
from custom_components.ecoflow_cloud.number import (
    MaxBatteryLevelEntity,
    MinBatteryLevelEntity,
    ValueUpdateEntity,
)
from custom_components.ecoflow_cloud.select import DictSelectEntity
from custom_components.ecoflow_cloud.sensor import (
    AmpSensorEntity,
    FrequencySensorEntity,
    InEnergySensorEntity,
    InWattsSensorEntity,
    LevelSensorEntity,
    MiscSensorEntity,
    OutEnergySensorEntity,
    OutWattsSensorEntity,
    QuotaStatusSensorEntity,
    RemainSensorEntity,
    TempSensorEntity,
    VoltSensorEntity,
    WattsSensorEntity,
)
from custom_components.ecoflow_cloud.switch import EnabledEntity

_LOGGER = logging.getLogger(__name__)


class SmartHomePanel(BaseDevice):
    """
    Smart Home Panel device implementation.

    Supports:
    - 10 load channels (0-9) with individual control
    - 2 backup/standby channels (10-11) for battery connections
    - Split-phase configuration for 240V circuits
    - EPS (Emergency Power Supply) mode
    - Scheduled charging/discharging jobs
    - Emergency mode configuration
    - Grid power monitoring and configuration
    """

    def sensors(self, client: EcoflowApiClient) -> list[SensorEntity]:
        """Return all sensor entities for the Smart Home Panel."""
        sensors = [
            # Status sensor for device health monitoring
            QuotaStatusSensorEntity(client, self),

            # ===== Heartbeat / Main Status Sensors =====
            # Battery level sensors
            LevelSensorEntity(
                client, self, "heartbeat.backupBatPer", const.COMBINED_BATTERY_LEVEL
            ),
            LevelSensorEntity(
                client, self, "heartbeat.energyInfos[0].batteryPercentage",
                const.BATTERY_N_LEVEL % 1
            ),
            LevelSensorEntity(
                client, self, "heartbeat.energyInfos[1].batteryPercentage",
                const.BATTERY_N_LEVEL % 2, False
            ),

            # Remaining time sensors
            RemainSensorEntity(
                client, self, "heartbeat.backupChaTime", const.REMAINING_TIME
            ),
            RemainSensorEntity(
                client, self, "heartbeat.energyInfos[0].chargeTime",
                const.BATTERY_N_CHARGE_REMAINING_TIME % 1, False
            ),
            RemainSensorEntity(
                client, self, "heartbeat.energyInfos[1].chargeTime",
                const.BATTERY_N_CHARGE_REMAINING_TIME % 2, False
            ),
            RemainSensorEntity(
                client, self, "heartbeat.energyInfos[0].dischargeTime",
                const.BATTERY_N_DISCHARGE_REMAINING_TIME % 1, False
            ),
            RemainSensorEntity(
                client, self, "heartbeat.energyInfos[1].dischargeTime",
                const.BATTERY_N_DISCHARGE_REMAINING_TIME % 2, False
            ),

            # Temperature sensors
            TempSensorEntity(
                client, self, "heartbeat.energyInfos[0].emsBatTemp",
                const.BATTERY_N_TEMP % 1
            ),
            TempSensorEntity(
                client, self, "heartbeat.energyInfos[1].emsBatTemp",
                const.BATTERY_N_TEMP % 2, False
            ),

            # Power sensors for batteries
            InWattsSensorEntity(
                client, self, "heartbeat.energyInfos[0].lcdInputWatts",
                const.BATTERY_N_IN_POWER % 1
            ).with_energy().with_icon("mdi:transmission-tower"),
            InWattsSensorEntity(
                client, self, "heartbeat.energyInfos[1].lcdInputWatts",
                const.BATTERY_N_IN_POWER % 2, False
            ).with_energy().with_icon("mdi:transmission-tower"),
            OutWattsSensorEntity(
                client, self, "heartbeat.energyInfos[0].outputPower",
                const.BATTERY_N_OUT_POWER % 1
            ).with_energy().with_icon("mdi:home-battery"),
            OutWattsSensorEntity(
                client, self, "heartbeat.energyInfos[1].outputPower",
                const.BATTERY_N_OUT_POWER % 2, False
            ).with_energy().with_icon("mdi:home-battery"),

            # Energy consumption sensors
            InEnergySensorEntity(
                client, self, "heartbeat.gridDayWatth", const.POWER_GRID_TODAY
            ),
            OutEnergySensorEntity(
                client, self, "heartbeat.backupDayWatth", const.BATTERY_TODAY
            ),

            # Work time sensor (device uptime in minutes)
            MiscSensorEntity(
                client, self, "heartbeat.workTime", const.WORK_TIME, False
            ).with_icon("mdi:timer-outline"),

            # Backup full capacity sensor
            WattsSensorEntity(
                client, self, "heartbeat.backupFullCap", const.BACKUP_FULL_CAPACITY, False
            ).with_icon("mdi:battery-high"),

            # ===== Grid Configuration Sensors (Diagnostic) =====
            VoltSensorEntity(
                client, self, "'gridInfo.gridVol'", const.POWER_GRID_VOLTAGE,
                diagnostic=True
            ),
            FrequencySensorEntity(
                client, self, "'gridInfo.gridFreq'", const.POWER_GRID_FREQUENCY,
                diagnostic=True
            ),

            # ===== Backup charging/discharging configuration sensors =====
            LevelSensorEntity(
                client, self, "'backupChaDiscCfg.forceChargeHigh'",
                const.MAX_CHARGE_LEVEL, False, diagnostic=True
            ),
            LevelSensorEntity(
                client, self, "'backupChaDiscCfg.discLower'",
                const.MIN_DISCHARGE_LEVEL, False, diagnostic=True
            ),

            # ===== Area/Region Information =====
            MiscSensorEntity(
                client, self, "'areaInfo.area'", const.AREA_INFO, False
            ).with_icon("mdi:map-marker"),

            # ===== Configuration Status =====
            MiscSensorEntity(
                client, self, "'cfgSta.sta'", const.CONFIGURATION_STATUS, False
            ).with_icon("mdi:cog"),

            # ===== Channel Current Configuration (Diagnostic) =====
            # Load channels (0-9) current ratings
            *[
                AmpSensorEntity(
                    client, self, f"'loadChCurInfo.cur'[{i}]",
                    const.CIRCUIT_N_CURRENT % (i + 1), False, diagnostic=True
                )
                for i in range(10)
            ],
            # Backup channels (10-11) current ratings
            *[
                AmpSensorEntity(
                    client, self, f"'loadChCurInfo.cur'[{i}]",
                    const.BATTERY_N_CURRENT % (i - 9), False, diagnostic=True
                )
                for i in range(10, 12)
            ],
        ]

        # ===== Load Channel Sensors (10 channels: 0-9) =====
        for i in range(10):
            channel_num = i + 1
            # Channel control status sensors
            sensors.extend([
                MiscSensorEntity(
                    client, self,
                    f"heartbeat.loadCmdChCtrlInfos[{i}].ctrlSta",
                    const.CIRCUIT_N_SUPPLY_STATUS % channel_num, False
                ).with_icon("mdi:power-plug"),
                MiscSensorEntity(
                    client, self,
                    f"heartbeat.loadCmdChCtrlInfos[{i}].ctrlMode",
                    const.CIRCUIT_N_CONTROL_MODE % channel_num, False
                ).with_icon("mdi:auto-fix"),
                MiscSensorEntity(
                    client, self,
                    f"heartbeat.loadCmdChCtrlInfos[{i}].priority",
                    const.CIRCUIT_N_PRIORITY % channel_num, False
                ).with_icon("mdi:priority-high"),
            ])

        # ===== Backup Channel Sensors (2 channels: 10-11) =====
        for i in range(2):
            channel_num = i + 1
            sensors.extend([
                MiscSensorEntity(
                    client, self,
                    f"heartbeat.backupCmdChCtrlInfos[{i}].ctrlSta",
                    const.BACKUP_CHANNEL_N_SUPPLY_STATUS % channel_num, False
                ).with_icon("mdi:battery-charging"),
                MiscSensorEntity(
                    client, self,
                    f"heartbeat.backupCmdChCtrlInfos[{i}].ctrlMode",
                    const.BACKUP_CHANNEL_N_CONTROL_MODE % channel_num, False
                ).with_icon("mdi:auto-fix"),
            ])

        # ===== Split-Phase Configuration Sensors (Diagnostic) =====
        for i in range(10):
            channel_num = i + 1
            sensors.extend([
                MiscSensorEntity(
                    client, self,
                    f"'splitPhaseInfo.cfgList'[{i}].linkMark",
                    const.SPLIT_PHASE_N_LINKED % channel_num, False
                ).with_icon("mdi:link-variant"),
                MiscSensorEntity(
                    client, self,
                    f"'splitPhaseInfo.cfgList'[{i}].linkCh",
                    const.SPLIT_PHASE_N_LINK_CHANNEL % channel_num, False
                ).with_icon("mdi:link"),
            ])

        # ===== Emergency Strategy Sensors =====
        sensors.extend([
            MiscSensorEntity(
                client, self, "'emergencyStrategy.isCfg'",
                const.EMERGENCY_MODE_CONFIGURED, False
            ).with_icon("mdi:alert"),
            MiscSensorEntity(
                client, self, "'emergencyStrategy.backupMode'",
                const.EMERGENCY_BACKUP_MODE, False
            ).with_icon("mdi:battery-alert"),
            MiscSensorEntity(
                client, self, "'emergencyStrategy.overloadMode'",
                const.EMERGENCY_OVERLOAD_MODE, False
            ).with_icon("mdi:flash-alert"),
        ])

        # ===== Self-Check Status =====
        sensors.append(
            MiscSensorEntity(
                client, self, "'selfCheck.flag'",
                const.SELF_CHECK_STATUS, False
            ).with_icon("mdi:check-circle")
        )

        return sensors

    def binary_sensors(self, client: EcoflowApiClient) -> list[BinarySensorEntity]:
        """Return all binary sensor entities for the Smart Home Panel."""
        return [
            # Grid power status (0 = off, 1 = on)
            MiscBinarySensorEntity(
                client, self, "heartbeat.gridSta", const.POWER_GRID
            ).with_icon("mdi:transmission-tower"),

            # EPS mode status
            MiscBinarySensorEntity(
                client, self, "'epsModeInfo.eps'", const.EPS_MODE
            ).with_icon("mdi:power-plug-battery"),
        ]

    def numbers(self, client: EcoflowApiClient) -> list[NumberEntity]:
        """Return all number entities for the Smart Home Panel."""
        numbers = [
            # ===== Backup Charging/Discharging Parameters (cmdSet: 11, id: 29) =====
            MinBatteryLevelEntity(
                client,
                self,
                "'backupChaDiscCfg.discLower'",
                const.MIN_DISCHARGE_LEVEL,
                0,
                30,
                lambda value, params: {
                    "operateType": "TCP",
                    "params": {
                        "cmdSet": 11,
                        "id": 29,
                        "discLower": int(value),
                        "forceChargeHigh": int(
                            params.get("backupChaDiscCfg.forceChargeHigh", 100)
                        ),
                    },
                },
            ),
            MaxBatteryLevelEntity(
                client,
                self,
                "'backupChaDiscCfg.forceChargeHigh'",
                const.MAX_CHARGE_LEVEL,
                50,
                100,
                lambda value, params: {
                    "operateType": "TCP",
                    "params": {
                        "cmdSet": 11,
                        "id": 29,
                        "forceChargeHigh": int(value),
                        "discLower": int(
                            params.get("backupChaDiscCfg.discLower", 0)
                        ),
                    },
                },
            ),
        ]

        # ===== Channel Current Configuration (cmdSet: 11, id: 20) =====
        # Channel current configuration for load channels 0-9
        for i in range(10):
            channel_num = i + 1
            numbers.append(
                ValueUpdateEntity(
                    client,
                    self,
                    f"'loadChCurInfo.cur'[{i}]",
                    const.CHANNEL_CURRENT_N % channel_num,
                    6,
                    30,
                    lambda value, ch=i: {
                        "operateType": "TCP",
                        "params": {
                            "cmdSet": 11,
                            "id": 20,
                            "chNum": ch,
                            "cur": int(value),
                        },
                    },
                ).with_icon("mdi:current-ac")
            )

        return numbers

    def switches(self, client: EcoflowApiClient) -> list[SwitchEntity]:
        """Return all switch entities for the Smart Home Panel."""
        switches = [
            # ===== EPS Mode Switch (cmdSet: 11, id: 24) =====
            EnabledEntity(
                client,
                self,
                "'epsModeInfo.eps'",
                const.EPS_MODE,
                lambda value: {
                    "operateType": "TCP",
                    "params": {
                        "cmdSet": 11,
                        "id": 24,
                        "eps": int(value),
                    },
                },
            )
            .with_category(EntityCategory.CONFIG)
            .with_icon("mdi:power-plug-battery"),
        ]

        # ===== Load Channel Switches (cmdSet: 11, id: 16) =====
        # Channels 0-9 (displayed as 1-10)
        for i in range(10):
            channel_num = i + 1
            ch_name = self.data.params.get(
                f"loadChInfo.info[{i}].chName",
                const.CIRCUIT_N_NAME % channel_num
            )
            switches.append(
                self._createLoadChannelSwitch(client, i, ch_name)
            )

        # ===== Backup/Standby Channel Switches (cmdSet: 11, id: 17) =====
        # Channels 10-11 (backup battery connections)
        switches.append(self._createBackupChannelSwitch(client, 1, True))
        switches.append(self._createBackupChannelSwitch(client, 2, False))

        # ===== Channel Enable Switches (cmdSet: 11, id: 26) =====
        for i in range(10):
            channel_num = i + 1
            switches.append(
                EnabledEntity(
                    client,
                    self,
                    f"'emergencyStrategy.chSta'[{i}].isEnable",
                    const.CIRCUIT_N_ENABLED % channel_num,
                    lambda value, ch=i: {
                        "operateType": "TCP",
                        "params": {
                            "cmdSet": 11,
                            "id": 26,
                            "chNum": ch,
                            "isEnable": int(value),
                        },
                    },
                    enabled=False,
                )
                .with_category(EntityCategory.CONFIG)
                .with_icon("mdi:electric-switch")
            )

        return switches

    def selects(self, client: EcoflowApiClient) -> list[SelectEntity]:
        """Return all select entities for the Smart Home Panel."""
        selects = [
            # ===== Grid Voltage Configuration (cmdSet: 11, id: 22) =====
            DictSelectEntity(
                client,
                self,
                "'gridInfo.gridVol'",
                const.POWER_GRID_VOLTAGE,
                const.GRID_VOLTAGE_OPTIONS,
                lambda value, params: {
                    "operateType": "TCP",
                    "params": {
                        "cmdSet": 11,
                        "id": 22,
                        "gridVol": int(value),
                        "gridFreq": int(params.get("gridInfo.gridFreq", 60)),
                    },
                },
                enabled=False,
            ).with_icon("mdi:flash"),

            # ===== Grid Frequency Configuration (cmdSet: 11, id: 22) =====
            DictSelectEntity(
                client,
                self,
                "'gridInfo.gridFreq'",
                const.POWER_GRID_FREQUENCY,
                const.GRID_FREQUENCY_OPTIONS,
                lambda value, params: {
                    "operateType": "TCP",
                    "params": {
                        "cmdSet": 11,
                        "id": 22,
                        "gridVol": int(params.get("gridInfo.gridVol", 120)),
                        "gridFreq": int(value),
                    },
                },
                enabled=False,
            ).with_icon("mdi:sine-wave"),

            # ===== Emergency Backup Mode (cmdSet: 11, id: 64) =====
            DictSelectEntity(
                client,
                self,
                "'emergencyStrategy.backupMode'",
                const.EMERGENCY_BACKUP_MODE,
                const.EMERGENCY_BACKUP_MODE_OPTIONS,
                lambda value, params: self._createEmergencyModeCommand(
                    backupMode=int(value),
                    overloadMode=int(params.get("emergencyStrategy.overloadMode", 0)),
                    params=params,
                ),
                enabled=False,
            ).with_icon("mdi:battery-alert"),

            # ===== Emergency Overload Mode (cmdSet: 11, id: 64) =====
            DictSelectEntity(
                client,
                self,
                "'emergencyStrategy.overloadMode'",
                const.EMERGENCY_OVERLOAD_MODE,
                const.EMERGENCY_OVERLOAD_MODE_OPTIONS,
                lambda value, params: self._createEmergencyModeCommand(
                    backupMode=int(params.get("emergencyStrategy.backupMode", 0)),
                    overloadMode=int(value),
                    params=params,
                ),
                enabled=False,
            ).with_icon("mdi:flash-alert"),
        ]

        # ===== Load Channel Control Mode Selects =====
        for i in range(10):
            channel_num = i + 1
            selects.append(
                DictSelectEntity(
                    client,
                    self,
                    f"heartbeat.loadCmdChCtrlInfos[{i}].ctrlMode",
                    const.CIRCUIT_N_CONTROL_MODE % channel_num,
                    const.CHANNEL_CONTROL_MODE_OPTIONS,
                    lambda value, ch=i: {
                        "operateType": "TCP",
                        "params": {
                            "cmdSet": 11,
                            "id": 16,
                            "ch": ch,
                            "ctrlMode": int(value),
                            "sta": 1,  # Keep current status
                        },
                    },
                    enabled=False,
                ).with_icon("mdi:auto-fix")
            )

        return selects

    def buttons(self, client: EcoflowApiClient) -> list[ButtonEntity]:
        """Return all button entities for the Smart Home Panel."""
        return [
            # ===== Device Reset Button (cmdSet: 1, id: 20) =====
            EnabledButtonEntity(
                client,
                self,
                "reset",
                "Reset Device",
                lambda _: {
                    "operateType": "TCP",
                    "params": {
                        "cmdSet": 1,
                        "id": 20,
                    },
                },
                enabled=False,
            ).with_icon("mdi:restart"),

            # ===== Self-Check Button (cmdSet: 11, id: 112) =====
            EnabledButtonEntity(
                client,
                self,
                "selfCheck",
                "Start Self-Check",
                lambda _: {
                    "operateType": "TCP",
                    "params": {
                        "cmdSet": 11,
                        "id": 112,
                        "selfCheckType": 1,
                    },
                },
                enabled=False,
            ).with_icon("mdi:check-circle-outline"),

            # ===== RTC Time Sync Button (cmdSet: 11, id: 3) =====
            # Note: This syncs the device RTC with current time
            EnabledButtonEntity(
                client,
                self,
                "rtcSync",
                "Sync RTC Time",
                lambda _: self._createRtcSyncCommand(),
                enabled=False,
            ).with_icon("mdi:clock-sync"),

            # ===== Configuration Status Set Button (cmdSet: 11, id: 7) =====
            EnabledButtonEntity(
                client,
                self,
                "cfgComplete",
                "Mark Configuration Complete",
                lambda _: {
                    "operateType": "TCP",
                    "params": {
                        "cmdSet": 11,
                        "id": 7,
                        "cfgSta": 1,
                    },
                },
                enabled=False,
            ).with_icon("mdi:check-bold"),
        ]

    def flat_json(self):
        """
        Indicate whether the device uses flat JSON structure.

        Smart Home Panel uses hierarchical JSON for public API,
        so we return False to use quoted keys for nested access.
        """
        return False

    def _createLoadChannelSwitch(
        self, client: EcoflowApiClient, channel: int, name: str
    ) -> SwitchEntity:
        """
        Create a load channel switch (cmdSet: 11, id: 16).

        Args:
            client: The API client
            channel: Channel number (0-9)
            name: Display name for the channel

        Returns:
            Switch entity for controlling the load channel
        """
        return (
            EnabledEntity(
                client,
                self,
                f"heartbeat.loadCmdChCtrlInfos[{channel}].ctrlSta",
                name,
                lambda value, ch=channel: {
                    "operateType": "TCP",
                    "params": {
                        "cmdSet": 11,
                        "id": 16,
                        "ch": ch,
                        "ctrlMode": 1,  # Manual mode
                        "sta": 1 if value else 2,  # 1=battery supply, 2=off
                    },
                },
                True,
                enableValue=1,  # Battery supply = on
                disableValue=2,  # Off
            )
            .with_icon("mdi:electric-switch")
        )

    def _createBackupChannelSwitch(
        self, client: EcoflowApiClient, index: int, enabled: bool = True
    ) -> SwitchEntity:
        """
        Create a backup/standby channel switch (cmdSet: 11, id: 17).

        Args:
            client: The API client
            index: Backup channel index (1-2, maps to channels 10-11)
            enabled: Whether the entity is enabled by default

        Returns:
            Switch entity for controlling the backup channel
        """
        return (
            EnabledEntity(
                client,
                self,
                f"heartbeat.backupCmdChCtrlInfos[{index - 1}].ctrlSta",
                const.BATTERY_N_CHARGE % index,
                lambda value, idx=index: {
                    "operateType": "TCP",
                    "params": {
                        "cmdSet": 11,
                        "id": 17,
                        "ch": 9 + idx,  # Channel 10 or 11
                        "ctrlMode": 1 if value else 0,  # Manual when on
                        "sta": 2 if value else 0,  # 2=battery supply when on, 0=grid
                    },
                },
                enabled,
                enableValue=2,  # Battery supply
                disableValue=0,  # Grid supply
            )
            .with_category(EntityCategory.CONFIG)
            .with_icon("mdi:battery-charging")
        )

    def _createEmergencyModeCommand(
        self, backupMode: int, overloadMode: int, params: dict[str, Any]
    ) -> dict[str, Any]:
        """
        Create emergency mode command (cmdSet: 11, id: 64).

        Args:
            backupMode: 0=disabled, 1=enabled
            overloadMode: 0=disabled, 1=enabled
            params: Current device parameters

        Returns:
            Command dictionary for setting emergency mode
        """
        # Build channel status array from current params
        chSta = []
        for i in range(10):
            priority = params.get(f"emergencyStrategy.chSta[{i}].priority", i)
            isEnable = params.get(f"emergencyStrategy.chSta[{i}].isEnable", 1)
            chSta.append({
                "priority": int(priority),
                "isEnable": int(isEnable),
            })

        return {
            "operateType": "TCP",
            "params": {
                "cmdSet": 11,
                "id": 64,
                "isCfg": 1,
                "backupMode": backupMode,
                "overloadMode": overloadMode,
                "chSta": chSta,
            },
        }

    def _createRtcSyncCommand(self) -> dict[str, Any]:
        """
        Create RTC time sync command (cmdSet: 11, id: 3).

        Syncs the device RTC with the current system time.

        Returns:
            Command dictionary for RTC time update
        """
        from datetime import datetime

        now = datetime.now()
        return {
            "operateType": "TCP",
            "params": {
                "cmdSet": 11,
                "id": 3,
                "year": now.year,
                "month": now.month,
                "day": now.day,
                "hour": now.hour,
                "min": now.minute,
                "sec": now.second,
                "week": now.isoweekday(),  # 1=Monday, 7=Sunday
            },
        }
