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

namespace ShareGISData
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
        public string getXmlFileName()
        {
            return _filename;
        }
        public void setXmlFileName(string fname)
        {
            // set to default/current value if null
            if(fname != null)
                _filename = fname;
            this.FileName.Text = _filename;
        }
        private string _filename = System.IO.Path.Combine(AddinAssemblyLocation(), "ConfigData.xml");
        System.Xml.XmlNodeList _datarows;

        string fieldXPath = "/SourceTargetMatrix/Fields/Field";
        System.Xml.XmlDocument _xml = new System.Xml.XmlDocument();
        TextInfo textInfo = new CultureInfo("en-US", false).TextInfo;
        //public int concatSequence = 0;
        private List<string> _concat = new List<string> { };
        string _noneField = "(None)";
        string _spaceVal = "(space)";
        private bool skipSelectionChanged = false;
        int _methodnum = -1;

        public Dockpane1View()
        {
            InitializeComponent();
        }
        public void loadFile(string fname)
        {
            // load the selected file
            if (fname != _filename && System.IO.File.Exists(fname))
            {
                setXmlFileName(fname);
                _xml.Load(_filename);
                this.skipSelectionChanged = true;
                setXmlDataProvider(this.FieldGrid, fieldXPath);
                this.skipSelectionChanged = false;
                setDatasetUI();
                _datarows = _xml.SelectNodes("//Data/Row");
            }
        }
        private void setDatasetUI()
        {
            SourceStack.IsEnabled = true;
            TargetStack.IsEnabled = true;
            ReplaceStack.IsEnabled = true;
            SourceStack.Visibility = System.Windows.Visibility.Visible;
            TargetStack.Visibility = System.Windows.Visibility.Visible;
            ReplaceStack.Visibility = System.Windows.Visibility.Visible;

            SourceLayer.Text = _xml.SelectSingleNode("//Datasets/Source").InnerText;
            TargetLayer.Text = _xml.SelectSingleNode("//Datasets/Target").InnerText;

            setXmlDataProvider(ReplaceField, "//TargetField/@Name");

            System.Xml.XmlNodeList nodes = _xml.SelectNodes("//Datasets/ReplaceBy");
            setReplaceValues(nodes);
            setPreviewValues(false);
            
        }
        private void setReplaceValues(System.Xml.XmlNodeList nodes)
        {
            if (nodes[0] != null)
            {
                try
                {
                    string field = getReplaceValue(nodes, "FieldName");
                    string op = getReplaceValue(nodes, "Operator");
                    string value = getReplaceValue(nodes, "Value");
                    if (field != null)
                        setReplaceValue(ReplaceField, field);
                    else
                        ReplaceField.SelectedIndex = -1;
                    if (op != null)
                        setReplaceValue(ReplaceOperator, op);
                    else
                        ReplaceOperator.SelectedIndex = -1;
                    if (value != null)
                        ReplaceValue.Text = value;
                    else
                        ReplaceValue.Text = "";
                }
                catch { MessageBox.Show("Error setting replace"); }
            }
            else
            {
                ReplaceField.SelectedIndex = -1;
                ReplaceOperator.SelectedIndex = -1;
                ReplaceValue.Text = "";
            }

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
            }           
        }
        private void setXmlDataProvider(object ctrl,string xpath)
        {
            System.Data.DataSet ds = new DataSet();
            XmlDataProvider dp = new XmlDataProvider();
            if (this.IsInitialized)
            {
                try
                {
                    dp.IsAsynchronous = false;
                    ds.ReadXml(getXmlFileName());
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
                    MessageBox.Show("Error setting Xml data provider");
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
            if (this.skipSelectionChanged)
                return;
            if(FieldGrid.SelectedIndex == -1)
                return;
            var cfg = getConfigSettingsForField();
            int methodnum = setFieldSelectionValues(cfg); // just use the int for now.
            
            setPanelVisibility(methodnum);
        }
        private System.Xml.XmlNodeList getFieldNodes(int fieldnum)
        {
            System.Xml.XmlNodeList nodes = null;
            string xpath = "//Field[position()=" + fieldnum.ToString() + "]"; // Field grid position to set
            System.Xml.XmlNodeList nodelist = _xml.SelectNodes(xpath);
            if (nodelist.Count == 1)
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
            string sname = fnodes.Item(0).SelectSingleNode("SourceName").InnerText;
            string xpath = "//SourceField[@Name='" + sname + "']"; // Source field values
            System.Xml.XmlNodeList nodelist = _xml.SelectNodes(xpath);
            if (nodelist.Count == 1)
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
                        if (val.EndsWith(node.InnerText.ToString()))
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
            setMethodVisibility(methodnum);
            _methodnum = methodnum;

            switch(methodnum){ // fill in the values for each stack panel
                case 0: // None
                    break;
                case 1: // Copy
                    break;
                case 2: // DefaultValue
                    Method2Value.Text = getPanelValue(2, "DefaultValue");
                    break;
                case 3: // ValueMap
                    setValueMapValues(3, getPanelValue(3, "ValueMap"));
                    break;
                case 4: // ChangeCase
                    setComboValue(4, getPanelValue(4, "ChangeCase"));
                    break;
                case 5: // Concatenate
                    _concat.Clear();
                    setConcatSeparator(getPanelValue(5,"Separator"));
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
                    Method91Value.Text = getPanelValue(91, "SplitAt");
                    Method92Value.Text = getPanelValue(92, "Part");
                    break;
                case 10: // Conditional Value
                    setConditionValues();
                    break;
                case 11: // Expression
                    Method11Value.Text = getPanelValue(11, "Expression");
                    break;

            }

            return methodnum;
        }
        private void setMethodVisibility(int methodnum)
        {
            if (MethodControls == null || ! MethodControls.IsInitialized)
            {
                return;
            }
            //if (methodnum < 3)
            //{
            //    MethodControls.Visibility = System.Windows.Visibility.Hidden;
            //}
            //else
            MethodControls.Visibility = System.Windows.Visibility.Visible;
            //PreviewText.Text = "";
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
 
        private void setConcatSeparator(string separator)
        {
            TextBox txt = Method5Value;
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
                if(!found && sourcename != _noneField)
                    grid.Items.Add(new ConcatRow() { Checked = found, Name = sourcename });
            }
            
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
            if (this.skipSelectionChanged)
                return;
            setFieldSelectionValues(comboMethod.SelectedIndex);
            setPanelVisibility(comboMethod.SelectedIndex);
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
                    StackPanel panel = ctrl as StackPanel;
                    if (panel != null)
                    {
                        try
                        {
                            panel.Visibility = System.Windows.Visibility.Visible;
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
                    StackPanel panel = ctrl as StackPanel;
                    if (panel != null)
                    {
                        try
                        {
                            panel.Visibility = System.Windows.Visibility.Hidden;
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

            if(check != null)
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
                            if (chk == true)
                                _concat.Add(row.Name);
                            else
                                _concat.Remove(row.Name);
                            setConcatValues();
                        }
                    }
                }

            }
        }



        private DataGridCell GetCell(DataGrid grid, DataGridRow row, int column)
        {
            if (row != null)
            {
                DataGridCellsPresenter presenter = GetVisualChild<DataGridCellsPresenter>(row);

                if (presenter == null)
                {
                    grid.ScrollIntoView(row, grid.Columns[column]);
                    presenter = GetVisualChild<DataGridCellsPresenter>(row);
                }

                DataGridCell cell = (DataGridCell)presenter.ItemContainerGenerator.ContainerFromIndex(column);
                return cell;
            }
            return null;
        }
        public T GetVisualChild<T>(Visual parent) where T : Visual
        {
            T child = default(T);
            int numVisuals = VisualTreeHelper.GetChildrenCount(parent);
            for (int i = 0; i < numVisuals; i++)
            {
                Visual v = (Visual)VisualTreeHelper.GetChild(parent, i);
                child = v as T;
                if (child == null)
                {
                    child = GetVisualChild<T>(v);
                }
                if (child != null)
                {
                    break;
                }
            }
            return child;
        }

        private void Method3Target_TextChanged(object sender, TextChangedEventArgs e)
        {
            Method3TextChanged(sender, "Target");
        }
        private void Method3Source_TextChanged(object sender, TextChangedEventArgs e)
        {
            Method3TextChanged(sender,"Source");
        }
        private void Method3TextChanged(object sender,string sourcetarget)
        {
            TextBox txt = sender as TextBox;

            if(Method3Grid.SelectedIndex == -1)
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
                //dlg.Description = "Browse for a Source-Target File (.xml)";
                System.Windows.Forms.DialogResult result = dlg.ShowDialog();
                if (result == System.Windows.Forms.DialogResult.OK)
                {
                    //this.FileName.Text = dlg.FileName;
                    loadFile(dlg.FileName);
                }
            }

        }

        private void FileName_TextChanged(object sender, TextChangedEventArgs e)
        {
            TextBox txt = sender as TextBox;
            loadFile(txt.Text);
        }
        /// <summary>
        /// SCRAP Heap
        /// </summary>
        private DataRowView rowBeingEdited = null;

        private void Method3Grid_CurrentCellChanged(object sender, EventArgs e)
        {

            DataGrid dataGrid = sender as DataGrid;
            DataGridRow row = (DataGridRow)dataGrid.ItemContainerGenerator.ContainerFromIndex(0);
            DataGridCell rowColumn = dataGrid.Columns[0].GetCellContent(row).Parent as DataGridCell;

            DataGridCell cell = GetCell(Method3Grid, row, 1);
            var cellValue = rowColumn.Content;
            if (cellValue != null)
            {
                ValueMapRow vmrow = rowColumn.Content as ValueMapRow;
                //string currValue = vmrow.Target;
            }
        }
        private void Method3Grid_CellEditEndingx(object sender, DataGridCellEditEndingEventArgs e)
        {
            DataRowView rowView = e.Row.Item as DataRowView;
            rowBeingEdited = rowView;

        }
        private bool isManualEditCommit;
        private void Method3Grid_CellEditEnding(object sender, DataGridCellEditEndingEventArgs e)
        {
            if (!isManualEditCommit)
            {
                isManualEditCommit = true;
                DataGrid grid = (DataGrid)sender;
                grid.CommitEdit(DataGridEditingUnit.Row, true);
                isManualEditCommit = false;
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
                Method3Grid.Items.RemoveAt(Method3Grid.SelectedIndex);
        }

        private void Method5Value_TextChanged(object sender, TextChangedEventArgs e)
        {
            TextBox txt = sender as TextBox;
            if (txt.Text.IndexOf(" ") > -1)
                txt.Text = txt.Text.Replace(" ", _spaceVal);

        }

        private void SourceField_SelectionChanged(object sender, SelectionChangedEventArgs e)
        {
            if (this.skipSelectionChanged)
                return;

            var comboBox = sender as ComboBox;
            int fieldnum = FieldGrid.SelectedIndex + 1;
            var nodes = getFieldNodes(fieldnum);
            if (nodes != null && comboBox != null) 
            {
                try
                {
                    string selected = comboBox.SelectedValue.ToString();
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
            if (node != null && node.InnerText != txt.Text)
                node.InnerText = txt.Text;

        }

        private void SourceLayer_TextChanged(object sender, TextChangedEventArgs e)
        {
            TextBox txt = sender as TextBox;
            if (txt != null && txt.Text != "")
            {
                System.Xml.XmlNode node = _xml.SelectSingleNode("//Datasets/Source");
                if (node != null && node.InnerText != txt.Text)
                    node.InnerText = txt.Text;
            }
        }

        private void ReplaceField_SelectionChanged(object sender, SelectionChangedEventArgs e)
        {
            ComboBox combo = sender as ComboBox;
            if (combo != null && combo.SelectedIndex != -1)
            {
                System.Xml.XmlNode node = _xml.SelectSingleNode("//Datasets/ReplaceBy/FieldName");
                if (node == null || node.InnerText != combo.SelectionBoxItem.ToString())
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
                    updateReplaceNodes();
            }
        }
    }
}
