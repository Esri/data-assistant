<?xml version="1.0"?>
<xsl:stylesheet version="1.0" xmlns:esri="http://esri.com" xmlns:xs="http://www.w3.org/2001/XMLSchema" xmlns:xsl="http://www.w3.org/1999/XSL/Transform">

	<xsl:output indent="yes" method="xml"/>
	<xsl:strip-space elements="cFields cField Field ValueMap tValue sValue"/>

	<xsl:param name="configFile" select="'SourceTargetAddr28.xml'"/>
	<xsl:variable name="xmlDoc" select="document($configFile)"/>
	<xsl:key name="fkey" match="Field" use="concat(Method,SourceName,TargetName)"/>

	<xsl:variable name="fieldNodes" select="/SourceTargetMatch"/>
	<xsl:variable name="uniqueFields" select="/SourceTargetMatch//Field[generate-id()=generate-id(key('fkey',concat(Method,SourceName,TargetName))[1])]"/>

	<xsl:template match="*">
		<xsl:element name="{name()}"> <!-- avoids writing xml namespace values to output elements -->
			<xsl:apply-templates select="@*|node()"/>
		</xsl:element>
	</xsl:template>

	<xsl:template match="/">

		<SourceTargetMatch xmlns:esri="http://esri.com">
			<xsl:comment>
				<xsl:value-of select="concat($configFile,' has field count = ')"/>
				<xsl:value-of select="count($xmlDoc/SourceTargetMatrix//Field)"/>
			</xsl:comment>
			<xsl:comment>match file field count = <xsl:value-of select="count(//Field)"/></xsl:comment>
			<xsl:comment>Looking for fields in new xmlDoc that are not in match list</xsl:comment>
			<xsl:for-each select="$xmlDoc/SourceTargetMatrix//Field">
				<xsl:variable name="fname" select="TargetName"/>
				<xsl:variable name="matchName"> <!-- look for field map by name in the list of matched fields -->
					<xsl:for-each select="$fieldNodes/Field">
						<xsl:if test="TargetName = $fname">
							<xsl:value-of select="TargetName"/>
						</xsl:if>
					</xsl:for-each>
				</xsl:variable>
				<xsl:choose>
					<xsl:when test="string($matchName) = '' and ./TargetName != ''">
						<!-- <xsl:comment><xsl:value-of select="concat($fname,'|',$tfname,'|',count($fieldNodes//Field))"/></xsl:comment>-->
						<xsl:call-template name="fieldprops">
							<xsl:with-param name="field" select="."/>
							<xsl:with-param name="count" select="1"/>
						</xsl:call-template>
					</xsl:when>
				</xsl:choose>
			</xsl:for-each>

			<xsl:comment>Looking for fields in new xmlDoc that are already in the match list</xsl:comment>
			<xsl:comment>
			<xsl:value-of select="count($uniqueFields)"/>unique fields</xsl:comment> <!-- unique list by source, target, and method -->
			<xsl:for-each select="$uniqueFields">
				<xsl:variable name="targetFieldName" select="./TargetName"/>
				<xsl:call-template name="Field">
					<xsl:with-param name="field" select="."/>
					<xsl:with-param name="fields" select="$uniqueFields"/>
				</xsl:call-template>
			</xsl:for-each>
		</SourceTargetMatch>
	</xsl:template>

	<xsl:template name="Field">
		<xsl:param name="field"/>
		<xsl:param name="fields"/>
		<xsl:variable name="targetFieldName" select="TargetName"/>
		<!-- look for a matching field in the field mapping file -->
		<xsl:variable name="matchField" select="$xmlDoc/SourceTargetMatrix//Field[TargetName=$targetFieldName]"/>
		<xsl:variable name="matchName" select="$matchField/TargetName"/>
		<xsl:choose>
			<xsl:when test="string($matchName) = ''">
				<xsl:comment>no matching source field in Xml</xsl:comment>
				<!-- this is the case where there is nothing for this target name-->
				<xsl:choose>
					<xsl:when test="string(TargetName)!=''">
						<xsl:call-template name="fieldprops">
							<xsl:with-param name="count" select="@count"/>
						</xsl:call-template>
					</xsl:when>
				</xsl:choose>
			</xsl:when>
			<xsl:when test="string($matchName) != ''">
				<!-- this is the case where there is a target name for this target name-->
				<xsl:variable name="newCount">
					<xsl:choose>
						<xsl:when test="@count &gt; 0">
							<xsl:value-of select="@count + 1"/>
						</xsl:when>
						<xsl:otherwise>
							<xsl:value-of select="1"/>
						</xsl:otherwise>
					</xsl:choose>
				</xsl:variable>
				<xsl:choose>
					<xsl:when test="string(./*) = string($matchField/*)"> <!-- compare descendant values minus the Field/@count -->
						<xsl:call-template name="fieldprops">
							<xsl:with-param name="count" select="$newCount"/>
						</xsl:call-template>
					</xsl:when>
					<xsl:otherwise>
						<xsl:comment>everything does not match</xsl:comment>

							<xsl:call-template name="fieldpropsField">
								<!-- write the matched field with existing properties including count -->
								<xsl:with-param name="field" select="$matchField"/>
							</xsl:call-template>

							<xsl:call-template name="fieldprops">
								<!-- write the match file element with an incremented value for the count  -->
								<xsl:with-param name="count" select="$newCount"/>
							</xsl:call-template>

					</xsl:otherwise>
				</xsl:choose>
			</xsl:when>
		</xsl:choose>
	</xsl:template>

	<xsl:template name="fieldprops">
		<xsl:param name="count"/>

		<xsl:element name="Field">
			<xsl:attribute name="count">
				<xsl:value-of select="$count"/>
			</xsl:attribute>
			<xsl:for-each select="./*">
				<xsl:element name="{local-name(.)}">
					<xsl:apply-templates select="@*|node()"/>
				</xsl:element>
			</xsl:for-each>
		</xsl:element>
	</xsl:template>

	<xsl:template name="fieldpropsField">
		<xsl:param name="field"/>

		<xsl:variable name="newCount">
			<xsl:choose>
				<xsl:when test="$field/@count &gt; 0">
					<xsl:value-of select="$field/@count"/>
				</xsl:when>
				<xsl:otherwise>
					<xsl:value-of select="1"/>
				</xsl:otherwise>
			</xsl:choose>
		</xsl:variable>
		<xsl:element name="Field">
			<xsl:attribute name="count">
				<xsl:value-of select="$newCount"/>
			</xsl:attribute>
			<xsl:for-each select="$field/*">
				<xsl:element name="{local-name(.)}">
					<xsl:apply-templates select="@*|node()"/>
				</xsl:element>
			</xsl:for-each>
		</xsl:element>
	</xsl:template>
