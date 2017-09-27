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
using System.IO;

namespace DataAssistant
{
    /// <summary>
    /// Interaction logic for Dockpane1View.xaml
    /// </summary>
    public partial class Dockpane1View : UserControl
    {
        public static string AddinAssemblyLocation()
        {
            var asm = System.Reflection.Assembly.GetExecutingAssembly();
            return System.IO.Path.GetDirectoryName(
                              Uri.UnescapeDataString(
                                      new Uri(asm.CodeBase).LocalPath));
        }
        public static string getXmlFileName()
        {
            if (_filename != null)
                return _filename;
            else
                return "";
        }
        public static System.Xml.XmlDocument getXmlDocument()
        {
            return _xml;
        }
        public static string getNoneFieldName()
        {
            return _noneField;
        }
        public void setXmlFileName(string fname)
        {
            // set to default/current value if null
            if (fname != null)
                _filename = fname;
            if ((String)this.FileName.ToolTip != _filename)
            {
                this.FileName.ToolTip = _filename;
                this.FileName.Text = _filename.Split('\\').Last();
                copyXml(_filename, _revertname);
            }
        }
        private string getProjectFolder()
        {
            string pth = "";
            ArcGIS.Desktop.Core.Project prj = ArcGIS.Desktop.Core.Project.Current;
            pth = prj.HomeFolderPath;
            return pth;
        }
        private string getFolder(string fname)
        {
            string folder = "";
            string prjFolder = getProjectFolder();
            string xmlFolder = System.IO.Path.GetDirectoryName(fname);
            if (!Equals(prjFolder, xmlFolder))
                folder = xmlFolder;
            else
                folder = xmlFolder;

            return folder;

        }
        private string setFolder(string fname)
        {
            _xmlFolder = getFolder(fname);
            return _xmlFolder;
        }
        private string getDatasetPath(string pth)
        {
            string dsPath = pth;
            if (pth.StartsWith("http://") || pth.Contains(":\\") || pth.StartsWith(_xmlFolder))
            { }
            else
                dsPath = System.IO.Path.Combine(_xmlFolder, pth);
            return dsPath;
        }
        private void setDatasetUI()
        {
            SourceStack.IsEnabled = true;
            TargetStack.IsEnabled = true;
            ReplaceStack.IsEnabled = true;

            SourceStack.Visibility = System.Windows.Visibility.Visible;
            TargetStack.Visibility = System.Windows.Visibility.Visible;
            ReplaceStack.Visibility = System.Windows.Visibility.Visible;

            System.Xml.XmlNode node = _xml.SelectSingleNode("//Datasets/Source");
            if (node == null)
                ArcGIS.Desktop.Framework.Dialogs.MessageBox.Show("There appears to be an issue in your Xml document, required element Datasets/Source is missing from the document.");
            else
            {
                SourceLayer.ToolTip = node.InnerText;
                SourceLayer.Text = node.InnerText.Split('\\').Last();
            }

            node = _xml.SelectSingleNode("//Datasets/Target");
            if (node == null)
                ArcGIS.Desktop.Framework.Dialogs.MessageBox.Show("There appears to be an issue in your Xml document, required element Datasets/Target is missing from the document.");
            else
            {
                TargetLayer.ToolTip = node.InnerText;
                TargetLayer.Text = node.InnerText.Split('\\').Last();
            }

            setXmlDataProvider(ReplaceField, "//TargetField/@Name");
            System.Xml.XmlNodeList nodes = _xml.SelectNodes("//Datasets/ReplaceBy");
            setReplaceValues(nodes);
            //MethodPanelApply.IsEnabled = false;
            //PreviewGrid.Visibility = Visibility.Collapsed;
            //setPreviewValues(false);
        }
        private void setRevertButton()
        {
            if (RevertButton.Visibility != System.Windows.Visibility.Visible)
            {
                RevertButton.Visibility = System.Windows.Visibility.Visible;
            }
        }
        private void setReplaceValues(System.Xml.XmlNodeList nodes)
        {
            if (nodes != null)
            {
                try
                {
                    bool hasValue = false;
                    string field = getReplaceValue(nodes, "FieldName");
                    string op = getReplaceValue(nodes, "Operator");
                    string value = getReplaceValue(nodes, "Value");
                    if (field != null)
                    {
                        setReplaceValue(ReplaceField, field);
                        hasValue = true;
                    }
                    if (op != null)
                    {
                        setReplaceValue(ReplaceOperator, op);
                        hasValue = true;
                    }
                    if (value != null)
                    {
                        ReplaceValue.Text = value;
                        hasValue = true;
                    }
                    if (hasValue == true)
                    {
                        ReplaceByCheckBox.IsChecked = true;
                        ReplaceByCheckBox_Checked(ReplaceByCheckBox, null);
                    }
                    else
                    {
                        clearReplaceValues();
                    }
                }
                catch { ArcGIS.Desktop.Framework.Dialogs.MessageBox.Show("Error setting replace"); }
            }
            else
            {
                clearReplaceValues();
            }

        }
        public void loadFile(string fname)
        {
            // load the selected file
            if (System.IO.File.Exists(fname))
            {
                setFolder(fname);
                setXmlFileName(fname);
                if (loadXml(_filename))
                {
                    this._skipSelectionChanged = true;
                    setXmlDataProvider(this.FieldGrid, fieldXPath);
                    this._skipSelectionChanged = false;
                    setDatasetUI();
                    _datarows = _xml.SelectNodes("//Data/Row");
                }
            }
        }
        private bool loadXml(string filename)
        {
            if (!System.IO.File.Exists(filename))
            {
                ArcGIS.Desktop.Framework.Dialogs.MessageBox.Show(filename + " does not exist, please select a file");
                return false;
            }
            string xmlstr = System.IO.File.ReadAllText(filename);
            // Encode in UTF-8 byte array
            byte[] encodedString = Encoding.UTF8.GetBytes(xmlstr);
            // Put the byte array into a stream and rewind
            System.IO.MemoryStream ms = new System.IO.MemoryStream(encodedString);
            ms.Flush();
            ms.Position = 0;
            _xml.Load(ms);
            return true;
        }
        private void clearReplaceValues()
        {
            ReplaceField.SelectedIndex = -1;
            ReplaceOperator.SelectedIndex = -1;
            ReplaceValue.Text = "";
            ReplaceByCheckBox.IsChecked = false;
            System.Xml.XmlNode node = _xml.SelectSingleNode("//Datasets/ReplaceBy");
            if (node != null)
            {
                node.RemoveAll();
                saveFieldGrid();
            }
            _skipSelectionChanged = true;
            ReplaceByCheckBox_Unchecked(ReplaceByCheckBox, null);
            _skipSelectionChanged = false;
        }

