<?xml version="1.0" encoding="utf-8"?>
<xsl:stylesheet version="1.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform">

  <!-- <xsl:import href="outputTokens.xsl"/> -->
  <xsl:output method="xml" omit-xml-declaration="no" standalone="no" indent="yes" encoding="utf-8"/>

  <xsl:param name="currdatetime">1970-01-01T00:00:00</xsl:param>

  <xsl:variable name="langCodes" select="document('langCodeMap.xml')/langCodeMap/langCode"/>
  <xsl:variable name="langIn" select="translate(/article/@xml:lang,'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz')"/>
  <!-- <xsl:variable name="langOut">eng</xsl:variable> -->
  <xsl:variable name="langOut" select="$langCodes[@iso639-1=$langIn]/@iso639-2"/>

  <xsl:template match="/">
  <mets xmlns="http://www.loc.gov/METS/"
    xmlns:xlink="http://www.w3.org/1999/xlink"
    xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
    xsi:schemaLocation="http://www.loc.gov/METS/ http://www.loc.gov/standards/mets/mets.xsd">
    <xsl:attribute name="ID"><xsl:text>sword-mets_mets</xsl:text></xsl:attribute>
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
                  <xsl:text>https://dx.doi.org/</xsl:text>
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
                    <xsl:when test="//article-meta/pub-date[contains(@pub-type,'epub')]/year">
                      <xsl:value-of select="//article-meta/pub-date[contains(@pub-type,'epub')]/year"/>
                    </xsl:when>
                    <xsl:when test="//article-meta/pub-date[contains(@publication-format,'electronic') and contains(@date-type,'pub')]/year">
                      <xsl:value-of select="//article-meta/pub-date[contains(@publication-format,'electronic') and contains(@date-type,'pub')]/year"/>
                    </xsl:when>
                    <xsl:otherwise>
                      <xsl:value-of select="//article-meta/pub-date[contains(@date-type,'pub')]/year"/>
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
                </epdcx:valueString>
              </epdcx:statement>
              <xsl:for-each select="//journal-meta//journal-title">
                <epdcx:statement>
                  <xsl:attribute name="epdcx:propertyURI">http://purl.org/dc/terms/source</xsl:attribute>
                  <epdcx:valueString>
                    <xsl:value-of select="normalize-space(text())"/>
                  </epdcx:valueString>
                </epdcx:statement>
              </xsl:for-each>
              <xsl:for-each select="//journal-meta/issn[@pub-type='ppub' or @publication-format='print']">
                <epdcx:statement>
                  <xsl:attribute name="epdcx:propertyURI">http://purl.org/dc/terms/source</xsl:attribute>
                  <epdcx:valueString>
                    <xsl:text>pISSN:</xsl:text>
                    <xsl:value-of select="normalize-space(text())"/>
                  </epdcx:valueString>
                </epdcx:statement>
              </xsl:for-each>
              <xsl:for-each select="//journal-meta/issn[@pub-type='epub' or @publication-format='electronic']">
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
