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
        private void Method4Preview_Click(object sender, RoutedEventArgs e)
        {
            object obj = Method4Combo;
            ComboBox combo = obj as ComboBox;
            string val = combo.SelectionBoxItem as string;
            if (val != null)
                switch (val)
                {
                    case "Uppercase":
                        MessageBox.Show(textInfo.ToUpper(sampleText));
                        break;
                    case "Lowercase":
                        MessageBox.Show(textInfo.ToLower(sampleText));
                        break;
                    case "Title":
                        MessageBox.Show(textInfo.ToTitleCase(sampleText));
                        break;
                    case "Capitalize":
                        MessageBox.Show(char.ToUpper(sampleText[0]) + sampleText.Substring(1));
                        break;
                }
        }
        private void Method5Preview_Click(object sender, RoutedEventArgs e)
        {
            showPreview5();
        }

        private void showPreview5()
        {
            string sep1 = "+\"";
            string sep2 = "\"+";
            string name = "Method" + 5 + "Grid";
            object ctrl = this.FindName(name);
            DataGrid grid = ctrl as DataGrid;
            if (grid == null)
                return;
            string theval = "";
            for (int i = 0; i < grid.Items.Count; i++)
            {
                ConcatRow row = grid.Items.GetItemAt(i) as ConcatRow;
                if (row != null)
                {
                    if (row.Checked == true)
                        theval += row.Name + sep1 + this.Method5Value.Text + sep2;
                }
            }
            if (theval.EndsWith(sep2))
                theval = theval.Substring(0, theval.LastIndexOf(sep1));
            MessageBox.Show(theval);
        }
        private void Method6Preview_Click(object sender, RoutedEventArgs e)
        {
            // Left
            int num;
            string name = "Method" + 6 + "Slider";
            Object ctrl = this.FindName(name);
            Slider slide = ctrl as Slider;
            if (slide != null)
            {
                Int32.TryParse(slide.Value.ToString(), out num);
                MessageBox.Show(sampleText.Substring(0, num));
            }
        }

        private void Method7Preview_Click(object sender, RoutedEventArgs e)
        {
            // Right
            int num;
            string name = "Method" + 7 + "Slider";
            Object ctrl = this.FindName(name);
            Slider slide = ctrl as Slider;
            if (slide != null)
            {
                Int32.TryParse(slide.Value.ToString(), out num);
                int start = sampleText.Length - num;

                MessageBox.Show(sampleText.Substring(start));
            }
        }

        private void Method8Preview_Click(object sender, RoutedEventArgs e)
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
                MessageBox.Show(sampleText.Substring(start, len));
            }
        }
        private void Method9Preview_Click(object sender, RoutedEventArgs e)
        {
            try
            {
                var split = sampleText.Split(Method91Value.Text.ToCharArray());
                int num;
                Int32.TryParse(Method92Value.Text, out num);
                string res = split[num];
                MessageBox.Show(res);
            }
            catch { }
        }

        private void Method10Preview_Click(object sender, RoutedEventArgs e)
        {
            int fieldnum = FieldGrid.SelectedIndex + 1;
            System.Xml.XmlNodeList nodes = getFieldNodes(fieldnum);
            System.Xml.XmlNode thenode = nodes.Item(0).SelectSingleNode("SourceName");
            string val = Method102Value.Text + " if " + thenode.InnerText + " " + Method101Value.Text + " else " + Method103Value.Text;
            MessageBox.Show(val);
        }

        private void Method11Preview_Click(object sender, RoutedEventArgs e)
        {
            MessageBox.Show(Method11Value.Text.Replace("!", ""));
        }

    }


}
