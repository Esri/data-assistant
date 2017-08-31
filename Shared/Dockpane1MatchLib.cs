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
using System.IO;

namespace DataAssistant
{
    public partial class Dockpane1View : UserControl
    {

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
            return new XElement("Field",
                        new XElement("SourceName", "None"),
                        new XElement("TargetName", getTargetFieldName()),
                        new XElement("Method", getMethodVal())
                    );
        }

        private void MatchSave_Click(object sender, RoutedEventArgs e)
        { 
            var xmlpath = AddinAssemblyLocation() + "\\MapLibrary.xml";
            if (!File.Exists(xmlpath))
                createMatchLibraryXML(xmlpath);

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
            switch (nodeMethod)
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
                        for (int s = 0; s < ValueMapGrid.Items.Count; s++)
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
            if (loadField != null)
            {
                //set xml file corresponding map if exists to this
                IEnumerable<XElement> docMatch =  // Searches for the corresponding match if exists
                    from el in docFields.Elements("Field")
                    where el.Element("SourceName").Value == getSourceFieldName() && el.Element("TargetName").Value == getTargetFieldName()
                    select el;
                XElement targField = null;
                foreach (XElement el in docMatch)
                    targField = el;
                if (targField != null)
                {
                    targField.ReplaceWith(loadField);
                    docRoot.Save(path);
                    MethodPanelrefreshXML_Click(null, null);
                }
            }
        }

        private void Load_All_MatchLibrary_Click(object sender, RoutedEventArgs e)
        {
            string xmlpath = AddinAssemblyLocation() + "\\MapLibrary.xml";
            if (!File.Exists(xmlpath))
                createMatchLibraryXML(xmlpath);
            string path = getXmlFileName();
            XElement matchRoot = XElement.Load(xmlpath);
            XElement docRoot = XElement.Load(path);

            XElement matchFields = matchRoot.Element("Fields");
            XElement docFields = docRoot.Element("Fields");

            Dictionary<String, XElement> matchLibDict = new Dictionary<String, XElement>();
            Dictionary<XElement, XElement> toChange = new Dictionary<XElement, XElement>();

            foreach (XElement el in matchFields.Elements("Field"))
            {
                matchLibDict.Add(el.Element("TargetName").Value, el);
            }

            foreach(XElement el in docFields.Elements("Field"))
            {
                var targName = el.Element("TargetName").Value;
                if(matchLibDict.ContainsKey(targName))
                {
                    matchLibDict[targName].Element("SourceName").Value = el.Element("SourceName").Value;
                    toChange.Add(el, matchLibDict[targName]);
                }
            }

            foreach (XElement el in toChange.Keys)
                el.ReplaceWith(toChange[el]);

            docRoot.Save(path);
            MethodPanelrefreshXML_Click(null, null);
        }

        private void createMatchLibraryXML(string xmlpath)
        {
            System.Xml.XmlWriter writer = System.Xml.XmlWriter.Create(xmlpath);

            writer.WriteStartElement("MatchLibrary");
            writer.WriteStartElement("Fields");

            writer.WriteEndDocument();
            writer.Close();
        }
    }
}
