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

namespace DataAssistant
{
    public partial class Dockpane1View : UserControl
    {
        private void Method0Preview_Click()
        {
            setPreviewRows(null);
        }
        private void Method1Preview_Click()
        {
            setPreviewRows(getSourceFieldName());
        }
        private void Method2Preview_Click()
        {
            setPreviewRows(Method2Value.Text);
        }
        private void Method3Preview_Click()
        {
            setPreviewValueMapRows(getSourceFieldName());
        }
        private void Method4Preview_Click()
        {
            DataGrid grid = PreviewGrid;
            grid.Items.Clear();
            object obj = Method4Combo;
            ComboBox combo = obj as ComboBox;
            string val = combo.SelectionBoxItem as string;
            string targName = getTargetFieldName();
            string attrName = getSourceFieldName();
            for (int i = 0; i < _datarows.Count; i++)
            {
                string textval = "";
                try
                {
                    System.Xml.XmlAttribute att = _datarows[i].Attributes[attrName];
                    if (att != null)
                    {
                        switch (val)
                        {
                            case "Uppercase":
                                textval = textInfo.ToUpper(att.InnerText);
                                break;
                            case "Lowercase":
                                textval = textInfo.ToLower(att.InnerText);
                                break;
                            case "Title":
                                textval = textInfo.ToTitleCase(att.InnerText.ToLower());
                                break;
                            case "Capitalize":
                                textval = char.ToUpper(att.InnerText[0]) + att.InnerText.Substring(1).ToLower();
                                break;
                        }
                    }
                    textval = targName + "=" + textval;
                }
                catch { textval = targName + "=" + "None"; }
                grid.Items.Add(new PreviewRow() { Value = textval });
            }
        }
        private void Method5Preview_Click()
        {
            string name = "Method" + 5 + "Grid";
            object ctrl = this.FindName(name);
            DataGrid grid = ctrl as DataGrid;
            if (grid == null)
                return;
            string theval = "";
            string sepvalue = "";
            try
            { sepvalue = this.Method5Value.Text.Replace("(space)", " ");}
            catch{}

            for (int i = 0; i < grid.Items.Count; i++)
            {
                ConcatRow row = grid.Items.GetItemAt(i) as ConcatRow;
                if (row != null)
                {
                    if (row.Checked == true)
                    {
                        theval += row.Name + sepvalue;
                    }
                }
            }
            if (theval.EndsWith(sepvalue))
                theval = theval.Substring(0, theval.LastIndexOf(sepvalue));
            setPreviewRows(theval);
        }

        private void Method6Preview_Click()
        {
            // Left
            int num;
            string name = "Method" + 6 + "Slider";
            Object ctrl = this.FindName(name);
            Slider slide = ctrl as Slider;
            if (slide != null)
            {
                Int32.TryParse(slide.Value.ToString(), out num);
                setPreviewSubstringRows(getSourceFieldName(),0, num);
            }
        }

        private void Method7Preview_Click()
        {
            // Right
            int num;
            string name = "Method" + 7 + "Slider";
            Object ctrl = this.FindName(name);
            Slider slide = ctrl as Slider;
            if (slide != null)
            {
                Int32.TryParse(slide.Value.ToString(), out num);
                //int start = sampleText.Length - num;
                setPreviewSubstringRows(getSourceFieldName(),num, -1);
            }
        }

        private void Method8Preview_Click()
        {
            // Substring
            string name = "Method" + 81 + "Slider";
            Object ctrl = this.FindName(name);
            Slider slide1 = ctrl as Slider;
            name = "Method" + 82 + "Slider";
            ctrl = this.FindName(name);
            Slider slide2 = ctrl as Slider;

            if (slide1 != null && slide2 != null)
            {
                int num;
                Int32.TryParse(slide1.Value.ToString(), out num);
                int start = num;
                Int32.TryParse(slide2.Value.ToString(), out num);
                int len = num;
                setPreviewSubstringRows(getSourceFieldName(),start, len);
            }
        }
        private void Method9Preview_Click()
        {
            DataGrid grid = PreviewGrid;
            grid.Items.Clear();
            string targName = getTargetFieldName();
            string attrName = getSourceFieldName();
            for (int i = 0; i < _datarows.Count; i++)
            {
                string textval = "";
                try
                {
                    string res = "";
                    System.Xml.XmlAttribute att = _datarows[i].Attributes[attrName];
                    if (att != null)
                    {
                        try
                        {
                            string txt = Method91Value.Text.Replace(_spaceVal, " ");
                            var split = att.InnerText.Split(txt.ToCharArray());
                            int num;
                            Int32.TryParse(Method92Value.Text, out num);
                            res = split[num];
                            textval = res;
                        }
                        catch { res = "Error"; }
                    }
                    textval = targName + "=" + res;
                }
                catch { textval = targName + "=" + "None"; }
                grid.Items.Add(new PreviewRow() { Value = textval });
            }

        }

