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
            if(fname != null)
                _filename = fname;
            if ((String)this.FileName.ToolTip != _filename)
            {
                this.FileName.ToolTip = _filename;
                this.FileName.Text = _filename.Split('\\').Last();
                copyXml(_filename,_revertname);
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
        private static string _filename;// = System.IO.Path.Combine(AddinAssemblyLocation(), "ConfigData.xml");
        System.Xml.XmlNodeList _datarows;

        string fieldXPath = "/SourceTargetMatrix/Fields/Field";
        static System.Xml.XmlDocument _xml = new System.Xml.XmlDocument();
        TextInfo textInfo = new CultureInfo("en-US", false).TextInfo;
        //public int concatSequence = 0;
        private List<string> _concat = new List<string> { };
        static string _noneField = "(None)";
        static string _spaceVal = "(space)";
        private bool _skipSelectionChanged = false;
        private int _selectedRowNum = -1;
        int _methodnum = -1;
        string _revertname = System.IO.Path.Combine(AddinAssemblyLocation(), "RevertFile.xml");
        string _xmlFolder = "";

        private List<ComboData> _domainTargetValues = new List<ComboData>();
        private List<ComboData> _domainSourceValues = new List<ComboData>();
        private List<ComboData> _domainValues = new List<ComboData>();
        private string _source = "Source";
        private string _target = "Target";
        public Dockpane1View()
        {
            InitializeComponent();
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

        private string getReplaceValue(System.Xml.XmlNodeList replace,string nodeName)
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
            if(this.IsInitialized)
            {
                XmlDataProvider dp = new XmlDataProvider();
                dp = this.FieldGrid.DataContext as XmlDataProvider;
                dp.IsAsynchronous = false;
                //setXmlFileName(FileName.Text);
                
                dp.Document.Save(getXmlFileName());
                setRevertButton();
            }           
        }
        private void setXmlDataProvider(object ctrl,string xpath)
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
            if (this._skipSelectionChanged || (_selectedRowNum == FieldGrid.SelectedIndex))
                return;
            if(FieldGrid.SelectedIndex == -1)
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
                    for(int i=0;i<comboMethod.Items.Count;i++)
                    {
                        string val = comboMethod.Items.GetItemAt(i).ToString().Replace(" ","");
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

            switch (methodnum){ // fill in the values for each stack panel
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
                    setSpaceVal(getPanelValue(5,"Separator"),Method5Value);
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
                    setSpaceVal(getPanelValue(91,"SplitAt"),Method91Value);
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

        private string getPanelValue(int methodnum,string nodename)
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
                    if(node != null)
                        theval = node.InnerText.ToString();
                }
                catch
                { }
            }
            return theval;
        }
        private void setComboValue(int combonum,string theval)
        {
            string comboname = "Method" + combonum + "Combo";
            Object ctrl = this.FindName(comboname);
            ComboBox comb = ctrl as ComboBox;
            if (comb != null)
            {
                for (int i = 0; i < comb.Items.Count;i++ )
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
            if(othnode != null)
                Method3Otherwise.Text = othnode.InnerText;
            else Method3Otherwise.Text = "";
            
            if (grid.Items.Count > 0)
                ValueMapRemove.IsEnabled = true;
            else
                ValueMapRemove.IsEnabled = false;
        }

        private void setSpaceVal(string separator,TextBox txt)
        {
            if (txt != null && separator != txt.Text)
            {
                txt.Text = separator.Replace(_spaceVal," ");
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
            if(_concat.Count > 0)
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
            if(source != _noneField)
                Method10Label.Content = "If (" + source + ") is";
            else
                Method10Label.Content = "If ";
            string iff = getPanelValue(101, "If");
            string oper = getPanelValue(10, "Oper");
            for (int i = 0; i < Method10Value.Items.Count; i++)
            {
                ComboBoxItem item = Method10Value.Items[i] as ComboBoxItem;
                if(item.Content.ToString() == oper)
                    Method10Value.SelectedIndex = i;
            }
            Method101Value.Text = iff;
            Method102Value.Text = getPanelValue(102, "Then");
            Method103Value.Text = getPanelValue(103, "Else");

        }
        private void FieldGrid_AutoGeneratingColumn(object sender, DataGridAutoGeneratingColumnEventArgs e)
        {
        }
        
        private void comboMethod_SelectionChanged(object sender, SelectionChangedEventArgs e)
        {
            if (this._skipSelectionChanged || FieldGrid == null || !FieldGrid.IsInitialized)
            {
                return;
            }
            if (comboMethod.SelectedIndex != _methodnum && !this._skipSelectionChanged)
            {
                setFieldSelectionValues(comboMethod.SelectedIndex);
                setPanelVisibility(comboMethod.SelectedIndex);
                //setPreviewValues(false);
                PreviewGrid.Visibility = Visibility.Collapsed;
                _methodnum = comboMethod.SelectedIndex;
                //MethodPanelApply.IsEnabled = true;
                if(Method0 != null)
                    MethodPanelApply_Click(sender, e);
            }
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
                            if(this.FieldGrid.SelectedIndex != -1)
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

        private void CloseButton_Click(object sender, RoutedEventArgs e)
        {
            Dockpane1ViewModel.doHide();
        }
        public bool setFiles()
        {
            //string dataFolder;
            //dataFolder = "this";
            return true;
        }

        private void Method5ClearAll_Click(object sender, RoutedEventArgs e)
        {
            setAllConcat(false,5);
            MethodPanelApply_Click(sender, e);
        }

        private void ConcatAll_Click(object sender, RoutedEventArgs e)
        {
            setAllConcat(true, 5);
        }
        private void setAllConcat(bool val,int combonum)
        {
            System.Xml.XmlNodeList sourcenodes = getSourceFields();

            string name = "Method" + combonum + "Grid";
            object ctrl = this.FindName(name);
            DataGrid grid = ctrl as DataGrid;
            if (grid == null)
                return;

            grid.Items.Clear();
            _concat.Clear();
            for (int i = 0; i < sourcenodes.Count; i++)
            {
                System.Xml.XmlNode sourcenode = sourcenodes.Item(i);
                string sourcename = sourcenode.Attributes.GetNamedItem("Name").InnerText;
                if (val == true && sourcename != _noneField)
                    _concat.Add(sourcename);
                if (sourcename != _noneField)
                    grid.Items.Add(new ConcatRow() { Checked = val, Name = sourcename});
            }
            if (val == false)
                Method5ClearAll.IsEnabled = false;
        }

        private void Method5Grid_SelectionChanged(object sender, SelectionChangedEventArgs e)
        {
        }
        private void Method5Check_Checked(object sender, RoutedEventArgs e)
        {
            CheckBox check = sender as CheckBox;
            if (Method5Grid.SelectedIndex == -1)
                return;
            if (check != null)
            {
                for (int i = 0; i < Method5Grid.Items.Count; i++)
                {
                    if (i == Method5Grid.SelectedIndex)
                    {
                        object item = Method5Grid.Items.GetItemAt(i);
                        ConcatRow row = item as ConcatRow;
                        if (row != null)
                        {
                            bool chk = (check.IsChecked.HasValue) ? check.IsChecked.Value : false;
                            row.Checked = chk;
                            bool present = false;
                            for (int c = 0; c < _concat.Count; c++)
                            {
                                if ( Equals(row.Name,_concat[c]))
                                    present = true;
                            }
                            if (chk && ! present)
                            {
                                _concat.Add(row.Name);
                                setConcatValues();
                            }
                            else if (! chk && present)
                            {
                                _concat.Remove(row.Name);
                                setConcatValues();
                            }  
                        }
                    }
                }
                MethodPanelApply_Click(sender, e);
            }
        }

        private void Method3Target_TextChanged(object sender, TextChangedEventArgs e)
        {
            Method3TextChanged(sender, "Target");
            MethodPanelApply_Click(sender, e);
        }
        private void Method3Source_TextChanged(object sender, TextChangedEventArgs e)
        {
            Method3TextChanged(sender,"Source");
            MethodPanelApply_Click(sender, e);
        }
        private void Method3TextChanged(object sender,string sourcetarget)
        {
            TextBox txt = sender as TextBox;
            if (Method3Grid.SelectedIndex == -1)
                return;

            if (txt != null)
            {
                for (int i = 0; i < Method3Grid.Items.Count; i++)
                {
                    if (i == Method3Grid.SelectedIndex)
                    {
                        object item = Method3Grid.Items.GetItemAt(i);
                        ValueMapRow row = item as ValueMapRow;
                        if (row != null)
                        {
                            if(sourcetarget == "Source")
                                row.Source = txt.Text;
                            else if (sourcetarget == "Target")
                                row.Target = txt.Text;
                        }
                    }
                }

            }

        }

        private void SelectButton_Click(object sender, RoutedEventArgs e)
        {
            using (var dlg = new System.Windows.Forms.OpenFileDialog())
            {
                dlg.Filter = "Data Assistant XML files|*.xml";//.Description = "Browse for a Source-Target File (.xml)";
                dlg.Multiselect = false;
                System.Windows.Forms.DialogResult result = dlg.ShowDialog();
                if (result == System.Windows.Forms.DialogResult.OK)
                {
                    //this.FileName.Text = dlg.FileName;
                    if (checkXmlFileName(dlg.FileName))
                    {
                        loadFile(dlg.FileName);
                    }
                }
            }

        }
        private void FileName_GotFocus(object sender, RoutedEventArgs e)
        {
            TextBox txt = sender as TextBox;
            if ((String)txt.ToolTip != "")
            {
                txt.Text = (String)txt.ToolTip;
            }
        }

        private void FileName_LostFocus(object sender, RoutedEventArgs e)
        {
            TextBox txt = sender as TextBox;
            FileName_TextChanged(sender);
            if(txt.Text == (String)txt.ToolTip)
            {
                //If a user engages the textbox but does not make changes, this will revert text to shortened version
                txt.Text = txt.Text.Split('\\').Last();
            }
        }

        private void FileName_Drop(object sender, DragEventArgs e)
        {
            TextBox txt = sender as TextBox;
            string[] files = (string[])e.Data.GetData(DataFormats.FileDrop);
            txt.Text = files[0];
            FileName_TextChanged(sender);
            if (txt.Text == (String)txt.ToolTip)
            {
                //Sometimes does not shorten after dragging in file
                txt.Text = txt.Text.Split('\\').Last();
            }
        }
        private void FileName_TextChanged(object sender)
        {
            TextBox txt = sender as TextBox;
            if (txt.ToolTip == null)
            {
                if (checkXmlFileName(txt.Text))
                {
                    //setXmlFileName(txt.Text); REMOVED 7/25/2017. Seems redundant as it is immediatley called within loadFile
                    loadFile(txt.Text);
                }
            }
            else
            {
                if (txt.ToolTip.ToString() != txt.Text)
                {
                    if (!txt.ToolTip.ToString().Split('\\').Contains(txt.Text))
                    {
                        if (getXmlFileName() != txt.Text)
                        {
                            if (checkXmlFileName(txt.Text))
                            {
                                //setXmlFileName(txt.Text); REMOVED 7/25/2017. Seems redundant as it is immediatley called within loadFile
                                loadFile(txt.Text);
                            }
                        }
                    }
                }
            }
        }

        private void ValueMapAdd_Click(object sender, RoutedEventArgs e)
        {
            Method3Grid.Items.Add(new ValueMapRow() { Source = "", Target = "" });
            Method3Grid.InvalidateArrange();
            ValueMapRemove.IsEnabled = true;
        }

        private void ValueMapRemove_Click(object sender, RoutedEventArgs e)
        {
            if (Method3Grid.SelectedIndex > -1 && Method3Grid.Items.Count > 0)
            {
                Method3Grid.Items.RemoveAt(Method3Grid.SelectedIndex);
            }
        }
        
        private void Method5Value_TextChanged(object sender, TextChangedEventArgs e)
        {
            TextBox txt = sender as TextBox;
            if (txt.Text.IndexOf(" ") > -1)
            {
                txt.Text = txt.Text.Replace(" ", _spaceVal);
            }
            if(Method6 != null)
                MethodPanelApply_Click(sender, e);
        }
        private void Method91Value_TextChanged(object sender, TextChangedEventArgs e)
        {
            TextBox txt = sender as TextBox;
            if (txt.Text.IndexOf(" ") > -1)
            {
                txt.Text = txt.Text.Replace(" ", _spaceVal);
            }
            if (Method10 != null)
                MethodPanelApply_Click(sender, e);
        }

        private void SourceField_SelectionChanged(object sender, SelectionChangedEventArgs e)
        {
            var comboBox = sender as ComboBox;
            if (this._skipSelectionChanged || comboBox.IsLoaded == false)
                return;
            bool doSave = false;
            
            if (((ComboBox)sender).IsLoaded && (e.AddedItems.Count > 0 || e.RemovedItems.Count > 0) && FieldGrid.SelectedIndex != -1)
            { // disregard SelectionChangedEvent fired on population from binding
                
                for (Visual visual = (Visual)sender; visual != null; visual = (Visual)VisualTreeHelper.GetParent(visual))
                { // Traverse tree to find correct selected item
                    if (visual is DataGridRow)
                    {
                        DataGridRow row = visual as DataGridRow;
                        object val = row.Item;
                        System.Xml.XmlElement xml = val as System.Xml.XmlElement;
                        if(xml != null)
                        {
                            try
                            {
                                string nm = xml.GetElementsByTagName("TargetName")[0].InnerText;
                                string xmlname = "";
                                try
                                {
                                    xmlname = _xml.SelectSingleNode("//Field[position()=" + (_selectedRowNum + 1).ToString() + "]/TargetName").InnerText;
                                }
                                catch { }
                                if (nm == xmlname)
                                {
                                    doSave = true;
                                    break;
                                }
                            }
                            catch { }
                        }
                    }
                }
            }            
            
            int fieldnum = FieldGrid.SelectedIndex + 1;
            var nodes = getFieldNodes(fieldnum);
            if (nodes != null && comboBox != null && comboBox.SelectedValue != null && doSave == true) 
            {
                try
                {
                    string selected = comboBox.SelectedValue.ToString();
                    this._skipSelectionChanged = true;
                    if (nodes.Count == 1)
                    {
                        // source field selection should change to Copy
                        var node = nodes.Item(0).SelectSingleNode("Method");
                        var nodeField = nodes.Item(0).SelectSingleNode("SourceName");
                        if (selected == _noneField && comboMethod.SelectedIndex != 0)
                        {
                            node.InnerText = "None";
                            nodeField.InnerText = selected;
                            comboMethod.SelectedIndex = 0;
                            saveFieldGrid();
                        }
                        else if (selected != _noneField)
                        {
                            node.InnerText = "Copy";
                            nodeField.InnerText = selected;
                            comboMethod.SelectedIndex = 1;
                            saveFieldGrid();
                        }
                        _selectedRowNum = fieldnum;
                        this._skipSelectionChanged = false;
                    }
                }
                catch
                { }
            }
        }

        private void TargetLayer_TextChanged(object sender, TextChangedEventArgs e)
        {
            TextBox txt = sender as TextBox;
            System.Xml.XmlNode node = _xml.SelectSingleNode("//Datasets/Target");
            if (node != null && node.InnerText != txt.ToolTip.ToString())
            {
                node.InnerText = txt.ToolTip.ToString();
                saveFieldGrid();
            }
        }

        private void SourceLayer_TextChanged(object sender, TextChangedEventArgs e)
        {
            TextBox txt = sender as TextBox;
            if (txt != null)
            {
                System.Xml.XmlNode node = _xml.SelectSingleNode("//Datasets/Source");
                if (txt.Text != txt.ToolTip.ToString())
                {
                    if(!txt.ToolTip.ToString().Split('\\').Contains(txt.Text))
                    {
                        if (node != null && node.InnerText != txt.Text) // this is checking if you added a different source to then write to the xml
                        {
                            node.InnerText = txt.Text;
                            saveFieldGrid();
                        }
                    }
                } 
            }
        }

        private void ReplaceField_SelectionChanged(object sender, SelectionChangedEventArgs e)
        {
            ComboBox combo = sender as ComboBox;
            if (combo != null && combo.SelectedIndex != -1)
            {
                System.Xml.XmlNode node = _xml.SelectSingleNode("//Datasets/ReplaceBy/FieldName");
                if (node == null || node.InnerText != combo.SelectionBoxItem.ToString())
                    if(_skipSelectionChanged != true)
                        updateReplaceNodes();
            }
        }

        private void ReplaceOperator_SelectionChanged(object sender, SelectionChangedEventArgs e)
        {
            ComboBox combo = sender as ComboBox;
            if (combo != null && combo.SelectedIndex != -1)
            {
                System.Xml.XmlNode node = _xml.SelectSingleNode("//Datasets/ReplaceBy/Operator");
                if (node == null || node.InnerText != combo.SelectionBoxItem.ToString())
                    if (_skipSelectionChanged != true)
                        updateReplaceNodes();
            }
        }
        private void ReplaceValue_SelectionChanged(object sender, TextChangedEventArgs e)
        {
            TextBox txt = sender as TextBox;
            if (txt != null && txt.Text != "")
            {
                System.Xml.XmlNode node = _xml.SelectSingleNode("//Datasets/ReplaceBy/Value");
                if (node == null || node.InnerText != txt.Text)
                    if (_skipSelectionChanged != true)
                        updateReplaceNodes();
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
                    ArcGIS.Desktop.Framework.Dialogs.MessageBox.Show(err2.ToString());
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

        private void ReplaceByCheckBox_Checked(object sender, RoutedEventArgs e)
        {
            CheckBox chk = sender as CheckBox;
            if (chk != null)
            {
                ReplaceStackSettings.Visibility = System.Windows.Visibility.Visible;
                FileGrid.InvalidateArrange();
                FileGrid.UpdateLayout();
            }

        }

        private void ReplaceByCheckBox_Unchecked(object sender, RoutedEventArgs e)
        {
            CheckBox chk = sender as CheckBox;
            if (chk != null)
            {
                if(!_skipSelectionChanged)
                    setReplaceValues(null);
                ReplaceStackSettings.Visibility = System.Windows.Visibility.Collapsed;
                FileGrid.InvalidateArrange();
                FileGrid.UpdateLayout();
            }

        }

        private void RevertButton_Click(object sender, RoutedEventArgs e)
        {
            if (ArcGIS.Desktop.Framework.Dialogs.MessageBox.Show("Are you sure you want to re-open this file?", "Revert/Re-Open File", MessageBoxButton.YesNo) == MessageBoxResult.Yes)
            {
                copyXml(_revertname, _filename);
                loadFile(_filename);
            }

        }

        private void Method4Combo_SelectionChanged(object sender, SelectionChangedEventArgs e)
        {
            if (Method5 != null)
                MethodPanelApply_Click(sender, e);
        }

        private void Method92Value_TextChanged(object sender, TextChangedEventArgs e)
        {
            if (Method10 != null)
                MethodPanelApply_Click(sender, e);
        }

        private XElement getBaseMatchInfo()
            ///<summary>
            ///Returns the base information for a new match library entry
            ///Format:
            ///<SourceName></SourceName>
            ///<TargetName></TargetName>
            ///<Method></Method>
            ///
            ///</summary>
        {
            return  new XElement("Field",
                        new XElement("SourceName","None"),
                        new XElement("TargetName", getTargetFieldName()),
                        new XElement("Method", getMethodVal())
                    );
        }

        private void MatchSave_Click(object sender, RoutedEventArgs e)
        {
            var xmlpath = AddinAssemblyLocation() + "\\MapLibrary.xml";
            if (!File.Exists(xmlpath))
            {
                XmlWriter writer = XmlWriter.Create(xmlpath);

                writer.WriteStartElement("MatchLibrary");
                writer.WriteStartElement("Fields");

                writer.WriteEndDocument();
                writer.Close();
            }

            XElement root = XElement.Load(xmlpath);
            XElement newNode = getBaseMatchInfo();
            XElement fields = root.Element("Fields");

            IEnumerable<XElement> previous =  // Checks if there was a previous mapping between these two field names
                from el in fields.Elements("Field")
                where el.Element("TargetName").Value == getTargetFieldName()
                select el;
            foreach (XElement el in previous)
                el.Remove();

            newNode = getMethodMatchInfo(newNode);

            fields.Add(newNode);
            root.Save(xmlpath);
        }

        private XElement getMethodMatchInfo(XElement newNode)
        {
            var nodeMethod = newNode.Element("Method").Value;
            switch(nodeMethod)
            {
                case "SetValue":
                    try
                    {
                        XElement setValue = new XElement(nodeMethod, Method2Value.Text);
                        newNode.Add(setValue);
                    }
                    catch { }
                    break;
                case "ValueMap":
                    XElement ValueMap = new XElement(nodeMethod);
                    DataGrid ValueMapGrid = this.Method3Grid as DataGrid;
                    try
                    {
                        for(int s = 0; s < ValueMapGrid.Items.Count; s++)
                        {
                            ValueMapRow row = ValueMapGrid.Items.GetItemAt(s) as ValueMapRow;
                            if (row != null)
                            {
                                ValueMap.Add(new XElement("sValue", row.Source));
                                ValueMap.Add(new XElement("tValue", row.Target));
                            }
                        }
                        ValueMap.Add(new XElement("Otherwise", Method3Otherwise.Text));
                        newNode.Add(ValueMap);
                    }
                    catch { }
                    break;
                case "ChangeCase":
                    XElement changeCase = new XElement(nodeMethod, Method4Combo.Items[Method4Combo.SelectedIndex].ToString().Split(':').Last().Trim());
                    newNode.Add(changeCase);
                    break;
                case "Concatenate":
                    XElement separator = new XElement("Separator", Method5Value.Text);
                    XElement cFields = new XElement("cFields");
                    try
                    {
                        DataGrid concatGrid = this.Method5Grid as DataGrid;
                        for (int i = 0; i < concatGrid.Items.Count; i++)
                        {
                            ConcatRow row = concatGrid.Items.GetItemAt(i) as ConcatRow;
                            if (row != null)
                            {
                                if (row.Checked)
                                {
                                    cFields.Add(new XElement("cField",
                                                    new XElement("Name", row.Name)));
                                }
                            }
                        }
                        newNode.Add(separator);
                        newNode.Add(cFields);
                    }
                    catch { }
                    break;
                case "Left":
                    try
                    {
                        newNode.Add(new XElement("Left", Method6Slider.Value.ToString()));
                    }
                    catch { }
                    break;
                case "Right":
                    try
                    {
                        newNode.Add(new XElement("Right", Method7Slider.Value.ToString()));
                    }
                    catch { }
                    break;
                case "Substring":
                    try
                    {
                        newNode.Add(new XElement("Start", Method81Slider.Value.ToString()));
                        newNode.Add(new XElement("Length", Method82Slider.Value.ToString()));
                    }
                    catch { }
                    break;
                case "Split":
                    try
                    {
                        newNode.Add(new XElement("SplitAt", Method91Value.Text));
                        newNode.Add(new XElement("Part", Method92Value.Text));
                    }
                    catch { }
                    break;
                case "ConditionalValue":
                    try
                    {
                        int i;
                        if (Method10Value.SelectedIndex == -1)
                            i = 0;
                        else
                            i = Method10Value.SelectedIndex;
                        newNode.Add(new XElement("Oper", Method10Value.Items[i].ToString().Split(':').Last().Trim()));
                        newNode.Add(new XElement("If", Method101Value.Text));
                        newNode.Add(new XElement("Then", Method102Value.Text));
                        newNode.Add(new XElement("Else", Method103Value.Text));
                    }
                    catch { }
                    break;
                case "DomainMap":
                    XElement DomainMap = new XElement(nodeMethod);
                    try
                    {
                        DataGrid domainGrid = this.Method11Grid as DataGrid;
                        for (int s = 0; s < domainGrid.Items.Count; s++)
                        {
                            DomainMapRow row = domainGrid.Items.GetItemAt(s) as DomainMapRow;
                            DomainMap.Add(new XElement("sValue", row.Source[row.SourceSelectedItem].Id));
                            DomainMap.Add(new XElement("SLabel", row.Source[row.SourceSelectedItem].Tooltip));
                            DomainMap.Add(new XElement("tValue", row.Target[row.TargetSelectedItem].Id));
                            DomainMap.Add(new XElement("tLabel", row.Target[row.TargetSelectedItem].Tooltip));
                        }
                        newNode.Add(DomainMap);
                    }
                    catch { }
                    break;
                default: // Handles the Copy case and None case
                    break;
            }
            return newNode;
        }

        private void MatchLoad_Click(object sender, RoutedEventArgs e)
        {
            string xmlpath = AddinAssemblyLocation() + "\\MapLibrary.xml";

            XElement root = XElement.Load(xmlpath);
            XElement fields = root.Element("Fields");
            string path = getXmlFileName();
            XElement docRoot = XElement.Load(path);
            XElement docFields = docRoot.Element("Fields");

            IEnumerable<XElement> match =  // Searches for the corresponding match if exists
               from el in fields.Elements("Field")
               where el.Element("TargetName").Value == getTargetFieldName()
               select el;
            XElement loadField = null;
            foreach (XElement el in match)
            {
                loadField = el;
                loadField.Element("SourceName").Value = getSourceFieldName();
            }
            if(loadField != null)
            {
                //set xml file corresponding map if exists to this
                IEnumerable<XElement> docMatch =  // Searches for the corresponding match if exists
                    from el in docFields.Elements("Field")
                    where el.Element("SourceName").Value == getSourceFieldName() && el.Element("TargetName").Value == getTargetFieldName()
                    select el;
                XElement targField = null;
                foreach (XElement el in docMatch)
                    targField = el;
                if(targField != null)
                {
                    targField.ReplaceWith(loadField);
                    docRoot.Save(path);
                    MethodPanelrefreshXML_Click(null, null);
                }
            }
        } 
    }
}
