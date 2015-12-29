# data-aggregation

This initial release of the Data sharing tools for ArcGIS Pro is a development release with limited functionality.

If you do not want to compile in Visual Studio you should be able to just click/install data-aggregation\ShareGISData\bin\Debug\ShareGISData.esriAddInX

<strong>Things to test:</strong>
<li>Overall user experience - use the Data Mapper and GP Tools to test all of the end user functionality</li>
<li>Tool interaction and basic behavior of the user interface for each method.</li>
<li>Save (Apply) functionality</li>
<li>Create new SourceTarget config files and test in ArcGIS Pro</li>

<strong>Things that do not work:</strong>
<li>Replace-by functionality for Publish has not been implemented yet.</li>
<li>Publish does not currently support Feature services.</li>
<li>Ability to write points instead of polygons for different feature types in target has not been implemented yet.</li>
<li>Automap functionality to learn from user interaction has not been implemented yet.</li>
<li>General UI improvements will be made to look closer to ArcGIS Pro Icons and UI styling. Suggestions are welcome.</li>
<li>We are looking at an option to recover/revert to a previous version of config files.</li>

<strong>Things Fixed Dec 2</strong>
<li>The Wizard Icons work now</li>
<li>Save on DataGrid (i.e., ValueMapper Method) now works.</li>

<strong>Things Fixed Dec 4</strong>
<li>ValueMap and Concatenate functionality</li>
<li>Save and Load functionality is functionally complete</li>
<li>Create new config files with new GP tool - find in your Debug\bin\GPTools folder</li>

<strong>Things Addressed Dec 29</strong>
<li>New File/Fields UI for Data Mapper</li>
<li>Significant work on GP tools and overall functionality for field calculator etc.</li>
<li>New field preview option shows a small sample of source data in Field Mapper.</li>
