<?xml version="1.0" encoding="utf-8"?>
<xsl:stylesheet version="1.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform">

    <!-- <xsl:import href="jats2mods.xsl"/> -->
    <xsl:output method="xml" omit-xml-declaration="no" standalone="no" indent="yes" encoding="utf-8"/>

    <xsl:param name="currdatetime">1970-01-01T00:00:00</xsl:param>

    <xsl:template match="/">
        <mets:mets xmlns:mets="http://www.loc.gov/METS/"
                   xmlns:mods="http://www.loc.gov/mods/v3"
              xmlns:xlink="http://www.w3.org/1999/xlink"
              xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
              xsi:schemaLocation="http://www.loc.gov/METS/ http://www.loc.gov/mets/mets.xsd http://www.loc.gov/mods/v3 https://www.loc.gov/standards/mods/v3/mods.xsd">
            <xsl:attribute name="ID"><xsl:text>sword-mets_mets</xsl:text></xsl:attribute>
            <xsl:attribute name="OBJID"><xsl:text>sword-mets</xsl:text></xsl:attribute>
            <xsl:attribute name="LABEL"><xsl:text>METS/MODS SWORD Item</xsl:text></xsl:attribute>
            <xsl:attribute name="PROFILE"><xsl:text>METS/MODS SIP Profile 1.0</xsl:text></xsl:attribute>
            <mets:metsHdr>
                <xsl:attribute name="CREATEDATE"><xsl:value-of select="$currdatetime"/></xsl:attribute>
                <mets:agent>
                    <xsl:attribute name="ROLE">CUSTODIAN</xsl:attribute>
                    <xsl:attribute name="TYPE">ORGANIZATION</xsl:attribute>
                    <mets:name>DeepGreen</mets:name>
                </mets:agent>
            </mets:metsHdr>
            <mets:dmdSec>
                <xsl:attribute name="ID">sword-mets-dmd-1</xsl:attribute>
                <xsl:attribute name="GROUPID">sword-mets-dmd-1_group-1</xsl:attribute>
                <mets:mdWrap>
                    <xsl:attribute name="LABEL"><xsl:text>SWAP Metadata</xsl:text></xsl:attribute>
                    <xsl:attribute name="MDTYPE">MODS</xsl:attribute>
                    <xsl:attribute name="MIMETYPE"><xsl:text>text/xml</xsl:text></xsl:attribute>
                    <mets:xmlData>
                        <xsl:apply-templates/>
                    </mets:xmlData>
                </mets:mdWrap>
            </mets:dmdSec>
        </mets:mets>
    </xsl:template>

    <!-- (Possible) mapping of affiliation(s) -->
    <xsl:key name="kAffById" match="//article-meta/aff" use="@id"/>

    
    <xsl:template match="/article">
        <mods:mods xmlns:mods="http://www.loc.gov/mods/v3"
                   xmlns:xlink="http://www.w3.org/1999/xlink"
                   xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
                   xsi:schemaLocation="http://www.loc.gov/mods/v3 https://www.loc.gov/standards/mods/v3/mods-3-6.xsd">

            <!--
                Since we are mapping JATS, we are only dealing with journal articles.
                According to a LOC example, these are attributed as follows.
                See https://www.loc.gov/standards/mods/v3/mods-userguide-examples.html#journal_article
            -->
            <mods:typeOfResource>text</mods:typeOfResource>
            <mods:genre>journal article</mods:genre>

            <!-- Language -->
            <mods:language>
                <mods:languageTerm type="code" authority="rfc3066">
                    <xsl:choose>
                        <xsl:when test="//article/@xml:lang">
                            <xsl:value-of select="//article/@xml:lang"/>
                        </xsl:when>
                        <xsl:otherwise>
                            <xsl:text>en</xsl:text>
                        </xsl:otherwise>
                    </xsl:choose>
                </mods:languageTerm>
            </mods:language>


            <!-- Title -->
            <mods:titleInfo>
                <xsl:for-each select="//article-meta/title-group/article-title">
                    <mods:title>
                        <xsl:call-template name="insert-lang-attribute"/>
                        <xsl:value-of select="."/>
                    </mods:title>
                </xsl:for-each>
                <xsl:for-each select="//article-meta/title-group/subtitle">
                    <mods:subTitle>
                        <xsl:call-template name="insert-lang-attribute"/>
                        <xsl:value-of select="."/>
                    </mods:subTitle>
                </xsl:for-each>
            </mods:titleInfo>
            <xsl:for-each select="//article-meta/title-group/trans-title-group/trans-title">
                <mods:titleInfo type="translated">
                    <mods:title>
                        <xsl:call-template name="insert-lang-attribute"/>
                        <xsl:value-of select="."/>
                    </mods:title>
                </mods:titleInfo>
            </xsl:for-each>
            <xsl:for-each select="//article-meta/title-group/trans-title-group/trans-subtitle">
                <mods:titleInfo type="translated">
                    <mods:subTitle>
                        <xsl:call-template name="insert-lang-attribute"/>
                        <xsl:value-of select="."/>
                    </mods:subTitle>
                </mods:titleInfo>
            </xsl:for-each>

            <!-- Appearance -->
            <mods:relatedItem type="host">
                <mods:titleInfo>
                    <xsl:for-each select="//journal-meta//journal-title">
                        <mods:title>
                            <xsl:call-template name="insert-lang-attribute"/>
                            <xsl:value-of select="."/>
                        </mods:title>
                    </xsl:for-each>
                </mods:titleInfo>
                <xsl:if test="//journal-meta/issn[@pub-type='ppub']">
                    <mods:identifier type="issn"><xsl:value-of select="//journal-meta/issn[@pub-type='ppub']"/></mods:identifier>
                </xsl:if>
                <xsl:if test="//journal-meta/issn[@pub-type='epub']">
                    <mods:identifier type="eIssn"><xsl:value-of select="//journal-meta/issn[@pub-type='epub']"/></mods:identifier>
                </xsl:if>
                <xsl:if test="//journal-meta/issn[@publication-format='print']">
                    <mods:identifier type="issn"><xsl:value-of select="//journal-meta/issn[@publication-format='print']"/></mods:identifier>
                </xsl:if>
                <xsl:if test="//journal-meta/issn[@publication-format='electronic']">
                    <mods:identifier type="eIssn"><xsl:value-of select="//journal-meta/issn[@publication-format='electronic']"/></mods:identifier>
                </xsl:if>
                <xsl:for-each select="//journal-meta/journal-id">
                    <mods:identifier>
                        <xsl:attribute name="type"><xsl:value-of select="@journal-id-type"/></xsl:attribute>
                        <xsl:value-of select="."/>
                    </mods:identifier>
                </xsl:for-each>
                <mods:part>
                    <xsl:if test="//article-meta/volume">
                        <mods:detail type="volume">
                            <mods:number><xsl:value-of select="//article-meta/volume"/></mods:number>
                        </mods:detail>
                    </xsl:if>
                    <xsl:if test="//article-meta/issue">
                        <mods:detail type="issue">
                            <mods:number><xsl:value-of select="//article-meta/issue"/></mods:number>
                        </mods:detail>
                    </xsl:if>
                    <xsl:if test="//article-meta/fpage">
                        <mods:extent unit="pages">
                            <mods:start><xsl:value-of select="//article-meta/fpage"/></mods:start>
                            <xsl:if test="//article-meta/lpage">
                                <mods:end><xsl:value-of select="//article-meta/lpage"/></mods:end>
                            </xsl:if>
                        </mods:extent>
                    </xsl:if>
                </mods:part>
            </mods:relatedItem>

            <!-- Creator / Contributor (Author, Editor...)-->
            <xsl:for-each select="//article-meta/contrib-group/contrib">
                <mods:name type="personal">
                    <mods:namePart type="family"><xsl:value-of select="name/surname"/></mods:namePart>
                    <xsl:if test="string-length(name/given-names/text()) > 0">
                        <mods:namePart type="given"><xsl:value-of select="name/given-names"/></mods:namePart>
                    </xsl:if>
                    <mods:role>
                        <mods:roleTerm type="text"><xsl:value-of select="@contrib-type"/></mods:roleTerm>
                    </mods:role>
		    <!-- Identifier: So far, support of ORCIDs (and email adresses?) only -->
		    <xsl:if test="contains(contrib-id/@contrib-id-type,'orcid')">
                        <mods:nameIdentifier type="orcid">
                            <xsl:copy-of select="contrib-id[@contrib-id-type='orcid']/text()"/>
                        </mods:nameIdentifier>
		    </xsl:if>
		    <!--
                    <mods:nameIdentifier type="email">
		    </mods:nameIdentifier>
                    -->
                    <!-- Affiliation: Need to deal with three different cases -->
                    <xsl:choose>
                        <xsl:when test="contains(xref/@ref-type,'aff') and string-length(xref/@rid) > 0">
                            <xsl:for-each select="xref[@ref-type='aff']">
                                <mods:affiliation>
                                    <xsl:copy-of select="key('kAffById',@rid)//text()"/>
                                </mods:affiliation>
                            </xsl:for-each> 
                        </xsl:when>
                        <xsl:when test="not(contains(xref/@ref-type,'aff')) and string-length(//article-meta/aff[position()=last()]/text()) > 0">
                            <xsl:for-each select="//article-meta/aff[not(@*)]">
                                <mods:affiliation>
                                    <xsl:copy-of select=".//text()"/>
                                </mods:affiliation>
                            </xsl:for-each>
                        </xsl:when>
                        <xsl:otherwise>
                            <xsl:if test="aff">
                                <mods:affiliation>
                                    <xsl:copy-of select="aff//text()"/>
                                </mods:affiliation>
                            </xsl:if>
                        </xsl:otherwise>
                    </xsl:choose>
                    <!--
                    <xsl:if test="aff">
                        <mods:affiliation>
                            <xsl:value-of select="aff"/>
                        </mods:affiliation>
                    </xsl:if>
                    -->
                </mods:name>
            </xsl:for-each>

            <!-- Description: Abstract / TOC -->
            <xsl:for-each select="//article-meta/abstract">
                <xsl:choose>
                    <xsl:when test="@type = 'toc'">
                        <mods:tableOfContents>
                            <xsl:call-template name="insert-lang-attribute"/>
                            <xsl:value-of select="."/>
                        </mods:tableOfContents>
                    </xsl:when>
                    <xsl:otherwise>
                        <mods:abstract>
                            <xsl:call-template name="insert-lang-attribute"/>
                            <xsl:value-of select="."/>
                        </mods:abstract>
                    </xsl:otherwise>
                </xsl:choose>
            </xsl:for-each>

            <!-- Description: Subject (Keywords) -->
            <xsl:if test="//article-meta/kwd-group/kwd">
                <mods:subject>
                    <xsl:for-each select="//article-meta/kwd-group/kwd">
                        <mods:topic><xsl:value-of select="."/></mods:topic>
                    </xsl:for-each>
                </mods:subject>
            </xsl:if>

            <!-- Publisher, Dates (in MODS under originInfo) -->
            <mods:originInfo>
                <mods:publisher><xsl:value-of select="//journal-meta/publisher/publisher-name"/></mods:publisher>
                <mods:place>
                    <mods:placeTerm type="text"><xsl:value-of select="//journal-meta/publisher/publisher-loc"/></mods:placeTerm>
                </mods:place>

                <!-- Publication date (= date available/issued) -->
                <xsl:for-each select="//article-meta/pub-date">
                    <xsl:if test="(contains(@pub-type, 'epub') and year and month) or
			    (contains(@publication-format, 'electronic') and contains(@date-type, 'pub') and year and month)">
                        <mods:dateIssued encoding="iso8601">
                            <xsl:call-template name="compose-date"></xsl:call-template>
                        </mods:dateIssued>
                    </xsl:if>
                </xsl:for-each>

                <!-- Other dates (received, accepted...) -->
                <xsl:for-each select="//article-meta/history/date">
                    <xsl:if test="year and month">
                        <mods:dateOther encoding="iso8601">
                            <xsl:attribute name="type"><xsl:value-of select="@date-type"/></xsl:attribute>
                            <xsl:call-template name="compose-date"></xsl:call-template>
                        </mods:dateOther>
                    </xsl:if>
                </xsl:for-each>
            </mods:originInfo>

            <!-- Identifiers -->
            <xsl:for-each select="//article-meta/article-id">
                <mods:identifier>
                    <xsl:attribute name="type"><xsl:value-of select="@pub-id-type"/></xsl:attribute>
                    <xsl:value-of select="."/>
                </mods:identifier>
            </xsl:for-each>

            <!-- License / Copyright -->
            <xsl:for-each select="//article-meta/permissions/license">
                <mods:accessCondition type="use and reproduction">
                    <xsl:choose>
                        <xsl:when test="@xlink:href"> 
                            <xsl:attribute name="description">uri</xsl:attribute>
                            <xsl:value-of select="@xlink:href"/>
                        </xsl:when>
                        <xsl:otherwise>
                            <xsl:value-of select="license-p"/>
                        </xsl:otherwise>
                    </xsl:choose>
                </mods:accessCondition>
            </xsl:for-each>

            <!-- Funding -->
            <xsl:for-each select="//article-meta/funding-group/award-group/funding-source">
                <mods:note type="funding">
                    <xsl:value-of select="."/>
                </mods:note>
            </xsl:for-each>

        </mods:mods>
    </xsl:template>

    <xsl:template name="compose-date">
        <xsl:value-of select="year"/>
        <xsl:text>-</xsl:text>
        <xsl:value-of select="format-number(month,'00')"/>
        <xsl:if test="day">
            <xsl:text>-</xsl:text>
            <xsl:value-of select="format-number(day,'00')"/>
        </xsl:if>
    </xsl:template>

    <xsl:template name="insert-lang-attribute">
        <xsl:if test="@xml:lang">
            <xsl:attribute name="xml:lang"><xsl:value-of select="@xml:lang"/></xsl:attribute>
        </xsl:if>
    </xsl:template>


</xsl:stylesheet>
