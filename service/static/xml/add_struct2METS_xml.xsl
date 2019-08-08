<?xml version="1.0" encoding="utf-8"?>
<xsl:stylesheet version="1.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform" xmlns:mets="http://www.loc.gov/METS/">

  <xsl:output method="xml" omit-xml-declaration="no" standalone="no" indent="yes" encoding="utf-8"/>

  <xsl:template match="@*|node()">
    <xsl:copy>
      <xsl:apply-templates select="@*|node()"/>
    </xsl:copy>
  </xsl:template>

  <xsl:template match="mets:mets">
    <xsl:copy>
      <xsl:apply-templates select="@* | *"/>
      <xsl:if test="not(./mets:structMap/div)">
        <mets:structMap xmlns="http://www.loc.gov/METS/">
          <xsl:attribute name="ID"><xsl:text>sword-mets-struct-1</xsl:text></xsl:attribute>
          <xsl:attribute name="LABEL"><xsl:text>structure</xsl:text></xsl:attribute>
          <xsl:attribute name="TYPE"><xsl:text>LOGICAL</xsl:text></xsl:attribute>
          <div>
             <xsl:attribute name="ID"><xsl:text>sword-mets-div-0</xsl:text></xsl:attribute>
             <xsl:attribute name="DMDID"><xsl:value-of select="//mets:dmdSec/@ID"/></xsl:attribute>
             <xsl:attribute name="TYPE"><xsl:text>SWORD Object</xsl:text></xsl:attribute>
             <xsl:for-each select="//mets:fileSec/mets:fileGrp/mets:file">
                <div>
                   <xsl:attribute name="ID">
                     <xsl:text>sword-mets-div-</xsl:text>
                     <xsl:value-of select="position()"/>
                     <!--
                     <xsl:value-of select="$cnt + 1"/>
                     -->
                   </xsl:attribute>
                   <xsl:attribute name="TYPE">
                     <xsl:text>File</xsl:text>
                   </xsl:attribute>
                   <fptr>
                      <xsl:attribute name="FILEID">
                        <xsl:value-of select="./@ID"/>
                        <!--
                        <xsl:text>sword-mets-file-</xsl:text>
                        <xsl:value-of select="format-number($cnt,'000')"/>
                        -->
                      </xsl:attribute>
                   </fptr>
                </div>
             </xsl:for-each>
          </div>
        </mets:structMap>
      </xsl:if>
    </xsl:copy>
  </xsl:template>
  
  <!--
  <xsl:template match="/mets:mets/structMap/div">
    <xsl:copy>
      <xsl:copy-of select="node()|@*"/>
      <xsl:if test="string-length($file)!=0 and string-length($md5)!=0">
        <div>
           <xsl:attribute name="ID">
             <xsl:text>sword-mets-div-</xsl:text>
             <xsl:value-of select="$cnt + 1"/>
           </xsl:attribute>
           <xsl:attribute name="TYPE">
             <xsl:text>File</xsl:text>
           </xsl:attribute>
           <fptr>
              <xsl:attribute name="FILEID">
                <xsl:text>sword-mets-file-</xsl:text>
                <xsl:value-of select="format-number($cnt,'000')"/>
              </xsl:attribute>
           </fptr>
        </div>
      </xsl:if>
    </xsl:copy>
  </xsl:template>
  -->

</xsl:stylesheet>

