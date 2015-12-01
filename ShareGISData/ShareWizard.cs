using System;
using System.Windows.Forms;
using ArcGIS.Desktop.Framework;
using ArcGIS.Desktop.Framework.Contracts;
using ArcGIS.Core.Data;

namespace ShareGISData
{
    class ShareWizard : ArcGIS.Desktop.Framework.Contracts.Button
    {
        protected override void OnClick()
        {
            Form frm = new Wizard();
            frm.Show();
        }
    }
}
