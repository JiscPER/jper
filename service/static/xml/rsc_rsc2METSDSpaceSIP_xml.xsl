<?xml version="1.0" encoding="utf-8"?>
<xsl:stylesheet version="1.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform">

  <!-- <xsl:import href="outputTokens.xsl"/> -->
  <xsl:output method="xml" omit-xml-declaration="no" standalone="no" indent="yes" encoding="utf-8"/>

  <xsl:param name="currdatetime">1970-01-01T00:00:00</xsl:param>

  <!-- mapping names of month -->
  <xsl:variable name="monthNames" select="document('monthNameMap.xml')/monthNameMap/monthName"/>

  <xsl:variable name="langCodes" select="document('langCodeMap.xml')/langCodeMap/langCode"/>
  <xsl:variable name="langIn" select="translate(/article/@xml:lang,'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz')"/>
  <!-- <xsl:variable name="langOut">eng</xsl:variable> -->
  <xsl:variable name="langOut" select="$langCodes[@iso639-1=$langIn]/@iso639-2"/>

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
        <name>DeepGreen</name>
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
                      <xsl:value-of select="//published[@type='web']/pubfront/date/year"/>
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
                    <xsl:when test="//published[@type='web']/pubfront/date/year">
                      <xsl:call-template name="compose-date">
                        <xsl:with-param name="xpub" select="'web'"/>
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
              <xsl:if test="//published[@type='print']/journalref/coden">
                <xsl:for-each select="//published[@type='print']/journalref/coden">
                  <epdcx:statement>
                    <xsl:attribute name="epdcx:propertyURI">http://purl.org/dc/terms/source</xsl:attribute>
                    <epdcx:valueString>
                      <xsl:text>CODEN:</xsl:text>
                      <xsl:value-of select="normalize-space(text())"/>
                    </epdcx:valueString>
                  </epdcx:statement>
                </xsl:for-each>
              </xsl:if>
              <epdcx:statement>
                <xsl:attribute name="epdcx:propertyURI">http://purl.org/dc/terms/publisher</xsl:attribute>
                <epdcx:valueString>
                  <xsl:for-each select="//published[@type='print']/journalref/publisher/orgname/nameelt">
                    <xsl:value-of select="normalize-space(text())"/>
                    <xsl:if test="position() != last()">
                      <xsl:text>, </xsl:text>
                    </xsl:if>
                  </xsl:for-each>
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
    <xsl:param name="xpub" select="'web'"/>
    <xsl:for-each select="//published[@type=$xpub]/pubfront/date">
      <xsl:if test="position() = last()">
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
        <xsl:if test="format-number(day,'00')!='NaN'">
          <xsl:text>-</xsl:text>
          <xsl:value-of select="format-number(day,'00')"/>
        </xsl:if>
      </xsl:if>
    </xsl:for-each>
  </xsl:template>

</xsl:stylesheet>
