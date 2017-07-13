<?xml version="1.0" encoding="utf-8"?>
<xsl:stylesheet version="1.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform">

  <!-- <xsl:import href="outputTokens.xsl"/> -->
  <xsl:output method="xml" omit-xml-declaration="no" indent="yes" encoding="utf-8"/>

  <xsl:param name="currdatetime">1970-01-01T00:00:00</xsl:param>

  <!-- mapping names of month -->
  <xsl:variable name="monthNames" select="document('monthNameMap.xml')/monthNameMap/monthName"/>

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
      <xsl:value-of select="//art-front/titlegrp/title"/>
    </atom:title>
    <atom:author>
      <atom:name>
        <xsl:value-of select="//art-front/authgrp/author[position()=1]/person/persname/surname/text()"/>
        <xsl:if test="string-length(//art-front/authgrp/author[position()=1]/person/persname/fname/text()) > 0">
          <xsl:text>, </xsl:text>
          <xsl:value-of select="//art-front/authgrp/author[position()=1]/person/persname/fname/text()"/>
        </xsl:if>
      </atom:name>
    </atom:author>
    <atom:id>
      <xsl:text>doi:</xsl:text>
      <xsl:value-of select="//art-admin/doi"/>
    </atom:id>
    <!-- <atom:source>Journal Title</atom:source> -->
    <atom:published>
      <xsl:for-each select="//published[@type='web']/pubfront/date">
        <xsl:if test="position() = last()">
          <xsl:call-template name="compose-date"></xsl:call-template>
          <xsl:text>T00:00:00Z</xsl:text>
        </xsl:if>
      </xsl:for-each>
    </atom:published>
    <atom:summary>
      <xsl:value-of select="//art-front/abstract"/>
    </atom:summary>
    <!-- and here now the non-atom metadata -->
    <dc:language>
      <xsl:value-of select="$langOut"/>
    </dc:language>
    <dcterms:type>
      <xsl:text>Article</xsl:text>
    </dcterms:type>
    <dcterms:bibliographicCitation>
        <xsl:value-of select="//art-front/authgrp/author[position()=1]/person/persname/surname/text()"/>
        <xsl:if test="string-length(//art-front/authgrp/author[position()=1]/person/persname/fname/text()) > 0">
          <xsl:text>, </xsl:text>
          <xsl:value-of select="//art-front/authgrp/author[position()=1]/person/persname/fname/text()"/>
        </xsl:if>
      <xsl:if test="//art-front/authgrp/author[position()>1]">
        <xsl:text> et al.</xsl:text>
      </xsl:if>
      <xsl:text>: </xsl:text>
      <xsl:value-of select="//published[@type='print']/journalref/title"/>
      <xsl:text> </xsl:text>
      <xsl:value-of select="//published[@type='print']/volumeref/link"/>
      <xsl:text> (</xsl:text>
      <xsl:value-of select="//published[@type='print']/pubfront/date/year"/>
      <xsl:text>), </xsl:text>
      <xsl:value-of select="//published[@type='print']/pubfront/fpage"/>
      <xsl:if test="string-length(//published[@type='print']/pubfront/lpage/text())!=0">
        <xsl:text> - </xsl:text>
        <xsl:value-of select="//published[@type='print']/pubfront/lpage"/>
      </xsl:if>
    </dcterms:bibliographicCitation>
    <!-- <dcterms:available>DatePublished</dcterms:available> -->
    <dcterms:issued>
      <xsl:for-each select="//published[@type='web']/pubfront/date">
        <xsl:if test="position() = last()">
          <xsl:call-template name="compose-date"></xsl:call-template>
        </xsl:if>
      </xsl:for-each>
    </dcterms:issued>
    <dcterms:title>
      <xsl:value-of select="//art-front/titlegrp/title"/>
    </dcterms:title>
    <xsl:for-each select="//art-front/authgrp/author">
      <dcterms:creator>
        <xsl:copy-of select="person/persname/surname/text()"/>
        <xsl:text>, </xsl:text>
        <xsl:copy-of select="person/persname/fname/text()"/>
      </dcterms:creator>
    </xsl:for-each>
    <!-- <dcterms:contributor>Affiliation</dcterms:contributor> -->
    <dcterms:identifier>
      <xsl:text>doi:</xsl:text>
      <xsl:value-of select="//art-admin/doi"/>
    </dcterms:identifier>
    <dcterms:source>
      <xsl:value-of select="//published[@type='print']/journalref/title"/>
    </dcterms:source>
    <xsl:for-each select="//published[@type='print']/journalref/issn[@type='print']">
      <dcterms:source>
        <xsl:text>pISSN:</xsl:text>
        <xsl:value-of select="normalize-space(text())"/>
      </dcterms:source>
    </xsl:for-each>
    <xsl:for-each select="//published[@type='print']/journalref/issn[@type='online']">
      <dcterms:source>
        <xsl:text>eISSN:</xsl:text>
        <xsl:value-of select="normalize-space(text())"/>
      </dcterms:source>
    </xsl:for-each>
    <dcterms:publisher>
      <xsl:for-each select="//published[@type='print']/journalref/publisher/orgname/nameelt">
        <xsl:value-of select="normalize-space(text())"/>
        <xsl:if test="position() != last()">
          <xsl:text>, </xsl:text>
        </xsl:if>
      </xsl:for-each>
    </dcterms:publisher>
    <!--
    <dcterms:abstract>
      <xsl:value-of select="//art-front/abstract"/>
    </dcterms:abstract>
    -->
    <!--  there are apparently no keywords in RSC ...
    <dc:subject>
        <xsl:text>-</xsl:text>
    </dc:subject>
    -->
  </entry>
  </xsl:template>

  <xsl:template name="compose-date">
      <xsl:variable name="mnth" select="month"/>
      <xsl:value-of select="year"/>
      <xsl:text>-</xsl:text>
      <xsl:choose>
          <xsl:when test="format-number(month,'00')!='NaN'">
              <xsl:value-of select="format-number(month,'00')"/>
          </xsl:when>
          <xsl:when test="$monthNames[@text=$mnth]/@number">
              <xsl:value-of select="$monthNames[@text=$mnth]/@number"/>
          </xsl:when>
          <xsl:otherwise>
              <xsl:text>12</xsl:text>
          </xsl:otherwise>
      </xsl:choose>
      <xsl:text>-</xsl:text>
      <xsl:choose>
          <xsl:when test="format-number(day,'00')!='NaN'">
              <xsl:value-of select="format-number(day,'00')"/>
          </xsl:when>
          <xsl:otherwise>
              <xsl:text>01</xsl:text>
          </xsl:otherwise>
      </xsl:choose>
  </xsl:template>

</xsl:stylesheet>
