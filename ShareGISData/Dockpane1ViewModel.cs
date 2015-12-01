using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Threading.Tasks;
using ArcGIS.Desktop.Framework;
using ArcGIS.Desktop.Framework.Contracts;

namespace ShareGISData
{
    internal class Dockpane1ViewModel : DockPane
    {
        private const string _dockPaneID = "ShareGISData_Dockpane1";

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
        private string _heading = "Field Mapper";
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
    internal class Dockpane1_ShowButton : Button
    {
        protected override void OnClick()
        {
            Dockpane1ViewModel.Show();
        }
    }
    internal class Dockpane1_PreviewButton : Button
    {
        protected override void OnClick()
        {
            System.Windows.Forms.MessageBox.Show("'Preview' is not implemented yet");
        }
    }
    internal class Dockpane1_PublishButton : Button
    {
        protected override void OnClick()
        {
            System.Windows.Forms.MessageBox.Show("'Publish' is not implemented yet");
        }
    }
    internal class Dockpane1_AggregateButton : Button
    {
        protected override void OnClick()
        {
            System.Windows.Forms.MessageBox.Show("'Aggregate' is not implemented yet");
        }
    }
}
