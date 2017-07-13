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
            <xsl:attribute name="ID"><xsl:text>sort-mets_mets</xsl:text></xsl:attribute>
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


    <xsl:variable name="monthNames" select="document('monthNameMap.xml')/monthNameMap/monthName"/>


    <xsl:template match="/article">
        <mods:mods xmlns:mods="http://www.loc.gov/mods/v3"
                   xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
                   xsi:schemaLocation="http://www.loc.gov/mods/v3 https://www.loc.gov/standards/mods/v3/mods-3-6.xsd">

            <!--
                Since we are mapping RSC, we are only dealing with journal articles.
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
                <xsl:for-each select="//art-front/titlegrp/title">
                    <mods:title>
                        <xsl:call-template name="insert-lang-attribute"/>
                        <xsl:value-of select="."/>
                    </mods:title>
                </xsl:for-each>
                <xsl:for-each select="//art-front/titlegrp/subtitle">
                    <mods:subTitle>
                        <xsl:call-template name="insert-lang-attribute"/>
                        <xsl:value-of select="."/>
                    </mods:subTitle>
                </xsl:for-each>
            </mods:titleInfo>
            <!-- Seems not to be provided by RSC
            <xsl:for-each select="//art-front/titlegrp/trans-titlegrp/trans-title">
                <mods:titleInfo type="translated">
                    <mods:title>
                        <xsl:call-template name="insert-lang-attribute"/>
                        <xsl:value-of select="."/>
                    </mods:title>
                </mods:titleInfo>
            </xsl:for-each>
            <xsl:for-each select="//art-front/titlegrp/trans-titlegrp/trans-subtitle">
                <mods:titleInfo type="translated">
                    <mods:subTitle>
                        <xsl:call-template name="insert-lang-attribute"/>
                        <xsl:value-of select="."/>
                    </mods:subTitle>
                </mods:titleInfo>
            </xsl:for-each>
            -->

            <!-- Appearance -->
            <mods:relatedItem type="host">
                <mods:titleInfo>
                    <xsl:for-each select="//published[@type='print']/journalref/title[@type='full']">
                        <mods:title>
                            <xsl:call-template name="insert-lang-attribute"/>
                            <xsl:value-of select="."/>
                        </mods:title>
                    </xsl:for-each>
                </mods:titleInfo>
                <xsl:if test="//published[@type='print']/journalref/issn[@type='print']">
                    <mods:identifier type="issn"><xsl:value-of select="//published[@type='print']/journalref/issn[@type='print']"/></mods:identifier>
                </xsl:if>
                <xsl:if test="//published[@type='print']/journalref/issn[@type='online']">
                    <mods:identifier type="eIssn"><xsl:value-of select="//published[@type='print']/journalref/issn[@type='online']"/></mods:identifier>
                </xsl:if>
                <xsl:if test="//published[@type='print']/journalref/title[@type='abbreviated']">
                    <mods:identifier type="abbreviated">
                       <xsl:value-of select="//published[@type='print']/journalref/title[@type='abbreviated']"/>
                    </mods:identifier>
                </xsl:if>
                <xsl:for-each select="//published[@type='print']/journalref/sercode">
                    <mods:identifier type="sercode"><xsl:value-of select="."/></mods:identifier>
                </xsl:for-each>
                <xsl:for-each select="//published[@type='print']/journalref/coden">
                    <mods:identifier type="coden"><xsl:value-of select="."/></mods:identifier>
                </xsl:for-each>
                <mods:part>
                    <xsl:if test="string-length(//published[@type='print']/volumeref/link/text()) > 0">
                        <mods:detail type="volume">
                            <mods:number><xsl:value-of select="//published[@type='print']/volumeref/link"/></mods:number>
                        </mods:detail>
                    </xsl:if>
                    <xsl:if test="string-length(//published[@type='print']/issueref/link/text()) > 0">
                        <mods:detail type="issue">
                            <mods:number><xsl:value-of select="//published[@type='print']/issueref/link"/></mods:number>
                        </mods:detail>
                    </xsl:if>
                    <xsl:if test="string-length(//published[@type='print']/pubfront/fpage/text()) > 0">
                        <mods:extent unit="pages">
                            <mods:start><xsl:value-of select="//published[@type='print']/pubfront/fpage"/></mods:start>
                            <xsl:if test="string-length(//published[@type='print']/pubfront/lpage/text()) > 0">
                                <mods:end><xsl:value-of select="//published[@type='print']/pubfront/lpage"/></mods:end>
                            </xsl:if>
                        </mods:extent>
                    </xsl:if>
                </mods:part>
            </mods:relatedItem>

            <!-- Creator / Contributor (Author, Editor...)-->
            <xsl:for-each select="//art-front/authgrp/author">
                <mods:name type="personal">
                    <mods:namePart type="family"><xsl:copy-of select="person/persname/surname/text()"/></mods:namePart>
                    <xsl:if test="string-length(person/persname/fname/text()) > 0">
                        <mods:namePart type="given"><xsl:copy-of select="person/persname/fname/text()"/></mods:namePart>
                    </xsl:if>
                    <mods:role>
                        <mods:roleTerm type="text"><xsl:text>author</xsl:text></mods:roleTerm>
                    </mods:role>
                    <!-- Affiliation -->
                    <xsl:if test="string-length(./@aff) > 0">
                        <xsl:variable name="affs" select="@aff"/>
                        <xsl:for-each select="//art-front/authgrp/aff[contains($affs,@id)]">
                            <mods:affiliation>
                                <xsl:for-each select="org/orgname/nameelt">
                                    <xsl:value-of select="normalize-space(text())"/>
                                    <xsl:if test="position() != last()">
                                        <xsl:text>, </xsl:text>
                                    </xsl:if>
                                 </xsl:for-each>
                            </mods:affiliation>
                        </xsl:for-each>
                    </xsl:if>
                </mods:name>
            </xsl:for-each>

            <!-- Description: Abstract / TOC -->
            <xsl:for-each select="//art-front/abstract">
                <!-- TOC is not available within RSC
                    <xsl:when test="@type = 'toc'">
                        <mods:tableOfContents>
                            <xsl:call-template name="insert-lang-attribute"/>
                            <xsl:value-of select="."/>
                        </mods:tableOfContents>
                    </xsl:when>
                -->
                <mods:abstract>
                    <xsl:call-template name="insert-lang-attribute"/>
                    <xsl:value-of select="."/>
                </mods:abstract>
            </xsl:for-each>

            <!-- Description: Subject (Keywords) -->
            <!-- Keywords are not provided by RSC
            <xsl:if test="//article-meta/kwd-group/kwd">
                <mods:subject>
                    <xsl:for-each select="//article-meta/kwd-group/kwd">
                        <mods:topic><xsl:value-of select="."/></mods:topic>
                    </xsl:for-each>
                </mods:subject>
            </xsl:if>
            -->

            <!-- Publisher, Dates (in MODS under originInfo) -->
            <mods:originInfo>
                <mods:publisher>
                    <xsl:for-each select="//published[@type='print']/journalref/publisher/orgname/nameelt">
                        <xsl:value-of select="normalize-space(text())"/>
                        <xsl:if test="position() != last()">
                            <xsl:text>, </xsl:text>
                        </xsl:if>
                    </xsl:for-each>
                </mods:publisher>
                <!-- Place of publishing is not provided by RSC
                <mods:place>
                    <mods:placeTerm type="text"><xsl:value-of select="//journal-meta/publisher/publisher-loc"/></mods:placeTerm>
                </mods:place>
                -->

                <!-- Publication date (= date available/issued) -->
                <xsl:for-each select="//published[@type='web']/pubfront/date">
                    <xsl:if test="year and month">
                        <mods:dateIssued encoding="iso8601">
                            <xsl:call-template name="compose-date"></xsl:call-template>
                        </mods:dateIssued>
                    </xsl:if>
                </xsl:for-each>

                <!-- Other dates (received, accepted...) -->
                <xsl:for-each select="//art-admin/received/date">
                    <xsl:if test="year and month">
                        <mods:dateOther encoding="iso8601" type="received">
                            <xsl:call-template name="compose-date"></xsl:call-template>
                        </mods:dateOther>
                    </xsl:if>
                </xsl:for-each>
                <xsl:for-each select="//art-admin/date">
                    <xsl:if test="year and month">
                        <mods:dateOther encoding="iso8601">
                            <xsl:attribute name="type"><xsl:value-of select="@role"/></xsl:attribute>
                            <xsl:call-template name="compose-date"></xsl:call-template>
                        </mods:dateOther>
                    </xsl:if>
                </xsl:for-each>
            </mods:originInfo>

            <!-- Identifiers -->
            <xsl:for-each select="//art-admin/doi">
                <mods:identifier type="doi">
                    <xsl:value-of select="."/>
                </mods:identifier>
            </xsl:for-each>
            <xsl:for-each select="//art-admin/ms-id">
                <mods:identifier type="ms-id">
                    <xsl:value-of select="."/>
                </mods:identifier>
            </xsl:for-each>

            <!-- License / Copyright -->
            <xsl:for-each select="//published[@type='web']/journalref/cpyrt">
                <mods:accessCondition type="use and reproduction">
                    <xsl:value-of select="."/>
                </mods:accessCondition>
            </xsl:for-each>

            <!-- Funding -->
            <!-- Funding source is not included by RSC
            <xsl:for-each select="//article-meta/funding-group/award-group/funding-source">
                <mods:note type="funding">
                    <xsl:value-of select="."/>
                </mods:note>
            </xsl:for-each>
            -->

        </mods:mods>

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
        <xsl:if test="format-number(day,'00')!='NaN'">
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
