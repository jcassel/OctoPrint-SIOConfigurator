$(function() {
    function SIOConfiguratorViewModel(parameters) {
        var self = this;
        
        // assign the injected parameters, e.g.:
        self.loginStateViewModel = parameters[0];
        self.settingsViewModel = parameters[1];
        self.accessViewModel = parameters[2];
        self.controlViewModel = parameters[3];
        self.settings = undefined;
        self.vmsioassignments = ko.observableArray();
        self.vmsiotypeconstants = ko.observableArray();
        self.ForceRePullIOAssignments = ko.observable(false);
        self.derivedStatus = ko.observable();
        self.sioconfigur_DStat = undefined;
        self.SIOReportedCompatibleVersion = ko.observable();
        self.SIOFirmwareVersion = ko.observable();

        // TODO: Implement your plugin's view model here.
        self.onBeforeBinding = function () {
            self.settings = self.settingsViewModel.settings;
            self.vmsioassignments(self.settingsViewModel.settings.plugins.SIOConfigurator.sioassignments.slice(0));
            self.vmsiotypeconstants(self.settingsViewModel.settings.plugins.SIOConfigurator.siotypeconstants.slice(0));
            //self.derivedStatus("--na--");
            self.getDeriveStatus();

        };

        self.onSettingsBeforeSave = function () {
            
            if(self.sioconfigur_DStat !== 'undefined') {
                clearInterval(self.sioconfigur_DStat); //stop existing polling.
            }
            self.settingsViewModel.settings.plugins.SIOConfigurator.sioassignments(self.vmsioassignments.slice(0));
        };

        self.onSettingsHidden = function () {
            self.vmsioassignments(self.settingsViewModel.settings.plugins.SIOConfigurator.sioassignments.slice(0));
            if(self.sioconfigur_DStat !== 'undefined') {
                clearInterval(self.sioconfigur_DStat); //stop existing polling.
            }
        };
        
        self.onSettingsShown = function () {
            self.RefreshIOAssignments();
            if(self.sioconfigur_DStat !== 'undefined') {
                clearInterval(self.sioconfigur_DStat); //stop existing polling.
            }

            self.sioconfigur_DStat = setInterval(function () { //start the updated one.
                self.getDeriveStatus();
            }, 3000); //3 sec
            //self.vmsioassignments(self.settingsViewModel.settings.plugins.SIOConfigurator.sioassignments.slice(0));
            //self.vmsiotypeconstants(self.settingsViewModel.settings.plugins.SIOConfigurator.siotypeconstants.slice(0));
            self.jsGetDisplayVars();
            
        };
        
        self.RefreshIOAssignments = function () {
            OctoPrint.simpleApiCommand("SIOConfigurator", "getIOConfig", {force: self.ForceRePullIOAssignments()}).then(function (templateVars) {
                self.vmsioassignments(templateVars.SIOAssignments);
                self.vmsiotypeconstants(templateVars.SIOTypeConstants);
            });
        };

        self.AssignmentChanged = function (obj, event) {
            if(!event.origenalEvent){
                OctoPrint.simpleApiCommand("SIOConfigurator", "AssignmentChanged", {}).then(function (isOK) {
                    result = isOK;
                    result2 = result;
                });
            }
        };

        self.jsGetDisplayVars   = function () {
            OctoPrint.simpleApiCommand("SIOConfigurator", "GetDisplayVars", {}).then(function (templateVars) {
                //self.vmsioassignments(templateVars.SIOAssignments);
                //self.vmsiotypeconstants(templateVars.SIOTypeConstants);
                self.SIOReportedCompatibleVersion(templateVars.SIOReportedCompatibleVersion);
                self.SIOFirmwareVersion(templateVars.SIOFirmwareVersion);
            });
        }



        self.SaveIOAssignments = function () {
            OctoPrint.simpleApiCommand("SIOConfigurator", "SaveIOAssignments", {sioassignments : self.vmsioassignments()}).then(function (result) {
                self.derivedStatus("Working");
            });
        };

        self.getDeriveStatus = function () {
            OctoPrint.simpleApiCommand("SIOConfigurator", "getDerivedStatus", {}).then(function (status) {
                self.derivedStatus(status.derivedStatus);
            });
        };

        self.ResetSIOController = function () {
            OctoPrint.simpleApiCommand("SIOConfigurator", "ResetSIOController", {}).then(function (result) {
                self.derivedStatus("Reset Requested");
            });
        }


        self.getIOTypeNames - function(){
            return self.vmsiotypes;
        };
    }

    /* view model class, parameters for constructor, container to bind to
     * Please see http://docs.octoprint.org/en/master/plugins/viewmodels.html#registering-custom-viewmodels for more details
     * and a full list of the available options.
     */
    OCTOPRINT_VIEWMODELS.push({
        construct: SIOConfiguratorViewModel,
        // ViewModels your plugin depends on, e.g. loginStateViewModel, settingsViewModel, ...
        dependencies: ["loginStateViewModel","settingsViewModel","accessViewModel", "controlViewModel"],
        // Elements to bind to, e.g. #settings_plugin_SIOReaction, #tab_plugin_SIOReaction, ...
        elements: ["#settings_plugin_SIOConfigurator"]
    });
});