        private string getReplaceValue(System.Xml.XmlNodeList replace, string nodeName)
        {
            string txt = null;
            System.Xml.XmlNode node = replace[0].SelectSingleNode(nodeName);
            if (node != null)
                txt = node.InnerText;
            return txt;
        }
        private void setReplaceValue(ComboBox combo, string theval)
        {
            if (combo != null)
            {
                _skipSelectionChanged = true;
                for (int i = 0; i < combo.Items.Count; i++)
                {
                    object obj = combo.Items.GetItemAt(i);
                    ComboBoxItem item = obj as ComboBoxItem;
                    if (item != null)
                    {
                        string comp = item.Content.ToString();
                        if (comp == theval)
                            combo.SelectedIndex = i;
                    }
                    else
                    {
                        System.Xml.XmlElement elem = obj as System.Xml.XmlElement;
                        if (elem != null)
                        {
                            string comp = elem.InnerText;
                            if (comp == theval)
                                combo.SelectedIndex = i;
                        }
                        else
                        {
                            System.Xml.XmlAttribute attr = obj as System.Xml.XmlAttribute;
                            if (attr != null)
                            {
                                string comp = attr.InnerText;
                                if (comp == theval)
                                    combo.SelectedIndex = i;
                            }

                        }
                    }
                }
                _skipSelectionChanged = false;
            }
        }
        private void saveFieldGrid()
        {
            if (this.IsInitialized)
            {
                XmlDataProvider dp = new XmlDataProvider();
                dp = this.FieldGrid.DataContext as XmlDataProvider;
                dp.IsAsynchronous = false;
                //setXmlFileName(FileName.Text);

                dp.Document.Save(getXmlFileName());
                setRevertButton();
            }
        }
        private void setXmlDataProvider(object ctrl, string xpath)
        {
            XmlDataProvider dp = new XmlDataProvider();
            if (this.IsInitialized)
            {
                try
                {
                    dp.IsAsynchronous = false;
                    dp.Document = _xml;
                    dp.XPath = xpath;
                    DataGrid uictrl = ctrl as DataGrid;
                    if (uictrl == null)
                    {
                        ComboBox cbctrl = ctrl as ComboBox;
                        cbctrl.DataContext = dp;
                    }
                    else
                        uictrl.DataContext = dp;
                }
                catch
                {
                    ArcGIS.Desktop.Framework.Dialogs.MessageBox.Show("Error setting Xml data provider");
                }
            }
        }
        private void FieldGrid_Selected(object sender, SelectedCellsChangedEventArgs e)
        {
            if (FieldGrid.SelectedIndex == -1 || FieldGrid == null)
                Methods.IsEnabled = false;
            else
                Methods.IsEnabled = true;
        }
        private void FieldGrid_SelectionChanged(object sender, SelectionChangedEventArgs e)
        {
            // Need to pull the current configuration values from the config, also need to set the correct panel as visible


            if (this._skipSelectionChanged)
                return;
            if (FieldGrid.SelectedIndex == -1)
                return;
            _selectedRowNum = FieldGrid.SelectedIndex;
            var cfg = getConfigSettingsForField();
            _skipSelectionChanged = true;
            int methodnum = setFieldSelectionValues(cfg); // just use the int for now.
            _skipSelectionChanged = false;
            _methodnum = methodnum;
            setPanelVisibility(methodnum);
        }
        private System.Xml.XmlNodeList getFieldNodes(int fieldnum)
        {
            System.Xml.XmlNodeList nodes = null;
            string xpath = "//Field[position()=" + fieldnum.ToString() + "]"; // Field grid position to set
            System.Xml.XmlNodeList nodelist = _xml.SelectNodes(xpath);
            if (nodelist != null && nodelist.Count == 1)
                return nodelist;
            else
                return nodes;
        }
        private System.Xml.XmlNodeList getSourceFieldNodes()
        {
            System.Xml.XmlNodeList nodes = null;
            if (FieldGrid.SelectedIndex == -1)
                return nodes;
            int fieldnum = FieldGrid.SelectedIndex + 1;
            System.Xml.XmlNodeList fnodes = getFieldNodes(fieldnum);
            string sname = "";
            try
            {
                sname = fnodes.Item(0).SelectSingleNode("SourceName").InnerText;
            }
            catch
            {
                ArcGIS.Desktop.Framework.Dialogs.MessageBox.Show("Could not find SourceName element for field (row) number " + fieldnum.ToString());
                return nodes;
            }
            string xpath = "//SourceField[@Name='" + sname + "']"; // Source field values
            System.Xml.XmlNodeList nodelist = _xml.SelectNodes(xpath);
            if (nodelist != null && nodelist.Count == 1)
                return nodelist;
            else
                return nodes;
        }
        private System.Xml.XmlNodeList getSourceFields()
        {
            string xpath = "//SourceField"; // Source field values
            System.Xml.XmlNodeList nodelist = _xml.SelectNodes(xpath);
            return nodelist;
        }
        private string getSourceFieldName()
        {
            string fname = "None";
            if (FieldGrid.SelectedIndex == -1)
                return fname;
            int fieldnum = FieldGrid.SelectedIndex + 1;
            var nodes = getFieldNodes(fieldnum);
            if (nodes.Count == 1 && nodes != null)
            {
                var node = nodes.Item(0).SelectSingleNode("SourceName");
                if (node != null)
                    fname = node.InnerText;
            }
            return fname;
        }
        private string getTargetFieldName()
        {
            string fname = "None";
            if (FieldGrid.SelectedIndex == -1)
                return fname;
            int fieldnum = FieldGrid.SelectedIndex + 1;
            var nodes = getFieldNodes(fieldnum);
            if (nodes.Count == 1 && nodes != null)
            {
                var node = nodes.Item(0).SelectSingleNode("TargetName");
                if (node != null)
                    fname = node.InnerText;
            }
            return fname;
        }
        private string getFieldIsEnabled()
        {
            string enabled = "true";
            if (FieldGrid.SelectedIndex == -1)
                return enabled;
            int fieldnum = FieldGrid.SelectedIndex + 1;
            var nodes = getFieldNodes(fieldnum);
            if (nodes.Count == 1 && nodes != null)
            {
                try
                {
                    string en = nodes.Item(0).Attributes["IsEnabled"].Value;
                    if (en != null)
                        enabled = en.ToLower();
                }
                catch { enabled = "true"; }
            }
            return enabled;
        }
        private int getConfigSettingsForField()
        {
            if (FieldGrid.SelectedIndex == -1)
                return -1;
            int num = -1;
            int fieldnum = FieldGrid.SelectedIndex + 1;
            var nodes = getFieldNodes(fieldnum);
            if (nodes.Count == 1 && nodes != null)
            {
                try
                {
                    var node = nodes.Item(0).SelectSingleNode("Method");
                    for (int i = 0; i < comboMethod.Items.Count; i++)
                    {
                        string val = comboMethod.Items.GetItemAt(i).ToString().Replace(" ", "");
                        // special case to convert DefaultValue to SetValue
                        if (val.EndsWith("SetValue") && node.InnerText.ToString() == "DefaultValue")
                            num = i;
                        else if (val.EndsWith(node.InnerText.ToString()))
                            num = i;
                    }
                }
                catch
                { }
            }

            return num;
        }
        private int setFieldSelectionValues(int methodnum)
        {
            comboMethod.SelectedIndex = methodnum;
            if (FieldGrid != null && FieldGrid.IsInitialized)
            {
                PreviewGrid.Visibility = Visibility.Collapsed;
            }

            switch (methodnum)
            { // fill in the values for each stack panel
                case 0: // None
                    break;
                case 1: // Copy
                    break;
                case 2: // SetValue
                    Method2Value.Text = getPanelValue(2, "SetValue");
                    break;
                case 3: // ValueMap
                    setValueMapValues(3, getPanelValue(3, "ValueMap"));
                    break;
                case 4: // ChangeCase
                    setComboValue(4, getPanelValue(4, "ChangeCase"));
                    break;
                case 5: // Concatenate
                    _concat.Clear();
                    setSpaceVal(getPanelValue(5, "Separator"), Method5Value);
                    setConcatValues();
                    Method5.InvalidateArrange();
                    break;
                case 6: // Left
                    setSliderValue(6, getPanelValue(6, "Left"));
                    break;
                case 7: // Right
                    setSliderValue(7, getPanelValue(7, "Right"));
                    break;
                case 8: // Substring
                    setSubstringValues(getPanelValue(81, "Start"), getPanelValue(82, "Length"));
                    break;
                case 9: // Split
                    setSpaceVal(getPanelValue(91, "SplitAt"), Method91Value);
                    Method92Value.Text = getPanelValue(92, "Part");
                    break;
                case 10: // Conditional Value
                    setConditionValues();
                    break;
                case 11: // Domain Map
                    setDomainMapValues(11, getPanelValue(11, "DomainMap"));
                    break;

                    //case 11: // Expression
                    //Method11Value.Text = getPanelValue(11, "Expression");
                    //break;

            }

            return methodnum;
        }

