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
using System.Collections.ObjectModel;

using System.Windows;
using System.Windows.Controls;


namespace DataAssistant
{
    public class ConcatRow
    {
        public bool Checked { get; set; }  
        public string Name  { get; set; }
    }
    public class ValueMapRow
    {
        public string Source { get; set; }
        public string Target { get; set; }
    }
    public class DomainMapRow
    {
        public List<ComboData> Source { get; set; }
        public int SourceSelectedItem { get; set; }
        public string SourceTooltip { get; set; }
        public string Target { get; set; }
        public string TargetTooltip { get; set; }
    }
    public class PreviewRow
    {
        public string Value { get; set; }
    }
    public class ComboData
    {
        public string Id { get; set; }
        public string Value { get; set; }
        public string Tooltip { get; set; }
    }
}
