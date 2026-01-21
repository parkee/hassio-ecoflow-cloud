"""
Smart Home Panel (SHP) device implementation for EcoFlow Cloud integration.

Based on the official EcoFlow IoT Developer Platform documentation for Smart Home Panel.
Implements both HTTP and MQTT communication modes with comprehensive sensor, switch,
number, select, button, and text entities.

API Reference:
- HTTP API: PUT/GET /iot-open/sign/device/quota
- MQTT Topics: /open/${certificateAccount}/${sn}/{set|set_reply|quota|status}

Features:
- 10 load channels (0-9) with individual power monitoring and control
- 2 backup/standby channels (10-11) for battery connections
- Split-phase configuration for 240V circuits
- EPS (Emergency Power Supply) mode
- Scheduled charging/discharging jobs
- Emergency mode configuration
- Grid power monitoring and configuration
- Circuit name configuration
- Command reply monitoring
"""
import logging
import random
from typing import Any

from homeassistant.components.binary_sensor import BinarySensorEntity
from homeassistant.components.button import ButtonEntity
from homeassistant.components.number import NumberEntity
from homeassistant.components.select import SelectEntity
from homeassistant.components.sensor import SensorEntity
from homeassistant.components.switch import SwitchEntity
from homeassistant.components.text import TextEntity
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
from custom_components.ecoflow_cloud.select import CircuitModeSelectEntity, DictSelectEntity
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
from custom_components.ecoflow_cloud.text import TextConfigEntity

_LOGGER = logging.getLogger(__name__)