        private void Method10Preview_Click()
        {
            string fname = getSourceFieldName();
            string val = "'" + Method102Value.Text + "' if '" + fname + "' " + Method10Value.Text + " '" + Method101Value.Text + "' else '" + Method103Value.Text + "'";
            setPreviewRows(val);
        }

        private void Method11Preview_Click()
        {
            setPreviewDomainMapRows(getSourceFieldName());
        }
        private void showResult(string value)
        {
            try
            {
                //MessageBox.Show(value);
                //PreviewText.Text = value;
            }
            catch
            {MessageBox.Show("Unable to preview results");}
        }
        private System.Xml.XmlNodeList getDataNodes()
        {
            string xpath = "//Data/Row"; // xpath for Rows
            System.Xml.XmlNodeList nodelist = _xml.SelectNodes(xpath);
            return nodelist;
        }
        //private void ClickLabel(object sender, MouseButtonEventArgs e)
        //{
        //    showResult("Click");
        //}
        private void ClickPreviewButton(object sender, RoutedEventArgs e)
        {
            if(_methodnum < 0 || PreviewCheckBox.IsChecked == false)
                return;
            switch (_methodnum) { // preview values for each stack panel
                case 0: // None
                    Method0Preview_Click();
                    break;
                case 1: // Copy
                    Method1Preview_Click();
                    break;
                case 2: // SetValue
                    Method2Preview_Click();
                    break;
                case 3: // ValueMap
                    Method3Preview_Click();
                    break;
                case 4: // ChangeCase
                    Method4Preview_Click();
                    break;
                case 5: // Concatenate
                    Method5Preview_Click();
                    break;
                case 6: // Left
                    Method6Preview_Click();
                    break;
                case 7: // Right
                    Method7Preview_Click();
                    break;
                case 8: // Substring
                    Method8Preview_Click();
                    break;
                case 9: // Split
                    Method9Preview_Click();
                    break;
                case 10: // Conditional Value
                    Method10Preview_Click();
                    break;
                case 11: // Expression
                    Method11Preview_Click();
                    break;

            }
        }
        private void PreviewCheckBox_Checked(object sender, RoutedEventArgs e)
        {
            CheckBox chk = sender as CheckBox;
            if (chk != null) 
            {
                setPreviewValues(chk.IsChecked);
            }
        }