        private bool getPanelEnabled(int methodnum)
        {
            bool theval = true;
            if (FieldGrid.SelectedIndex == -1)
                return theval;
            int fieldnum = FieldGrid.SelectedIndex + 1;
            var nodes = getFieldNodes(fieldnum);
            if (nodes.Count == 1)
            {
                try
                {
                    var node = nodes.Item(0).Attributes.Item(0);
                    if (node != null)
                        bool.TryParse(node.InnerText.ToLower(), out theval);
                }
                catch
                { }
            }
            return theval;
        }

        private string getPanelValue(int methodnum, string nodename)
        {
            if (FieldGrid.SelectedIndex == -1)
                return "error!";
            string theval = "";
            int fieldnum = FieldGrid.SelectedIndex + 1;
            var nodes = getFieldNodes(fieldnum);
            if (nodes.Count == 1)
            {
                try
                {
                    var node = nodes.Item(0).SelectSingleNode(nodename);
                    if (node == null && nodename == "SetValue")
                    {
                        node = nodes.Item(0).SelectSingleNode("DefaultValue");
                    }
                    if (node != null)
                        theval = node.InnerText.ToString();
                }
                catch
                { }
            }
            return theval;
        }
        private void setComboValue(int combonum, string theval)
        {
            string comboname = "Method" + combonum + "Combo";
            Object ctrl = this.FindName(comboname);
            ComboBox comb = ctrl as ComboBox;
            if (comb != null)
            {
                for (int i = 0; i < comb.Items.Count; i++)
                {
                    string comp = comb.Items.GetItemAt(i).ToString();
                    if (comp.EndsWith(theval))
                        comb.SelectedIndex = i;
                }
            }
        }
        private void setSliderValue(int combonum, string theval)
        {
            string name = "Method" + combonum + "Slider";
            Object ctrl = this.FindName(name);
            Slider slide = ctrl as Slider;
            if (slide != null)
            {
                int val;
                Int32.TryParse(theval, out val);
                slide.Value = val;
            }
        }