class SmartHomePanel(BaseDevice):
    """
    Smart Home Panel device implementation.

    Supports:
    - 10 load channels (0-9) with individual control and power monitoring
    - 2 backup/standby channels (10-11) for battery connections
    - Split-phase configuration for 240V circuits
    - EPS (Emergency Power Supply) mode
    - Scheduled charging/discharging jobs
    - Emergency mode configuration
    - Grid power monitoring and configuration
    - Circuit name configuration
    - Command status monitoring
    """

    def sensors(self, client: EcoflowApiClient) -> list[SensorEntity]:
        """Return all sensor entities for the Smart Home Panel."""
        sensors = [
            # Status sensor for device health monitoring
            QuotaStatusSensorEntity(client, self),

            # ===== Heartbeat / Main Status Sensors =====
            # Combined battery level
            LevelSensorEntity(
                client, self, "heartbeat.backupBatPer", const.COMBINED_BATTERY_LEVEL
            ),

            # Individual battery levels (for multi-battery setups)
            LevelSensorEntity(
                client, self, "heartbeat.energyInfos[0].batteryPercentage",
                const.BATTERY_N_LEVEL % 1, False
            ),
            LevelSensorEntity(
                client, self, "heartbeat.energyInfos[1].batteryPercentage",
                const.BATTERY_N_LEVEL % 2, False
            ),

            # Backup full capacity (Wh)
            WattsSensorEntity(
                client, self, "heartbeat.backupFullCap", const.BACKUP_FULL_CAPACITY, True
            ).with_icon("mdi:battery-high"),

            # Grid status (0=disconnected, 1=connected)
            MiscSensorEntity(
                client, self, "heartbeat.gridSta", const.POWER_GRID
            ).with_icon("mdi:transmission-tower"),

            # Energy consumption - Daily
            InEnergySensorEntity(
                client, self, "heartbeat.gridDayWatth", const.POWER_GRID_TODAY
            ),
            OutEnergySensorEntity(
                client, self, "heartbeat.backupDayWatth", const.BATTERY_TODAY
            ),

            # Work time (device uptime in minutes)
            MiscSensorEntity(
                client, self, "heartbeat.workTime", const.WORK_TIME, True
            ).with_icon("mdi:timer-outline"),

            # Backup charge/discharge time remaining
            RemainSensorEntity(
                client, self, "heartbeat.backupChaTime", const.REMAINING_TIME
            ),

            # Individual battery remaining times
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

            # Battery temperatures
            TempSensorEntity(
                client, self, "heartbeat.energyInfos[0].emsBatTemp",
                const.BATTERY_N_TEMP % 1, False
            ),
            TempSensorEntity(
                client, self, "heartbeat.energyInfos[1].emsBatTemp",
                const.BATTERY_N_TEMP % 2, False
            ),

            # Battery power in/out
            InWattsSensorEntity(
                client, self, "heartbeat.energyInfos[0].lcdInputWatts",
                const.BATTERY_N_IN_POWER % 1, False
            ).with_energy().with_icon("mdi:transmission-tower"),
            InWattsSensorEntity(
                client, self, "heartbeat.energyInfos[1].lcdInputWatts",
                const.BATTERY_N_IN_POWER % 2, False
            ).with_energy().with_icon("mdi:transmission-tower"),
            OutWattsSensorEntity(
                client, self, "heartbeat.energyInfos[0].outputPower",
                const.BATTERY_N_OUT_POWER % 1, False
            ).with_energy().with_icon("mdi:home-battery"),
            OutWattsSensorEntity(
                client, self, "heartbeat.energyInfos[1].outputPower",
                const.BATTERY_N_OUT_POWER % 2, False
            ).with_energy().with_icon("mdi:home-battery"),

            # ===== Grid Configuration Sensors =====
            VoltSensorEntity(
                client, self, "'gridInfo.gridVol'", const.POWER_GRID_VOLTAGE, True
            ),
            FrequencySensorEntity(
                client, self, "'gridInfo.gridFreq'", const.POWER_GRID_FREQUENCY, True
            ),

            # ===== Backup Charging/Discharging Configuration =====
            LevelSensorEntity(
                client, self, "'backupChaDiscCfg.forceChargeHigh'",
                const.MAX_CHARGE_LEVEL, False
            ),
            LevelSensorEntity(
                client, self, "'backupChaDiscCfg.discLower'",
                const.MIN_DISCHARGE_LEVEL, False
            ),

            # ===== EPS Mode Status =====
            MiscSensorEntity(
                client, self, "'epsModeInfo.eps'", const.EPS_MODE, False
            ).with_icon("mdi:power-plug-battery"),

            # ===== Area/Region Information =====
            MiscSensorEntity(
                client, self, "'areaInfo.area'", const.AREA_INFO, False
            ).with_icon("mdi:map-marker"),

            # ===== Configuration Status =====
            MiscSensorEntity(
                client, self, "'cfgSta.sta'", const.CONFIGURATION_STATUS, False
            ).with_icon("mdi:cog"),

            # ===== Self-Check Status =====
            MiscSensorEntity(
                client, self, "'selfCheck.flag'", const.SELF_CHECK_STATUS, False
            ).with_icon("mdi:check-circle"),
        ]

        # ===== Circuit Power Consumption Sensors (from infoList) =====
        # These show real-time power consumption per circuit
        for i in range(10):
            channel_num = i + 1
            sensors.append(
                OutWattsSensorEntity(
                    client, self,
                    f"'infoList'[{i}].chWatt",
                    const.CIRCUIT_N_POWER % channel_num, True
                ).with_energy().with_icon("mdi:lightning-bolt")
            )

        # ===== Load Channel Status Sensors (from heartbeat.loadCmdChCtrlInfos) =====
        for i in range(10):
            channel_num = i + 1
            sensors.extend([
                # Control status (0=grid, 1=battery, 2=off)
                MiscSensorEntity(
                    client, self,
                    f"heartbeat.loadCmdChCtrlInfos[{i}].ctrlSta",
                    const.CIRCUIT_N_SUPPLY_STATUS % channel_num, False
                ).with_icon("mdi:power-plug"),
                # Control mode (0=auto, 1=manual)
                MiscSensorEntity(
                    client, self,
                    f"heartbeat.loadCmdChCtrlInfos[{i}].ctrlMode",
                    const.CIRCUIT_N_CONTROL_MODE % channel_num, False
                ).with_icon("mdi:auto-fix"),
                # Priority
                MiscSensorEntity(
                    client, self,
                    f"heartbeat.loadCmdChCtrlInfos[{i}].priority",
                    const.CIRCUIT_N_PRIORITY % channel_num, False
                ).with_icon("mdi:priority-high"),
            ])

        # ===== Backup Channel Status Sensors (from heartbeat.backupCmdChCtrlInfos) =====
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

        # ===== Channel Current Configuration Sensors =====
        # Load channels (0-9)
        for i in range(10):
            channel_num = i + 1
            sensors.append(
                AmpSensorEntity(
                    client, self, f"'loadChCurInfo.cur'[{i}]",
                    const.CIRCUIT_N_CURRENT % channel_num, False
                )
            )
        # Backup channels (10-11)
        for i in range(10, 12):
            channel_num = i - 9
            sensors.append(
                AmpSensorEntity(
                    client, self, f"'loadChCurInfo.cur'[{i}]",
                    const.BACKUP_CHANNEL_N_CURRENT % channel_num, False
                )
            )

        # ===== Channel Name Sensors (from loadChInfo) =====
        for i in range(10):
            channel_num = i + 1
            sensors.append(
                MiscSensorEntity(
                    client, self,
                    f"'loadChInfo.info'[{i}].chName",
                    const.CIRCUIT_N_NAME % channel_num, False
                ).with_icon("mdi:tag")
            )

        # ===== Split-Phase Configuration Sensors =====
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

        # ===== Emergency Strategy Channel Status =====
        for i in range(10):
            channel_num = i + 1
            sensors.extend([
                MiscSensorEntity(
                    client, self,
                    f"'emergencyStrategy.chSta'[{i}].priority",
                    f"Emergency Priority Circuit {channel_num}", False
                ).with_icon("mdi:priority-high"),
                MiscSensorEntity(
                    client, self,
                    f"'emergencyStrategy.chSta'[{i}].isEnable",
                    f"Emergency Enabled Circuit {channel_num}", False
                ).with_icon("mdi:check-circle"),
            ])

        return sensors

    def binary_sensors(self, client: EcoflowApiClient) -> list[BinarySensorEntity]:
        """Return all binary sensor entities for the Smart Home Panel."""
        return [
            # Grid power status (0=off, 1=on)
            MiscBinarySensorEntity(
                client, self, "heartbeat.gridSta", const.POWER_GRID
            ).with_icon("mdi:transmission-tower"),

            # EPS mode active
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
                100,
                lambda value, params: self._create_mqtt_command(
                    cmdSet=11,
                    cmdId=29,
                    params={
                        "discLower": int(value),
                        "forceChargeHigh": int(
                            params.get("backupChaDiscCfg.forceChargeHigh", 100)
                        ),
                    },
                ),
            ),
            MaxBatteryLevelEntity(
                client,
                self,
                "'backupChaDiscCfg.forceChargeHigh'",
                const.MAX_CHARGE_LEVEL,
                0,
                100,
                lambda value, params: self._create_mqtt_command(
                    cmdSet=11,
                    cmdId=29,
                    params={
                        "forceChargeHigh": int(value),
                        "discLower": int(
                            params.get("backupChaDiscCfg.discLower", 0)
                        ),
                    },
                ),
            ),

            # ===== Grid Voltage Setting (cmdSet: 11, id: 22) =====
            ValueUpdateEntity(
                client,
                self,
                "'gridInfo.gridVol'",
                const.POWER_GRID_VOLTAGE + " Setting",
                100,
                250,
                lambda value, params: self._create_mqtt_command(
                    cmdSet=11,
                    cmdId=22,
                    params={
                        "gridVol": int(value),
                        "gridFreq": int(params.get("gridInfo.gridFreq", 60)),
                    },
                ),
                enabled=False,
            ).with_icon("mdi:flash"),

            # ===== Grid Frequency Setting (cmdSet: 11, id: 22) =====
            ValueUpdateEntity(
                client,
                self,
                "'gridInfo.gridFreq'",
                const.POWER_GRID_FREQUENCY + " Setting",
                50,
                60,
                lambda value, params: self._create_mqtt_command(
                    cmdSet=11,
                    cmdId=22,
                    params={
                        "gridVol": int(params.get("gridInfo.gridVol", 120)),
                        "gridFreq": int(value),
                    },
                ),
                enabled=False,
            ).with_icon("mdi:sine-wave"),
        ]

        # ===== Channel Current Configuration (cmdSet: 11, id: 20) =====
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
                    self._make_channel_current_command(i),
                    enabled=False,
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
                lambda value: self._create_mqtt_command(
                    cmdSet=11,
                    cmdId=24,
                    params={"eps": 1 if value else 0},
                ),
            )
            .with_category(EntityCategory.CONFIG)
            .with_icon("mdi:power-plug-battery"),
        ]

        # NOTE: Load Channel On/Off Switches removed - redundant with Circuit Mode selects
        # which provide Auto/Grid/Battery/Off options (more comprehensive control)

        # ===== Backup/Standby Channel Switches (cmdSet: 11, id: 17) =====
        for i in range(2):
            channel_num = i + 1
            switches.append(
                self._create_backup_channel_switch(client, i, channel_num)
            )

        # ===== Channel Enable Switches for Emergency Mode (cmdSet: 11, id: 26) =====
        for i in range(10):
            channel_num = i + 1
            switches.append(
                EnabledEntity(
                    client,
                    self,
                    f"'emergencyStrategy.chSta'[{i}].isEnable",
                    const.CIRCUIT_N_ENABLED % channel_num,
                    self._make_emergency_channel_command(i),
                    enabled=False,
                )
                .with_category(EntityCategory.CONFIG)
                .with_icon("mdi:electric-switch")
            )

        return switches

    def selects(self, client: EcoflowApiClient) -> list[SelectEntity]:
        """Return all select entities for the Smart Home Panel."""
        selects = [
            # ===== Grid Voltage Select (cmdSet: 11, id: 22) =====
            DictSelectEntity(
                client,
                self,
                "'gridInfo.gridVol'",
                const.POWER_GRID_VOLTAGE + " Select",
                const.GRID_VOLTAGE_OPTIONS,
                lambda value, params: self._create_mqtt_command(
                    cmdSet=11,
                    cmdId=22,
                    params={
                        "gridVol": int(value),
                        "gridFreq": int(params.get("gridInfo.gridFreq", 60)),
                    },
                ),
                enabled=False,
            ).with_icon("mdi:flash"),

            # ===== Grid Frequency Select (cmdSet: 11, id: 22) =====
            DictSelectEntity(
                client,
                self,
                "'gridInfo.gridFreq'",
                const.POWER_GRID_FREQUENCY + " Select",
                const.GRID_FREQUENCY_OPTIONS,
                lambda value, params: self._create_mqtt_command(
                    cmdSet=11,
                    cmdId=22,
                    params={
                        "gridVol": int(params.get("gridInfo.gridVol", 120)),
                        "gridFreq": int(value),
                    },
                ),
                enabled=False,
            ).with_icon("mdi:sine-wave"),

            # ===== Emergency Backup Mode (cmdSet: 11, id: 64) =====
            DictSelectEntity(
                client,
                self,
                "'emergencyStrategy.backupMode'",
                const.EMERGENCY_BACKUP_MODE,
                const.EMERGENCY_BACKUP_MODE_OPTIONS,
                lambda value, params: self._create_emergency_mode_command(
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
                lambda value, params: self._create_emergency_mode_command(
                    backupMode=int(params.get("emergencyStrategy.backupMode", 0)),
                    overloadMode=int(value),
                    params=params,
                ),
                enabled=False,
            ).with_icon("mdi:flash-alert"),
        ]

        # ===== Circuit Current Limit Selects (cmdSet: 11, id: 20) =====
        for i in range(10):
            channel_num = i + 1
            selects.append(
                DictSelectEntity(
                    client,
                    self,
                    f"'loadChCurInfo.cur'[{i}]",
                    f"Circuit {channel_num} Current Limit",
                    const.CHANNEL_CURRENT_OPTIONS,
                    self._make_channel_current_command(i),
                    enabled=False,
                ).with_icon("mdi:current-ac")
            )

        # ===== Circuit Mode Control Selects (cmdSet: 11, id: 16) =====
        # Options: Auto, Grid, Battery, Off
        # Uses CircuitModeSelectEntity to properly compute state from ctrlMode + ctrlSta
        for i in range(10):
            channel_num = i + 1
            selects.append(
                CircuitModeSelectEntity(
                    client,
                    self,
                    f"heartbeat.loadCmdChCtrlInfos[{i}].ctrlMode",
                    f"heartbeat.loadCmdChCtrlInfos[{i}].ctrlSta",
                    f"Circuit {channel_num} Mode",
                    const.CIRCUIT_MODE_OPTIONS,
                    self._make_circuit_mode_command_factory(i),
                )
            )

        # ===== Backup Channel Mode Control Selects (cmdSet: 11, id: 17) =====
        for i in range(2):
            channel_num = i + 1
            selects.append(
                DictSelectEntity(
                    client,
                    self,
                    f"heartbeat.backupCmdChCtrlInfos[{i}].ctrlMode",
                    f"Backup Channel {channel_num} Mode",
                    const.CHANNEL_CONTROL_MODE_OPTIONS,
                    self._make_backup_mode_command(i),
                    enabled=False,
                ).with_icon("mdi:battery-charging")
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
                lambda _: self._create_mqtt_command(cmdSet=1, cmdId=20, params={}),
                enabled=False,
            ).with_icon("mdi:restart"),

            # ===== Self-Check Button (cmdSet: 11, id: 112) =====
            EnabledButtonEntity(
                client,
                self,
                "selfCheck",
                "Start Self-Check",
                lambda _: self._create_mqtt_command(
                    cmdSet=11,
                    cmdId=112,
                    params={"selfCheckType": 1},
                ),
                enabled=False,
            ).with_icon("mdi:check-circle-outline"),

            # ===== RTC Time Sync Button (cmdSet: 11, id: 3) =====
            EnabledButtonEntity(
                client,
                self,
                "rtcSync",
                "Sync RTC Time",
                lambda _: self._create_rtc_sync_command(),
            ).with_icon("mdi:clock-sync"),

            # ===== Configuration Status Set Button (cmdSet: 11, id: 7) =====
            EnabledButtonEntity(
                client,
                self,
                "cfgComplete",
                "Mark Configuration Complete",
                lambda _: self._create_mqtt_command(
                    cmdSet=11,
                    cmdId=7,
                    params={"cfgSta": 1},
                ),
                enabled=False,
            ).with_icon("mdi:check-bold"),

            # ===== Get Configuration Status Button (cmdSet: 11, id: 8) =====
            EnabledButtonEntity(
                client,
                self,
                "getCfgSta",
                "Get Configuration Status",
                lambda _: self._create_mqtt_command(cmdSet=11, cmdId=8, params={}),
                enabled=False,
            ).with_icon("mdi:cog-refresh"),
        ]

    def texts(self, client: EcoflowApiClient) -> list[TextEntity]:
        """Return all text entities for the Smart Home Panel."""
        texts = []

        # ===== Circuit Name Configuration (cmdSet: 11, id: 32) =====
        # Allows setting custom names for each load channel
        for i in range(10):
            channel_num = i + 1
            texts.append(
                TextConfigEntity(
                    client,
                    self,
                    f"'loadChInfo.info'[{i}].chName",
                    f"Circuit {channel_num} Name",
                    self._make_circuit_name_command(i),
                    enabled=False,
                    max_length=32,
                ).with_icon("mdi:rename")
            )

        return texts

    def flat_json(self):
        """
        Indicate whether the device uses flat JSON structure.

        Smart Home Panel uses hierarchical JSON for public API,
        so we return False to use quoted keys for nested access.
        """
        return False

    def _create_mqtt_command(
        self, cmdSet: int, cmdId: int, params: dict[str, Any]
    ) -> dict[str, Any]:
        """
        Create a properly formatted MQTT command with all required fields.

        Args:
            cmdSet: Command set number
            cmdId: Command ID within the set
            params: Command-specific parameters

        Returns:
            Complete MQTT command dictionary
        """
        return {
            "id": random.randint(100000, 999999),
            "moduleType": 1,
            "operateType": "TCP",
            "version": "1.0",
            "params": {
                "cmdSet": cmdSet,
                "id": cmdId,
                **params,
            },
        }

    def _create_load_channel_switch(
        self, client: EcoflowApiClient, channel_index: int, channel_num: int
    ) -> SwitchEntity:
        """
        Create a load channel on/off switch (cmdSet: 11, id: 16).

        Args:
            client: The API client
            channel_index: Channel index (0-9)
            channel_num: Channel number for display (1-10)

        Returns:
            Switch entity for controlling the load channel on/off state
        """
        return (
            EnabledEntity(
                client,
                self,
                f"heartbeat.loadCmdChCtrlInfos[{channel_index}].ctrlSta",
                f"Circuit {channel_num}",
                lambda value, ch=channel_index: self._create_mqtt_command(
                    cmdSet=11,
                    cmdId=16,
                    params={
                        "ch": ch,
                        "ctrlMode": 1,  # Manual mode
                        "sta": 1 if value else 2,  # 1=on (battery), 2=off
                    },
                ),
                True,  # enabled
                True,  # auto_enable
                1,  # enableValue (battery supply = on)
                2,  # disableValue (off)
            )
            .with_icon("mdi:electric-switch")
        )

    def _create_backup_channel_switch(
        self, client: EcoflowApiClient, channel_index: int, channel_num: int
    ) -> SwitchEntity:
        """
        Create a backup/standby channel switch (cmdSet: 11, id: 17).

        Args:
            client: The API client
            channel_index: Backup channel index (0-1)
            channel_num: Channel number for display (1-2)

        Returns:
            Switch entity for controlling the backup channel
        """
        return (
            EnabledEntity(
                client,
                self,
                f"heartbeat.backupCmdChCtrlInfos[{channel_index}].ctrlSta",
                f"Backup Channel {channel_num}",
                lambda value, idx=channel_index: self._create_mqtt_command(
                    cmdSet=11,
                    cmdId=17,
                    params={
                        "ch": 10 + idx,  # Channel 10 or 11
                        "ctrlMode": 1 if value else 0,
                        "sta": 1 if value else 0,
                    },
                ),
                True,  # enabled
                True,  # auto_enable
                1,  # enableValue
                0,  # disableValue
            )
            .with_category(EntityCategory.CONFIG)
            .with_icon("mdi:battery-charging")
        )

    def _create_circuit_mode_command(
        self, channel: int, mode: int, params: dict[str, Any]
    ) -> dict[str, Any]:
        """
        Create a circuit mode control command (cmdSet: 11, id: 16).

        The mode value is encoded as:
        - 0: Auto (ctrlMode=0)
        - 1: Grid (ctrlMode=1, sta=0)
        - 2: Battery (ctrlMode=1, sta=1)
        - 3: Off (ctrlMode=1, sta=2)

        Args:
            channel: Channel number (0-9)
            mode: Mode value (0=Auto, 1=Grid, 2=Battery, 3=Off)
            params: Current device parameters

        Returns:
            Command dictionary for circuit mode control
        """
        if mode == 0:  # Auto
            ctrl_mode = 0
            sta = params.get(f"heartbeat.loadCmdChCtrlInfos[{channel}].ctrlSta", 0)
        elif mode == 1:  # Grid
            ctrl_mode = 1
            sta = 0
        elif mode == 2:  # Battery
            ctrl_mode = 1
            sta = 1
        else:  # Off
            ctrl_mode = 1
            sta = 2

        return self._create_mqtt_command(
            cmdSet=11,
            cmdId=16,
            params={
                "ch": channel,
                "ctrlMode": ctrl_mode,
                "sta": sta,
            },
        )

    def _create_emergency_mode_command(
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

        return self._create_mqtt_command(
            cmdSet=11,
            cmdId=64,
            params={
                "isCfg": 1,
                "backupMode": backupMode,
                "overloadMode": overloadMode,
                "chSta": chSta,
            },
        )

    def _create_rtc_sync_command(self) -> dict[str, Any]:
        """
        Create RTC time sync command (cmdSet: 11, id: 3).

        Syncs the device RTC with the current system time.

        Returns:
            Command dictionary for RTC time update
        """
        from datetime import datetime

        now = datetime.now()
        return self._create_mqtt_command(
            cmdSet=11,
            cmdId=3,
            params={
                "year": now.year,
                "month": now.month,
                "day": now.day,
                "hour": now.hour,
                "min": now.minute,
                "sec": now.second,
                "week": now.isoweekday(),
            },
        )

    # ===== Factory methods for creating channel-specific commands =====
    # These methods return 1 or 2 parameter callables that can be used with
    # the entity command system, which only supports commands with 1 or 2 parameters.

    def _make_channel_current_command(self, channel: int):
        """Create a command factory for channel current configuration."""
        def command(value: int, params: dict[str, Any]) -> dict[str, Any]:
            return self._create_mqtt_command(
                cmdSet=11,
                cmdId=20,
                params={"chNum": channel, "cur": int(value)},
            )
        return command

    def _make_circuit_mode_command_factory(self, channel: int):
        """Create a command factory for circuit mode control."""
        def command(value: int, params: dict[str, Any]) -> dict[str, Any]:
            return self._create_circuit_mode_command(
                channel=channel, mode=int(value), params=params
            )
        return command

    def _make_backup_mode_command(self, channel: int):
        """Create a command factory for backup channel mode control."""
        def command(value: int, params: dict[str, Any]) -> dict[str, Any]:
            return self._create_mqtt_command(
                cmdSet=11,
                cmdId=17,
                params={"ch": 10 + channel, "ctrlMode": int(value), "sta": 1},
            )
        return command

    def _make_emergency_channel_command(self, channel: int):
        """Create a command factory for emergency channel enable."""
        def command(value: int, params: dict[str, Any]) -> dict[str, Any]:
            return self._create_mqtt_command(
                cmdSet=11,
                cmdId=26,
                params={"chNum": channel, "isEnable": int(value)},
            )
        return command

    def _make_channel_switch_command(self, channel: int):
        """Create a command factory for channel on/off switch."""
        def command(value: int) -> dict[str, Any]:
            return self._create_mqtt_command(
                cmdSet=11,
                cmdId=16,
                params={"ch": channel, "ctrlMode": 1, "sta": 2 if value == 0 else 1},
            )
        return command

    def _make_circuit_name_command(self, channel: int):
        """Create a command factory for circuit name configuration."""
        def command(value: str, params: dict[str, Any]) -> dict[str, Any]:
            return self._create_mqtt_command(
                cmdSet=11,
                cmdId=32,
                params={
                    "chNum": channel,
                    "info": {
                        "chName": value,
                        "iconInfo": int(params.get(f"loadChInfo.info[{channel}].iconNum", 0)),
                    },
                },
            )
        return command
