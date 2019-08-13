<?xml version="1.0" encoding="utf-8"?>
<xsl:stylesheet version="1.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform">

  <!-- <xsl:import href="outputTokens.xsl"/> -->
  <xsl:output method="xml" omit-xml-declaration="yes" indent="yes" encoding="utf-8"/>

  <!-- mapping names of month -->
  <xsl:variable name="monthNames" select="document('monthNameMap.xml')/monthNameMap/monthName"/>

  <xsl:variable name="langCodes" select="document('langCodeMap.xml')/langCodeMap/langCode"/>
  <xsl:variable name="langIn" select="translate(/article/@xml:lang,'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz')"/>
  <!-- <xsl:variable name="langOut">eng</xsl:variable> -->
  <xsl:variable name="langOut" select="$langCodes[@iso639-1=$langIn]/@iso639-2"/>

  <xsl:template match="/">
  <import>
    <opusDocument>
          <xsl:attribute name="language"> 
            <xsl:value-of select="$langOut"/>
          </xsl:attribute>
          <xsl:attribute name="type">
            <xsl:text>article</xsl:text>
          </xsl:attribute>
          <xsl:if test="//published[@type='print']/pubfront/fpage">
            <xsl:attribute name="pageFirst">
              <xsl:value-of select="//published[@type='print']/pubfront/fpage"/>
            </xsl:attribute>
          </xsl:if>
          <xsl:if test="//published[@type='print']/pubfront/lpage">
            <xsl:attribute name="pageLast">
              <xsl:value-of select="//published[@type='print']/pubfront/lpage"/>
            </xsl:attribute>
          </xsl:if>
          <xsl:if test="//published[@type='print']/volumeref/link">
            <xsl:attribute name="volume">
              <xsl:value-of select="//published[@type='print']/volumeref/link"/>
            </xsl:attribute>
          </xsl:if>
          <xsl:if test="//published[@type='print']/issueref/link">
            <xsl:attribute name="issue">
              <xsl:value-of select="//published[@type='print']/issueref/link"/>
            </xsl:attribute>
          </xsl:if>
          <xsl:attribute name="publisherName">
            <xsl:for-each select="//published[@type='print']/journalref/publisher/orgname/nameelt">
              <xsl:value-of select="normalize-space(text())"/>
              <xsl:if test="position() != last()">
                <xsl:text>, </xsl:text>
              </xsl:if>
            </xsl:for-each>
          </xsl:attribute>
          <!--
          <xsl:if test="//publisher//publisher-loc">
            <xsl:attribute name="publisherPlace">
              <xsl:value-of select="//publisher//publisher-loc"/>
            </xsl:attribute>
          </xsl:if>
          -->
          <xsl:attribute name="belongsToBibliography">
            <xsl:text>false</xsl:text>
          </xsl:attribute>
          <xsl:attribute name="serverState">
            <xsl:text>unpublished</xsl:text>
          </xsl:attribute>
          <!-- 
          language="eng"
          type="article|bachelorthesis|bookpart|book|conferenceobject|contributiontoperiodical|coursematerial|diplom|doctoralthesis|examen|habilitation|image|lecture|magister|masterthesis|movingimage|other|periodical|preprint|report|review|studythesis|workingpaper"
          pageFirst=""
          pageLast=""
          pageNumber=""
          edition=""
          volume=""
          issue=""
          publisherName=""
          publisherPlace=""
          creatingCorporation=""
          contributingCorporation=""
          belongsToBibliography="true|false"
          serverState="audited|published|restricted|inprogress|unpublished"
          -->
      <titlesMain>
          <titleMain>
            <xsl:attribute name="language"><xsl:value-of select="$langOut"/></xsl:attribute>
            <xsl:value-of select="//art-front/titlegrp/title"/>
          </titleMain>
      </titlesMain>
      <titles>
          <xsl:if test="//published[@type='print']/journalref/title[@type='full']">
            <title> 
              <xsl:attribute name="language"><xsl:value-of select="$langOut"/></xsl:attribute>
              <xsl:attribute name="type"><xsl:text>parent</xsl:text></xsl:attribute> 
              <xsl:value-of select="//published[@type='print']/journalref/title"/>
            </title>
          </xsl:if>
      </titles>
      <abstracts>
          <xsl:if test="//art-front/abstract">
            <abstract>
              <xsl:attribute name="language"><xsl:value-of select="$langOut"/></xsl:attribute>
              <xsl:value-of select="//art-front/abstract"/>
            </abstract>
          </xsl:if>
      </abstracts>
      <persons>
          <xsl:for-each select="//art-front/authgrp/author">
            <person>
                <xsl:attribute name="role"><xsl:text>author</xsl:text></xsl:attribute>
                <xsl:attribute name="firstName"><xsl:copy-of select="person/persname/fname/text()"/></xsl:attribute>
                <xsl:attribute name="lastName"><xsl:copy-of select="person/persname/surname/text()"/></xsl:attribute>
                <!--
                role="advisor|author|contributor|editor|referee|translator|submitter|other"
                firstName=""
                lastName=""
                academicTitle=""
                email=""
                allowEmailContact="true|false"
                placeOfBirth=""
                dateOfBirth="1999-12-31"
                -->
                <!--
                <identifiers>
                  <identifier type="orcid|gnd|intern">?????</identifier>
                </identifiers>
                -->
            </person>
          </xsl:for-each>
      </persons>
      <keywords>
          <keyword> 
            <xsl:attribute name="language"><xsl:value-of select="$langOut"/></xsl:attribute>
            <xsl:attribute name="type"><xsl:text>swd</xsl:text></xsl:attribute>
            <xsl:text>-</xsl:text>
          </keyword>
      </keywords>
      <!--
      <dnbInstitutions>
          <dnbInstitution id="<integer>" role="grantor|publisher"/>
      </dnbInstitutions>
      -->
      <dates>
          <xsl:for-each select="//published[@type='web']/pubfront/date">
          <xsl:if test="position() = last()">
            <xsl:variable name="mnth" select="month"/>
            <date>
              <xsl:attribute name="type"><xsl:text>published</xsl:text></xsl:attribute>
              <xsl:attribute name="monthDay">
                <xsl:text>--</xsl:text>
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
              </xsl:attribute>
              <xsl:attribute name="year">
                <xsl:value-of select="year"/>
              </xsl:attribute>
            </date>
          </xsl:if>
          </xsl:for-each>
      </dates>
      <identifiers>
        <xsl:for-each select="//published[@type='print']/journalref/issn[@type='print']">
          <identifier>
             <xsl:attribute name="type"><xsl:text>issn</xsl:text></xsl:attribute>
             <xsl:value-of select="normalize-space(text())"/>
          </identifier>
        </xsl:for-each>
        <xsl:for-each select="//published[@type='print']/journalref/issn[@type='online']">
          <identifier>
             <xsl:attribute name="type"><xsl:text>issn</xsl:text></xsl:attribute>
             <xsl:value-of select="normalize-space(text())"/>
          </identifier>
        </xsl:for-each>
	<xsl:if test="//art-admin/doi">
          <identifier>
             <xsl:attribute name="type"><xsl:text>doi</xsl:text></xsl:attribute>
             <xsl:value-of select="//art-admin/doi"/>
          </identifier>
        </xsl:if>
      </identifiers>
      <!--
      <identifiers>
          <identifier>
             <xsl:attribute name="type"><xsl:text>issn</xsl:text></xsl:attribute>
             <xsl:for-each select="//published[@type='print']/journalref/issn[@type='print']">
                <xsl:value-of select="normalize-space(text())"/>
                <xsl:if test="position() != last()">
                   <xsl:text> , </xsl:text>
                </xsl:if>
                <xsl:if test="position() = last()">
                   <xsl:text> (pISSN)</xsl:text>
                </xsl:if>
             </xsl:for-each>
             <xsl:if test="//published[@type='print']/journalref/issn[@type='online']">
                <xsl:text> ; </xsl:text>
                <xsl:for-each select="//published[@type='print']/journalref/issn[@type='online']">
                   <xsl:value-of select="normalize-space(text())"/>
                   <xsl:if test="position() != last()">
                      <xsl:text> , </xsl:text>
                   </xsl:if>
                   <xsl:if test="position() = last()">
                      <xsl:text> (eISSN)</xsl:text>
                   </xsl:if>
                </xsl:for-each>
             </xsl:if>
          </identifier>
          <identifier>
             <xsl:attribute name="type"><xsl:text>doi</xsl:text></xsl:attribute>
             <xsl:value-of select="//art-admin/doi"/>
          </identifier>
      </identifiers>
      -->
      <!--
      <notes>
          <note visibility="private|public">?????</note>
      </notes>
      <collections>
          <collection id="<integer>"/>
      </collections>
      <series>
          <seriesItem id="<integer>" number=""/>
      </series>
      <enrichments>
          <enrichment key="">?????</enrichment>
      </enrichments>
      <licences>
          <licence id="<integer>"/>
      </licences>
      <files basedir="">
          <file 
                path=""
                name=""
                language=""
                displayName=""
                visibleInOai="true|false"
                visibleInFrontdoor="true|false"
                sortOrder="<int>">
            <comment>?????</comment>
            <checksum type="md5|sha256|sha512">?????</checksum>
          </file>
      </files>
      -->
    </opusDocument>
  </import>
  </xsl:template>

</xsl:stylesheet>
