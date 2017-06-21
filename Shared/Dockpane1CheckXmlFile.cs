using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Threading.Tasks;
using System.Windows;
using System.Windows.Controls;
using System.Windows.Data;
using System.Windows.Documents;
using System.Windows.Input;
using System.Windows.Media;
using System.Windows.Media.Imaging;
using System.Windows.Navigation;
using System.Windows.Shapes;
using System.Xml.Linq;
using System.Data;
using System.Collections.ObjectModel;
using System.Globalization;
using System.Windows.Controls.Primitives;

using ArcGIS.Core.Data;
using ArcGIS.Desktop.Core.Geoprocessing;
using ArcGIS.Desktop.Core;
using ArcGIS.Desktop.Catalog;
using ArcGIS.Desktop.Mapping;
using System.Xml;
using System.Xml.Xsl;
using System.Xml.XPath;

namespace DataAssistant
{
    /// <summary>
    /// Interaction logic for Dockpane1View.xaml
    /// </summary>
    public partial class Dockpane1View : UserControl
    {

        private bool checkXmlFileName(string filepath)
        {
            bool valid = false;
            bool srcValid = false;
            bool targValid = false;
            bool projValid = false;

            string _project = "//Project";
            string _source = "//Source";
            string _target = "//Target";


            if (System.IO.File.Exists(filepath))
            {
                string folder = getFolder(filepath);
                loadXml(filepath); // load the xml file but do not update the UI

                System.Xml.XmlNode project = _xml.SelectSingleNode(_project);
                if (project == null)
                    ArcGIS.Desktop.Framework.Dialogs.MessageBox.Show("Warning: Unable to locate Project xml element in folder " + folder);
                else
                    projValid = checkSourceTargetPath(folder, project.InnerText,false);

                System.Xml.XmlNode source = _xml.SelectSingleNode(_source);
                if (source == null)
                    ArcGIS.Desktop.Framework.Dialogs.MessageBox.Show("Error: Unable to locate Source xml element in the file");
                else
                    srcValid = checkSourceTargetPath(folder, source.InnerText);

                System.Xml.XmlNode target = _xml.SelectSingleNode(_target);
                if (target == null)
                    ArcGIS.Desktop.Framework.Dialogs.MessageBox.Show("Error: Unable to locate Target xml element in the file");
                else
                    targValid = checkSourceTargetPath(folder, target.InnerText);

                if (srcValid && targValid) // ignore the Project value in error messages.
                    valid = true;
                else
                    ArcGIS.Desktop.Framework.Dialogs.MessageBox.Show("All files should be fully qualified paths or be relative to the selected xml file");

            }
            else
                ArcGIS.Desktop.Framework.Dialogs.MessageBox.Show(filepath + " does not exist");

            return valid;
        }
        private bool checkSourceTargetPath(string folder, string dataset, bool promptNotValid = true)
        {
            bool valid = false;
            if (dataset != null && dataset != "")
            {
                if (!checkDatasetExists(dataset))
                {
                    string ds = System.IO.Path.Combine(folder, dataset);
                    valid = checkDatasetExists(ds);
                }
                else
                    valid = true;
            }
            if (!valid && promptNotValid)
                ArcGIS.Desktop.Framework.Dialogs.MessageBox.Show("Unable to locate dataset '" + dataset + "'");
            return valid;
        }

        private bool checkDatasetExists(string dataset)
        {
            string _shp = ".shp";
            string _sde = ".sde\\";
            string _gdb = ".gdb\\";
            string _lyrx = ".lyrx";
            string _aprx = ".aprx";
            string _http = "http://";
            string _https = "https://";
            bool exists = false;
            if (dataset.ToLower().StartsWith(_http))
            {
                Uri ds = new Uri(dataset);
                try
                {
                    var query = ds.Query; // just a simple url test
                    exists = true;
                }
                catch { exists = false; }

            }
            if (dataset.ToLower().StartsWith(_https))
            {
                Uri ds = new Uri(dataset);
                try
                {
                    var query = ds.Query; // just a simple url test
                    exists = true;
                }
                catch { exists = false; }

            }
            if (dataset.ToLower().Contains(_sde))
            {
                string sde = dataset.Substring(0, dataset.LastIndexOf(_sde) + (_sde.Length-1));
                if (System.IO.File.Exists(sde)) // just checking .sde file 
                    exists = true;
            }
            if (dataset.ToLower().Contains(_gdb))
            {
                string db = dataset.Substring(0, dataset.LastIndexOf(_gdb) + (_gdb.Length-1));
                if (System.IO.Directory.Exists(db)) // just checking .gdb folder exists
                    exists = true;
            }
            if (dataset.ToLower().EndsWith(_lyrx))
            {
                if (System.IO.File.Exists(dataset))
                    exists = true;
            }
            if (dataset.ToLower().EndsWith(_aprx))
            {
                if (System.IO.File.Exists(dataset))
                    exists = true;
            }
            if (dataset.ToLower().EndsWith(_shp))
            {
                if (System.IO.File.Exists(dataset))
                    exists = true;
            }
            return exists;
        }



    }
}