</xsl:stylesheet><!-- Stylus Studio meta-information - (c) 2004-2009. Progress Software Corporation. All rights reserved.

<metaInformation>
	<scenarios>
		<scenario default="yes" name="Scenario1" userelativepaths="yes" externalpreview="no" url="SourceTargetAddr28.xml" htmlbaseurl="" outputurl="MatchLocal2.xml" processortype="msxmldotnet" useresolver="no" profilemode="0" profiledepth=""
		          profilelength="" urlprofilexml="" commandline="" additionalpath="" additionalclasspath="" postprocessortype="none" postprocesscommandline="" postprocessadditionalpath="" postprocessgeneratedext="" validateoutput="no" validator="internal"
		          customvalidator="">
			<advancedProp name="sInitialMode" value=""/>
			<advancedProp name="schemaCache" value="||"/>
			<advancedProp name="bXsltOneIsOkay" value="true"/>
			<advancedProp name="bSchemaAware" value="false"/>
			<advancedProp name="bGenerateByteCode" value="false"/>
			<advancedProp name="bXml11" value="false"/>
			<advancedProp name="iValidation" value="0"/>
			<advancedProp name="bExtensions" value="true"/>
			<advancedProp name="iWhitespace" value="0"/>
			<advancedProp name="sInitialTemplate" value=""/>
			<advancedProp name="bTinyTree" value="true"/>
			<advancedProp name="xsltVersion" value="2.0"/>
			<advancedProp name="bWarnings" value="true"/>
			<advancedProp name="bUseDTD" value="false"/>
			<advancedProp name="iErrorHandling" value="fatal"/>
		</scenario>
		<scenario default="no" name="Scenario2" userelativepaths="yes" externalpreview="no" url="MatchLocal2.xml" htmlbaseurl="" outputurl="MatchLocal3.xml" processortype="msxmldotnet2" useresolver="no" profilemode="0" profiledepth="" profilelength=""
		          urlprofilexml="" commandline="" additionalpath="" additionalclasspath="" postprocessortype="none" postprocesscommandline="" postprocessadditionalpath="" postprocessgeneratedext="" validateoutput="no" validator="internal"
		          customvalidator="">
			<advancedProp name="sInitialMode" value=""/>
			<advancedProp name="bXsltOneIsOkay" value="true"/>
			<advancedProp name="bSchemaAware" value="false"/>
			<advancedProp name="bGenerateByteCode" value="false"/>
			<advancedProp name="bXml11" value="false"/>
			<advancedProp name="iValidation" value="0"/>
			<advancedProp name="bExtensions" value="true"/>
			<advancedProp name="iWhitespace" value="0"/>
			<advancedProp name="sInitialTemplate" value=""/>
			<advancedProp name="bTinyTree" value="true"/>
			<advancedProp name="xsltVersion" value="2.0"/>
			<advancedProp name="bWarnings" value="true"/>
			<advancedProp name="bUseDTD" value="false"/>
			<advancedProp name="iErrorHandling" value="fatal"/>
		</scenario>
		<scenario default="no" name="Scenario3" userelativepaths="yes" externalpreview="no" url="MatchLocal3.xml" htmlbaseurl="" outputurl="MatchLocal4.xml" processortype="msxmldotnet" useresolver="no" profilemode="0" profiledepth="" profilelength=""
		          urlprofilexml="" commandline="" additionalpath="" additionalclasspath="" postprocessortype="none" postprocesscommandline="" postprocessadditionalpath="" postprocessgeneratedext="" validateoutput="no" validator="internal"
		          customvalidator="">
			<advancedProp name="sInitialMode" value=""/>
			<advancedProp name="schemaCache" value="||"/>
			<advancedProp name="bXsltOneIsOkay" value="true"/>
			<advancedProp name="bSchemaAware" value="false"/>
			<advancedProp name="bGenerateByteCode" value="false"/>
			<advancedProp name="bXml11" value="false"/>
			<advancedProp name="iValidation" value="0"/>
			<advancedProp name="bExtensions" value="true"/>
			<advancedProp name="iWhitespace" value="0"/>
			<advancedProp name="sInitialTemplate" value=""/>
			<advancedProp name="bTinyTree" value="true"/>
			<advancedProp name="xsltVersion" value="2.0"/>
			<advancedProp name="bWarnings" value="true"/>
			<advancedProp name="bUseDTD" value="false"/>
			<advancedProp name="iErrorHandling" value="fatal"/>
		</scenario>
	</scenarios>
	<MapperMetaTag>
		<MapperInfo srcSchemaPathIsRelative="yes" srcSchemaInterpretAsXML="no" destSchemaPath="" destSchemaRoot="" destSchemaPathIsRelative="yes" destSchemaInterpretAsXML="no"/>
		<MapperBlockPosition></MapperBlockPosition>
		<TemplateContext></TemplateContext>
		<MapperFilter side="source"></MapperFilter>
	</MapperMetaTag>
</metaInformation>
-->