<?xml version="1.0" encoding="utf-8"?>
<xsl:stylesheet version="1.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform">

  <!-- <xsl:import href="outputTokens.xsl"/> -->
  <xsl:output method="xml" omit-xml-declaration="no" standalone="no" indent="yes" encoding="utf-8"/>

  <!-- mapping names of month -->
  <xsl:variable name="monthNames" select="document('monthNameMap.xml')/monthNameMap/monthName"/>

  <xsl:variable name="langCodes" select="document('langCodeMap.xml')/langCodeMap/langCode"/>
  <xsl:variable name="langIn" select="translate(/article/@xml:lang,'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz')"/>
  <!-- <xsl:variable name="langOut">eng</xsl:variable> -->
  <xsl:variable name="langOut" select="$langCodes[@iso639-1=$langIn]/@iso639-1"/>

  <xsl:template match="/">
  <dublin_core>
    <xsl:attribute name="schema"><xsl:text>dc</xsl:text></xsl:attribute>
    <xsl:for-each select="//art-front/authgrp/author">
      <dcvalue>
        <xsl:attribute name="element"><xsl:text>contributor</xsl:text></xsl:attribute>
        <xsl:attribute name="qualifier"><xsl:text>author</xsl:text></xsl:attribute>
        <xsl:value-of select="person/persname/surname/text()"/>
        <xsl:if test="string-length(person/persname/fname/text()) > 0">
          <xsl:text>, </xsl:text>
          <xsl:value-of select="person/persname/fname/text()"/>
        </xsl:if>
      </dcvalue>
    </xsl:for-each>
    <dcvalue>
      <xsl:attribute name="element"><xsl:text>date</xsl:text></xsl:attribute>
      <xsl:attribute name="qualifier"><xsl:text>issued</xsl:text></xsl:attribute>
      <xsl:for-each select="//published[@type='web']/pubfront/date">
        <xsl:if test="position() = last()">
          <xsl:call-template name="compose-date"></xsl:call-template>
        </xsl:if>
      </xsl:for-each>
    </dcvalue>
    <xsl:for-each select="//published[@type='print']/journalref/issn[@type='print']">
      <dcvalue>
        <xsl:attribute name="element"><xsl:text>identifier</xsl:text></xsl:attribute>
        <xsl:attribute name="qualifier"><xsl:text>issn</xsl:text></xsl:attribute>
        <xsl:value-of select="normalize-space(text())"/>
      </dcvalue>
    </xsl:for-each>
    <xsl:if test="//published[@type='print']/journalref/issn[@type='online']">
      <xsl:for-each select="//published[@type='print']/journalref/issn[@type='online']">
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
      <xsl:value-of select="//art-admin/doi"/>
    </dcvalue>
    <dcvalue>
      <xsl:attribute name="element"><xsl:text>language</xsl:text></xsl:attribute>
      <xsl:attribute name="qualifier"><xsl:text>rfc3066</xsl:text></xsl:attribute>
      <xsl:choose>
        <xsl:when test="string-length($langIn) > 0">
          <xsl:value-of select="$langIn"/>
        </xsl:when>
        <xsl:otherwise>
          <xsl:text>en</xsl:text>
        </xsl:otherwise>
      </xsl:choose>
    </dcvalue>
    <dcvalue>
      <xsl:attribute name="element"><xsl:text>title</xsl:text></xsl:attribute>
      <xsl:attribute name="qualifier"><xsl:text>none</xsl:text></xsl:attribute>
      <xsl:value-of select="//art-front/titlegrp/title"/>
    </dcvalue>
    <xsl:if test="//art-front/abstract">
      <dcvalue>
        <xsl:attribute name="element"><xsl:text>description</xsl:text></xsl:attribute>
        <xsl:attribute name="qualifier"><xsl:text>abstract</xsl:text></xsl:attribute>
        <xsl:value-of select="//art-front/abstract"/>
      </dcvalue>
    </xsl:if>
    <dcvalue>
      <xsl:attribute name="element"><xsl:text>type</xsl:text></xsl:attribute>
      <xsl:attribute name="qualifier"><xsl:text>none</xsl:text></xsl:attribute>
      <xsl:text>Journal Article</xsl:text>
    </dcvalue>
    <dcvalue>
      <xsl:attribute name="element"><xsl:text>rights</xsl:text></xsl:attribute>
      <xsl:attribute name="qualifier"><xsl:text>holder</xsl:text></xsl:attribute>
      <xsl:for-each select="//published[@type='print']/journalref/publisher/orgname/nameelt">
        <xsl:value-of select="normalize-space(text())"/>
        <xsl:if test="position() != last()">
          <xsl:text>, </xsl:text>
        </xsl:if>
      </xsl:for-each>
    </dcvalue>
  </dublin_core>
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