        private void setValueMapValues(int combonum, string nodename)
        {
            if (FieldGrid.SelectedIndex == -1)
                return;
            int fieldnum = FieldGrid.SelectedIndex + 1;
            System.Xml.XmlNodeList nodes = getFieldNodes(fieldnum);
            System.Xml.XmlNodeList snodes;
            System.Xml.XmlNodeList tnodes;
            tnodes = nodes[0].SelectNodes("ValueMap/tValue");
            snodes = nodes[0].SelectNodes("ValueMap/sValue");

            string name = "Method" + combonum + "Grid";
            Object ctrl = this.FindName(name);
            DataGrid grid = ctrl as DataGrid;
            if (grid == null)
                return;

            grid.Items.Clear();
            for (int i = 0; i < snodes.Count; i++)
            {
                System.Xml.XmlNode sourcenode = snodes.Item(i);
                string sourcename = sourcenode.InnerText;
                System.Xml.XmlNode targetnode = tnodes.Item(i);
                string targetname = targetnode.InnerText;

                grid.Items.Add(new ValueMapRow() { Source = sourcename, Target = targetname });
            }
            System.Xml.XmlNode othnode = nodes[0].SelectSingleNode("ValueMap/Otherwise");
            if (othnode != null)
                Method3Otherwise.Text = othnode.InnerText;
            else Method3Otherwise.Text = "";

            if (grid.Items.Count > 0)
                ValueMapRemove.IsEnabled = true;
            else
                ValueMapRemove.IsEnabled = false;
        }

