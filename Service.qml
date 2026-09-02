import QtQuick
import Quickshell
import Quickshell.Io
import Quickshell.Services.UPower
import "BatteryModel.js" as BatteryModel

Item {
  id: root

  property var shell: null
  property string omarchyPath: Quickshell.env("OMARCHY_PATH")

  readonly property int batteryThreshold: 10
  property string pendingPowerSource: ""
  property bool z13Present: false

  PersistentProperties {
    id: persisted
    reloadableId: "omarchy-battery"
    property bool notifiedLowBattery: false
  }

  function batteryPercentage() {
    return BatteryModel.batteryPercentage(UPower.displayDevice)
  }

  function isDischarging() {
    return BatteryModel.isDischarging(UPower.displayDevice, UPower.onBattery, UPowerDeviceState.Discharging)
  }

  function checkBattery() {
    var state = BatteryModel.shouldWarnLowBattery(UPower.displayDevice, UPower.onBattery, UPowerDeviceState.Discharging, batteryThreshold, persisted.notifiedLowBattery)
    persisted.notifiedLowBattery = state.notifiedLowBattery
    if (state.notify) sendLowBatteryWarning(state.level)
  }

  readonly property string ioScript: String(Qt.resolvedUrl("z13-io.py")).replace(/^file:\/\//, "")

  function ioCmd() {
    var a = ["/usr/bin/python3", root.ioScript]
    for (var i = 0; i < arguments.length; i++) a.push(arguments[i])
    return a
  }

  function sendLowBatteryWarning(level) {
    if (warningProcess.running) return
    warningProcess.command = root.ioCmd("run", "--timeout", "3", "--", "omarchy-battery-low", String(level))
    warningProcess.running = true
  }

  function applyPowerProfile() {
    if (root.z13Present) return
    pendingPowerSource = UPower.onBattery ? "battery" : "ac"
    if (!powerProfileProcess.running) runPendingPowerProfile()
  }

  function runPendingPowerProfile() {
    powerProfileProcess.command = root.ioCmd("run", "--timeout", "3", "--", "omarchy-powerprofiles-set", pendingPowerSource)
    pendingPowerSource = ""
    powerProfileProcess.running = true
  }

  Process {
    id: statusProc
    command: root.ioCmd("read-status")
    stdout: StdioCollector {
      waitForEnd: true
      onStreamFinished: {
        try {
          var s = JSON.parse(String(text || "{}"))
          root.z13Present = !!(s && s.mode)
        } catch (e) {
          root.z13Present = false
        }
      }
    }
  }

  Timer {
    interval: 2000
    running: true
    repeat: true
    triggeredOnStart: true
    onTriggered: if (!statusProc.running) statusProc.running = true
  }

  Process { id: warningProcess }

  Process {
    id: powerProfileProcess
    onExited: if (root.pendingPowerSource !== "") root.runPendingPowerProfile()
  }

  Timer {
    interval: 30000
    running: true
    repeat: true
    triggeredOnStart: true
    onTriggered: root.checkBattery()
  }

  Connections {
    target: UPower
    function onOnBatteryChanged() {
      root.checkBattery()
      root.applyPowerProfile()
    }
  }
}
