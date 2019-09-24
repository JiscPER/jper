<?xml version="1.0" encoding="utf-8"?>
<xsl:stylesheet version="1.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform">

  <xsl:output method="xml" indent="yes" encoding="UTF-8"/>

  <xsl:param name="contentmodel"><xsl:text>escidoc:persistent4</xsl:text></xsl:param>

  <xsl:variable name="langCodes" select="document('./langCodeMap.xml')/langCodeMap/langCode"/>
  <xsl:variable name="langIn" select="translate(/article/@xml:lang,'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz')"/>
  <xsl:variable name="langOut" select="$langCodes[@iso639-1=$langIn]/@iso639-3"/>

  <xsl:key name="kAffById" match="//article-meta/aff" use="@id"/>

  <xsl:template match="/">
  <escidocItem:item xmlns:escidocContext="http://www.escidoc.de/schemas/context/0.7"
    xmlns:escidocContextList="http://www.escidoc.de/schemas/contextlist/0.7"
    xmlns:escidocComponents="http://www.escidoc.de/schemas/components/0.9"
    xmlns:escidocItem="http://www.escidoc.de/schemas/item/0.10"
    xmlns:escidocItemList="http://www.escidoc.de/schemas/itemlist/0.10"
    xmlns:escidocMetadataRecords="http://www.escidoc.de/schemas/metadatarecords/0.5"
    xmlns:escidocRelations="http://www.escidoc.de/schemas/relations/0.3"
    xmlns:escidocSearchResult="http://www.escidoc.de/schemas/searchresult/0.8"
    xmlns:xlink="http://www.w3.org/1999/xlink"
    xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
    xmlns:prop="http://escidoc.de/core/01/properties/"
    xmlns:srel="http://escidoc.de/core/01/structural-relations/"
    xmlns:version="http://escidoc.de/core/01/properties/version/"
    xmlns:release="http://escidoc.de/core/01/properties/release/"
    xmlns:member-list="http://www.escidoc.de/schemas/memberlist/0.10"
    xmlns:container="http://www.escidoc.de/schemas/container/0.9"
    xmlns:container-list="http://www.escidoc.de/schemas/containerlist/0.9"
    xmlns:struct-map="http://www.escidoc.de/schemas/structmap/0.4"
    xmlns:mods-md="http://www.loc.gov/mods/v3"
    xmlns:file="http://purl.org/escidoc/metadata/profiles/0.1/file"
    xmlns:publication="http://purl.org/escidoc/metadata/profiles/0.1/publication"
    xmlns:yearbook="http://purl.org/escidoc/metadata/profiles/0.1/yearbook"
    xmlns:face="http://purl.org/escidoc/metadata/profiles/0.1/face"
    xmlns:jhove="http://hul.harvard.edu/ois/xml/ns/jhove">
      <escidocItem:properties>
        <srel:content-model>
          <xsl:attribute name="objid"><xsl:value-of select="$contentmodel"/></xsl:attribute>
        </srel:content-model>
        <prop:content-model-specific xmlns:prop="http://escidoc.de/core/01/properties/"/> 
      </escidocItem:properties>
      <escidocMetadataRecords:md-records>
        <escidocMetadataRecords:md-record>
          <xsl:attribute name="name"><xsl:text>escidoc</xsl:text></xsl:attribute>
          <publication:publication xmlns:dc="http://purl.org/dc/elements/1.1/"
            xmlns:dcterms="http://purl.org/dc/terms/"
            xmlns:eterms="http://purl.org/escidoc/metadata/terms/0.1/"
            xmlns:person="http://purl.org/escidoc/metadata/profiles/0.1/person" 
            xmlns:event="http://purl.org/escidoc/metadata/profiles/0.1/event" 
            xmlns:source="http://purl.org/escidoc/metadata/profiles/0.1/source" 
            xmlns:organization="http://purl.org/escidoc/metadata/profiles/0.1/organization" 
            xmlns:legalCase="http://purl.org/escidoc/metadata/profiles/0.1/legal-case"
            xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
            <xsl:attribute name="type"><xsl:text>http://purl.org/escidoc/metadata/ves/publication-types/article</xsl:text></xsl:attribute>
            <xsl:for-each select="//article-meta/contrib-group/contrib">
              <eterms:creator>
                <xsl:attribute name="role">
                  <xsl:text>http://www.loc.gov/loc.terms/relators/</xsl:text>
                  <xsl:choose>
                    <xsl:when test="contains(@contrib-type,'editor')"><xsl:text>EDT</xsl:text></xsl:when>
                    <xsl:otherwise><xsl:text>AUT</xsl:text></xsl:otherwise>
                  </xsl:choose>
                </xsl:attribute>
                <person:person>
                  <eterms:family-name><xsl:copy-of select="name/surname/text()"/></eterms:family-name>
                  <eterms:given-name><xsl:copy-of select="name/given-names/text()"/></eterms:given-name>
                      <xsl:choose>
                        <xsl:when test="contains(xref/@ref-type,'aff') and string-length(xref/@rid)!=0">
                           <xsl:for-each select="./xref[@ref-type='aff']">
                             <organization:organization>
                               <dc:title><xsl:copy-of select="key('kAffById', @rid)/text()"/></dc:title>
                               <!-- <eterms:address><xsl:copy-of select="key('kAffById', @rid)/text()"/></eterms:address> -->
                               <!--
                               <dc:title><xsl:value-of select="key('kAffById', @rid)/text()[normalize-space()][1]"/></dc:title>
                               -->
                               <!-- for an explanation of the last select expression see 
                                    http://stackoverflow.com/questions/16134646/how-to-return-text-of-node-without-child-nodes-text
                                    the solved problem here is to get rid of the footnote markers inside the affiliation texts that are often given by child nodes...
                                -->
                             </organization:organization>
                          </xsl:for-each> 
                        </xsl:when>
                        <xsl:when test="not(contains(xref/@ref-type,'aff')) and string-length(//article-meta/aff[position()=last()]/text())!=0">
                          <xsl:for-each select="//article-meta/aff[not(@*)]">
                            <organization:organization>
                              <dc:title><xsl:copy-of select="./text()"/></dc:title>
                              <!-- <eterms:address><xsl:copy-of select="./text()"/></eterms:address> -->
                            </organization:organization>
                          </xsl:for-each>
                        </xsl:when>
                        <xsl:otherwise>
                           <organization:organization>
                             <dc:title><xsl:text>-</xsl:text></dc:title> 
                             <!-- <eterms:address><xsl:text>-</xsl:text></eterms:address> -->
                           </organization:organization>
                        </xsl:otherwise>
                      </xsl:choose>
                  <!--
                  <organization:organization>
                    <dc:title></dc:title>
                    <eterms:address/>
                  </organization:organization>
                  -->
                </person:person>
              </eterms:creator>
            </xsl:for-each>
            <dc:title><xsl:value-of select="//article-meta/title-group/article-title"/></dc:title>
            <dc:language>
              <xsl:attribute name="xsi:type"><xsl:text>dcterms:ISO639-3</xsl:text></xsl:attribute>
              <xsl:value-of select="$langOut"/>
            </dc:language>
            <dc:identifier>
              <xsl:attribute name="xsi:type"><xsl:text>eterms:DOI</xsl:text></xsl:attribute>
              <xsl:value-of select="//article-meta/article-id[@pub-id-type='doi']"/>
            </dc:identifier>
            <xsl:if test="//article-meta/article-id[@pub-id-type='pmid']">
              <dc:identifier>
                <xsl:attribute name="xsi:type"><xsl:text>eterms:PMID</xsl:text></xsl:attribute>
                <xsl:value-of select="//article-meta/article-id[@pub-id-type='pmid']"/>
              </dc:identifier>
            </xsl:if>
            <dcterms:issued>
              <xsl:attribute name="xsi:type"><xsl:text>dcterms:W3CDTF</xsl:text></xsl:attribute>
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
                <xsl:when test="//article-meta/pub-date[contains(@date-type,'pub')]/year">
                  <xsl:call-template name="compose-date">
                    <xsl:with-param name="xpub" select="'pub'"/>
                    <xsl:with-param name="xtype" select="@date-type"/>
                  </xsl:call-template>
                </xsl:when>
                <xsl:otherwise>
                  <xsl:text>1111-11-11</xsl:text>
                </xsl:otherwise>
              </xsl:choose>
            </dcterms:issued>
            <source:source>
              <xsl:attribute name="type"><xsl:text>http://purl.org/escidoc/metadata/ves/publication-types/journal</xsl:text></xsl:attribute>
              <dc:title><xsl:value-of select="//journal-meta//journal-title"/></dc:title>
              <eterms:volume><xsl:value-of select="//article-meta/volume"/></eterms:volume>
              <eterms:issue><xsl:value-of select="//article-meta/issue"/></eterms:issue>
              <eterms:start-page><xsl:value-of select="//article-meta/fpage"/></eterms:start-page>
              <eterms:end-page><xsl:value-of select="//article-meta/lpage"/></eterms:end-page>
              <xsl:if test="string-length(//article-meta/fpage/text())!=0 and string-length(//article-meta/lpage/text())!=0">
                <eterms:total-number-of-pages><xsl:value-of select="//article-meta/lpage - //article-meta/fpage + 1"/></eterms:total-number-of-pages>
              </xsl:if>
              <eterms:publishing-info>
                <dc:publisher><xsl:value-of select="//journal-meta/publisher/publisher-name"/></dc:publisher>
                <eterms:place><xsl:value-of select="//journal-meta/publisher/publisher-loc"/></eterms:place>
              </eterms:publishing-info>
              <xsl:if test="//journal-meta/issn[@pub-type='ppub']">
                <dc:identifier>
                  <xsl:attribute name="xsi:type"><xsl:text>eterms:ISSN</xsl:text></xsl:attribute>
                  <xsl:value-of select="//journal-meta/issn[@pub-type='ppub']"/><xsl:text> (pISSN)</xsl:text>
                </dc:identifier>
              </xsl:if>
              <xsl:if test="//journal-meta/issn[@pub-type='epub']">
                <dc:identifier>
                  <xsl:attribute name="xsi:type"><xsl:text>eterms:ISSN</xsl:text></xsl:attribute>
                  <xsl:value-of select="//journal-meta/issn[@pub-type='epub']"/><xsl:text> (eISSN)</xsl:text>
                </dc:identifier>
              </xsl:if>
              <xsl:if test="//journal-meta/issn[@publication-format='print']">
                <dc:identifier>
                  <xsl:attribute name="xsi:type"><xsl:text>eterms:ISSN</xsl:text></xsl:attribute>
                  <xsl:value-of select="//journal-meta/issn[@publication-format='print']"/><xsl:text> (pISSN)</xsl:text>
                </dc:identifier>
              </xsl:if>
              <xsl:if test="//journal-meta/issn[@publication-format='electronic']">
                <dc:identifier>
                  <xsl:attribute name="xsi:type"><xsl:text>eterms:ISSN</xsl:text></xsl:attribute>
                  <xsl:value-of select="//journal-meta/issn[@publication-format='electronic']"/><xsl:text> (eISSN)</xsl:text>
                </dc:identifier>
              </xsl:if>
            </source:source>
            <dcterms:abstract><xsl:value-of select="//article-meta/abstract"/></dcterms:abstract>
            <dcterms:subject>
              <xsl:for-each select="//article-meta/kwd-group/kwd">
                <xsl:value-of select="normalize-space(text())"/>
                <xsl:if test="position() != last()">
                  <xsl:text> , </xsl:text>
                </xsl:if>
              </xsl:for-each>
            </dcterms:subject>
            <dc:subject>
              <xsl:attribute name="xsi:type"><xsl:text>eterms:DDC</xsl:text></xsl:attribute>
            </dc:subject>
          </publication:publication>
        </escidocMetadataRecords:md-record>
      </escidocMetadataRecords:md-records>
    </escidocItem:item>
  </xsl:template>

  <xsl:template name="compose-date">
    <xsl:param name="xpub" select="'epub'"/>
    <xsl:param name="xtype" select="@pub-type"/>
    <xsl:value-of select="//article-meta/pub-date[contains($xtype,$xpub)]/year"/>
    <xsl:text>-</xsl:text>
    <xsl:choose>
      <xsl:when test="//article-meta/pub-date[contains($xtype,$xpub)]/month">
        <xsl:value-of select="format-number(//article-meta/pub-date[contains($xtype,$xpub)]/month,'00')"/>
      </xsl:when>
      <xsl:otherwise>
        <xsl:text>12</xsl:text>
      </xsl:otherwise>
      </xsl:choose>
      <xsl:if test="//article-meta/pub-date[contains($xtype,$xpub)]/day">
        <xsl:text>-</xsl:text>
        <xsl:value-of select="format-number(//article-meta/pub-date[contains($xtype,$xpub)]/day,'00')"/>
      </xsl:if>
  </xsl:template>

</xsl:stylesheet>
