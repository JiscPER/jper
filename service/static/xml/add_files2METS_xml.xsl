<?xml version="1.0" encoding="utf-8"?>
<xsl:stylesheet version="1.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform" xmlns:mets="http://www.loc.gov/METS/">

  <xsl:output method="xml" omit-xml-declaration="no" standalone="no" indent="yes" encoding="utf-8"/>

  <xsl:param name="file"/>
  <xsl:param name="md5"/>
  <xsl:param name="mime"><xsl:text>application/octet-stream</xsl:text></xsl:param>
  <xsl:param name="cnt"><xsl:text>1</xsl:text></xsl:param>

  <xsl:template match="@*|node()">
    <xsl:copy>
      <xsl:apply-templates select="@*|node()"/>
    </xsl:copy>
  </xsl:template>

  <xsl:template match="mets:mets">
    <xsl:copy>
      <xsl:apply-templates select="@* | *"/>
      <xsl:if test="not(./mets:fileSec/mets:fileGrp) and string-length($file)!=0 and string-length($md5)!=0">
        <mets:fileSec xmlns="http://www.loc.gov/METS/">
          <mets:fileGrp>
             <xsl:attribute name="ID"><xsl:text>sword-mets-fgrp-1</xsl:text></xsl:attribute>
             <xsl:attribute name="USE"><xsl:text>CONTENT</xsl:text></xsl:attribute>
             <mets:file>
               <xsl:attribute name="GROUPID">
                 <xsl:text>sword-mets-fgid-</xsl:text>
                 <xsl:value-of select="$cnt"/>
               </xsl:attribute>
               <xsl:attribute name="ID">
                 <xsl:text>sword-mets-file-</xsl:text>
                 <xsl:value-of select="format-number($cnt,'000')"/>
               </xsl:attribute>
               <xsl:attribute name="CHECKSUM">
                 <xsl:value-of select="$md5"/>
               </xsl:attribute>
               <xsl:attribute name="CHECKSUMTYPE">
                 <xsl:text>MD5</xsl:text>
               </xsl:attribute>
               <xsl:attribute name="MIMETYPE">
                 <xsl:value-of select="$mime"/>
               </xsl:attribute>
               <mets:FLocat xmlns:xlink="http://www.w3.org/1999/xlink">
                 <xsl:attribute name="LOCTYPE">
                   <xsl:text>URL</xsl:text>
                 </xsl:attribute>
                 <xsl:attribute name="xlink:href">
                   <xsl:value-of select="$file"/>
                 </xsl:attribute>
               </mets:FLocat>
             </mets:file>
          </mets:fileGrp>
        </mets:fileSec>
        <!--
        <structMap xmlns="http://www.loc.gov/METS/">
          <xsl:attribute name="ID"><xsl:text>sword-mets-struct-1</xsl:text></xsl:attribute>
          <xsl:attribute name="LABEL"><xsl:text>structure</xsl:text></xsl:attribute>
          <xsl:attribute name="TYPE"><xsl:text>LOGICAL</xsl:text></xsl:attribute>
          <div>
             <xsl:attribute name="ID"><xsl:text>sword-mets-div-1</xsl:text></xsl:attribute>
             <xsl:attribute name="DMDID"><xsl:value-of select="//mets:dmdSec/@ID"/></xsl:attribute>
             <xsl:attribute name="TYPE"><xsl:text>SWORD Object</xsl:text></xsl:attribute>
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
          </div>
        </structMap>
        -->
      </xsl:if>
    </xsl:copy>
  </xsl:template>
  
  <xsl:template match="mets:fileSec/mets:fileGrp">
    <xsl:copy>
      <xsl:apply-templates select="@* | *"/>
      <xsl:if test="string-length($file)!=0 and string-length($md5)!=0">
        <mets:file>
          <xsl:attribute name="GROUPID">
            <xsl:text>sword-mets-fgid-</xsl:text>
            <xsl:value-of select="$cnt"/>
          </xsl:attribute>
          <xsl:attribute name="ID">
            <xsl:text>sword-mets-file-</xsl:text>
            <xsl:value-of select="format-number($cnt,'000')"/>
          </xsl:attribute>
          <xsl:attribute name="CHECKSUM">
            <xsl:value-of select="$md5"/>
          </xsl:attribute>
          <xsl:attribute name="CHECKSUMTYPE">
            <xsl:text>MD5</xsl:text>
          </xsl:attribute>
          <xsl:attribute name="MIMETYPE">
            <xsl:value-of select="$mime"/>
          </xsl:attribute>
          <mets:FLocat xmlns:xlink="http://www.w3.org/1999/xlink">
            <xsl:attribute name="LOCTYPE">
              <xsl:text>URL</xsl:text>
            </xsl:attribute>
            <xsl:attribute name="xlink:href">
              <xsl:value-of select="$file"/>
            </xsl:attribute>
          </mets:FLocat>
        </mets:file>
      </xsl:if>
    </xsl:copy>
  </xsl:template>

  <!--
  <xsl:template match="/mets:mets/mets:structMap/div">
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

