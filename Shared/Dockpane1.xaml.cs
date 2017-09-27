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
    }
}
