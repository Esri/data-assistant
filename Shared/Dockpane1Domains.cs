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
        private void setDomainMapValues(int combonum, string nodename)
        {
            if (FieldGrid.SelectedIndex == -1)
                return;
            int fieldnum = FieldGrid.SelectedIndex + 1;
            System.Xml.XmlNodeList nodes = getFieldNodes(fieldnum);
            System.Xml.XmlNodeList tValueNodes;

            tValueNodes = nodes[0].SelectNodes("DomainMap/tValue");
            string name = "Method" + combonum + "Grid";
            Object ctrl = this.FindName(name);
            DataGrid grid = ctrl as DataGrid;
            if (grid == null)
                return;
            grid.Items.Clear();
            grid.InvalidateArrange();

            if (tValueNodes.Count > 0)
            {
                // only need to set this now if something present in config file, false for resetUI will call method to load from config.
                setDomainValues(getDatasetPath(SourceLayer.ToolTip.ToString()), getSourceFieldName(), _source, false);
                setDomainValues(getDatasetPath(TargetLayer.ToolTip.ToString()), getTargetFieldName(), _target, false);
            }

        }

        private void LoadDomains_Click(object sender, RoutedEventArgs e)
        {
            // Need to get the domain values from the target dataset - NB do domain but could also be based on values if no domain
            //if (ArcGIS.Desktop.Framework.Dialogs.MessageBox.Show("Load Domains from source datasets and replace current values?", "Replace Domains", MessageBoxButton.YesNo) == MessageBoxResult.Yes)
            //{
                setDomainValues(getDatasetPath(this.TargetLayer.ToolTip.ToString()), getTargetFieldName(), _target, true);
                setDomainValues(getDatasetPath(this.SourceLayer.ToolTip.ToString()), getSourceFieldName(), _source, true);
            //}
        }

        public void setDomainValues(string dataset, string fieldName, string sourceTarget, bool resetUI)
        {

            if (fieldName.Equals(_noneField))
            {
                ArcGIS.Desktop.Framework.Dialogs.MessageBox.Show("No field to map");
            }

            if (dataset.ToLower().StartsWith("http://") && dataset.ToLower().StartsWith("https://"))
            {
                //ArcGIS.Desktop.Framework.Dialogs.MessageBox.Show("service url: " + dataset);
                if (MapView.Active == null)
                    ArcGIS.Desktop.Framework.Dialogs.MessageBox.Show("There must be an active map to get the service domain values");
                else if (MapView.Active.Map == null)
                    ArcGIS.Desktop.Framework.Dialogs.MessageBox.Show("There must be an active map to get the service domain values");
                //System.Text.RegularExpressions.Regex regex = new System.Text.RegularExpressions.Regex(@"\d");
                bool containsNum = System.Text.RegularExpressions.Regex.IsMatch(dataset.Substring(dataset.LastIndexOf("/") + 1), @"\d"); 
                if (!containsNum)
                    ArcGIS.Desktop.Framework.Dialogs.MessageBox.Show("Layer file " + dataset + " does not end with an integer which is required for services");
                else
                    setDomainValuesLayer(dataset, fieldName, sourceTarget, resetUI);

            }

            if (dataset.ToLower().Contains(".sde"))
            {
                string sde = dataset.Substring(0, dataset.LastIndexOf(".sde") + 4);
                if (!System.IO.File.Exists(sde))
                {
                    ArcGIS.Desktop.Framework.Dialogs.MessageBox.Show("SDE connection file " + sde + " does not exist");
                }
                setDomainValuesSQL(sde, dataset, fieldName, sourceTarget, resetUI);
            }
            else if (dataset.ToLower().Contains(".gdb"))
            {
                string db = dataset.Substring(0, dataset.LastIndexOf(".gdb") + 4);
                if (!System.IO.Directory.Exists(db))
                {
                    ArcGIS.Desktop.Framework.Dialogs.MessageBox.Show("File Geodatabase " + db + " does not exist");
                }
                else
                    setDomainValuesFile(db, dataset, fieldName, sourceTarget, resetUI);
            }
            else if (dataset.ToLower().EndsWith(".lyrx"))
            {
                if (MapView.Active == null)
                    ArcGIS.Desktop.Framework.Dialogs.MessageBox.Show("There must be an active map to get the layer domain values");
                else if (MapView.Active.Map == null)
                    ArcGIS.Desktop.Framework.Dialogs.MessageBox.Show("There must be an active map to get the layer domain values");
                else if (!System.IO.File.Exists(dataset))
                    ArcGIS.Desktop.Framework.Dialogs.MessageBox.Show("Layer file " + dataset + " does not exist");
                else
                {
                    setDomainValuesLayer(dataset, fieldName, sourceTarget, resetUI);
                }
            }
            return;
        }

        public void resetDomainValuesUIFromConfig(List<ComboData> domainValues, string sourceTarget)
        {
            int fieldnum = FieldGrid.SelectedIndex + 1;
            System.Xml.XmlNodeList nodes = getFieldNodes(fieldnum);
            System.Xml.XmlNodeList sValueNodes, sLabelNodes, tValueNodes, tLabelNodes;

            if (sourceTarget == _source)
                _domainSourceValues = domainValues;
            else if (sourceTarget == _target)
                _domainTargetValues = domainValues;

            if (sourceTarget == _source) // just run this for target...
                return;

            //<Method>ValueMap</Method>
            //<ValueMap>
            //  <sValue>1</sValue>
            //  <sLabel>A things</sLabel>
            //  <tValue>12</tValue>
            //  <tLabel>12 things</tLabel>
            //  <sValue>2</sValue>
            //  <sLabel>2 things</sLabel>
            //  <tValue>22</tValue>
            //  <tLabel>22 things</tLabel>
            //  <Otherwise>
            //  </Otherwise>
            //</ValueMap>
            tValueNodes = nodes[0].SelectNodes("DomainMap/tValue");
            tLabelNodes = nodes[0].SelectNodes("DomainMap/tLabel");

            sValueNodes = nodes[0].SelectNodes("DomainMap/sValue");
            sLabelNodes = nodes[0].SelectNodes("DomainMap/sLabel");

            string name = "Method11Grid";
            Object ctrl = this.FindName(name);
            DataGrid grid = ctrl as DataGrid;
            if (grid == null)
                return;

            grid.Items.Clear();
            for (int i = 0; i < tValueNodes.Count; i++)
            {
                System.Xml.XmlNode targetnode = tValueNodes.Item(i);

                System.Xml.XmlNode sourcenode = sValueNodes.Item(i); // look at the source value node
                string sVal = "";
                string tVal = "";
                int selectedS = -1;
                int selectedT = -1;

                string sTooltip = "";
                if (sourcenode != null)
                    sVal = sourcenode.InnerText;
                for (int s = 0; s < _domainSourceValues.Count; s++)
                {
                    if (Equals(_domainSourceValues[s].Id, sVal))
                        selectedS = s;
                }
                sourcenode = sLabelNodes.Item(i);
                if (sourcenode != null)
                    sTooltip = sourcenode.InnerText;

                if (targetnode != null)
                    tVal = targetnode.InnerText;
                targetnode = tLabelNodes.Item(i);
                string tTooltip = "";
                if (targetnode != null)
                    tTooltip = targetnode.InnerText;
                for (int t = 0; t < _domainTargetValues.Count; t++)
                {
                    if (Equals(_domainTargetValues[t].Tooltip, tTooltip))
                    {
                        selectedT = t;
                        break;
                    }
                }
                grid.Items.Add(new DomainMapRow() { Source = _domainSourceValues, SourceSelectedItem = selectedS, SourceTooltip = sTooltip, TargetTooltip = tTooltip, Target = _domainTargetValues, TargetSelectedItem = selectedT });
            }
            grid.Items.Refresh();
            grid.InvalidateArrange();

            if (grid.Items.Count > 0)
            {
                DomainMapRemove.IsEnabled = true;
            }
            else
                DomainMapRemove.IsEnabled = false;
        }
        public void resetDomainValuesUI(List<ComboData> domainValues, string sourceTarget)
        {
            if (sourceTarget == _source)
                _domainSourceValues = domainValues;
            else if (sourceTarget == _target)
                _domainTargetValues = domainValues;

            //Following code loads the source side of the domains first, leaving target None until selected otherwise
            if (_domainSourceValues != null && _domainSourceValues.Count > 0)
            {
                Method11Grid.Items.Clear();
                for (int i = 0; i < _domainSourceValues.Count; i++)
                {
                    ComboData domainValue = _domainSourceValues[i];
                    if (domainValue.Id != _noneField) // don't want to create a row for None by default
                    {
                        int selected = 0; // use the default None here...
                        for (int s = 0; s < _domainTargetValues.Count; s++)
                        {
                            if (Equals(_domainTargetValues[s].Tooltip, domainValue.Tooltip)) // tooltip includes both coded value and description, only do initial match if identical values
                                selected = s;
                        }
                        Method11Grid.Items.Add(new DomainMapRow() { Source = _domainSourceValues, SourceSelectedItem = i, SourceTooltip = getDomainTooltip(domainValue.Id, domainValue.Value), Target = _domainTargetValues, TargetSelectedItem = selected, TargetTooltip = "None" });
                    }
                }
            }
            if (Method11Grid.Items.Count > 0)
            {
                DomainMapRemove.IsEnabled = true;
            }
            else
                DomainMapRemove.IsEnabled = false;

            Method11Grid.InvalidateArrange();
        }
        public List<ComboData> getDomainValuesforTable(TableDefinition def, string fieldName)
        {
            List<ComboData> domainValues = new List<ComboData>();
            // always add a blank at the start
            ComboData item = new ComboData();
            item.Id = _noneField;
            item.Value = _noneField;
            item.Tooltip = _noneField;
            domainValues.Add(item);

            try
            {
                IReadOnlyList<ArcGIS.Core.Data.Field> fields = def.GetFields();
                ArcGIS.Core.Data.Field thefield = fields.First(field => field.Name.ToLower() == fieldName.ToLower());
                IReadOnlyList<ArcGIS.Core.Data.Subtype> subtypes = def.GetSubtypes();
                if (subtypes.Count == 0)
                {
                    Domain domain = thefield.GetDomain();
                    if (domain is CodedValueDomain)
                    {
                        var codedValueDomain = domain as CodedValueDomain;
                        SortedList<object, string> codedValuePairs = codedValueDomain.GetCodedValuePairs();
                        for (int i = 0; i < codedValuePairs.Count; i++)
                        {
                            item = new ComboData();
                            item.Id = codedValuePairs.ElementAt(i).Key.ToString();
                            item.Value = codedValuePairs.ElementAt(i).Value.ToString();
                            item.Tooltip = getDomainTooltip(item.Id, item.Value);
                            domainValues.Add(item);
                        }
                    }
                }
                else if (subtypes.Count > 0)
                {
                    List<string> domainNames = new List<string>();
                    for (int s = 0; s < subtypes.Count; s++)
                    {
                        ArcGIS.Core.Data.Subtype stype = subtypes[s];
                        Domain domain = thefield.GetDomain(stype);
                        if (domain != null)
                        {
                            string dname = domain.GetName();
                            if (domain is CodedValueDomain && !domainNames.Contains(dname))
                            {
                                domainNames.Add(dname);
                                var codedValueDomain = domain as CodedValueDomain;
                                SortedList<object, string> codedValuePairs = codedValueDomain.GetCodedValuePairs();
                                for (int i = 0; i < codedValuePairs.Count; i++)
                                {
                                    item = new ComboData();
                                    item.Id = codedValuePairs.ElementAt(i).Key.ToString();
                                    item.Value = codedValuePairs.ElementAt(i).Value.ToString();
                                    item.Tooltip = getDomainTooltip(item.Id, item.Value) + " - " + dname;
                                    bool found = false;
                                    for (int cv = 0; cv < domainValues.Count; cv++)
                                    {
                                        ComboData dv = domainValues[cv];
                                        if (item.Id.Equals(dv.Id) && item.Value.Equals(dv.Value) && item.Tooltip.Equals(dv.Tooltip))
                                            found = true;
                                    }
                                    if (!found)
                                        domainValues.Add(item);
                                }
                            }
                        }
                    }
                    if (domainValues.Count == 1)
                    {
                        Domain field_domain = thefield.GetDomain(); //this tests that if the domain wasn't tied to a subtype, there still might be one on the field itself
                        if (field_domain != null)
                        {
                            string fdname = field_domain.GetName();
                            if (field_domain is CodedValueDomain && !domainNames.Contains(fdname))
                            {
                                domainNames.Add(fdname);
                                var cvd = field_domain as CodedValueDomain;
                                SortedList<object, string> cvp = cvd.GetCodedValuePairs();
                                for (int i = 0; i < cvp.Count; i++)
                                {
                                    item = new ComboData();
                                    item.Id = cvp.ElementAt(i).Key.ToString();
                                    item.Value = cvp.ElementAt(i).Value.ToString();
                                    item.Tooltip = getDomainTooltip(item.Id, item.Value) + "-" + fdname;
                                    domainValues.Add(item);
                                }
                            }
                        }
                    }
                }
            }

            catch
            {
                ArcGIS.Desktop.Framework.Dialogs.MessageBox.Show("Unable to retrieve domain values for " + fieldName);
                return domainValues;
            }
            return domainValues;

        }

        public async void setDomainValuesSQL(string sde, string dataset, string fieldName, string sourceTarget, bool resetUI)
        {
            List<ComboData> domain = new List<ComboData>();
            await ArcGIS.Desktop.Framework.Threading.Tasks.QueuedTask.Run(() =>
            {
                ArcGIS.Core.Data.TableDefinition def = null;
                try
                {
                    string table = dataset.Substring(dataset.LastIndexOf("\\") + 1);
                    ArcGIS.Core.Data.Geodatabase geodatabase = new Geodatabase(new DatabaseConnectionFile(new Uri(sde)));
                    using (ArcGIS.Core.Data.Table tab = geodatabase.OpenDataset<ArcGIS.Core.Data.Table>(table))
                    {
                        def = tab.GetDefinition();
                        domain = getDomainValuesforTable(def, fieldName);
                    }
                }
                catch { raiseDomainErrorMessage(dataset, fieldName); }
                return;
            });
            if (resetUI == true)
                resetDomainValuesUI(domain, sourceTarget);
            else
                resetDomainValuesUIFromConfig(domain, sourceTarget);
            return;
        }
        public async void setDomainValuesFile(string db, string dataset, string fieldName, string sourceTarget, bool resetUI)
        {
            List<ComboData> domain = new List<ComboData>();
            await ArcGIS.Desktop.Framework.Threading.Tasks.QueuedTask.Run(() =>
            {
                ArcGIS.Core.Data.TableDefinition def = null;
                try
                {
                    string table = dataset.Substring(dataset.LastIndexOf("\\") + 1);
                    ArcGIS.Core.Data.Geodatabase geodatabase = new Geodatabase(new FileGeodatabaseConnectionPath(new Uri(db)));
                    using (ArcGIS.Core.Data.Table tab = geodatabase.OpenDataset<ArcGIS.Core.Data.Table>(table))
                    {
                        def = tab.GetDefinition();
                        domain = getDomainValuesforTable(def, fieldName);
                    }
                }
                catch { raiseDomainErrorMessage(dataset, fieldName); }
                return;
            });
            if (resetUI == true)
                resetDomainValuesUI(domain, sourceTarget);
            else
                resetDomainValuesUIFromConfig(domain, sourceTarget);
            return;
        }
        public async void setDomainValuesLayer(string dataset, string fieldName, string sourceTarget, bool resetUI)
        {
            List<ComboData> domain = new List<ComboData>();
            await ArcGIS.Desktop.Framework.Threading.Tasks.QueuedTask.Run(() =>
            {
                try
                {
                    var lyr = Helpers.CreateFeatureLayer(new Uri(dataset), MapView.Active.Map);
                    FeatureLayer flayer = lyr as FeatureLayer;
                    ArcGIS.Core.Data.TableDefinition def = null;
                    ArcGIS.Core.CIM.CIMDataConnection cim = flayer.GetDataConnection();
                    FeatureClass fclass = flayer.GetFeatureClass();
                    def = fclass.GetDefinition();
                    domain = getDomainValuesforTable(def, fieldName);
                }
                catch { raiseDomainErrorMessage(dataset, fieldName); }
                return;
            });
            if (resetUI == true)
                resetDomainValuesUI(domain, sourceTarget);
            else
                resetDomainValuesUIFromConfig(domain, sourceTarget);
            return;
        }

        private void raiseDomainErrorMessage(string dataset,string fieldName)
        {
            ArcGIS.Desktop.Framework.Dialogs.MessageBox.Show("Unable to retrieve domain values for " + dataset + ", " + fieldName);

        }
        private string getDomainTooltip(string code, string value)
        {
            string ttip = "";
            try
            {
                ttip = code + " (" + value + ")";
            }
            catch
            { }
            return ttip;
        }

        private void Method11Source_SelectionChanged(object sender, SelectionChangedEventArgs e)
        {
            ComboBox cb = sender as ComboBox;
            if (cb != null)
            {
                if (cb.SelectedIndex == -1)
                    return;
                else
                {
                    DataGrid grid = this.Method11Grid as DataGrid;
                    if (grid == null || grid.SelectedIndex == -1)
                        return;

                    //object values = grid.Items[grid.SelectedIndex];
                    DomainMapRow row = grid.Items.GetItemAt(grid.SelectedIndex) as DomainMapRow;
                    ComboData rowSource = _domainSourceValues[cb.SelectedIndex] as ComboData;
                    if (row != null) // if there is a matching source domain value for the selection
                    {
                        // Then update the row DomainMapValues and set the tooltip to the value for the code 
                        row.SourceSelectedItem = cb.SelectedIndex;
                        row.SourceTooltip = rowSource.Tooltip;
                        cb.ToolTip = rowSource.Tooltip;
                        MethodPanelApply_Click(sender, e);
                    }
                }
            }
        }
        private void Method11Target_SelectionChanged(object sender, SelectionChangedEventArgs e)
        {
            ComboBox cb = sender as ComboBox;
            if (cb != null)
            {
                if (cb.SelectedIndex == -1)
                    return;
                else
                {
                    DataGrid grid = this.Method11Grid as DataGrid;
                    if (grid == null || grid.SelectedIndex == -1)
                        return;

                    //object values = grid.Items[grid.SelectedIndex];
                    DomainMapRow row = grid.Items.GetItemAt(grid.SelectedIndex) as DomainMapRow;
                    ComboData rowSource = _domainTargetValues[cb.SelectedIndex] as ComboData;
                    if (row != null) // if there is a matching target domain value for the selection
                    {
                        // Then update the row DomainMapValues and set the tooltip to the value for the code 
                        row.TargetSelectedItem = cb.SelectedIndex;
                        row.TargetTooltip = rowSource.Tooltip;
                        cb.ToolTip = rowSource.Tooltip;
                        MethodPanelApply_Click(sender, e);
                    }
                }
            }
        }

        private void DomainMapAdd_Click(object sender, RoutedEventArgs e)
        {
            Method11Grid.Items.Add(new DomainMapRow() { Source = _domainSourceValues, Target = _domainTargetValues });
            Method11Grid.InvalidateArrange();
            DomainMapRemove.IsEnabled = true;
        }

        private void DomainMapRemove_Click(object sender, RoutedEventArgs e)
        {
            if (Method11Grid.SelectedIndex > -1 && Method11Grid.Items.Count > 0)
                Method11Grid.Items.RemoveAt(Method11Grid.SelectedIndex);
        }
    }
}

