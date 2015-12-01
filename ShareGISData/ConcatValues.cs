using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Threading.Tasks;
using System.Collections.ObjectModel;

namespace ShareGISData
{
    public class ConcatRow
    {
        public bool Checked { get; set; }  
        public string Name  { get; set; }
        public int Sequence { get; set; }
        //        public static ObservableCollection<ConcatRow> ConcatValues()  
        //     {  
        //          ObservableCollection<ConcatRow> concatrows = new ObservableCollection<ConcatRow>()  
        //          {  
        //              new ConcatRow{ Checked=false, Name="Test"} 
        //          };  
        //         return concatrows;     
        //     }
    }
    public class ValueMapRow
    {
        public string Source { get; set; }
        public string Target { get; set; }
    }
}
