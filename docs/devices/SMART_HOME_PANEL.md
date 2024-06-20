## SMART_HOME_PANEL

*Sensors*
- AC1 Battery Level (`energyInfos[0].batteryPercentage`)
- AC1 Out Power (`energyInfos[0].outputPower`)
- AC1 In Power (`energyInfos[0].lcdInputWatts`)
- AC1 Charge Time (`energyInfos[0].chargeTime`)
- AC1 Discharge Time (`energyInfos[0].dischargeTime`)
- AC1 Connected (`energyInfos[0].stateBean.isConnect`)
- AC1 Enabled (`energyInfos[0].stateBean.isEnable`)
- AC2 Battery Level (`energyInfos[1].batteryPercentage`)
- AC2 Out Power (`energyInfos[1].outputPower`)
- AC2 In Power (`energyInfos[1].lcdInputWatts`)
- AC2 Charge Time (`energyInfos[1].chargeTime`)
- AC2 Discharge Time (`energyInfos[1].dischargeTime`)
- AC2 Connected (`energyInfos[1].stateBean.isConnect`)
- AC2 Enabled (`energyInfos[1].stateBean.isEnable`)
- Status

*Switches*
- AC1 Charging (`energyInfos[0].stateBean.isGridCharge` -> `{"moduleType": 0, "operateType": "TCP", "params": {"sta": "VALUE", "ctrlMode": "VALUE", "ch": 10, "cmdSet": 11, "id": 17}}`)
- AC2 Charging (`energyInfos[1].stateBean.isGridCharge` -> `{"moduleType": 0, "operateType": "TCP", "params": {"sta": "VALUE", "ctrlMode": "VALUE", "ch": 11, "cmdSet": 11, "id": 17}}`)

*Sliders (numbers)*
- Max Charge Level (`forceChargeHigh` -> `{"moduleType": 0, "operateType": "TCP", "params": {"discLower": 0, "forceChargeHigh": "VALUE", "cmdSet": 11, "id": 29}}` [50 - 100])
- Max Charge Level (`discLower` -> `{"moduleType": 0, "operateType": "TCP", "params": {"discLower": "VALUE", "forceChargeHigh": 100, "cmdSet": 11, "id": 29}}` [0 - 30])

*Selects*
- Circuit 1 Mode (`loadCmdChCtrlInfos[0]` -> `{"moduleType": 0, "operateType": "TCP", "params": {"sta": "VALUE", "ctrlMode": "VALUE", "ch": 0, "cmdSet": 11, "id": 16}}` [Auto ({'sta': 0, 'ctrlMode': 0}), Grid ({'sta': 0, 'ctrlMode': 1}), Battery ({'sta': 1, 'ctrlMode': 1}), Off ({'sta': 2, 'ctrlMode': 1})])
- Circuit 2 Mode (`loadCmdChCtrlInfos[1]` -> `{"moduleType": 0, "operateType": "TCP", "params": {"sta": "VALUE", "ctrlMode": "VALUE", "ch": 1, "cmdSet": 11, "id": 16}}` [Auto ({'sta': 0, 'ctrlMode': 0}), Grid ({'sta': 0, 'ctrlMode': 1}), Battery ({'sta': 1, 'ctrlMode': 1}), Off ({'sta': 2, 'ctrlMode': 1})])
- Circuit 3 Mode (`loadCmdChCtrlInfos[2]` -> `{"moduleType": 0, "operateType": "TCP", "params": {"sta": "VALUE", "ctrlMode": "VALUE", "ch": 2, "cmdSet": 11, "id": 16}}` [Auto ({'sta': 0, 'ctrlMode': 0}), Grid ({'sta': 0, 'ctrlMode': 1}), Battery ({'sta': 1, 'ctrlMode': 1}), Off ({'sta': 2, 'ctrlMode': 1})])
- Circuit 4 Mode (`loadCmdChCtrlInfos[3]` -> `{"moduleType": 0, "operateType": "TCP", "params": {"sta": "VALUE", "ctrlMode": "VALUE", "ch": 3, "cmdSet": 11, "id": 16}}` [Auto ({'sta': 0, 'ctrlMode': 0}), Grid ({'sta': 0, 'ctrlMode': 1}), Battery ({'sta': 1, 'ctrlMode': 1}), Off ({'sta': 2, 'ctrlMode': 1})])
- Circuit 5 Mode (`loadCmdChCtrlInfos[4]` -> `{"moduleType": 0, "operateType": "TCP", "params": {"sta": "VALUE", "ctrlMode": "VALUE", "ch": 4, "cmdSet": 11, "id": 16}}` [Auto ({'sta': 0, 'ctrlMode': 0}), Grid ({'sta': 0, 'ctrlMode': 1}), Battery ({'sta': 1, 'ctrlMode': 1}), Off ({'sta': 2, 'ctrlMode': 1})])
- Circuit 6 Mode (`loadCmdChCtrlInfos[5]` -> `{"moduleType": 0, "operateType": "TCP", "params": {"sta": "VALUE", "ctrlMode": "VALUE", "ch": 5, "cmdSet": 11, "id": 16}}` [Auto ({'sta': 0, 'ctrlMode': 0}), Grid ({'sta': 0, 'ctrlMode': 1}), Battery ({'sta': 1, 'ctrlMode': 1}), Off ({'sta': 2, 'ctrlMode': 1})])
- Circuit 7 Mode (`loadCmdChCtrlInfos[6]` -> `{"moduleType": 0, "operateType": "TCP", "params": {"sta": "VALUE", "ctrlMode": "VALUE", "ch": 6, "cmdSet": 11, "id": 16}}` [Auto ({'sta': 0, 'ctrlMode': 0}), Grid ({'sta': 0, 'ctrlMode': 1}), Battery ({'sta': 1, 'ctrlMode': 1}), Off ({'sta': 2, 'ctrlMode': 1})])
- Circuit 8 Mode (`loadCmdChCtrlInfos[7]` -> `{"moduleType": 0, "operateType": "TCP", "params": {"sta": "VALUE", "ctrlMode": "VALUE", "ch": 7, "cmdSet": 11, "id": 16}}` [Auto ({'sta': 0, 'ctrlMode': 0}), Grid ({'sta': 0, 'ctrlMode': 1}), Battery ({'sta': 1, 'ctrlMode': 1}), Off ({'sta': 2, 'ctrlMode': 1})])
- Circuit 9 Mode (`loadCmdChCtrlInfos[8]` -> `{"moduleType": 0, "operateType": "TCP", "params": {"sta": "VALUE", "ctrlMode": "VALUE", "ch": 8, "cmdSet": 11, "id": 16}}` [Auto ({'sta': 0, 'ctrlMode': 0}), Grid ({'sta': 0, 'ctrlMode': 1}), Battery ({'sta': 1, 'ctrlMode': 1}), Off ({'sta': 2, 'ctrlMode': 1})])
- Circuit 10 Mode (`loadCmdChCtrlInfos[9]` -> `{"moduleType": 0, "operateType": "TCP", "params": {"sta": "VALUE", "ctrlMode": "VALUE", "ch": 9, "cmdSet": 11, "id": 16}}` [Auto ({'sta': 0, 'ctrlMode': 0}), Grid ({'sta': 0, 'ctrlMode': 1}), Battery ({'sta': 1, 'ctrlMode': 1}), Off ({'sta': 2, 'ctrlMode': 1})])


