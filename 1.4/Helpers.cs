using ArcGIS.Desktop.Core;
using ArcGIS.Desktop.Mapping;
using System;
using System.Threading.Tasks;

namespace DataAssistant
{
  internal static class Helpers
  {
    internal static FeatureLayer CreateFeatureLayer(Uri uri, Map map)
    {
      return LayerFactory.CreateFeatureLayer(uri, MapView.Active.Map);
    }
    
    internal static Task AddProjectItem(string path)
    {
      return Project.Current.AddAsync(ItemFactory.Create(path)); 
    } 
  }
}
