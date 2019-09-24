<?xml version="1.0" encoding="utf-8"?>
<xsl:stylesheet version="1.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform">

  <!-- <xsl:import href="outputTokens.xsl"/> -->
  <xsl:output method="xml" omit-xml-declaration="no" indent="yes" encoding="utf-8"/>

  <xsl:param name="currdatetime">1970-01-01T00:00:00</xsl:param>

  <xsl:variable name="langCodes" select="document('langCodeMap.xml')/langCodeMap/langCode"/>
  <xsl:variable name="langIn" select="translate(/article/@xml:lang,'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz')"/>
  <!-- <xsl:variable name="langOut">eng</xsl:variable> -->
  <xsl:variable name="langOut" select="$langCodes[@iso639-1=$langIn]/@iso639-2"/>

  <xsl:template match="/">
  <entry xmlns="http://www.w3.org/2005/Atom"
         xmlns:dc="http://purl.org/dc/elements/"
         xmlns:dcterms="http://purl.org/dc/terms/"
         xmlns:atom="http://www.w3.org/2005/Atom">
    <atom:updated><xsl:value-of select="$currdatetime"/></atom:updated>
    <atom:title>
      <xsl:value-of select="//article-meta/title-group/article-title"/>
    </atom:title>
    <atom:author>
      <atom:name>
        <xsl:value-of select="//article-meta/contrib-group/contrib[position()=1]/name/surname"/>
        <xsl:if test="string-length(//article-meta/contrib-group/contrib[position()=1]/name/given-names/text()) > 0">
          <xsl:text>, </xsl:text>
          <xsl:value-of select="//article-meta/contrib-group/contrib[position()=1]/name/given-names"/>
        </xsl:if>
      </atom:name>
    </atom:author>
    <atom:id>
      <xsl:text>doi:</xsl:text>
      <xsl:value-of select="//article-meta/article-id[@pub-id-type='doi']"/>
    </atom:id>
    <!-- <atom:source>Journal Title</atom:source> -->
    <atom:published>
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
      <xsl:text>T00:00:00Z</xsl:text>
    </atom:published>
    <atom:summary>
      <xsl:value-of select="//article-meta/abstract"/>
    </atom:summary>
    <!-- and here now the non-atom metadata -->
    <dc:language>
      <xsl:value-of select="$langOut"/>
    </dc:language>
    <dcterms:type>
      <xsl:text>Article</xsl:text>
    </dcterms:type>
    <dcterms:bibliographicCitation>
      <xsl:value-of select="//article-meta/contrib-group/contrib[position()=1]/name/surname"/>
      <xsl:if test="string-length(//article-meta/contrib-group/contrib[position()=1]/name/given-names/text()) > 0">
        <xsl:text>, </xsl:text>
        <xsl:value-of select="//article-meta/contrib-group/contrib[position()=1]/name/given-names"/>
      </xsl:if>
      <xsl:if test="//article-meta/contrib-group/contrib[position()>1]">
        <xsl:text> et al.</xsl:text>
      </xsl:if>
      <xsl:text>: </xsl:text>
      <xsl:for-each select="//journal-meta//journal-title">
        <xsl:value-of select="normalize-space(text())"/>
        <xsl:text> </xsl:text>
      </xsl:for-each>
      <xsl:value-of select="//article-meta/volume"/>
      <xsl:text> (</xsl:text>
      <xsl:choose>
        <xsl:when test="//article-meta/pub-date[contains(@pub-type,'ppub')]/year">
          <xsl:value-of select="//article-meta/pub-date[contains(@pub-type,'ppub')]/year"/>
        </xsl:when>
        <xsl:otherwise>
          <xsl:value-of select="//article-meta/pub-date[contains(@pub-type,'epub')]/year"/>
        </xsl:otherwise>
      </xsl:choose>
      <xsl:text>), </xsl:text>
      <xsl:value-of select="//article-meta/fpage"/>
      <xsl:if test="string-length(//article-meta/lpage/text())!=0">
        <xsl:text> - </xsl:text>
        <xsl:value-of select="//article-meta/lpage"/>
      </xsl:if>
    </dcterms:bibliographicCitation>
    <!-- <dcterms:available>DatePublished</dcterms:available> -->
    <dcterms:issued>
      <xsl:choose>
        <xsl:when test="//article-meta/pub-date[contains(@pub-type,'epub')]/year">
          <xsl:call-template name="compose-date">
            <xsl:with-param name="xpub" select="'epub'"/>
          </xsl:call-template>
        </xsl:when>
        <xsl:when test="//article-meta/pub-date[contains(@pub-type,'ppub')]/year">
          <xsl:call-template name="compose-date">
            <xsl:with-param name="xpub" select="'ppub'"/>
          </xsl:call-template>
        </xsl:when>
        <xsl:otherwise>
          <xsl:text>1111-11-11</xsl:text>
        </xsl:otherwise>
      </xsl:choose>
    </dcterms:issued>
    <dcterms:title>
      <xsl:value-of select="//article-meta/title-group/article-title"/>
    </dcterms:title>
    <xsl:for-each select="//article-meta/contrib-group/contrib">
      <dcterms:creator>
        <xsl:value-of select="name/surname"/>
        <xsl:text>, </xsl:text>
        <xsl:value-of select="name/given-names"/>
      </dcterms:creator>
    </xsl:for-each>
    <!-- <dcterms:contributor>Affiliation</dcterms:contributor> -->
    <dcterms:identifier>
      <xsl:text>doi:</xsl:text>
      <xsl:value-of select="//article-meta/article-id[@pub-id-type='doi']"/>
    </dcterms:identifier>
    <xsl:for-each select="//journal-meta//journal-title">
      <dcterms:source>
        <xsl:value-of select="normalize-space(text())"/>
      </dcterms:source>
    </xsl:for-each>
    <xsl:for-each select="//journal-meta/issn[@pub-type='ppub']">
      <dcterms:source>
        <xsl:text>pISSN:</xsl:text>
        <xsl:value-of select="normalize-space(text())"/>
      </dcterms:source>
    </xsl:for-each>
    <xsl:for-each select="//journal-meta/issn[@pub-type='epub']">
      <dcterms:source>
        <xsl:text>eISSN:</xsl:text>
        <xsl:value-of select="normalize-space(text())"/>
      </dcterms:source>
    </xsl:for-each>
    <dcterms:publisher>
      <xsl:value-of select="//journal-meta/publisher/publisher-name"/>
    </dcterms:publisher>
    <!--
    <dcterms:abstract>
      <xsl:value-of select="//article-meta/abstract"/>
    </dcterms:abstract>
    -->
    <xsl:for-each select="//article-meta/kwd-group/kwd">
      <dc:subject>
        <xsl:value-of select="normalize-space(text())"/>
      </dc:subject>
    </xsl:for-each>
  </entry>
  </xsl:template>

  <xsl:template name="compose-date">
    <xsl:param name="xpub" select="'epub'"/>
    <xsl:value-of select="//article-meta/pub-date[contains(@pub-type,$xpub)]/year"/>
    <xsl:text>-</xsl:text>
    <xsl:choose>
      <xsl:when test="//article-meta/pub-date[contains(@pub-type,$xpub)]/month">
        <xsl:value-of select="format-number(//article-meta/pub-date[contains(@pub-type,$xpub)]/month,'00')"/>
      </xsl:when>
      <xsl:otherwise>
        <xsl:text>12</xsl:text>
      </xsl:otherwise>
      </xsl:choose>
      <xsl:if test="//article-meta/pub-date[contains(@pub-type,$xpub)]/day">
        <xsl:text>-</xsl:text>
        <xsl:value-of select="format-number(//article-meta/pub-date[contains(@pub-type,$xpub)]/day,'00')"/>
      </xsl:if>
  </xsl:template>

</xsl:stylesheet>
