<?xml version="1.0" encoding="utf-8"?>
<xsl:stylesheet version="1.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform">

  <!-- <xsl:import href="outputTokens.xsl"/> -->
  <xsl:output method="xml" omit-xml-declaration="yes" indent="yes" encoding="utf-8"/>

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
          <xsl:if test="//article-meta/fpage">
            <xsl:attribute name="pageFirst">
              <xsl:value-of select="//article-meta/fpage"/>
            </xsl:attribute>
          </xsl:if>
          <xsl:if test="//article-meta/lpage">
            <xsl:attribute name="pageLast">
              <xsl:value-of select="//article-meta/lpage"/>
            </xsl:attribute>
          </xsl:if>
          <xsl:if test="//article-meta/volume">
            <xsl:attribute name="volume">
              <xsl:value-of select="//article-meta/volume"/>
            </xsl:attribute>
          </xsl:if>
          <xsl:if test="//article-meta/issue">
            <xsl:attribute name="issue">
              <xsl:value-of select="//article-meta/issue"/>
            </xsl:attribute>
          </xsl:if>
          <xsl:attribute name="publisherName">
            <xsl:value-of select="//journal-meta/publisher/publisher-name"/>
          </xsl:attribute>
          <xsl:if test="//journal-meta/publisher/publisher-loc">
            <xsl:attribute name="publisherPlace">
              <xsl:value-of select="//journal-meta/publisher/publisher-loc"/>
            </xsl:attribute>
          </xsl:if>
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
            <xsl:value-of select="//article-meta/title-group/article-title"/>
          </titleMain>
      </titlesMain>
      <titles>
          <xsl:for-each select="//journal-meta//journal-title">
            <title> 
              <xsl:attribute name="language"><xsl:value-of select="$langOut"/></xsl:attribute>
              <xsl:attribute name="type"><xsl:text>parent</xsl:text></xsl:attribute> 
              <xsl:value-of select="normalize-space(text())"/>
            </title>
          </xsl:for-each>
      </titles>
      <abstracts>
          <xsl:if test="//article-meta/abstract">
            <abstract>
              <xsl:attribute name="language"><xsl:value-of select="$langOut"/></xsl:attribute>
              <xsl:value-of select="//article-meta/abstract"/>
            </abstract>
          </xsl:if>
      </abstracts>
      <persons>
          <xsl:for-each select="//article-meta/contrib-group/contrib">
            <xsl:if test="name/surname">
            <person>
                <xsl:attribute name="role">
                  <xsl:choose>
                    <xsl:when test="@contrib-type='guest-editor'">
                       <xsl:text>editor</xsl:text>
                    </xsl:when>
                    <xsl:otherwise>
                       <xsl:value-of select="@contrib-type"/>
                    </xsl:otherwise>
                  </xsl:choose>
                </xsl:attribute>
                <xsl:attribute name="firstName"><xsl:value-of select="name/given-names"/></xsl:attribute>
                <xsl:attribute name="lastName"><xsl:value-of select="name/surname"/></xsl:attribute>
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
            </xsl:if>
          </xsl:for-each>
      </persons>
      <keywords>
          <keyword> 
            <xsl:attribute name="language"><xsl:value-of select="$langOut"/></xsl:attribute>
            <xsl:attribute name="type"><xsl:text>swd</xsl:text></xsl:attribute>
            <xsl:text>-</xsl:text>
          </keyword>
          <xsl:for-each select="//article-meta/kwd-group/kwd">
            <xsl:if test="string-length(normalize-space(text()))>0">
              <keyword> 
                <xsl:attribute name="language"><xsl:value-of select="$langOut"/></xsl:attribute>
                <xsl:attribute name="type"><xsl:text>uncontrolled</xsl:text></xsl:attribute>
                <xsl:value-of select="normalize-space(text())"/>
              </keyword>
	    </xsl:if>
          </xsl:for-each>
      </keywords>
      <!--
      <dnbInstitutions>
          <dnbInstitution id="<integer>" role="grantor|publisher"/>
      </dnbInstitutions>
      -->
      <dates>
        <!-- 
        <xsl:for-each select="//article-meta/pub-date">
           <xsl:if test="(contains(@pub-type, 'epub') and year and month) or
                         (contains(@publication-format, 'electronic') and contains(@date-type, 'pub') and year and month)">
              <mods:dateIssued encoding="iso8601">
                 <xsl:call-template name="compose-date"></xsl:call-template>
              </mods:dateIssued>
           </xsl:if>
	</xsl:for-each>
        -->
        <xsl:for-each select="//article-meta/pub-date">
        <xsl:choose>
          <xsl:when test="contains(@pub-type,'epub') and year and month">
            <xsl:call-template name="compose-date">
              <!-- <xsl:with-param name="xpub" select="'epub'"/> -->
            </xsl:call-template>
          </xsl:when>
          <xsl:when test="contains(@pub-type,'ppub') and year and month">
            <xsl:call-template name="compose-date">
              <!-- <xsl:with-param name="xpub" select="'ppub'"/> -->
            </xsl:call-template>
          </xsl:when>
          <xsl:when test="contains(@date-type,'pub') and year and month">
            <xsl:call-template name="compose-date">
              <!-- <xsl:with-param name="xpub" select="'pub'"/> -->
            </xsl:call-template>
          </xsl:when>
          <xsl:otherwise>
            <xsl:if test="not(year)">
            <date>
              <xsl:attribute name="type"><xsl:text>completed</xsl:text></xsl:attribute>
              <xsl:attribute name="monthDay">
                <xsl:text>--11-11</xsl:text>
              </xsl:attribute>
              <xsl:attribute name="year">
                <xsl:text>1111</xsl:text>
              </xsl:attribute>
            </date>
            </xsl:if>
          </xsl:otherwise>
        </xsl:choose>
        </xsl:for-each> 
      </dates>
      <identifiers>
        <xsl:for-each select="//journal-meta/issn[@pub-type='ppub' or @pub-type='epub' or @publication-format='print' or @publication-format='electronic']">
          <identifier>
             <xsl:attribute name="type"><xsl:text>issn</xsl:text></xsl:attribute>
             <xsl:value-of select="normalize-space(text())"/>
          </identifier>
        </xsl:for-each>
        <xsl:if test="//article-meta/article-id[@pub-id-type='doi']">
          <identifier>
             <xsl:attribute name="type"><xsl:text>doi</xsl:text></xsl:attribute>
             <xsl:value-of select="//article-meta/article-id[@pub-id-type='doi']"/>
          </identifier>
        </xsl:if>
        <xsl:if test="//article-meta/article-id[@pub-id-type='pmid']">
          <identifier>
             <xsl:attribute name="type"><xsl:text>pmid</xsl:text></xsl:attribute>
             <xsl:value-of select="//article-meta/article-id[@pub-id-type='pmid']"/>
          </identifier>
        </xsl:if>
      </identifiers>
      <!--
      <identifiers>
          <identifier>
             <xsl:for-each select="//journal-meta/issn[@pub-type='ppub' or @publication-format='print']">
                <xsl:value-of select="normalize-space(text())"/>
                <xsl:if test="position() != last()">
                   <xsl:text> , </xsl:text>
                </xsl:if>
                <xsl:if test="position() = last()">
                   <xsl:text> (pISSN)</xsl:text>
                </xsl:if>
             </xsl:for-each>
             <xsl:if test="//journal-meta/issn[@pub-type='epub' or @publication-format='electronic']">
                <xsl:text> ; </xsl:text>
                <xsl:for-each select="//journal-meta/issn[@pub-type='epub' or @publication-format='electronic']">
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
             <xsl:value-of select="//article-meta/article-id[@pub-id-type='doi']"/>
          </identifier>
        <xsl:if test="//article-meta/article-id[@pub-id-type='pmid']">
          <identifier>
             <xsl:attribute name="type"><xsl:text>pmid</xsl:text></xsl:attribute>
             <xsl:value-of select="//article-meta/article-id[@pub-id-type='pmid']"/>
          </identifier>
        </xsl:if>
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

  <xsl:template name="compose-date">
    <xsl:param name="xpath" select="."/>
          <date>
             <xsl:attribute name="type"><xsl:text>published</xsl:text></xsl:attribute>
             <xsl:attribute name="monthDay">
                <xsl:text>--</xsl:text>
                <xsl:choose>
                  <!-- <xsl:when test="//article-meta/pub-date[contains(@pub-type,$xpub)]/month"> -->
                  <xsl:when test="$xpath/month">
                     <xsl:value-of select="format-number($xpath/month,'00')"/>
                  </xsl:when>
                  <xsl:otherwise>
                     <xsl:text>12</xsl:text>
                  </xsl:otherwise>
                </xsl:choose>
                <xsl:text>-</xsl:text>
                <xsl:choose>
                  <xsl:when test="$xpath/day">
                     <xsl:value-of select="format-number($xpath/day,'00')"/>
                  </xsl:when>
                  <xsl:otherwise>
                     <xsl:text>01</xsl:text>
                  </xsl:otherwise>
                </xsl:choose>
             </xsl:attribute>
             <xsl:attribute name="year">
                <xsl:value-of select="$xpath/year"/>
             </xsl:attribute>
          </date>
  </xsl:template>

</xsl:stylesheet>