// scrap for auto-matching domain values
//string target = domainValue.Id;
//int selected = -1;
//for (int s = 0; s < sourceValues.Count; s++) *** was trying to automatch here but sometimes want to match on Codes, other times values, other times None, other times both...
//{
//    string dvalue = sourceValues[s].Id;
//    if (target.Equals(dvalue))
//        selected = s;
//}
// string ttip = "";
// if (selected > -1)
//      ttip = sourceValues[selected].Tooltip; // get the tooltip for this domain value from source

//private void Method11Target_TextChanged(object sender, TextChangedEventArgs e) scrap for text box on domain targets
//{
//    TextBox tb = sender as TextBox;
//    if (tb != null)
//    {
//        DataGrid grid = this.Method11Grid as DataGrid;
//        if (grid == null || grid.SelectedIndex == -1)
//            return;

//        DomainMapRow row = grid.Items.GetItemAt(grid.SelectedIndex) as DomainMapRow;
//        if (row != null)
//        {
//            List<ComboData> domainValues = getDomainValues(this.TargetLayer.Text, getTargetFieldName());
//            row.Target = tb.Text;
//            if (tb.Text != "")
//            {
//                row.TargetTooltip = tb.Text + " (no target domain match)";
//                tb.ToolTip = row.TargetTooltip;
//                for (int s = 0; s < domainValues.Count; s++)
//                {
//                    string dvalue = domainValues[s].Id;
//                    if (tb.Text.Equals(dvalue)) // if there is a match to a domain value 
//                    {
//                        // then update the tooltip to domain value to provide feedback
//                        string ttip = domainValues[s].Tooltip;
//                        tb.ToolTip = ttip;
//                        row.TargetTooltip = ttip;
//                    }
//                }

//            }
//        }
//    }
//}
