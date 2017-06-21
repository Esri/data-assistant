using ArcGIS.Desktop.Core;
using ArcGIS.Desktop.Framework.Threading.Tasks;
using ArcGIS.Desktop.Mapping;
using System;
using System.Threading.Tasks;

namespace DataAssistant
{
  internal static class Helpers
  {
    internal static FeatureLayer CreateFeatureLayer(Uri uri, Map map)
    {
      return LayerFactory.Instance.CreateFeatureLayer(uri, MapView.Active.Map);
    }
    
    internal static Task AddProjectItem(string path)
    {
      var folderToAdd = ItemFactory.Instance.Create(path);
      return QueuedTask.Run(() => Project.Current.AddItem(folderToAdd as IProjectItem));
    } 
  }
}
