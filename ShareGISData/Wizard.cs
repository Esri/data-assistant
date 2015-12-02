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
using System.ComponentModel;
using System.Data;
using System.Drawing;
using System.Linq;
using System.Text;
using System.Windows.Forms;
using System.IO;
using System.Xml;
using System.Xml.Xsl;
using System.Xml.XPath;
using System.Threading.Tasks;
using System.Threading;
using System.Resources;
using System.Windows.Media.Imaging;

namespace ShareGISData
{
    public partial class Wizard : Form
    {
        WindowsFormsSynchronizationContext uiContext = new WindowsFormsSynchronizationContext();
        object userData = null;

        public Wizard()
        {
            InitializeComponent();
            if (wizardPages1.SelectedIndex == 0)
            {
                backButton.Visible = false;
                pictureBoxChanges.Image = getImage();
            }
            //setupEvents();          
        }

        private void setupEvents()
        {            
            //textBox4.DragEnter += new System.Windows.Forms.DragEventHandler(textBox4_DragEnter);
            //textBox4.DragDrop += new System.Windows.Forms.DragEventHandler(textBox4_DragDrop);
        }


        private void changeChecked(TreeView treeView, TreeViewEventArgs e)
        {
            TreeNode node = e.Node;
            if (node.Parent == null)
            {
                Boolean checkState = treeView.Nodes[0].Checked;
                for (int i = 0; i < treeView.Nodes[0].Nodes.Count; i++)
                {
                    treeView.Nodes[0].Nodes[i].Checked = checkState;
                }
            }
        }

        public WizardPages get()
        {
            return wizardPages1;
        }

        private void backButton_Click(object sender, EventArgs e)
        {
            wizardPages1.PriorPage();
            setGraphicsPanel();
            if (wizardPages1.SelectedIndex == 0)
                backButton.Visible = false;
            if (wizardPages1.SelectedIndex < wizardPages1.TabCount - 1)
                nextButton.Text = "Next";
        }

        private void nextButton_Click(object sender, EventArgs e)
        {
            if(wizardPages1.SelectedIndex == 0)               
            {
                wizardPages1.NextPage();
                setGraphicsPanel();
            }
            else if (wizardPages1.SelectedIndex == 1)
            {
                wizardPages1.NextPage();
                setGraphicsPanel();
                
                refreshWizardcb();
            }
            else
            {
                wizardPages1.NextPage();
                setGraphicsPanel();
            }
            if (wizardPages1.SelectedIndex > 0)
                backButton.Visible = true;

            if (wizardPages1.SelectedIndex == (wizardPages1.TabCount - 1) && nextButton.Text == "Finish")
            {
                wizardPages1.Visible = false;
                wizardPages1.Parent.Hide();
               // Application.Exit();
            }
            else if (wizardPages1.SelectedIndex == (wizardPages1.TabCount - 1) && nextButton.Text == "Next")
            {
                nextButton.Text = "Finish";
            }
        }

        private bool doOpenAnalyze()
        {
            BackgroundWorker worker = new BackgroundWorker();
            worker.WorkerReportsProgress = true;
            bool cancel = false;
            worker.DoWork += new DoWorkEventHandler(worker_doWork);
            worker.ProgressChanged += new ProgressChangedEventHandler(worker_ProgressChanged);
            worker.RunWorkerCompleted += new RunWorkerCompletedEventHandler(worker_RunWorkerCompleted);
            this.Invoke((MethodInvoker)delegate
            {
            });
            if (!worker.IsBusy)
                worker.RunWorkerAsync();
            if ((worker.CancellationPending == true))
            {
                cancel = true;
            }
            else
            {
            }
            return !cancel;
        }

        private void worker_doWork(object sender, DoWorkEventArgs e)
        {
            BackgroundWorker worker = sender as BackgroundWorker;
        }

        private void worker_ProgressChanged(object sender, ProgressChangedEventArgs e)
        {
            this.Invoke((MethodInvoker)delegate
            {
            });
            return;
        }
 
        private void worker_RunWorkerCompleted(object sender, RunWorkerCompletedEventArgs e)
        {
            this.Invoke((MethodInvoker)delegate
            {
                
            });
            return;
        }

        private void cancelButton_Click(object sender, EventArgs e)
        {
            var option = MessageBox.Show("Are you sure you want to cancel?", "Confirm cancel wizard", MessageBoxButtons.YesNo);
            if (option == DialogResult.Yes)
            {
                wizardPages1.Parent.Hide();
                wizardPages1.Dispose();
                Application.Exit();
            }   
        }
        private void selectOriginal_Click(object sender, EventArgs e)
        {
            uiContext.Post(refreshWizard,userData);
        }

