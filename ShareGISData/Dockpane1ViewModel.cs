using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Threading.Tasks;
using ArcGIS.Desktop.Framework;
using ArcGIS.Desktop.Framework.Contracts;
using ArcGIS.Desktop.Core.Geoprocessing;
using ArcGIS.Desktop.Core;
using ArcGIS.Desktop.Catalog;

namespace DataAssistant
{
    internal class Dockpane1ViewModel : DockPane
    {
        private const string _dockPaneID = "DataAssistant_Dockpane1";

        protected Dockpane1ViewModel() { }

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
        private string _heading = "Configure Data Mapping";
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
    internal class Dockpane1_CreateFile : Button
    {
        protected override void OnClick()
        {
            setupGP.init();
            string source = "";
            string target = "";
            string file = System.IO.Path.Combine(Project.Current.HomeFolderPath,"SourceTarget.xml");

            var param_values = Geoprocessing.MakeValueArray(source,target,file);

            Geoprocessing.OpenToolDialog(setupGP.getToolbox("SourceTargetMapping"), param_values);
        }
    }
    
    internal class Dockpane1_ShowButton : Button
    {
        private const string _dockPaneID = "DataAssistant_Dockpane1";
        string fileloc = setupGP.init();
        protected override void OnClick()
        {
            DockPane pane = FrameworkApplication.DockPaneManager.Find(_dockPaneID);
            try
            {
                if (pane.IsVisible)
                    Dockpane1ViewModel.doHide();
                else
                    Dockpane1ViewModel.Show();
            }
            catch { }
        }
    }
    internal class Dockpane1_PreviewButton : Button
    {
        protected override void OnClick()
        {
            setupGP.init();
            var param_values = Geoprocessing.MakeValueArray(DataAssistant.Dockpane1View.getXmlFileName());

            Geoprocessing.OpenToolDialog(setupGP.getToolbox("Preview"), param_values);
        }
    }
    internal class Dockpane1_AppendDataButton : Button
    {
        protected override void OnClick()
        {
            setupGP.init();
            var param_values = Geoprocessing.MakeValueArray(DataAssistant.Dockpane1View.getXmlFileName());

            Geoprocessing.OpenToolDialog(setupGP.getToolbox("AppendData"), param_values);
        }
    }
    internal class Dockpane1_ReplaceDataButton : Button
    {
        protected override void OnClick()
        {
            setupGP.init();
            var param_values = Geoprocessing.MakeValueArray(DataAssistant.Dockpane1View.getXmlFileName());

            Geoprocessing.OpenToolDialog(setupGP.getToolbox("ReplaceData"), param_values);
        }
    }
    internal class setupGP : Button
    {
        public static string AddinAssemblyLocation()
        {
            var asm = System.Reflection.Assembly.GetExecutingAssembly();
            return System.IO.Path.GetDirectoryName(
                                Uri.UnescapeDataString(
                                        new Uri(asm.CodeBase).LocalPath));
        }
        static string _gpFolder = System.IO.Path.Combine(AddinAssemblyLocation(),"GPTools");
        public static string init()
        {
            var projectFolders = Project.Current.GetItems<FolderConnectionProjectItem>();
            bool found = false;
            foreach (var FolderItem in projectFolders)
            {
                if (FolderItem.Path == _gpFolder)
                    found = true;
            }
            if (!found)
                Project.Current.AddAsync(ItemFactory.Create(_gpFolder));

            //var pth = Project.Current.DefaultToolboxPath;
                
            return _gpFolder;
        }
        public static string getToolbox(string toolname)
        {
            string gpref = System.IO.Path.Combine(setupGP._gpFolder, "DataLoadingAssistant.tbx", toolname);
            return gpref;
        }
        public static string getConfigFileName() 
        {
            //Dockpane1View.getXmlFileName();
            return "";
        }
    }
}
