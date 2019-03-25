<?xml version="1.0" encoding="utf-8"?>
<xsl:stylesheet version="1.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform">

  <!-- <xsl:import href="outputTokens.xsl"/> -->
  <xsl:output method="xml" omit-xml-declaration="no" standalone="no" indent="yes" encoding="utf-8"/>

  <xsl:variable name="langCodes" select="document('langCodeMap.xml')/langCodeMap/langCode"/>
  <xsl:variable name="langIn" select="translate(/article/@xml:lang,'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz')"/>
  <!-- <xsl:variable name="langOut">eng</xsl:variable> -->
  <xsl:variable name="langOut" select="$langCodes[@iso639-1=$langIn]/@iso639-2"/>

  <xsl:template match="/">
  <dublin_core>
    <xsl:attribute name="schema"><xsl:text>dc</xsl:text></xsl:attribute>
    <xsl:for-each select="//article-meta/contrib-group/contrib">
      <dcvalue>
        <xsl:attribute name="element"><xsl:text>contributor</xsl:text></xsl:attribute>
        <xsl:attribute name="qualifier">
          <xsl:choose>
            <xsl:when test="@contrib-type='guest-editor'">
              <xsl:text>editor</xsl:text>
            </xsl:when>
            <xsl:otherwise>
              <xsl:value-of select="@contrib-type"/>
            </xsl:otherwise>
          </xsl:choose>
        </xsl:attribute>
        <xsl:value-of select="name/surname"/>
        <xsl:if test="string-length(name/given-names/text()) > 0">
          <xsl:text>, </xsl:text>
          <xsl:value-of select="name/given-names"/>
        </xsl:if>
      </dcvalue>
    </xsl:for-each>
    <dcvalue>
      <xsl:attribute name="element"><xsl:text>date</xsl:text></xsl:attribute>
      <xsl:attribute name="qualifier"><xsl:text>issued</xsl:text></xsl:attribute>
      <xsl:value-of select="//article-meta/pub-date[contains(@pub-type,'ppub')]/year"/>
      <xsl:text>-</xsl:text>
      <xsl:choose>
        <xsl:when test="//article-meta/pub-date[contains(@pub-type,'ppub')]/month">
          <xsl:value-of select="format-number(//article-meta/pub-date[contains(@pub-type,'ppub')]/month,'00')"/>
        </xsl:when>
        <xsl:otherwise>
          <xsl:text>12</xsl:text>
        </xsl:otherwise>
      </xsl:choose>
      <xsl:text>-</xsl:text>
      <xsl:choose>
        <xsl:when test="//article-meta/pub-date[contains(@pub-type,'ppub')]/day">
          <xsl:value-of select="format-number(//article-meta/pub-date[contains(@pub-type,'ppub')]/day,'00')"/>
        </xsl:when>
        <xsl:otherwise>
          <xsl:text>01</xsl:text>
        </xsl:otherwise>
      </xsl:choose>
    </dcvalue>
    <xsl:for-each select="//journal-meta/issn[@pub-type='ppub' or @publication-format='print']">
      <dcvalue>
        <xsl:attribute name="element"><xsl:text>identifier</xsl:text></xsl:attribute>
        <xsl:attribute name="qualifier"><xsl:text>issn</xsl:text></xsl:attribute>
        <xsl:value-of select="normalize-space(text())"/>
      </dcvalue>
    </xsl:for-each>
    <xsl:if test="//journal-meta/issn[@pub-type='epub' or @publication-format='electronic']">
      <xsl:for-each select="//journal-meta/issn[@pub-type='epub' or @publication-format='electronic']">
        <dcvalue>
          <xsl:attribute name="element"><xsl:text>identifier</xsl:text></xsl:attribute>
          <xsl:attribute name="qualifier"><xsl:text>issn</xsl:text></xsl:attribute>
          <xsl:value-of select="normalize-space(text())"/>
        </dcvalue>
      </xsl:for-each>
    </xsl:if>
    <dcvalue>
      <xsl:attribute name="element"><xsl:text>identifier</xsl:text></xsl:attribute>
      <xsl:attribute name="qualifier"><xsl:text>other</xsl:text></xsl:attribute>
      <xsl:text>DOI: </xsl:text>
      <xsl:value-of select="//article-meta/article-id[@pub-id-type='doi']"/>
    </dcvalue>
    <dcvalue>
      <xsl:attribute name="element"><xsl:text>language</xsl:text></xsl:attribute>
      <xsl:attribute name="qualifier"><xsl:text>rfc3066</xsl:text></xsl:attribute>
      <xsl:value-of select="$langIn"/>
    </dcvalue>
    <dcvalue>
      <xsl:attribute name="element"><xsl:text>title</xsl:text></xsl:attribute>
      <xsl:attribute name="qualifier"><xsl:text>none</xsl:text></xsl:attribute>
      <xsl:value-of select="//article-meta/title-group/article-title"/>
    </dcvalue>
    <dcvalue>
      <xsl:attribute name="element"><xsl:text>description</xsl:text></xsl:attribute>
      <xsl:attribute name="qualifier"><xsl:text>abstract</xsl:text></xsl:attribute>
      <xsl:value-of select="//article-meta/abstract"/>
    </dcvalue>
    <dcvalue>
      <xsl:attribute name="element"><xsl:text>type</xsl:text></xsl:attribute>
      <xsl:attribute name="qualifier"><xsl:text>none</xsl:text></xsl:attribute>
      <xsl:text>Journal Article</xsl:text>
    </dcvalue>
    <dcvalue>
      <xsl:attribute name="element"><xsl:text>rights</xsl:text></xsl:attribute>
      <xsl:attribute name="qualifier"><xsl:text>holder</xsl:text></xsl:attribute>
      <xsl:value-of select="//journal-meta/publisher/publisher-name"/>
    </dcvalue>
  </dublin_core>
  </xsl:template>

</xsl:stylesheet>