        private void setPreviewValues(bool? onoff)
        {
            if (onoff == false && PreviewCheckBox.IsChecked == false)
            {
                PreviewGrid.Items.Clear();
                PreviewGrid.Height = 0;
                PreviewGrid.InvalidateArrange();
            }
            else if (onoff == true || PreviewCheckBox.IsChecked == true)
            {
                PreviewGrid.Height = 100;
                setPreviewRowsInit();
                PreviewGrid.InvalidateArrange();
            }

        }
        private void setPreviewRowsInit()
        {
            DataGrid grid = PreviewGrid;
            grid.Items.Clear();

            string textval = "";
            textval = "Click Apply to Preview";
            grid.Items.Add(new PreviewRow() { Value = textval });


        }
        private void setPreviewRows(string attrName)
        {
            DataGrid grid = PreviewGrid;
            grid.Items.Clear();
            string targName = getTargetFieldName();
            for (int i = 0; i < _datarows.Count; i++)
            {
                string textval = "";
                try
                {
                    if(attrName == null)
                        textval = targName + "=None";
                    else
                    {
                        System.Xml.XmlAttribute att = _datarows[i].Attributes[attrName];
                        if (att != null)
                            textval = targName + "=\"" + att.InnerText + "\"";
                        else
                        {
                            //textval = targName + "=" + attrName;
                            textval = targName + "=\"" + replaceFieldValues(attrName, i) + "\"";
                            //MessageBox.Show(textval);
                        }   
                    }
                }
                catch { textval = targName + "=" + "None"; }
                grid.Items.Add(new PreviewRow() { Value = textval });
            }
        }
        private void setPreviewSubstringRows(string attrName, int start, int length)
        {
            DataGrid grid = PreviewGrid;
            grid.Items.Clear();
            string targName = getTargetFieldName();
            for (int i = 0; i < _datarows.Count; i++)
            {
                string textval = "";
                try
                {
                    if (attrName == null)
                        textval = targName + "=None";
                    else
                    {
                        System.Xml.XmlAttribute att = _datarows[i].Attributes[attrName];
                        if (att != null)
                        {
                            try
                            {
                                if (length == -1)
                                {
                                    // num chars for right function
                                    textval = targName + "=" + att.InnerText.Substring(att.InnerText.Length - start);
                                }
                                else
                                {
                                    textval = targName + "=" + att.InnerText.Substring(start, length);
                                }
                            }
                            catch { textval = targName + "=" + "None"; }
                        }
                    }
                }
                catch { textval = targName + "=" + "None"; }
                grid.Items.Add(new PreviewRow() { Value = textval });
            }
        }
        private void setPreviewValueMapRows(string attrName)
        {
            DataGrid grid = PreviewGrid;
            grid.Items.Clear();
            string targName = getTargetFieldName();
            for (int i = 0; i < _datarows.Count; i++)
            {
                string textval = "";
                try
                {
                    if (attrName == null)
                        textval = targName + "=None";
                    else
                    {
                        System.Xml.XmlAttribute att = _datarows[i].Attributes[attrName];
                        if (att != null)
                        {
                            try
                            {
                                textval = att.InnerText;
                                for (int r = 0; r < Method3Grid.Items.Count; r++)
                                {
                                    // value map replace function
                                    ValueMapRow row = Method3Grid.Items.GetItemAt(r) as ValueMapRow;
                                    if(att.InnerText.ToString() == row.Source.ToString())
                                    {
                                        textval = textval.Replace(row.Source, row.Target);                 
                                    }
                                    else if(Method3Otherwise.Text != "" && Method3Otherwise.Text != null)
                                    { 
                                        textval = Method3Otherwise.Text; 
                                    }
                                }
                                textval = targName + "=" + textval;
                            }
                            catch { textval = targName + "=" + "None"; }
                        }
                    }
                }
                catch { textval = targName + "=" + "None"; }
                grid.Items.Add(new PreviewRow() { Value = textval });
            }
        }

        private void setPreviewDomainMapRows(string attrName)
        {
            DataGrid grid = PreviewGrid;
            grid.Items.Clear();
            string targName = getTargetFieldName();
            for (int i = 0; i < _datarows.Count; i++)
            {
                string textval = "";
                try
                {
                    if (attrName == null)
                        textval = targName + "=None";
                    else
                    {
                        System.Xml.XmlAttribute att = _datarows[i].Attributes[attrName]; // the data rows from source dataset
                        if (att != null)
                        {
                            try
                            {
                                textval = att.InnerText.ToString();
                                for (int r = 0; r < Method11Grid.Items.Count; r++)
                                {
                                    // domain map replace function
                                    DomainMapRow row = Method11Grid.Items.GetItemAt(r) as DomainMapRow;
                                    if (att.InnerText.ToString() == row.Source[row.SourceSelectedItem].Id)
                                    {
                                        textval = textval.Replace(row.Source[row.SourceSelectedItem].Id, row.Target);
                                    }
                                }
                                textval = targName + "=" + textval;
                            }
                            catch { textval = targName + "=" + "None"; }
                        }
                    }
                }
                catch { textval = targName + "=" + "None"; }
                grid.Items.Add(new PreviewRow() { Value = textval });
            }
        }

        private string replaceFieldValues(string expr, int rownum)
        {
            for (int i = 0; i < _datarows.Count; i++)
            {
                if (i == rownum)
                {
                    foreach (System.Xml.XmlAttribute att in _datarows[i].Attributes)
                    {
                        try
                        {
                            string val = att.InnerText;
                            expr = expr.Replace(att.Name, val);
                        }
                        catch {  }
                    }
                }
            }
            return expr;

        }
        
        
        private StackPanel getVisiblePanel()
        {
            for (int i = 0; i <= comboMethod.Items.Count; i++)
            {
                string method = "Method" + i;
                Object ctrl = this.FindName(method);
                StackPanel panel = ctrl as StackPanel;
                if (panel != null)
                {
                    return panel;
                }
            }
            return null;
        }

    }


}
