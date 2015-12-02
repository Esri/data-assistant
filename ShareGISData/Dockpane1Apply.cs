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

namespace ShareGISData
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
            // Default Value
            // make sure method is saved to Xml for the field node
            System.Xml.XmlNodeList nodes = getFieldNodes(this.FieldGrid.SelectedIndex + 1);
            if (nodes != null)
            {
                try
                {
                    nodes[0].SelectSingleNode("Method").InnerText = getMethodVal();
                    System.Xml.XmlNode node = nodes[0].LastChild.SelectSingleNode("DefaultValue");
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
                    nodes[0].SelectSingleNode("Method").InnerText = getMethodVal();
                    //DataGridRow row0 = (DataGridRow)Method3Grid.ItemContainerGenerator.ContainerFromIndex(0);
                    //TextBox txt = ((TextBox)Method3Grid.Columns[0].GetCellContent(row0));
                    System.Xml.XmlNode node = nodes[0].SelectSingleNode("ValueMap");
                    trimNodes(nodes, 3);
                    if(node != null)
                    {
                        node.RemoveAll();
                        for (int s = 0; s < grid.Items.Count; s++)
                        {
                            object values = grid.Items[s];
                            ValueMapRow row = grid.Items.GetItemAt(s) as ValueMapRow; 
                            if (row != null)
                            {
                                string source = row.Source;
                                string target = row.Target;
                                System.Xml.XmlNode snode = xml.CreateElement("sValue");
                                snode.InnerText = source;
                                node.AppendChild(snode);
                                System.Xml.XmlNode tnode = xml.CreateElement("tValue");
                                tnode.InnerText = target;
                                node.AppendChild(tnode);
                                nodes[0].AppendChild(node);
                            }

                        }
                    saveFieldGrid();
                    }
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
                    System.Xml.XmlNode cnodes = xml.CreateElement("cFields");
                    nodes[0].AppendChild(cnodes);

                    for (int i = 0; i < grid.Items.Count; i++)
                    {
                        ConcatRow row = grid.Items.GetItemAt(i) as ConcatRow;
                        if (row != null)
                        {
                            if (row.Checked == true)
                            {
                                System.Xml.XmlNode cnode = xml.CreateElement("cField");

                                System.Xml.XmlNode nm = xml.CreateElement("Name");
                                nm.InnerText = row.Name;
                                cnode.AppendChild(nm);

                                System.Xml.XmlNode chk = xml.CreateElement("Checked");
                                chk.InnerText = "True";
                                cnode.AppendChild(chk);

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
                    System.Xml.XmlNode node = nodes[0].LastChild.SelectSingleNode("If");
                    trimNodes(nodes, 3);
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
            // Expression
            System.Xml.XmlNodeList nodes = getFieldNodes(this.FieldGrid.SelectedIndex + 1);
            if (nodes != null)
            {
                try
                {
                    nodes[0].SelectSingleNode("Method").InnerText = getMethodVal();
                    System.Xml.XmlNode node = nodes[0].LastChild.SelectSingleNode("Expression");
                    trimNodes(nodes, 3);
                    if (node != null)
                        node.InnerText = Method11Value.Text;
                    else
                        addNode(nodes, getMethodVal(), Method11Value.Text);
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
        private void trimNodes(System.Xml.XmlNodeList nodes,int trimval)
        {
            while(nodes[0].ChildNodes.Count > trimval)
            {
                nodes[0].RemoveChild(nodes[0].LastChild);
            }
        }
        private void addNode(System.Xml.XmlNodeList nodes,string name,string value)
        {
            System.Xml.XmlNode nodenew = xml.CreateElement(name);
            nodenew.InnerText = value;
            nodes[0].AppendChild(nodenew);
        }
    }
}
