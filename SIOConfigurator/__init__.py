# coding=utf-8
from __future__ import absolute_import
import octoprint.plugin
from octoprint.util import fqfn

from . import IOAssignment, SIOTypeConstant
import threading
import time


class SIOConfigurator(
    octoprint.plugin.SettingsPlugin,
    octoprint.plugin.AssetPlugin,
    octoprint.plugin.TemplatePlugin,
    octoprint.plugin.StartupPlugin,
    octoprint.plugin.SimpleApiPlugin,
):
    def __init__(self):
        self.has_SIOC = False
        self.available_plugins = dict()
        self.IOState = ""
        self.IOStatus = []
        self.SIOConfiguration = []
        self.SIO_Assignments = []
        self.SIO_TypeConstants = []
        self.siocontrol_helper = None
        self.RequireTC = True  # have to get a reading of the types to be ready for reconfig and before we get current IT assignments
        self.RequireIT = True  # have to get a reading to be ready for reconfig.
        self.RequireVC = True  # have check to see if this controler will even respond correctly to the TC and IT commands.
        self.compatability = ["SIO_ESP32WRM_Relay_X2 1.1.6", "SIO_ESP12F_Relay_X2 1.0.10", "SIO_Arduino_General 1.0.11"]
        self.firmwareVersion = ""
        self.compatabible = False
        self.isAssignmentChanged = False
        return

    def get_settings_defaults(self):
        return dict(
            sioassignments=[],
            siotypeconstants=[],
        )

    def reload_settings(self):
        for k, v in self.get_settings_defaults().items():
            if type(v) is str:
                v = self._settings.get([k])
            elif type(v) is int:
                v = self._settings.get_int([k])
            elif type(v) is float:
                v = self._settings.get_float([k])
            elif type(v) is bool:
                v = self._settings.get_boolean([k])

    def get_template_configs(self):
        return [dict(type="settings", custom_bindings=True, template="SIOConfigurator_settings.jinja2",),]

    def get_template_vars(self):
        return {
            "SIOAssignments": self._settings.get(["sioassignments"]),
            "SIOTypeConstants": self._settings.get(["siotypeconstants"]),
            "SIOCompatability": self.compatability,
            "SIOCompatible": self.compatabible,
            "SIOFirmwareVersion": self.firmwareVersion,
        }

    def on_settings_initialized(self):
        return super().on_settings_initialized()

    def on_settings_save(self, data):
        if self.compatabible is False:
            self._logger.error("SIO Controller is not Compatible with this Plugin.\n\tPlease update the controller firmware to a compatible version.")
            return

        if self.isAssignmentChanged is False:
            self._logger.debug("No changes to IO Configuration were made.")
            return

        # currently there are no local(to OctoPrint) settings to save. IO config is sent to the controller and saved in the controller.
        sioPattern = "CIO "
        idx = 0
        for ioa in data["sioassignments"]:
            if idx == int(ioa["index"]):
                if idx > 0:  # only add the comma where needed
                    sioPattern = sioPattern + ","
                if int(ioa["iotype"]) < 10:
                    sioPattern += "0" + ioa["iotype"]
                else:
                    sioPattern += ioa["iotype"]

                idx = idx+1  # must increment check index
            else:
                data["sioassignments"] = []
                data["siotypeconstants"] = []
                self.RequireIT = True
                self.RequireTC = True
                self._logger.Exception("New IO Pattern data is not in the expected order, Pattern will not be saved: {}!={}".format(idx, ioa["index"]))
                return

        self.make_Serial_Request("EIO")  # stop auto reporting while we update the IO configuration.

        sioSaveCommand = "SIO"
        self.make_Serial_Request(sioPattern)  # make request to change IO Configuration.
        self._logger.info("Settings sent to SIO Device using this command: {}".format(sioPattern))
        self.make_Serial_Request(sioSaveCommand)  # make request to save current IO Config to controller local memory.
        self._logger.info("Settings saved to SIO Device using this command: {}".format(sioSaveCommand))
        self._logger.info("Resetting request for IO config.")
        data["sioassignments"] = []
        data["siotypeconstants"] = []
        self.RequireIT = True
        self.RequireTC = True
        self.isAssignmentChanged = False
        self._logger.info("Resetting IO Controller")
        resetThread = threading.Thread(target=self.resetIOController)
        resetThread.start()
        # self.make_Serial_Request("reset")  # reset the IO controller to apply the new configuration.
        octoprint.plugin.SettingsPlugin.on_settings_save(self, data)
        # removed do not need because we are resetting the controller now.
        # self.make_Serial_Request("BIO")# start auto reporting while we update the IO configuration.

        return super().on_settings_save(data)

    def resetIOController(self):
        time.sleep(5)
        self._logger.info("Calling reset to IO Controller to apply new configuration.")
        self.make_Serial_Request("reset")

    def on_after_startup(self):
        try:
            self.siocontrol_helper = self._plugin_manager.get_helpers("siocontrol")
            if not self.siocontrol_helper:
                self._logger.warning("siocontrol Plugin not found.")
            elif "register_plugin" not in self.siocontrol_helper.keys():
                self._logger.warning("The version of siocontrol that is installed does not support plugin registration. Version 1.0.1 or higher is required.")
            else:
                self.siocontrol_helper["register_plugin"](self)
                self._logger.info("Regestered as Sub Plugin to SIO Control")

        except Exception as err:
            self._logger.exception("Exception: {}, {}".format(err, type(err)))

    def get_api_commands(self):
        return dict(
            getIOConfig="", AssignmentChanged=""
        )

    def on_api_command(self, command, data):
        if command == "getIOConfig":
            self.isAssignmentChanged = False
            return self.get_template_vars()
        elif command == "AssignmentChanged":
            self._logger.info("AssignmentChanged")
            self.isAssignmentChanged = True
            return "OK"

