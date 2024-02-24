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


        // TODO: Implement your plugin's view model here.
        self.onBeforeBinding = function () {
            self.settings = self.settingsViewModel.settings;
            self.vmsioassignments(self.settingsViewModel.settings.plugins.SIOConfigurator.sioassignments.slice(0));
            self.vmsiotypeconstants(self.settingsViewModel.settings.plugins.SIOConfigurator.siotypeconstants.slice(0));
            //self.vmsioconfiguration(self.settings.plugins.siocontrol.sio_configurations.slice(0)); //this is for/from SIO Parent plugin.
        };

        self.onSettingsBeforeSave = function () {
            self.settingsViewModel.settings.plugins.SIOConfigurator.sioassignments(self.vmsioassignments.slice(0));
            //self.settingsViewModel.settings.plugins.SIOConfigurator.siotypeconstants(self.siotypeconstants.slice(0));
        };

        self.onSettingsHidden = function () {
            self.vmsioassignments(self.settingsViewModel.settings.plugins.SIOConfigurator.sioassignments.slice(0));
            //self.vmsioconfiguration(self.settings.plugins.siocontrol.sio_configurations.slice(0));  //this is for/from SIO Parent plugin.        };
        };
        
        self.onSettingsShown = function () {
            self.vmsioassignments(self.settingsViewModel.settings.plugins.SIOConfigurator.sioassignments.slice(0));
            self.vmsiotypeconstants(self.settingsViewModel.settings.plugins.SIOConfigurator.siotypeconstants.slice(0));
            //self.vmsioconfiguration(self.settings.plugins.siocontrol.sio_configurations.slice(0));  //this is for/from SIO Parent plugin.
        };
        
        

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