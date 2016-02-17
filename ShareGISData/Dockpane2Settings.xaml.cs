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
using ArcGIS.Desktop.Core.Geoprocessing;
using ArcGIS.Desktop.Core;
using ArcGIS.Desktop.Catalog;
using System.Xml;
using System.Xml.Xsl;
using System.Xml.XPath;


namespace DataAssistant
{
    /// <summary>
    /// Interaction logic for Dockpane2SettingsView.xaml
    /// </summary>
    public partial class Dockpane2SettingsView : UserControl
    {
        string _matchFile = System.IO.Path.Combine(Dockpane1View.AddinAssemblyLocation(), "GPTools\\arcpy\\MatchLocal.xml");
        string _xsltFile = System.IO.Path.Combine(Dockpane1View.AddinAssemblyLocation(), "GPTools\\arcpy\\FieldMatcher.xsl");
        public Dockpane2SettingsView()
        {
            InitializeComponent();
        }
        public void Enable()
        {
            this.MatchLibraryGrid.IsEnabled = true;
        }
        public void Disable()
        {
            this.MatchLibraryStack.IsEnabled = false;
        }
        private void UpdateMatchLibraryButton_Click(object sender, RoutedEventArgs e)
        {
            string xmlFile = Dockpane1View.getXmlFileName();
            if (xmlFile != "" && xmlFile != null)
            {
                if (System.Windows.Forms.MessageBox.Show("Update Match Library Values using the settings in your current configuration file?", "Update Match Library", System.Windows.Forms.MessageBoxButtons.YesNo) == System.Windows.Forms.DialogResult.Yes)
                {
                    XsltArgumentList argList = new XsltArgumentList();
                    argList.AddParam("configFile", "", xmlFile);
                    string outfile = _matchFile.Replace(".xml", "1.xml");

                    runTransform(_matchFile, _xsltFile, outfile, argList);
                    copyXml(outfile, _matchFile);
                }
            }
            else
            {
                System.Windows.Forms.MessageBox.Show("Please open a Configuration File before updating the Match Library", "Update Match Library");
            }
        }

        private void ResetMatchLibraryButton_Click(object sender, RoutedEventArgs e)
        {
            string xmlFile = Dockpane1View.getXmlFileName();
            if (xmlFile != "" && xmlFile != null)
            {
            if (System.Windows.Forms.MessageBox.Show("Clear all Match Library Values?", "Clear Match Library", System.Windows.Forms.MessageBoxButtons.YesNo) == System.Windows.Forms.DialogResult.Yes)
            {
                XsltArgumentList argList = new XsltArgumentList();
                argList.AddParam("configFile", "",  _matchFile);
                string outfile = _matchFile.Replace(".xml", "1.xml");
                runTransform(Dockpane1View.getXmlFileName(), _xsltFile, outfile, argList);
                copyXml(outfile, _matchFile);
            }
            }
            else
            {
                System.Windows.Forms.MessageBox.Show("Please open a Configuration File before clearing the Match Library", "Clear Match Library");
            }

        }
        public static bool runTransform(string xmlPath, string xsltPath, string outputPath, XsltArgumentList argList)
        {
            XmlTextReader reader = null;
            XmlWriter writer = null;
            try
            {
                XsltSettings xslt_set = new XsltSettings();
                xslt_set.EnableScript = true;
                xslt_set.EnableDocumentFunction = true;

                // Load the XML source file.
                reader = new XmlTextReader(xmlPath);

                // Create an XmlWriter.
                XmlWriterSettings settings = new XmlWriterSettings();
                settings.Indent = true;
                settings.Encoding = new UTF8Encoding();
                settings.OmitXmlDeclaration = false;

                writer = XmlWriter.Create(outputPath, settings);

                XslCompiledTransform xslt = new XslCompiledTransform();
                xslt.Load(xsltPath, xslt_set, new XmlUrlResolver());
                if (argList == null)
                    xslt.Transform(reader, writer);
                else
                    xslt.Transform(reader, argList, writer);
                reader.Close();
                writer.Close();

                return true;
            }
            catch (Exception err)
            {
                try
                {
                    if (reader != null)
                        reader.Close();
                    if (writer != null)
                        writer.Close();
                    throw (err);
                }
                catch (Exception err2)
                {
                    MessageBox.Show(err2.ToString());
                    return false;
                }
            }
        }
        private bool copyXml(string fName1, string fName2)
        {
            System.IO.FileInfo fp1 = new System.IO.FileInfo(fName1);
            try
            {
                fp1.CopyTo(fName2, true);
            }
            catch (Exception e)
            {
                string errStr = e.Message;
                return false;
            }
            return true;
        }
    }
}