# SIO Related Calls
    def make_Serial_Request(self, command):
        callback = self.siocontrol_helper["send_sio_command"]
        try:
            self.IOState = callback(command)

        except Exception:
            self._logger.exception("Error while executing callback {}".format(callback), extra={"callback": fqfn(callback)},)

# SIO Events
    def hook_sio_serial_stream(self, line):
        self._logger.debug("SIOConfiguration hook_sio_serial_Stream: {}".format(line))

        if line[:2] == "RR":  # means it is ready for commands

            if self.RequireVC:
                self.make_Serial_Request("VC")  # get IO Version info
                self.RequireVC = False  # do nothing for now. just set this to true as it is true.
            else:
                if self.RequireTC:
                    self.make_Serial_Request("TC")  # get type list.
                    self.RequireTC = False
                else:
                    if self.RequireIT:
                        self.make_Serial_Request("IOT")  # get current IOT assignments
                        self.RequireIT = False

        elif line[:2] == "TC":
            self.RequireTC = False
            self._logger.debug("***********************************************************************************************")
            self._logger.debug("SIO Configurator capture IO Types as: {}".format(line))
            self._logger.debug("***********************************************************************************************")
            TC = line[3:].split(',')
            self.SIO_TypeConstants.clear()
            istc = []
            for tc in TC:
                tcnv = tc.split(':')
                sioTC = SIOTypeConstant.SIOTypeConstant(self, tcnv[0], tcnv[1])
                istc.append({"typestring": sioTC.TypeString, "typeid": sioTC.TypeId})
                self.SIO_TypeConstants.append(sioTC)
                self._logger.info("IO Type [{}] is named [{}]".format(sioTC.TypeId, sioTC.TypeString))

            self._settings.set(["siotypeconstants"], istc)
            self.RequireTC = len(self.SIO_TypeConstants) == 0

        elif line[:2] == "IT":

            # this is the current configuation for IO.
            self._logger.debug("***********************************************************************************************")
            self._logger.debug("SIO Configurator capture IO Types as: {}".format(line))
            self._logger.debug("***********************************************************************************************")
            IOTypes = line[3:].split(',')
            idx = 0
            self.SIO_Assignments.clear()
            iosa = []  # self._settings.get(["sioassignments"])
            for iot in IOTypes:
                ioa = IOAssignment.IOAssignment(self, idx, iot)
                if iot != "":
                    iosa.append({"index": idx, "iotype": iot})
                    self.SIO_Assignments.append(ioa)
                    self._logger.debug("IO point [{}] is of Types [{}]".format(ioa.Index, ioa.IOType))
                    idx = idx+1

            self._settings.set(["sioassignments"], iosa)
            self.RequireIT = len(self.SIO_Assignments) == 0

        elif line[:2] == "VI":  # VC is the command that is sent for this response
            self.RequireVC = False
            self._logger.debug("***********************************************************************************************")
            self._logger.debug("SIO Configurator capture Version as: {}".format(line))
            self._logger.debug("***********************************************************************************************")
            if line[3:] in self.compatability:
                self.firmwareVersion = line[3:]
                # self.has_SIOC = True
                self._logger.info("SIO Controller is Compatible with this Plugin.")
                self.compatabible = True
            else:
                # self.has_SIOC = False
                self._logger.error("SIO Controller is not Compatible with this Plugin.\n\tPlease update the controller firmware to a compatible version.")
                self.compatabible = False

    def sioStateChanged(self, newIOstate, newIOStatus):
        previousIOState = self.IOState
        # previousIOStatus = self.IOStatus
        self.IOState = newIOstate
        self.IOStatus = newIOStatus
        if previousIOState is not None:
            self._logger.debug("sioStateChanged: {}".format(newIOstate))

    def get_assets(self):
        # Define your plugin's asset files to automatically include in the
        # core UI here.
        return {
            "js": ["js/SIOConfigurator.js"],
            "css": ["css/SIOConfigurator.css"],
            "less": ["less/SIOConfigurator.less"]
        }

    # ~~ Softwareupdate hook

    def get_update_information(self):
        # Define the configuration for your plugin to use with the Software Update
        # Plugin here. See https://docs.octoprint.org/en/master/bundledplugins/softwareupdate.html
        # for details.
        return {
            "SIOConfigurator": {
                "displayName": "SIO Configurator Sub PlugIn",
                "displayVersion": self._plugin_version,

                # version check: github repository
                "type": "github_release",
                "user": "jcassel",
                "repo": "OctoPrint-SIOConfigurator",
                "current": self._plugin_version,

                # update method: pip
                "pip": "https://github.com/jcassel/OctoPrint-SIOConfigurator/archive/{target_version}.zip",
            }
        }


# If you want your plugin to be registered within OctoPrint under a different name than what you defined in setup.py
# ("OctoPrint-PluginSkeleton"), you may define that here. Same goes for the other metadata derived from setup.py that
# can be overwritten via __plugin_xyz__ control properties. See the documentation for that.
__plugin_name__ = "SIO Configurator"


# Set the Python version your plugin is compatible with below. Recommended is Python 3 only for all new plugins.
# OctoPrint 1.4.0 - 1.7.x run under both Python 3 and the end-of-life Python 2.
# OctoPrint 1.8.0 onwards only supports Python 3.
__plugin_pythoncompat__ = ">=3,<4"  # Only Python 3


def __plugin_load__():
    global __plugin_implementation__
    __plugin_implementation__ = SIOConfigurator()

    global __plugin_hooks__
    __plugin_hooks__ = {
        "octoprint.plugin.softwareupdate.check_config": __plugin_implementation__.get_update_information
    }
