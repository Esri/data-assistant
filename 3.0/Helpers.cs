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
      QueuedTask.Run(() =>
      {
       var createParams = new FeatureLayerCreationParams(uri);
       return LayerFactory.Instance.CreateLayer<FeatureLayer>(createParams, MapView.Active.Map);
      }
      );
      return null;
    }
    
    internal static Task AddProjectItem(string path)
    {
      var folderToAdd = ItemFactory.Instance.Create(path);
      return QueuedTask.Run(() => Project.Current.AddItem(folderToAdd as IProjectItem));
    } 
  }
}
