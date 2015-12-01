/*
 | Version 10.2
 | Copyright 2013 Esri
 |
 | Licensed under the Apache License, Version 2.0 (the "License");
 | you may not use this file except in compliance with the License.
 | You may obtain a copy of the License at
 |
 |    http://www.apache.org/licenses/LICENSE-2.0
 |
 | Unless required by applicable law or agreed to in writing, software
 | distributed under the License is distributed on an "AS IS" BASIS,
 | WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 | See the License for the specific language governing permissions and
 | limitations under the License.
 */
using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Windows.Forms;

namespace ShareGISData
{
    public class WizardPages : TabControl
    {
        protected override void WndProc(ref Message m)
        {
            // Hide tabs by trapping the TCM_ADJUSTRECT message
            if (m.Msg == 0x1328 && ! DesignMode) m.Result = (IntPtr)1;
            else base.WndProc(ref m);
        }
        bool blockTabChange = true;

        protected override void OnSelecting(TabControlCancelEventArgs e)
        {
            if (!DesignMode)
                e.Cancel = blockTabChange;
        }
        public void NextPage()
        {
            blockTabChange = false;
            SelectedIndex = ++SelectedIndex;
            blockTabChange = true;
        }
        public void PriorPage()
        {
            blockTabChange = false;
            if(SelectedIndex > 0)
                SelectedIndex = --SelectedIndex;
            blockTabChange = true;
        }
    }

}