        private void selectXmlButton_Click(object sender, EventArgs e)
        {
            uiContext.Post(refreshWizard, userData);

        }
        public void OpenFileDialog(string title,TextBox textBox)
        {
            // Displays an OpenFileDialog so the user can select an Xml document to open.
            OpenFileDialog dialog = new OpenFileDialog();
            dialog.Filter = "XML Workspace Files|*.xml";
            dialog.Title = title;

            if (dialog.ShowDialog() == DialogResult.OK)
            {
            }
        }
        public void SaveFileDialog(string title, TextBox textBox)
        {
            // Displays an OpenFileDialog so the user can select an output file name.
            OpenFileDialog dialog = new OpenFileDialog();
            dialog.Filter = "XML Config Files|*.xml";
            dialog.Title = title;

            if (dialog.ShowDialog() == DialogResult.OK)
            {
                textBox.Text = dialog.FileName;
            }
        }

        //public void OpenGxDialog(string title, TextBox textBox)
        //{
        //    //dialog.set_StartingLocation(xslt.s_comboGDB.Text);
        //    IGxDialog dialog = new GxDialog();
        //    dialog.Title = title;
        //    dialog.AllowMultiSelect = false;
        //    IGxObjectFilter filter = new CustomFilter("open");
        //    dialog.ObjectFilter = filter;
        //    IEnumGxObject selection;
        //    dialog.DoModalOpen((int)wizardPages1.Handle, out selection);
        //    IGxObject obj = selection.Next();
        //    while (obj != null)
        //    {
        //        textBox.Text = obj.FullName;
        //        obj = selection.Next();
        //    }
        //    uiContext.Post(refreshWizard, userData);
        //}
        //public void SaveGxDialog(string title, TextBox textBox)
        //{
        //    IGxDialog dialog = new GxDialog();

        //    dialog.Title = title;
        //    dialog.AllowMultiSelect = false;
        //    IGxObjectFilter filter = new CustomFilter("save");
        //    dialog.ObjectFilter = filter;
        //    dialog.DoModalSave((int)wizardPages1.Handle);
        //    IGxObject obj = dialog.FinalLocation;
        //    string textVal = System.IO.Path.Combine(obj.FullName, dialog.Name);
        //    textBox.Text = textVal;
        //    uiContext.Post(refreshWizard, userData);
        //}

        private void dataModelComboBox_SelectedIndexChanged(object sender, EventArgs e)
        {
        }
        //private bool getEsriLicense()
        //{
        //    // check for a license here
        //    bool license = false;
        //    esriLicenseStatus licenseStatus = esriLicenseStatus.esriLicenseUnavailable;
        //    // try to get arcview/basic license
        //    ESRI.ArcGIS.RuntimeManager.BindLicense(ProductCode.Desktop);
        //    IAoInitialize init = new AoInitializeClass();
        //    licenseStatus = init.Initialize(esriLicenseProductCode.esriLicenseProductCodeBasic);
        //    if (licenseStatus == esriLicenseStatus.esriLicenseUnavailable || licenseStatus == esriLicenseStatus.esriLicenseFailure || licenseStatus == esriLicenseStatus.esriLicenseNotInitialized ||
        //        licenseStatus == esriLicenseStatus.esriLicenseFailure || licenseStatus == esriLicenseStatus.esriLicenseUnavailable)
        //    {
        //        System.Windows.Forms.MessageBox.Show("License level required for this wizard is ArcGIS Basic or higher:" + licenseStatus.ToString() + "\nExiting Wizard");
        //    }
        //    else if (licenseStatus == esriLicenseStatus.esriLicenseAlreadyInitialized || licenseStatus == esriLicenseStatus.esriLicenseCheckedOut)
        //        license = true;
        //    return license;
        //}

