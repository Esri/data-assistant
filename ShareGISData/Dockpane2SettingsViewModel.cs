﻿/***
Copyright 2016 Esri

   Licensed under the Apache License, Version 2.0 (the "License");
   you may not use this file except in compliance with the License.
   You may obtain a copy of the License at

       http://www.apache.org/licenses/LICENSE-2.0

   Unless required by applicable law or agreed to in writing, software
   distributed under the License is distributed on an "AS IS" BASIS,
   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
   See the License for the specific language governing permissions and
   limitations under the License.​
 ***/
using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Threading.Tasks;
using ArcGIS.Desktop.Framework;
using ArcGIS.Desktop.Framework.Contracts;

namespace DataAssistant
{
    internal class Dockpane2SettingsViewModel : DockPane
    {
        private const string _dockPaneID = "DataAssistant_Dockpane2Settings";

        protected Dockpane2SettingsViewModel() { }

        /// <summary>
        /// Show the DockPane.
        /// </summary>
        internal static void Show()
        {
            DockPane pane = FrameworkApplication.DockPaneManager.Find(_dockPaneID);
            if (pane == null)
                return;

            pane.Activate();
        }
        internal static void doHide()
        {
            DockPane pane = FrameworkApplication.DockPaneManager.Find(_dockPaneID);

            if (pane == null)
                return;
            pane.Hide();
        }
        /// <summary>
        /// Text shown near the top of the DockPane.
        /// </summary>
        private string _heading = "Settings";
        public string Heading
        {
            get { return _heading; }
            set
            {
                SetProperty(ref _heading, value, () => Heading);
            }
        }
    }

    /// <summary>
    /// Button implementation to show the DockPane.
    /// </summary>
    internal class Dockpane2Settings_ShowButton : Button
    {
        private const string _dockPaneID = "DataAssistant_Dockpane2Settings";
        protected override void OnClick()
        {
            DockPane pane = FrameworkApplication.DockPaneManager.Find(_dockPaneID);
            try
            {
                //if (pane.IsVisible)
                //    Dockpane2SettingsViewModel.doHide();
                //else
                Dockpane2SettingsViewModel.Show();
            }
            catch { }
        }
    }
}
