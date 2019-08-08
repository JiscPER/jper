<?xml version="1.0" encoding="utf-8"?>
<xsl:stylesheet version="1.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform">

  <xsl:output method="xml" omit-xml-declaration="yes" indent="yes" encoding="utf-8"/>

  <xsl:param name="file"/>
  <xsl:param name="md5"/>

  <xsl:template match="@*|node()">
    <xsl:copy>
      <xsl:apply-templates select="@*|node()"/>
    </xsl:copy>
  </xsl:template>

  <xsl:template match="opusDocument">
    <xsl:copy>
      <xsl:apply-templates select="@* | *"/>
      <xsl:if test="not(./files) and string-length($file)!=0 and string-length($md5)!=0">
        <files>
           <xsl:attribute name="basedir"><xsl:text>.</xsl:text></xsl:attribute>
           <file>
             <xsl:attribute name="name"><xsl:value-of select="$file"/></xsl:attribute>
             <xsl:attribute name="language"><xsl:value-of select="//opusDocument/@language"/></xsl:attribute>
             <xsl:attribute name="visibleInOai"><xsl:text>true</xsl:text></xsl:attribute>
             <comment>
               <!-- <xsl:text>A component of the fulltext article</xsl:text> -->
             </comment>
             <checksum>
               <xsl:attribute name="type"><xsl:text>md5</xsl:text></xsl:attribute>
               <xsl:value-of select="$md5"/>
             </checksum>
           </file>
        </files>
      </xsl:if>
    </xsl:copy>
  </xsl:template>
  
  <xsl:template match="files">
    <xsl:copy>
      <xsl:apply-templates select="@* | *"/>
      <xsl:if test="string-length($file)!=0 and string-length($md5)!=0">
        <file>
          <xsl:attribute name="name"><xsl:value-of select="$file"/></xsl:attribute>
          <xsl:attribute name="language"><xsl:value-of select="//opusDocument/@language"/></xsl:attribute>
          <xsl:attribute name="visibleInOai"><xsl:text>true</xsl:text></xsl:attribute>
          <comment>
            <!-- <xsl:text>A component of the fulltext article</xsl:text> -->
          </comment>
          <checksum>
            <xsl:attribute name="type"><xsl:text>md5</xsl:text></xsl:attribute>
            <xsl:value-of select="$md5"/>
          </checksum>
        </file>
      </xsl:if>
    </xsl:copy>
  </xsl:template>

</xsl:stylesheet>