        private void setSpaceVal(string separator, TextBox txt)
        {
            if (txt != null && separator != txt.Text)
            {
                txt.Text = separator.Replace(_spaceVal, " ");
            }
        }
        private void setConcatValues()
        {
            System.Xml.XmlNodeList sourcenodes = getSourceFields();

            int fieldnum = FieldGrid.SelectedIndex + 1;
            DataGrid grid = Method5Grid;
            if (grid == null)
                return;
            System.Xml.XmlNodeList cnodes = getFieldNodes(fieldnum);
            try { cnodes = cnodes[0].SelectNodes("cFields/cField"); }
            catch { }

            grid.Items.Clear();
            if (_concat.Count == 0 && cnodes != null)
            {
                for (int c = 0; c < cnodes.Count; c++)
                {
                    // assume source nodes written in sequence order... and only checked items in the xml
                    System.Xml.XmlNode cnode = cnodes.Item(c);
                    string cname = cnode.SelectSingleNode("Name").InnerText;
                    if (cname != _noneField)
                    {
                        grid.Items.Add(new ConcatRow() { Checked = true, Name = cname });
                        _concat.Add(cname);
                    }
                }
            }
            else
            {
                for (int c = 0; c < _concat.Count; c++)
                {
                    // if there are items in the concat list use them in order
                    grid.Items.Add(new ConcatRow() { Checked = true, Name = _concat[c] });
                }
            }
            if (_concat.Count > 0)
                Method5ClearAll.IsEnabled = true;

            for (int i = 0; i < sourcenodes.Count; i++)
            {
                // add the unchecked items in row order
                System.Xml.XmlNode sourcenode = sourcenodes.Item(i);
                string sourcename = sourcenode.Attributes.GetNamedItem("Name").InnerText;
                bool found = false;
                for (int c = 0; c < _concat.Count; c++)
                {
                    // look for a matching field that has a checked value, don't add if checked.
                    string cname = _concat[c];
                    if (cname == sourcename)
                        found = true;
                }
                if (!found && sourcename != _noneField)
                {
                    try
                    {
                        grid.Items.Add(new ConcatRow() { Checked = found, Name = sourcename });
                    }
                    catch
                    {
                        ArcGIS.Desktop.Framework.Dialogs.MessageBox.Show("Error setting checkbox values");
                    }
                }
            }
            grid.Items.Refresh();
        }

