"""
A quasi-model object used to represent xml stylesheets (xslt) for package convertion tasks
"""

class XSLT(object):

  # 2017-03-30 TD : snippet used for global xml injection needed as
  #                 iso639 code table for language codes mapping
  #                 (well, only the most likely are included so far...)
  #
  iso639codes = '''
<langCodeMap>
  <langCode iso639-1="" iso639-2="eng" iso639-3="eng"/>
  <langCode iso639-1="en" iso639-2="eng" iso639-3="eng"/>
  <langCode iso639-1="de" iso639-2="deu" iso639-3="deu"/>
  <langCode iso639-1="nl" iso639-2="nld" iso639-3="nld"/>
  <langCode iso639-1="fr" iso639-2="fra" iso639-3="fra"/>
  <langCode iso639-1="es" iso639-2="spa" iso639-3="spa"/>
  <langCode iso639-1="it" iso639-2="ita" iso639-3="ita"/>
  <langCode iso639-1="el" iso639-2="ell" iso639-3="ell"/>
  <langCode iso639-1="fi" iso639-2="fin" iso639-3="fin"/>
  <langCode iso639-1="ru" iso639-2="rus" iso639-3="rus"/>
  <langCode iso639-1="he" iso639-2="heb" iso639-3="heb"/>
</langCodeMap>
  '''


  # 2017-04-20 TD : static(!!) strings containing the xsl code RSC --> OPUS4
  #                 Note that there MUST NOT be any kind of '<?xml ...?>' header!
  #
  rsc2opus4 = '''
<xsl:stylesheet version="1.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform">

  <!-- <xsl:import href="outputTokens.xsl"/> -->
  <xsl:output method="xml" omit-xml-declaration="yes" indent="yes" encoding="utf-8"/>

  <xsl:variable name="inject">
    {xmlinject}
  </xsl:variable>
  <xsl:variable name="langIn" select="translate(/article/@xml:lang,'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz')"/>
  <!-- <xsl:variable name="langOut">eng</xsl:variable> -->
  <xsl:variable name="langOut" select="document('')//langCodeMap/langCodes[@iso639-1=$langIn]/@iso639-2"/>

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
              <xsl:value-of select="//article-meta/lpage"/>
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
            <xsl:value-of select="//published[@type='print']/journalref/publisher/orgname/nameelt"/>
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
                <xsl:attribute name="firstName"><xsl:value-of select="person/persname/fname"/></xsl:attribute>
                <xsl:attribute name="lastName"><xsl:value-of select="person/persname/surname/text()"/></xsl:attribute>
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
          <date>
             <xsl:attribute name="type"><xsl:text>published</xsl:text></xsl:attribute>
             <xsl:attribute name="monthDay">
                <xsl:text>--</xsl:text>
                <xsl:value-of select="format-number(//published[@type='print']/pubfront/date/month,'00')"/>
                <xsl:text>-</xsl:text>
                <xsl:choose>
                  <xsl:when test="//published[@type='print']/pubfront/date/day">
                     <xsl:value-of select="format-number(//published[@type='print']/pubfront/date/day,'00')"/>
                  </xsl:when>
                  <xsl:otherwise>
                     <xsl:text>01</xsl:text>
                  </xsl:otherwise>
                </xsl:choose>
             </xsl:attribute>
             <xsl:attribute name="year">
                <xsl:value-of select="//published[@type='print']/pubfront/date/year"/>
             </xsl:attribute>
          </date>
      </dates>
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
  '''.format(xmlinject=iso639codes)


  # 2017-05-15 TD : static string containing the xsl code for RSC --> ESciDoc
  #                 Note that there MUST NOT be any kind of '<?xml ...?>' header!
  #
  rsc2escidoc = '''
<xsl:stylesheet version="1.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform">

  <xsl:output method="xml" indent="yes" encoding="UTF-8"/>

  <xsl:param name="contentmodel"><xsl:text>escidoc:persistent4</xsl:text></xsl:param>

  <xsl:variable name="inject">
    {xmlinject}
  </xsl:variable>
  <xsl:variable name="langIn" select="translate(/article/@xml:lang,'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz')"/>
  <xsl:variable name="langOut" select="document('')//langCodeMap/langCodes[@iso639-1=$langIn]/@iso639-3"/>

  <!--
  <xsl:key name="kAffById" match="//art-front/aff" use="@id"/>

  <xsl:template name="split">
     <xsl:param name="pText" select="."/>
     <xsl:if test="string-length($pText)">
        <xsl:if test="not($pText=.)">
        </xsl:if>
        <xsl:value-of select="substring-before(concat($pText,' '),' ')"/>
        <xsl:call-template name="split">
           <xsl:with-param name="pText" select="substring-after($pText,' ')"/>
        </xsl:call-template>
     </xsl:if>
  </xsl:template>
  -->

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
            <xsl:for-each select="//art-front/authgrp/author">
              <eterms:creator>
                <xsl:attribute name="role">
                  <xsl:text>http://www.loc.gov/loc.terms/relators/AUT</xsl:text>
                </xsl:attribute>
                <person:person>
                  <eterms:family-name><xsl:copy-of select="person/persname/surname/text()"/></eterms:family-name>
                  <eterms:given-name><xsl:copy-of select="person/persname/fname/text()"/></eterms:given-name>
                      <xsl:choose>
                        <xsl:when test="string-length(./@aff)!=0">
                          <xsl:variable name="affs" select="./@aff"/>
                          <xsl:for-each select="//art-front/authgrp/aff[contains($affs,@id)]">
                             <organization:organization>
                               <dc:title>
                                 <xsl:for-each select="org/orgname/nameelt">
                                    <xsl:value-of select="normalize-space(text())"/>
                                    <xsl:if test="position() != last()">
                                       <xsl:text>, </xsl:text>
                                    </xsl:if>
                                 </xsl:for-each>
                               </dc:title>
                               <eterms:address>
                                 <xsl:for-each select="address/addrelt">
                                    <xsl:value-of select="normalize-space(text())"/>
                                    <xsl:if test="position() != last()">
                                       <xsl:text>, </xsl:text>
                                    </xsl:if>
                                 </xsl:for-each>
                                 <xsl:if test="address/city">
                                    <xsl:if test="string-length(address/addrelt[position()=last()]/text())!=0">
                                       <xsl:text>, </xsl:text>
                                    </xsl:if>
                                    <xsl:value-of select="normalize-space(address/city/text())"/>
                                 </xsl:if>
                                 <xsl:if test="address/country">
                                    <xsl:if test="string-length(address/addrelt[position()=last()]/text())!=0 or string-length(address/city/text())!=0">
                                       <xsl:text>, </xsl:text>
                                    </xsl:if>
                                    <xsl:value-of select="normalize-space(address/country/text())"/>
                                 </xsl:if>
                               </eterms:address>
                               <!--
                               <eterms:address><xsl:copy-of select="key('kAffById', @rid)/text()"/></eterms:address>
                               <dc:title><xsl:value-of select="key('kAffById', @rid)/text()[normalize-space()][1]"/></dc:title>
                               -->
                               <!-- for an explanation of the last select expression see 
                                    http://stackoverflow.com/questions/16134646/how-to-return-text-of-node-without-child-nodes-text
                                    the solved problem here is to get rid of the footnote markers inside the affiliation texts that are often given by child nodes...
                                -->
                             </organization:organization>
                          </xsl:for-each> 
                        </xsl:when>
                        <xsl:otherwise>
                           <organization:organization>
                             <dc:title><xsl:text>-</xsl:text></dc:title> 
                             <eterms:address><xsl:text>-</xsl:text></eterms:address>
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
            <dc:title><xsl:value-of select="//art-front/titlegrp/title"/></dc:title>
            <dc:language>
              <xsl:attribute name="xsi:type"><xsl:text>dcterms:ISO639-3</xsl:text></xsl:attribute>
              <xsl:value-of select="$langOut"/>
            </dc:language>
            <dc:identifier>
              <xsl:attribute name="xsi:type"><xsl:text>eterms:DOI</xsl:text></xsl:attribute>
              <xsl:value-of select="//art-admin/doi"/>
            </dc:identifier>
            <!--
            <xsl:if test="//article-meta/article-id[@pub-id-type='pmid']">
              <dc:identifier>
                <xsl:attribute name="xsi:type"><xsl:text>eterms:PMID</xsl:text></xsl:attribute>
                <xsl:value-of select="//article-meta/article-id[@pub-id-type='pmid']"/>
              </dc:identifier>
            </xsl:if>
            -->
            <dcterms:issued>
              <xsl:attribute name="xsi:type"><xsl:text>dcterms:W3CDTF</xsl:text></xsl:attribute>
              <xsl:choose>
                <xsl:when test="//published[@type='online']/pubfront/date/year">
                  <xsl:call-template name="compose-date">
                    <xsl:with-param name="xpub" select="'online'"/>
                  </xsl:call-template>
                </xsl:when>
                <xsl:when test="//published[@type='print']/pubfront/date/year">
                  <xsl:call-template name="compose-date">
                    <xsl:with-param name="xpub" select="'print'"/>
                  </xsl:call-template>
                </xsl:when>
                <xsl:otherwise>
                  <xsl:text>1111-11-11</xsl:text>
                </xsl:otherwise>
              </xsl:choose>
            </dcterms:issued>
            <source:source>
              <xsl:attribute name="type"><xsl:text>http://purl.org/escidoc/metadata/ves/publication-types/journal</xsl:text></xsl:attribute>
              <dc:title><xsl:value-of select="//published[@type='print']/journalref/title[@type='full']"/></dc:title>
              <eterms:volume><xsl:value-of select="//published[@type='print']/volumeref/link"/></eterms:volume>
              <eterms:issue><xsl:value-of select="//published[@type='print']/issueref/link"/></eterms:issue>
              <eterms:start-page><xsl:value-of select="//published[@type='print']/pubfront/fpage"/></eterms:start-page>
              <eterms:end-page><xsl:value-of select="//published[@type='print']/pubfront/lpage"/></eterms:end-page>
              <eterms:total-number-of-pages><xsl:value-of select="//published[@type='print']/pubfront/no-of-pages"/></eterms:total-number-of-pages>
              <eterms:publishing-info>
                <dc:publisher><xsl:value-of select="//published[@type='print']/publisher/orgname/nameelt"/></dc:publisher>
                <!--
                <eterms:place><xsl:value-of select="//published[@type='print']/publisher//orgname/locelt"/></eterms:place>
                -->
              </eterms:publishing-info>
              <xsl:if test="//published[@type='print']/journalref/issn[@type='print']">
                <dc:identifier>
                  <xsl:attribute name="xsi:type"><xsl:text>eterms:ISSN</xsl:text></xsl:attribute>
                  <xsl:value-of select="//published[@type='print']/journalref/issn[@type='print']"/><xsl:text> (pISSN)</xsl:text>
                </dc:identifier>
              </xsl:if>
              <xsl:if test="//published[@type='print']/journalref/issn[@type='online']">
                <dc:identifier>
                  <xsl:attribute name="xsi:type"><xsl:text>eterms:ISSN</xsl:text></xsl:attribute>
                  <xsl:value-of select="//published[@type='print']/journalref/issn[@type='online']"/><xsl:text> (eISSN)</xsl:text>
                </dc:identifier>
              </xsl:if>
            </source:source>
            <dcterms:abstract><xsl:value-of select="//art-front/abstract"/></dcterms:abstract>
            <dcterms:subject><xsl:text>-</xsl:text></dcterms:subject>
            <dc:subject>
              <xsl:attribute name="xsi:type"><xsl:text>eterms:DDC</xsl:text></xsl:attribute>
            </dc:subject>
          </publication:publication>
        </escidocMetadataRecords:md-record>
      </escidocMetadataRecords:md-records>
    </escidocItem:item>
  </xsl:template>

  <xsl:template name="compose-date">
    <xsl:param name="xpub" select="'online'"/>
    <xsl:value-of select="//published[@type=$xpub]/pubfront/date/year"/>
    <xsl:text>-</xsl:text>
    <xsl:choose>
      <xsl:when test="//published[@type=$xpub]/pubfront/date/month">
        <xsl:value-of select="format-number(//published[@type=$xpub]/pubfront/date/month,'00')"/>
      </xsl:when>
      <xsl:otherwise>
        <xsl:text>12</xsl:text>
      </xsl:otherwise>
      </xsl:choose>
      <xsl:if test="//published[@type=$xpub]/pubfront/date/day">
        <xsl:text>-</xsl:text>
        <xsl:value-of select="format-number(//published[@type=$xpub]/pubfront/date/day,'00')"/>
      </xsl:if>
  </xsl:template>

</xsl:stylesheet>
  '''.format(xmlinject=iso639codes)


  # 2017-05-15 TD : static string containing the xsl code for RSC --> METSDspaceSIP
  #                 Note that there MUST NOT be any kind of '<?xml ...?>' header!
  #
  rsc2metsdspace = '''
<xsl:stylesheet version="1.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform">

  <!-- <xsl:import href="outputTokens.xsl"/> -->
  <xsl:output method="xml" omit-xml-declaration="no" standalone="no" indent="yes" encoding="utf-8"/>

  <xsl:param name="currdatetime">1970-01-01T00:00:00</xsl:param>

  <xsl:variable name="inject">
    {xmlinject}
  </xsl:variable>
  <xsl:variable name="langIn" select="translate(/article/@xml:lang,'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz')"/>
  <!-- <xsl:variable name="langOut">eng</xsl:variable> -->
  <xsl:variable name="langOut" select="document('')//langCodeMap/langCodes[@iso639-1=$langIn]/@iso639-2"/>

  <xsl:template match="/">
  <mets xmlns="http://www.loc.gov/METS/"
    xmlns:xlink="http://www.w3.org/1999/xlink"
    xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
    xsi:schemaLocation="http://www.loc.gov/METS/ http://www.loc.gov/standards/mets/mets.xsd">
    <xsl:attribute name="ID"><xsl:text>sort-mets_mets</xsl:text></xsl:attribute>
    <xsl:attribute name="OBJID"><xsl:text>sword-mets</xsl:text></xsl:attribute>
    <xsl:attribute name="LABEL"><xsl:text>DSpace SWORD Item</xsl:text></xsl:attribute>
    <xsl:attribute name="PROFILE"><xsl:text>DSpace METS SIP Profile 1.0</xsl:text></xsl:attribute>
    <metsHdr>
      <xsl:attribute name="CREATEDATE"><xsl:value-of select="$currdatetime"/></xsl:attribute>
      <agent>
        <xsl:attribute name="ROLE">CUSTODIAN</xsl:attribute>
        <xsl:attribute name="TYPE">ORGANIZATION</xsl:attribute>
        <name>Green DeepGreen</name>
      </agent>
    </metsHdr>
    <dmdSec>
      <xsl:attribute name="ID">sword-mets-dmd-1</xsl:attribute>
      <xsl:attribute name="GROUPID">sword-mets-dmd-1_group-1</xsl:attribute>
      <mdWrap>
        <xsl:attribute name="LABEL"><xsl:text>SWAP Metadata</xsl:text></xsl:attribute>
        <xsl:attribute name="MDTYPE">OTHER</xsl:attribute>
        <xsl:attribute name="OTHERMDTYPE">EPDCX</xsl:attribute>
        <xsl:attribute name="MIMETYPE"><xsl:text>text/xml</xsl:text></xsl:attribute>
        <xmlData>
          <epdcx:descriptionSet xmlns:epdcx="http://purl.org/eprint/epdcx/2006-11-16/"
            xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
            xsi:schemaLocation="http://purl.org/eprint/epdcx/2006-11-16/ http://purl.org/eprint/epdcx/xsd/2006-11-16/epdcx.xsd">
            <epdcx:description>
              <xsl:attribute name="epdcx:resourceId">sword-mets-epdcx-1</xsl:attribute>
              <epdcx:statement>
                <xsl:attribute name="epdcx:propertyURI">http://purl.org/dc/elements/1.1/type</xsl:attribute>
                <xsl:attribute name="epdcx:valueURI">http://purl.org/eprint/entityType/ScholarlyWork</xsl:attribute>
              </epdcx:statement>
              <epdcx:statement>
                <xsl:attribute name="epdcx:propertyURI">http://purl.org/dc/elements/1.1/title</xsl:attribute>
                <epdcx:valueString><xsl:value-of select="//art-front/titlegrp/title"/></epdcx:valueString>
              </epdcx:statement>
              <epdcx:statement>
                <xsl:attribute name="epdcx:propertyURI">http://purl.org/dc/terms/abstract</xsl:attribute>
                <epdcx:valueString><xsl:value-of select="//art-front/abstract"/></epdcx:valueString>
              </epdcx:statement>
              <xsl:for-each select="//art-front/authgrp/author">
                <epdcx:statement>
                  <xsl:attribute name="epdcx:propertyURI">http://purl.org/dc/elements/1.1/creator</xsl:attribute>
                  <epdcx:valueString>
                    <xsl:copy-of select="person/persname/surname/text()"/>
                    <xsl:if test="string-length(person/persname/fname/text()) > 0">
                      <xsl:text>, </xsl:text>
                      <xsl:copy-of select="person/persname/fname/text()"/>
                    </xsl:if>
                  </epdcx:valueString>
                </epdcx:statement>
              </xsl:for-each>
              <epdcx:statement>
                <xsl:attribute name="epdcx:propertyURI">http://purl.org/dc/elements/1.1/identifier</xsl:attribute>
                <epdcx:valueString>
                  <xsl:attribute name="epdcx:sesURI">http://purl.org/dc/terms/URI</xsl:attribute>
                  <xsl:text>http://dx.doi.org/</xsl:text>
                  <xsl:value-of select="//art-admin/doi"/>
                </epdcx:valueString>
              </epdcx:statement>
              <epdcx:statement>
                <xsl:attribute name="epdcx:propertyURI">http://purl.org/eprint/terms/isExpressedAs</xsl:attribute>
                <xsl:attribute name="epdcx:valueRef">sword-mets-expr-1</xsl:attribute>
              </epdcx:statement>
            </epdcx:description>
            <!-- Second (level?) description starts here -->
            <epdcx:description>
              <xsl:attribute name="epdcx:resourceId">sword-mets-expr-1</xsl:attribute>
              <epdcx:statement>
                <xsl:attribute name="epdcx:propertyURI">http://purl.org/dc/elements/1.1/type</xsl:attribute>
                <xsl:attribute name="epdcx:valueURI">http://purl.org/eprint/entityType/Expression</xsl:attribute>
              </epdcx:statement>
              <epdcx:statement>
                <xsl:attribute name="epdcx:propertyURI">http://purl.org/dc/terms/bibliographicCitation</xsl:attribute>
                <epdcx:valueString>
                  <xsl:copy-of select="//art-front/authgrp/author[position()=1]/person/persname/surname/text()"/>
                  <xsl:if test="string-length(//art-front/authgrp/author[position()=1]/person/persname/fname/text()) > 0">
                    <xsl:text>, </xsl:text>
                    <xsl:copy-of select="//art-front/authgrp/author[position()=1]/person/persname/fname/text()"/>
                  </xsl:if>
                  <xsl:if test="//art-front/authgrp/author[position()>1]">
                    <xsl:text> et al.</xsl:text>
                  </xsl:if>
                  <xsl:text>: </xsl:text>
                  <xsl:value-of select="//published[@type='print']/journalref/title"/>
                  <xsl:text> </xsl:text>
                  <xsl:value-of select="//published[@type='print']/volumeref/link"/>
                  <xsl:text> (</xsl:text>
                  <xsl:choose>
                    <xsl:when test="//published[@type='print']/pubfront/date/year">
                      <xsl:value-of select="//published[@type='print']/pubfront/date/year"/>
                    </xsl:when>
                    <xsl:otherwise>
                      <xsl:value-of select="//published[@type='online']/pubfront/date/year"/>
                    </xsl:otherwise>
                  </xsl:choose>
                  <xsl:text>), </xsl:text>
                  <xsl:value-of select="//published[@type='print']/pubfront/fpage"/>
                    <xsl:if test="string-length(//published[@type='print']/pubfront/lpage/text())!=0">
                    <xsl:text> - </xsl:text>
                    <xsl:value-of select="//published[@type='print']/pubfront/lpage"/>
                  </xsl:if>
                </epdcx:valueString>
              </epdcx:statement>
              <epdcx:statement>
                <xsl:attribute name="epdcx:propertyURI">http://purl.org/dc/elements/1.1/language</xsl:attribute>
                <xsl:attribute name="epdcx:vesURI">http://purl.org/dc/terms/ISO639-2</xsl:attribute>
                <epdcx:valueString>
                  <xsl:value-of select="$langOut"/>
                </epdcx:valueString>
              </epdcx:statement>
              <epdcx:statement>
                <xsl:attribute name="epdcx:propertyURI">http://purl.org/dc/elements/1.1/type</xsl:attribute>
                <xsl:attribute name="epdcx:vesURI">http://purl.org/eprint/terms/Type</xsl:attribute>
                <xsl:attribute name="epdcx:valueURI">http://purl.org/eprint/type/JournalArticle</xsl:attribute>
              </epdcx:statement>
              <epdcx:statement>
                <xsl:attribute name="epdcx:propertyURI">http://purl.org/dc/terms/available</xsl:attribute>
                <epdcx:valueString>
                  <xsl:attribute name="epdcx:sesURI">http://purl.org/dc/terms/W3CDTF</xsl:attribute>
                  <xsl:choose>
                    <xsl:when test="//published[@type='online']/pubfront/date/year">
                      <xsl:call-template name="compose-date">
                        <xsl:with-param name="xpub" select="'online'"/>
                      </xsl:call-template>
                    </xsl:when>
                    <xsl:when test="//published[@type='print']/pubfront/date/year">
                      <xsl:call-template name="compose-date">
                        <xsl:with-param name="xpub" select="'print'"/>
                      </xsl:call-template>
                    </xsl:when>
                    <xsl:otherwise>
                      <xsl:text>1111-11-11</xsl:text>
                    </xsl:otherwise>
                  </xsl:choose>
                </epdcx:valueString>
              </epdcx:statement>
              <epdcx:statement>
                <xsl:attribute name="epdcx:propertyURI">http://purl.org/dc/terms/source</xsl:attribute>
                <epdcx:valueString>
                  <xsl:value-of select="//published[@type='print']/journalref/title"/>
                </epdcx:valueString>
              </epdcx:statement>
              <xsl:for-each select="//published[@type='print']/journalref/issn[@type='print']">
                <epdcx:statement>
                  <xsl:attribute name="epdcx:propertyURI">http://purl.org/dc/terms/source</xsl:attribute>
                  <epdcx:valueString>
                    <xsl:text>pISSN:</xsl:text>
                    <xsl:value-of select="normalize-space(text())"/>
                  </epdcx:valueString>
                </epdcx:statement>
              </xsl:for-each>
              <xsl:if test="//published[@type='print']/journalref/issn[@type='online']">
                <xsl:for-each select="//published[@type='print']/journalref/issn[@type='online']">
                  <epdcx:statement>
                    <xsl:attribute name="epdcx:propertyURI">http://purl.org/dc/terms/source</xsl:attribute>
                    <epdcx:valueString>
                      <xsl:text>eISSN:</xsl:text>
                      <xsl:value-of select="normalize-space(text())"/>
                    </epdcx:valueString>
                  </epdcx:statement>
                </xsl:for-each>
              </xsl:if>
              <epdcx:statement>
                <xsl:attribute name="epdcx:propertyURI">http://purl.org/dc/terms/publisher</xsl:attribute>
                <epdcx:valueString>
                  <xsl:value-of select="//published[@type='print']/journalref/publisher/orgname/nameelt"/>
                </epdcx:valueString>
              </epdcx:statement>
            </epdcx:description>
            <!-- End of DescriptionSet -->
          </epdcx:descriptionSet>
        </xmlData>
      </mdWrap>
    </dmdSec>
    <!--
    <fileSec>
       <fileGrp ID="sword-mets-fgrp-0" USE="CONTENT">
          <file GROUPID="sword-mets-fgid-1" 
                ID="sword-mets-file-1"
                MIMETYPE="application/pdf" 
                CHECKSUM="2362eff352a3b452523" 
                CHECKSUMTYPE="MD5">
                <FLocat LOCTYPE="URL" xlink:href="pdf1.pdf" />
          </file>
          <file GROUPID="sword-mets-fgid-2" 
                ID="sword-mets-file-2"
                MIMETYPE="application/pdf">
                <FLocat LOCTYPE="URL" xlink:href="pdf2.pdf" />
          </file>
          <file GROUPID="sword-mets-fgid-3" 
                ID="sword-mets-file-3"
                MIMETYPE="application/pdf">
                <FLocat LOCTYPE="URL" xlink:href="pdf3.pdf" />
          </file>
       </fileGrp>
    </fileSec>
    <structMap ID="sword-mets-struct-1" LABEL="structure" TYPE="LOGICAL">
       <div ID="sword-mets-div-0" DMDID="sword-mets-dmd-1" TYPE="SWORD Object">
          <div ID="sword-mets-div-1" TYPE="File">
              <fptr FILEID="sword-mets-file-1" />
          </div>
          <div ID="sword-mets-div-2" TYPE="File">
              <fptr FILEID="sword-mets-file-2" />
          </div>
          <div ID="sword-mets-div-3" TYPE="File">
              <fptr FILEID="sword-mets-file-3" />
          </div>
       </div>
    </structMap>
    -->
  </mets>
  </xsl:template>

  <xsl:template name="compose-date">
    <xsl:param name="xpub" select="'online'"/>
    <xsl:value-of select="//published[@type=$xpub]/pubfront/date/year"/>
    <xsl:text>-</xsl:text>
    <xsl:choose>
      <xsl:when test="//published[@type=$xpub]/pubfront/date/month">
        <xsl:value-of select="format-number(//published[@type=$xpub]/pubfront/date/month,'00')"/>
      </xsl:when>
      <xsl:otherwise>
        <xsl:text>12</xsl:text>
      </xsl:otherwise>
      </xsl:choose>
      <xsl:if test="//published[@type=$xpub]/pubfront/date/day">
        <xsl:text>-</xsl:text>
        <xsl:value-of select="format-number(//published[@type=$xpub]/pubfront/date/day,'00')"/>
      </xsl:if>
  </xsl:template>

</xsl:stylesheet>
  '''.format(xmlinject=iso639codes)


  # -----------------------------------------------------------------------------
  # =============================================================================
  # -----------------------------------------------------------------------------


  # 2017-03-22 TD : static(!!) strings containing the xsl code JATS --> OPUS4
  #                 Note that there MUST NOT be any kind of '<?xml ...?>' header!
  #
  jats2opus4 = '''
<xsl:stylesheet version="1.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform">

  <!-- <xsl:import href="outputTokens.xsl"/> -->
  <xsl:output method="xml" omit-xml-declaration="yes" indent="yes" encoding="utf-8"/>

  <xsl:variable name="inject">
    {xmlinject}
  </xsl:variable>
  <xsl:variable name="langIn" select="translate(/article/@xml:lang,'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz')"/>
  <!-- <xsl:variable name="langOut">eng</xsl:variable> -->
  <xsl:variable name="langOut" select="document('')//langCodeMap/langCodes[@iso639-1=$langIn]/@iso639-2"/>

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
          <xsl:if test="//journal-meta/journal-title-group/journal-title">
            <title> 
              <xsl:attribute name="language"><xsl:value-of select="$langOut"/></xsl:attribute>
              <xsl:attribute name="type"><xsl:text>parent</xsl:text></xsl:attribute> 
              <xsl:value-of select="//journal-meta/journal-title-group/journal-title"/>
            </title>
          </xsl:if>
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
          </xsl:for-each>
      </persons>
      <keywords>
          <keyword> 
            <xsl:attribute name="language"><xsl:value-of select="$langOut"/></xsl:attribute>
            <xsl:attribute name="type"><xsl:text>swd</xsl:text></xsl:attribute>
            <xsl:text>-</xsl:text>
          </keyword>
          <xsl:for-each select="//article-meta/kwd-group/kwd">
            <keyword> 
              <xsl:attribute name="language"><xsl:value-of select="$langOut"/></xsl:attribute>
              <xsl:attribute name="type"><xsl:text>uncontrolled</xsl:text></xsl:attribute>
              <xsl:value-of select="normalize-space(text())"/>
            </keyword>
          </xsl:for-each>
      </keywords>
      <!--
      <dnbInstitutions>
          <dnbInstitution id="<integer>" role="grantor|publisher"/>
      </dnbInstitutions>
      -->
      <dates>
          <date>
             <xsl:attribute name="type"><xsl:text>published</xsl:text></xsl:attribute>
             <xsl:attribute name="monthDay">
                <xsl:text>--</xsl:text>
                <xsl:value-of select="format-number(//article-meta/pub-date[contains(@pub-type,'ppub')]/month,'00')"/>
                <xsl:text>-</xsl:text>
                <xsl:choose>
                  <xsl:when test="//article-meta/pub-date[contains(@pub-type,'ppub')]/day">
                     <xsl:value-of select="format-number(//article-meta/pub-date[contains(@pub-type,'ppub')]/day,'00')"/>
                  </xsl:when>
                  <xsl:otherwise>
                     <xsl:text>01</xsl:text>
                  </xsl:otherwise>
                </xsl:choose>
             </xsl:attribute>
             <xsl:attribute name="year">
                <xsl:value-of select="//article-meta/pub-date[contains(@pub-type,'ppub')]/year"/>
             </xsl:attribute>
          </date>
      </dates>
      <identifiers>
          <identifier>
             <xsl:attribute name="type"><xsl:text>issn</xsl:text></xsl:attribute>
             <xsl:for-each select="//journal-meta/issn[@pub-type='ppub']">
                <xsl:value-of select="normalize-space(text())"/>
                <xsl:if test="position() != last()">
                   <xsl:text> , </xsl:text>
                </xsl:if>
                <xsl:if test="position() = last()">
                   <xsl:text> (pISSN)</xsl:text>
                </xsl:if>
             </xsl:for-each>
             <xsl:if test="//journal-meta/issn[@pub-type='epub']">
                <xsl:text> ; </xsl:text>
                <xsl:for-each select="//journal-meta/issn[@pub-type='epub']">
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
'''.format(xmlinject=iso639codes)


  # 2017-05-15 TD : static string containing the xsl code for JATS --> ESciDoc
  #                 Note that there MUST NOT be any kind of '<?xml ...?>' header!
  #
  jats2escidoc = '''
<xsl:stylesheet version="1.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform">

  <xsl:output method="xml" indent="yes" encoding="UTF-8"/>

  <xsl:param name="contentmodel"><xsl:text>escidoc:persistent4</xsl:text></xsl:param>

  <xsl:variable name="inject">
    {xmlinject}
  </xsl:variable>
  <xsl:variable name="langIn" select="translate(/article/@xml:lang,'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz')"/>
  <xsl:variable name="langOut" select="document('')//langCodeMap/langCodes[@iso639-1=$langIn]/@iso639-3"/>

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
                <xsl:otherwise>
                  <xsl:text>1111-11-11</xsl:text>
                </xsl:otherwise>
              </xsl:choose>
            </dcterms:issued>
            <source:source>
              <xsl:attribute name="type"><xsl:text>http://purl.org/escidoc/metadata/ves/publication-types/journal</xsl:text></xsl:attribute>
              <dc:title><xsl:value-of select="//journal-meta/journal-title-group/journal-title"/></dc:title>
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
  '''.format(xmlinject=iso639codes)


  # 2017-05-15 TD : static string containing the xsl code for JATS --> METSDspaceSIP
  #                 Note that there MUST NOT be any kind of '<?xml ...?>' header!
  #
  jats2metsdspace = '''
<xsl:stylesheet version="1.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform">

  <!-- <xsl:import href="outputTokens.xsl"/> -->
  <xsl:output method="xml" omit-xml-declaration="no" standalone="no" indent="yes" encoding="utf-8"/>

  <xsl:param name="currdatetime">1970-01-01T00:00:00</xsl:param>

  <xsl:variable name="inject">
    {xmlinject}
  </xsl:variable>
  <xsl:variable name="langCodes" select="document('langCodeMap.xml')/langCodeMap/langCode"/>
  <xsl:variable name="langIn" select="translate(/article/@xml:lang,'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz')"/>
  <!-- <xsl:variable name="langOut">eng</xsl:variable> -->
  <xsl:variable name="langOut" select="document('')//langCodeMap/langCodes[@iso639-1=$langIn]/@iso639-2"/>

  <xsl:template match="/">
  <mets xmlns="http://www.loc.gov/METS/"
    xmlns:xlink="http://www.w3.org/1999/xlink"
    xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
    xsi:schemaLocation="http://www.loc.gov/METS/ http://www.loc.gov/standards/mets/mets.xsd">
    <xsl:attribute name="ID"><xsl:text>sort-mets_mets</xsl:text></xsl:attribute>
    <xsl:attribute name="OBJID"><xsl:text>sword-mets</xsl:text></xsl:attribute>
    <xsl:attribute name="LABEL"><xsl:text>DSpace SWORD Item</xsl:text></xsl:attribute>
    <xsl:attribute name="PROFILE"><xsl:text>DSpace METS SIP Profile 1.0</xsl:text></xsl:attribute>
    <metsHdr>
      <xsl:attribute name="CREATEDATE"><xsl:value-of select="$currdatetime"/></xsl:attribute>
      <agent>
        <xsl:attribute name="ROLE">CUSTODIAN</xsl:attribute>
        <xsl:attribute name="TYPE">ORGANIZATION</xsl:attribute>
        <name>Green DeepGreen</name>
      </agent>
    </metsHdr>
    <dmdSec>
      <xsl:attribute name="ID">sword-mets-dmd-1</xsl:attribute>
      <xsl:attribute name="GROUPID">sword-mets-dmd-1_group-1</xsl:attribute>
      <mdWrap>
        <xsl:attribute name="LABEL"><xsl:text>SWAP Metadata</xsl:text></xsl:attribute>
        <xsl:attribute name="MDTYPE">OTHER</xsl:attribute>
        <xsl:attribute name="OTHERMDTYPE">EPDCX</xsl:attribute>
        <xsl:attribute name="MIMETYPE"><xsl:text>text/xml</xsl:text></xsl:attribute>
        <xmlData>
          <epdcx:descriptionSet xmlns:epdcx="http://purl.org/eprint/epdcx/2006-11-16/"
            xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
            xsi:schemaLocation="http://purl.org/eprint/epdcx/2006-11-16/ http://purl.org/eprint/epdcx/xsd/2006-11-16/epdcx.xsd">
            <epdcx:description>
              <xsl:attribute name="epdcx:resourceId">sword-mets-epdcx-1</xsl:attribute>
              <epdcx:statement>
                <xsl:attribute name="epdcx:propertyURI">http://purl.org/dc/elements/1.1/type</xsl:attribute>
                <xsl:attribute name="epdcx:valueURI">http://purl.org/eprint/entityType/ScholarlyWork</xsl:attribute>
              </epdcx:statement>
              <epdcx:statement>
                <xsl:attribute name="epdcx:propertyURI">http://purl.org/dc/elements/1.1/title</xsl:attribute>
                <epdcx:valueString><xsl:value-of select="//article-meta/title-group/article-title"/></epdcx:valueString>
              </epdcx:statement>
              <epdcx:statement>
                <xsl:attribute name="epdcx:propertyURI">http://purl.org/dc/terms/abstract</xsl:attribute>
                <epdcx:valueString><xsl:value-of select="//article-meta/abstract"/></epdcx:valueString>
              </epdcx:statement>
              <xsl:for-each select="//article-meta/contrib-group/contrib">
                <epdcx:statement>
                  <xsl:attribute name="epdcx:propertyURI">http://purl.org/dc/elements/1.1/creator</xsl:attribute>
                  <epdcx:valueString>
                    <xsl:value-of select="name/surname"/>
                    <xsl:if test="string-length(name/given-names/text()) > 0">
                      <xsl:text>, </xsl:text>
                      <xsl:value-of select="name/given-names"/>
                    </xsl:if>
                  </epdcx:valueString>
                </epdcx:statement>
              </xsl:for-each>
              <epdcx:statement>
                <xsl:attribute name="epdcx:propertyURI">http://purl.org/dc/elements/1.1/identifier</xsl:attribute>
                <epdcx:valueString>
                  <xsl:attribute name="epdcx:sesURI">http://purl.org/dc/terms/URI</xsl:attribute>
                  <xsl:text>http://dx.doi.org/</xsl:text>
                  <xsl:value-of select="//article-meta/article-id[@pub-id-type='doi']"/>
                </epdcx:valueString>
              </epdcx:statement>
              <epdcx:statement>
                <xsl:attribute name="epdcx:propertyURI">http://purl.org/eprint/terms/isExpressedAs</xsl:attribute>
                <xsl:attribute name="epdcx:valueRef">sword-mets-expr-1</xsl:attribute>
              </epdcx:statement>
            </epdcx:description>
            <!-- Second (level?) description starts here -->
            <epdcx:description>
              <xsl:attribute name="epdcx:resourceId">sword-mets-expr-1</xsl:attribute>
              <epdcx:statement>
                <xsl:attribute name="epdcx:propertyURI">http://purl.org/dc/elements/1.1/type</xsl:attribute>
                <xsl:attribute name="epdcx:valueURI">http://purl.org/eprint/entityType/Expression</xsl:attribute>
              </epdcx:statement>
              <epdcx:statement>
                <xsl:attribute name="epdcx:propertyURI">http://purl.org/dc/terms/bibliographicCitation</xsl:attribute>
                <epdcx:valueString>
                  <xsl:value-of select="//article-meta/contrib-group/contrib[position()=1]/name/surname"/>
                  <xsl:if test="string-length(//article-meta/contrib-group/contrib[position()=1]/name/given-names/text()) > 0">
                    <xsl:text>, </xsl:text>
                    <xsl:value-of select="//article-meta/contrib-group/contrib[position()=1]/name/given-names"/>
                  </xsl:if>
                  <xsl:if test="//article-meta/contrib-group/contrib[position()>1]">
                    <xsl:text> et al.</xsl:text>
                  </xsl:if>
                  <xsl:text>: </xsl:text>
                  <xsl:value-of select="//journal-meta/journal-title-group/journal-title"/>
                  <xsl:text> </xsl:text>
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
                </epdcx:valueString>
              </epdcx:statement>
              <epdcx:statement>
                <xsl:attribute name="epdcx:propertyURI">http://purl.org/dc/elements/1.1/language</xsl:attribute>
                <xsl:attribute name="epdcx:vesURI">http://purl.org/dc/terms/ISO639-2</xsl:attribute>
                <epdcx:valueString>
                  <xsl:value-of select="$langOut"/>
                </epdcx:valueString>
              </epdcx:statement>
              <epdcx:statement>
                <xsl:attribute name="epdcx:propertyURI">http://purl.org/dc/elements/1.1/type</xsl:attribute>
                <xsl:attribute name="epdcx:vesURI">http://purl.org/eprint/terms/Type</xsl:attribute>
                <xsl:attribute name="epdcx:valueURI">http://purl.org/eprint/type/JournalArticle</xsl:attribute>
              </epdcx:statement>
              <epdcx:statement>
                <xsl:attribute name="epdcx:propertyURI">http://purl.org/dc/terms/available</xsl:attribute>
                <epdcx:valueString>
                  <xsl:attribute name="epdcx:sesURI">http://purl.org/dc/terms/W3CDTF</xsl:attribute>
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
                </epdcx:valueString>
              </epdcx:statement>
              <epdcx:statement>
                <xsl:attribute name="epdcx:propertyURI">http://purl.org/dc/terms/source</xsl:attribute>
                <epdcx:valueString>
                  <xsl:value-of select="//journal-meta/journal-title-group/journal-title"/>
                </epdcx:valueString>
              </epdcx:statement>
              <xsl:for-each select="//journal-meta/issn[@pub-type='ppub']">
                <epdcx:statement>
                  <xsl:attribute name="epdcx:propertyURI">http://purl.org/dc/terms/source</xsl:attribute>
                  <epdcx:valueString>
                    <xsl:text>pISSN:</xsl:text>
                    <xsl:value-of select="normalize-space(text())"/>
                  </epdcx:valueString>
                </epdcx:statement>
              </xsl:for-each>
              <xsl:for-each select="//journal-meta/issn[@pub-type='epub']">
                <epdcx:statement>
                  <xsl:attribute name="epdcx:propertyURI">http://purl.org/dc/terms/source</xsl:attribute>
                  <epdcx:valueString>
                    <xsl:text>eISSN:</xsl:text>
                    <xsl:value-of select="normalize-space(text())"/>
                  </epdcx:valueString>
                </epdcx:statement>
              </xsl:for-each>
              <epdcx:statement>
                <xsl:attribute name="epdcx:propertyURI">http://purl.org/dc/terms/publisher</xsl:attribute>
                <epdcx:valueString>
                  <xsl:value-of select="//journal-meta/publisher/publisher-name"/>
                </epdcx:valueString>
              </epdcx:statement>
            </epdcx:description>
            <!-- End of DescriptionSet -->
          </epdcx:descriptionSet>
        </xmlData>
      </mdWrap>
    </dmdSec>
    <!--
    <fileSec>
       <fileGrp ID="sword-mets-fgrp-0" USE="CONTENT">
          <file GROUPID="sword-mets-fgid-1" 
                ID="sword-mets-file-1"
                MIMETYPE="application/pdf" 
                CHECKSUM="2362eff352a3b452523" 
                CHECKSUMTYPE="MD5">
                <FLocat LOCTYPE="URL" xlink:href="pdf1.pdf" />
          </file>
          <file GROUPID="sword-mets-fgid-2" 
                ID="sword-mets-file-2"
                MIMETYPE="application/pdf">
                <FLocat LOCTYPE="URL" xlink:href="pdf2.pdf" />
          </file>
          <file GROUPID="sword-mets-fgid-3" 
                ID="sword-mets-file-3"
                MIMETYPE="application/pdf">
                <FLocat LOCTYPE="URL" xlink:href="pdf3.pdf" />
          </file>
       </fileGrp>
    </fileSec>
    <structMap ID="sword-mets-struct-1" LABEL="structure" TYPE="LOGICAL">
       <div ID="sword-mets-div-0" DMDID="sword-mets-dmd-1" TYPE="SWORD Object">
          <div ID="sword-mets-div-1" TYPE="File">
              <fptr FILEID="sword-mets-file-1" />
          </div>
          <div ID="sword-mets-div-2" TYPE="File">
              <fptr FILEID="sword-mets-file-2" />
          </div>
          <div ID="sword-mets-div-3" TYPE="File">
              <fptr FILEID="sword-mets-file-3" />
          </div>
       </div>
    </structMap>
    -->
  </mets>
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
  '''.format(xmlinject=iso639codes)


  # -----------------------------------------------------------------------------
  # =============================================================================
  # -----------------------------------------------------------------------------


  # 2017-03-30 TD : xslt specific to file addition to already transformed opus4.xml
  #                 Note again that, here too, there MUST NOT be any "<?xml ...>" header!
  #
  addfiles2opus4 = '''
<xsl:stylesheet version="1.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform">

  <xsl:output method="xml" omit-xml-declaration="yes" indent="yes" encoding="utf-8"/>

  <xsl:param name="file"/>
  <xsl:param name="md5"/>

  <xsl:template match="node()|@*">
    <xsl:copy>
      <xsl:apply-templates select="node()|@*"/>
    </xsl:copy>
  </xsl:template>

  <xsl:template match="/import/opusDocument">
    <xsl:copy>
      <xsl:copy-of select="node()|@*"/>
      <xsl:if test="not(./files) and string-length($file)!=0 and string-length($md5)!=0">
        <files>
           <xsl:attribute name="basedir"><xsl:text>.</xsl:text></xsl:attribute>
           <file>
             <xsl:attribute name="name"><xsl:value-of select="$file"/></xsl:attribute>
             <xsl:attribute name="language"><xsl:value-of select="//opusDocument/@language"/></xsl:attribute>
             <xsl:attribute name="visibleInOai"><xsl:text>true</xsl:text></xsl:attribute>
             <comment>
               <xsl:text>A component of the fulltext article</xsl:text>
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
  
  <xsl:template match="/import/opusDocument/files">
    <xsl:copy>
      <xsl:copy-of select="node()|@*"/>
      <xsl:if test="string-length($file)!=0 and string-length($md5)!=0">
        <file>
          <xsl:attribute name="name"><xsl:value-of select="$file"/></xsl:attribute>
          <xsl:attribute name="language"><xsl:value-of select="//opusDocument/@language"/></xsl:attribute>
          <xsl:attribute name="visibleInOai"><xsl:text>true</xsl:text></xsl:attribute>
          <comment>
            <xsl:text>A component of the fulltext article</xsl:text>
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
'''


  # 2017-05-15 TD : xslt specific to file addition to already transformed METSDSpaceSIP.xml
  #                 Note again that, here too, there MUST NOT be any "<?xml ...>" header!
  #
  addfiles2metsdspace = '''
<xsl:stylesheet version="1.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform" xmlns:mets="http://www.loc.gov/METS/">

  <xsl:output method="xml" omit-xml-declaration="no" standalone="no" indent="yes" encoding="utf-8"/>

  <xsl:param name="file"/>
  <xsl:param name="md5"/>
  <xsl:param name="mime"><xsl:text>application/octet-stream</xsl:text></xsl:param>
  <xsl:param name="cnt"><xsl:text>1</xsl:text></xsl:param>

  <xsl:template match="node()|@*">
    <xsl:copy>
      <xsl:apply-templates select="node()|@*"/>
    </xsl:copy>
  </xsl:template>

  <xsl:template match="/mets:mets">
    <xsl:copy>
      <xsl:copy-of select="node()|@*"/>
      <xsl:if test="not(./fileSec/fileGrp) and string-length($file)!=0 and string-length($md5)!=0">
        <fileSec xmlns="http://www.loc.gov/METS/">
          <fileGrp>
             <xsl:attribute name="ID"><xsl:text>sword-mets-fgrp-1</xsl:text></xsl:attribute>
             <xsl:attribute name="USE"><xsl:text>CONTENT</xsl:text></xsl:attribute>
             <file>
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
               <FLocat xmlns:xlink="http://www.w3.org/1999/xlink">
                 <xsl:attribute name="LOCTYPE">
                   <xsl:text>URL</xsl:text>
                 </xsl:attribute>
                 <xsl:attribute name="xlink:href">
                   <xsl:value-of select="$file"/>
                 </xsl:attribute>
               </FLocat>
             </file>
          </fileGrp>
        </fileSec>
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
      </xsl:if>
    </xsl:copy>
  </xsl:template>
  
  <xsl:template match="/mets:mets/fileSec/fileGrp">
    <xsl:copy>
      <xsl:copy-of select="node()|@*"/>
      <xsl:if test="string-length($file)!=0 and string-length($md5)!=0">
        <file>
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
          <FLocat xmlns:xlink="http://www.w3.org/1999/xlink">
            <xsl:attribute name="LOCTYPE">
              <xsl:text>URL</xsl:text>
            </xsl:attribute>
            <xsl:attribute name="xlink:href">
              <xsl:value-of select="$file"/>
            </xsl:attribute>
          </FLocat>
        </file>
      </xsl:if>
    </xsl:copy>
  </xsl:template>

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

</xsl:stylesheet>
'''


  def __init__(self):
    pass

