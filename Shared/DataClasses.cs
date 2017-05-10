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
    // Data Classes used for various methods
    public class ConcatRow // concatenate method
    {
        public bool Checked { get; set; }  
        public string Name  { get; set; }
    }
    public class ValueMapRow // ValueMap method
    {
        public string Source { get; set; } // source values
        public string Target { get; set; } // target values to set
    }
    public class DomainMapRow // for DomainMap method
    {
        public List<ComboData> Source { get; set; } // combo items 
        public int SourceSelectedItem { get; set; } // selected item num
        public string SourceTooltip { get; set; } // tooltip on source control - show domain value for code
        public List<ComboData> Target { get; set; } // target textbox, will try to match to source domain values, always display all target values
        public int TargetSelectedItem { get; set; } // selected item num
        public string TargetTooltip { get; set; } // tooltip for target, wil be set to matching domain value if available
    }
    public class ComboData // combobox data for DomainMap
    {
        public string Id { get; set; } // domain code
        public string Value { get; set; } // domain value
        public string Tooltip { get; set; } // set tooltip - just using value seems like the best idea
    }
    public class PreviewRow // preview rows
    {
        public string Value { get; set; }
    }
}