        private void setSubstringValues(string start, string length)
        {
            try
            {
                setSliderValue(81, start);
                System.Xml.XmlNodeList source = getSourceFieldNodes();
                int max = Int32.Parse(source.Item(0).Attributes.GetNamedItem("Length").InnerText);
                Method82Slider.Maximum = max;
                setSliderValue(82, length);
            }
            catch
            { }
        }

        private void setConditionValues()
        {
            string source = getPanelValue(101, "SourceName");
            if (source != _noneField)
                Method10Label.Content = "If (" + source + ") is";
            else
                Method10Label.Content = "If ";
            string iff = getPanelValue(101, "If");
            string oper = getPanelValue(10, "Oper");
            for (int i = 0; i < Method10Value.Items.Count; i++)
            {
                ComboBoxItem item = Method10Value.Items[i] as ComboBoxItem;
                if (item.Content.ToString() == oper)
                    Method10Value.SelectedIndex = i;
            }
            Method101Value.Text = iff;
            Method102Value.Text = getPanelValue(102, "Then");
            Method103Value.Text = getPanelValue(103, "Else");

        }
        private void setPanelVisibility(int index)
        {
            string methnum = index.ToString();

            for (int i = 0; i < comboMethod.Items.Count; i++)
            {
                if (i == index)
                {
                    string method = "Method" + methnum;
                    Object ctrl = this.FindName(method);
                    Panel panel = ctrl as Panel;
                    if (panel != null)
                    {
                        try
                        {
                            panel.Visibility = System.Windows.Visibility.Visible;
                            if (this.FieldGrid.SelectedIndex != -1)
                            {
                                bool enabled = getPanelEnabled(this.FieldGrid.SelectedIndex);
                                panel.IsEnabled = enabled;
                                comboMethod.IsEnabled = enabled;
                            }
                            panel.InvalidateArrange();
                            panel.UpdateLayout();
                        }
                        catch { }
                    }
                }
                else
                {
                    string method = "Method" + i;
                    Object ctrl = this.FindName(method);
                    Panel panel = ctrl as Panel;
                    if (panel != null)
                    {
                        try
                        {
                            panel.Visibility = System.Windows.Visibility.Collapsed;
                            panel.InvalidateArrange();
                            panel.UpdateLayout();
                        }
                        catch { }
                    }
                }
            }
        }
    }
}
