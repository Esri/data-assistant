/***
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
using ArcGIS.Desktop.Core;
using ArcGIS.Desktop.Catalog;

namespace DataAssistant
{
    public partial class Dockpane1View : UserControl
    {
        private void MethodPanelCancel_Click(object sender, RoutedEventArgs e)
        {
            // Just reload
            setFieldSelectionValues(comboMethod.SelectedIndex);
            setPanelVisibility(comboMethod.SelectedIndex);
        }
        private void MethodPanelApply_Click(object sender, RoutedEventArgs e)
        {
            // Figure out which panel is visible and then write the document section for the panel
            _skipSelectionChanged = true;
            if(Method0.IsVisible)
                saveM0();
            else if(Method1.IsVisible)
                saveM1();
            else if (Method2.IsVisible)
                saveM2();
            else if (Method3.IsVisible)
                saveM3();
            else if (Method4.IsVisible)
                saveM4();
            else if (Method5.IsVisible)
                saveM5();
            else if (Method6.IsVisible)
                saveM6();
            else if (Method7.IsVisible)
                saveM7();
            else if (Method8.IsVisible)
                saveM8();
            else if (Method9.IsVisible)
                saveM9();
            else if (Method10.IsVisible)
                saveM10();
            else if (Method11.IsVisible)
                saveM11();
            ClickPreviewButton(sender, e);
            _skipSelectionChanged = false;
        }
        private void MethodPanelrefreshXML_Click(object sender, RoutedEventArgs e)
        {
                try
                {
                    if (loadXml(_filename))
                    {
                        this._skipSelectionChanged = true;
                        setXmlDataProvider(this.FieldGrid, fieldXPath);
                        this._skipSelectionChanged = false;
                        setDatasetUI();
                        _datarows = _xml.SelectNodes("//Data/Row");
                    }
                }
                catch{
                    //Usually catches due to an error in the XML file load
            }
        }
        private void saveM0()
        {
            // make sure method is saved to Xml for the field node
            System.Xml.XmlNodeList nodes = getFieldNodes(this.FieldGrid.SelectedIndex + 1);
            if (nodes != null)
            {
                try
                {
                    nodes[0].SelectSingleNode("Method").InnerText= getMethodVal();
                    trimNodes(nodes,3);
                    saveFieldGrid();
                }
                catch { }
            }
        }
        private void saveM1()
        {
            // make sure method is saved to Xml for the field node
            System.Xml.XmlNodeList nodes = getFieldNodes(this.FieldGrid.SelectedIndex + 1);
            if (nodes != null)
            {
                try
                {
                    nodes[0].SelectSingleNode("Method").InnerText = getMethodVal();
                    trimNodes(nodes, 3);
                    saveFieldGrid();
                }
                catch { }
            }
        }
        private void saveM2()
        {
            // Set Value
            // make sure method is saved to Xml for the field node
            System.Xml.XmlNodeList nodes = getFieldNodes(this.FieldGrid.SelectedIndex + 1);
            if (nodes != null)
            {
                try
                {
                    nodes[0].SelectSingleNode("Method").InnerText = getMethodVal();
                    System.Xml.XmlNode node = nodes[0].LastChild.SelectSingleNode("SetValue");
                    trimNodes(nodes, 3);
                    if (node != null)
                        node.InnerText = Method2Value.Text;
                    else
                        addNode(nodes, getMethodVal(), Method2Value.Text);
                    saveFieldGrid();
                }
                catch { }
            }
        }
        private void saveM3()
        {
            // Value Map
            System.Xml.XmlNodeList nodes = getFieldNodes(this.FieldGrid.SelectedIndex + 1);
            if (nodes != null)
            {
                DataGrid grid = this.Method3Grid as DataGrid;
                if (grid == null)
                    return;

                try
                {
                    string method = getMethodVal();
                    nodes[0].SelectSingleNode("Method").InnerText = method;
                    //DataGridRow row0 = (DataGridRow)Method3Grid.ItemContainerGenerator.ContainerFromIndex(0);
                    //TextBox txt = ((TextBox)Method3Grid.Columns[0].GetCellContent(row0));
                    trimNodes(nodes, 3);
                    System.Xml.XmlNode noder = nodes[0].SelectSingleNode(method);
                    if (noder == null)
                    {
                        noder = _xml.CreateElement(method);
                        nodes[0].AppendChild(noder);
                    }
                    noder.RemoveAll();
                    for (int s = 0; s < grid.Items.Count; s++)
                    {
                        object values = grid.Items[s];
                        ValueMapRow row = grid.Items.GetItemAt(s) as ValueMapRow; 
                        if (row != null)
                        {
                            System.Xml.XmlNode snode = _xml.CreateElement("sValue");
                            snode.InnerText = row.Source;
                            noder.AppendChild(snode);
                            System.Xml.XmlNode tnode = _xml.CreateElement("tValue");
                            tnode.InnerText = row.Target;
                            noder.AppendChild(tnode);
                        }
                    }
                    System.Xml.XmlNode othnode = _xml.CreateElement("Otherwise");
                    string oth = Method3Otherwise.Text;
                    if (oth.StartsWith("\n ") || oth.Equals(""))
                        oth = "None";
                    othnode.InnerText = oth;
                    noder.AppendChild(othnode);
                    saveFieldGrid();
                }
                catch { }
            }
        }

        private void saveM4()
        {
            // Change Case
            System.Xml.XmlNodeList nodes = getFieldNodes(this.FieldGrid.SelectedIndex + 1);
            if (nodes != null)
            {
                try
                {
                    nodes[0].SelectSingleNode("Method").InnerText = getMethodVal();
                    System.Xml.XmlNode node = nodes[0].LastChild.SelectSingleNode("ChangeCase");
                    trimNodes(nodes, 3);
                    if (node != null)
                        node.InnerText = Method4Combo.Text;
                    else
                        addNode(nodes, getMethodVal(), Method4Combo.Text);
                    saveFieldGrid();
                }
                catch { }
            }

        }
        private void saveM5()
        {
            // Concat
            System.Xml.XmlNodeList nodes = getFieldNodes(this.FieldGrid.SelectedIndex + 1);
            if (nodes != null)
            {
                try
                {
                    nodes[0].SelectSingleNode("Method").InnerText = getMethodVal();
                    System.Xml.XmlNode node = nodes[0].LastChild.SelectSingleNode("Concatenate");
                    trimNodes(nodes, 3);
                    addNode(nodes, "Separator", Method5Value.Text);

                    DataGrid grid = this.Method5Grid as DataGrid;
                    if (grid == null)
                        return;
                    System.Xml.XmlNode cnodes = _xml.CreateElement("cFields");
                    nodes[0].AppendChild(cnodes);

                    for (int i = 0; i < grid.Items.Count; i++)
                    {
                        ConcatRow row = grid.Items.GetItemAt(i) as ConcatRow;
                        if (row != null)
                        {
                            if (row.Checked == true)
                            {
                                System.Xml.XmlNode cnode = _xml.CreateElement("cField");

                                System.Xml.XmlNode nm = _xml.CreateElement("Name");
                                nm.InnerText = row.Name;
                                cnode.AppendChild(nm);

                                // not writing these nodes since assuming row order and only writing checked items.
                                //System.Xml.XmlNode chk = _xml.CreateElement("Checked");
                                //chk.InnerText = "True";
                                //cnode.AppendChild(chk);

                                //System.Xml.XmlNode seq = _xml.CreateElement("Sequence");
                                //chk.InnerText = i.ToString(); // write in row order
                                //cnode.AppendChild(chk); 

                                cnodes.AppendChild(cnode);
                            }
                        }
                    }
                    saveFieldGrid();                
                }
                catch { }
            }

        }
        private void saveM6()
        {
            // Left
            // make sure method is saved to Xml for the field node
            System.Xml.XmlNodeList nodes = getFieldNodes(this.FieldGrid.SelectedIndex + 1);
            if (nodes != null)
            {
                try
                {
                    nodes[0].SelectSingleNode("Method").InnerText = getMethodVal();
                    System.Xml.XmlNode node = nodes[0].LastChild.SelectSingleNode("Left");
                    trimNodes(nodes, 3);
                    if (node != null)
                        node.InnerText = Method6Slider.Value.ToString();
                    else
                        addNode(nodes, getMethodVal(), Method6Slider.Value.ToString());
                    saveFieldGrid();
                }
                catch { }
            }

        }
        private void saveM7()
        {
            // Right
            System.Xml.XmlNodeList nodes = getFieldNodes(this.FieldGrid.SelectedIndex + 1);
            if (nodes != null)
            {
                try
                {
                    nodes[0].SelectSingleNode("Method").InnerText = getMethodVal();
                    System.Xml.XmlNode node = nodes[0].LastChild.SelectSingleNode("Right");
                    trimNodes(nodes, 3);
                    if (node != null)
                        node.InnerText = Method7Slider.Value.ToString();
                    else
                        addNode(nodes, getMethodVal(), Method7Slider.Value.ToString());
                    saveFieldGrid();
                }
                catch { }
            }
        }
        private void saveM8()
        {
            // Substring
            System.Xml.XmlNodeList nodes = getFieldNodes(this.FieldGrid.SelectedIndex + 1);
            if (nodes != null)
            {
                try
                {
                    nodes[0].SelectSingleNode("Method").InnerText = getMethodVal();
                    System.Xml.XmlNode node = nodes[0].LastChild.SelectSingleNode("Start");
                    trimNodes(nodes, 3);
                    if (node != null)
                        node.InnerText = Method81Slider.Value.ToString();
                    else
                        addNode(nodes, "Start", Method81Slider.Value.ToString());
                    node = nodes[0].LastChild.SelectSingleNode("Length");
                    if (node != null)
                        node.InnerText = Method82Slider.Value.ToString();
                    else
                        addNode(nodes, "Length", Method82Slider.Value.ToString());
                    saveFieldGrid();
                }
                catch { }
            }
        }
        private void saveM9()
        {
            // Split
            System.Xml.XmlNodeList nodes = getFieldNodes(this.FieldGrid.SelectedIndex + 1);
            if (nodes != null)
            {
                try
                {
                    nodes[0].SelectSingleNode("Method").InnerText = getMethodVal();
                    System.Xml.XmlNode node = nodes[0].LastChild.SelectSingleNode("SplitAt");
                    trimNodes(nodes, 3);
                    if (node != null)
                        node.InnerText = Method91Value.Text;
                    else
                        addNode(nodes, "SplitAt", Method91Value.Text);
                    node = nodes[0].LastChild.SelectSingleNode("Part");
                    if (node != null)
                        node.InnerText = Method92Value.Text;
                    else
                        addNode(nodes, "Part", Method92Value.Text);

                    saveFieldGrid();
                }
                catch { }
            }
        }
        private void saveM10()
        {
            // ConditionalValue
            System.Xml.XmlNodeList nodes = getFieldNodes(this.FieldGrid.SelectedIndex + 1);
            if (nodes != null)
            {
                try
                {
                    nodes[0].SelectSingleNode("Method").InnerText = getMethodVal();
                    System.Xml.XmlNode node = nodes[0].LastChild.SelectSingleNode("Oper");
                    trimNodes(nodes, 3);
                    if (node != null)
                        node.InnerText = Method10Value.Text;
                    else
                        addNode(nodes, "Oper", Method10Value.Text);

                    node = nodes[0].LastChild.SelectSingleNode("If");
                    if (node != null)
                        node.InnerText = Method101Value.Text;
                    else
                        addNode(nodes, "If", Method101Value.Text);

                    node = nodes[0].LastChild.SelectSingleNode("Then");
                    if (node != null)
                        node.InnerText = Method102Value.Text;
                    else
                        addNode(nodes, "Then", Method102Value.Text);

                    node = nodes[0].LastChild.SelectSingleNode("Else");
                    if (node != null)
                        node.InnerText = Method103Value.Text;
                    else
                        addNode(nodes, "Else", Method103Value.Text);

                    saveFieldGrid();
                }
                catch { }
            }

        }
        private void saveM11()
        {
            // DomainMap
            System.Xml.XmlNodeList nodes = getFieldNodes(this.FieldGrid.SelectedIndex + 1);
            if (nodes != null)
            {
                DataGrid grid = this.Method11Grid as DataGrid;
                if (grid == null)
                    return;
                try
                {
                    string method = getMethodVal();
                    nodes[0].SelectSingleNode("Method").InnerText = method;
                    trimNodes(nodes, 3);
                    System.Xml.XmlNode noder = nodes[0].SelectSingleNode(method);
                    if (noder == null)
                    {
                        noder = _xml.CreateElement(method);
                        nodes[0].AppendChild(noder);
                    }
                    noder.RemoveAll();
                    for (int s = 0; s < grid.Items.Count; s++)
                    {
                        object values = grid.Items[s];
                        DomainMapRow row = grid.Items.GetItemAt(s) as DomainMapRow;
                        if (row != null)
                        {
                            System.Xml.XmlNode snode = _xml.CreateElement("sValue");
                            if (row.SourceSelectedItem > -1) // there may not be a selection
                            {
                                snode.InnerText = row.Source[row.SourceSelectedItem].Id;
                                noder.AppendChild(snode);
                                snode = _xml.CreateElement("sLabel");
                                snode.InnerText = row.Source[row.SourceSelectedItem].Tooltip;
                                noder.AppendChild(snode);
                            }
                            else
                            {
                                snode.InnerText = _noneField;
                                noder.AppendChild(snode);
                                snode = _xml.CreateElement("sLabel");
                                snode.InnerText = _noneField;
                                noder.AppendChild(snode);
                            }
                            System.Xml.XmlNode tnode = _xml.CreateElement("tValue");
                            tnode.InnerText = row.Target[row.TargetSelectedItem].Id;
                            noder.AppendChild(tnode);

                            tnode = _xml.CreateElement("tLabel");
                            tnode.InnerText = row.Target[row.TargetSelectedItem].Tooltip;
                            noder.AppendChild(tnode);
                        }
                    }
                    saveFieldGrid();
                }
                catch { }
            }
        }
        private string getMethodVal()
        {
            string method = comboMethod.SelectedValue.ToString();
            method = method.Substring(method.LastIndexOf(':') + 2);
            return method;
        }
        private void SourceButton_Click(object sender, RoutedEventArgs e)
        {
            System.Xml.XmlNode node = _xml.SelectSingleNode("//Datasets/Source");
            string fileloc = getSourceTargetLocation("", "Select Target Dataset");
            if (fileloc != null)
            {
                if (System.Windows.Forms.MessageBox.Show("You should only Change the source dataset if the schemas match", "Update Source Layer?", System.Windows.Forms.MessageBoxButtons.YesNo) == System.Windows.Forms.DialogResult.Yes)
                    SourceLayer.Text = fileloc;
            }
        }
        private void TargetButton_Click(object sender, RoutedEventArgs e)
        {
            System.Xml.XmlNode node = _xml.SelectSingleNode("//Datasets/Target");
            string fileloc = getSourceTargetLocation("", "Select Target");
            if (fileloc != null)
            {
                if (System.Windows.Forms.MessageBox.Show("You should only Change the target dataset if the schemas match", "Update Target Layer?", System.Windows.Forms.MessageBoxButtons.YesNo) == System.Windows.Forms.DialogResult.Yes)
                    TargetLayer.Text = fileloc;
            }
        }
        private string getSourceTargetLocation(string initialLocation, string title)
        {
            string thePath = "";
            var dlg = new ArcGIS.Desktop.Catalog.OpenItemDialog();
            {
                dlg.Title = title;
                dlg.InitialLocation = initialLocation;
                dlg.MultiSelect = false;
                bool? result = dlg.ShowDialog();
                if (result == true)
                {
                    IEnumerable<Item> items = dlg.Items;
                    foreach (Item selectedItem in items)
                        thePath = selectedItem.Path;
                }
            }
            return thePath;
        }
        private void updateReplaceNodes()
        {
            // Replace By Field value selection
            System.Xml.XmlNode dsnode = _xml.SelectSingleNode("//Datasets");
            System.Xml.XmlNodeList nodes;
            System.Xml.XmlNode nodenew;
            nodes = _xml.SelectNodes("//ReplaceBy");
            if (nodes[0] == null)
            {
                nodenew = _xml.CreateElement("ReplaceBy");
                dsnode.AppendChild(nodenew);
                nodes = _xml.SelectNodes("//ReplaceBy");
            }
            else
                trimNodes(nodes, 0);
            if (nodes != null)
            {
                if (ReplaceField.SelectedIndex != -1)
                {
                    object content = ReplaceField.SelectedItem;
                    System.Xml.XmlAttribute item = content as System.Xml.XmlAttribute;
                    if (item != null)
                    {
                        string txt = item.InnerText;
                        addNode(nodes, "FieldName", txt);
                    }
                }
                if (ReplaceOperator.SelectedIndex != -1)
                {
                    object content = ReplaceOperator.SelectedItem;
                    ComboBoxItem item = content as ComboBoxItem;
                    if (item != null)
                    {
                        string txt = item.Content.ToString();
                        addNode(nodes, "Operator", txt);
                    }
                }
                if(ReplaceValue.Text != null && ReplaceValue.Text != "")
                    addNode(nodes, "Value", ReplaceValue.Text);
                saveFieldGrid();
            }
        }        
        private void trimNodes(System.Xml.XmlNodeList nodes,int trimval)
        {
            if (nodes != null && nodes[0] != null)
            {
                while (nodes[0].ChildNodes.Count > trimval)
                    nodes[0].RemoveChild(nodes[0].LastChild);
            }
        }
        private void addNode(System.Xml.XmlNodeList nodes,string name,string value)
        {
            if (nodes != null && value != null)
            {
                System.Xml.XmlNode nodenew = _xml.CreateElement(name);
                nodenew.InnerText = value;
                nodes[0].AppendChild(nodenew);
            }
        }
    }
}