        Image getImage()
        {
            int page = wizardPages1.SelectedIndex;
            string iconName = "Images\\icon" + page.ToString() + ".png";
            string ass = Dockpane1View.AddinAssemblyLocation();
            string fileName = System.IO.Path.Combine(Dockpane1View.AddinAssemblyLocation(), iconName);
            Image image = null;
            if (File.Exists(fileName) == true)
                image = Image.FromFile(fileName);
            else if (File.Exists(iconName) == true)
                image = Image.FromFile(iconName);
            if (image == null)
                MessageBox.Show("Unable to locate image file: " + iconName);

            return image;
        }
        void setGraphicsPanel()
        {
            int page = wizardPages1.SelectedIndex;

            //Image is defined as Embedded Resource. Copy to Output Directory = Do not copy
            //var asm = System.Reflection.Assembly.GetExecutingAssembly();
            //var stm = asm.GetManifestResourceStream(this.wizardPages1.GetType(), "Images. " + iconName);
            //BitmapImage embeddedResource = new BitmapImage();
            //embeddedResource .BeginInit();
            //embeddedResource .StreamSource = stm;
            //embeddedResource .EndInit();            
            
            //BitmapImage fromResource = new BitmapImage(new Uri("pack://application:,,,/ShareGISData;component/Images/" + iconName, UriKind.Absolute));
            //Bitmap image = BitmapImage2Bitmap(embeddedResource);
            string txt = "";

            switch (page)
            {
                case 0:
                    txt = "This tool enables data sharing between systems and organizations.";
                    break;
                case 1:
                    txt = "Select the source and target layers to use for data sharing.";
                    break;
                case 2:
                    txt = "Map source fields to target fields";
                    break;
                case 3:
                    txt = "Save the configuration file. Note that you can use the 'Share Data' tool to run this configuration later.";
                    break;
                case 4:
                    txt = "How did you get here?";
                    break;
            }
            try
            {
                this.Invoke((MethodInvoker)delegate
                {
                    try
                    {
                        pictureBoxChanges.Image = getImage();
                        textBoxChanges.Text = txt;
                    }
                    catch (Exception e)
                    {
                        MessageBox.Show("Error loading image\n" + e);
                    }
                });
            }
            catch { }
            refreshWizardcb();
        }
        //private Bitmap BitmapImage2Bitmap(BitmapImage bitmapImage)
        //{
        //    // BitmapImage bitmapImage = new BitmapImage(new Uri("../Images/test.png", UriKind.Relative));

        //    using (MemoryStream outStream = new MemoryStream())
        //    {
        //        BitmapEncoder enc = new BmpBitmapEncoder();
        //        enc.Frames.Add(BitmapFrame.Create(bitmapImage));
        //        enc.Save(outStream);
        //        System.Drawing.Bitmap bitmap = new System.Drawing.Bitmap(outStream);

        //        return new Bitmap(bitmap);
        //    }
        //}
        private void refreshWizard(object userData)
        {
            refreshWizardcb();
        }
        private void refreshWizardcb()
        {
            wizardPages1.Parent.Invalidate();
            wizardPages1.Parent.Update();
            wizardPages1.Parent.BringToFront();
        }

        private bool doSaveWork()
        {
            BackgroundWorker worker = new BackgroundWorker();
            //worker.WorkerReportsProgress = true;
            bool cancel = false;
            worker.DoWork += new DoWorkEventHandler(worker_doSave);
            //worker.ProgressChanged += new ProgressChangedEventHandler(worker_ProgressChanged);
            //worker.RunWorkerCompleted += new RunWorkerCompletedEventHandler(worker_RunWorkerCompleted);
            //this.Invoke((MethodInvoker)delegate
            //{
            //    analyzeLabel.Text = "Saving Workspace...";
            //});
            if (!worker.IsBusy)
                worker.RunWorkerAsync();
            if ((worker.CancellationPending == true))
            {
                cancel = true;
            }
            else
            {
            }
            return !cancel;
        }
        private void worker_doSave(object sender, DoWorkEventArgs e)
        {
            //BackgroundWorker worker = sender as BackgroundWorker;
        }

        private void richTextBox2_TextChanged(object sender, EventArgs e)
        {

        }

        private void buttonSummary_Click(object sender, EventArgs e)
        {
        }

        private void richTextBox3_TextChanged(object sender, EventArgs e)
        {

        }

        private void richTextBox1_TextChanged(object sender, EventArgs e)
        {

        }

        private void textBoxChanges_TextChanged(object sender, EventArgs e)
        {

        }

        private void richTextBox5_TextChanged(object sender, EventArgs e)
        {

        }

        private void label3_Click(object sender, EventArgs e)
        {

        }

        private void textBox1_TextChanged(object sender, EventArgs e)
        {

        }

        private void dataGridView1_CellContentClick(object sender, DataGridViewCellEventArgs e)
        {

        }

        private void richTextBox1_TextChanged_1(object sender, EventArgs e)
        {

        }

        private void label3_Click_1(object sender, EventArgs e)
        {

        }

    }
}
