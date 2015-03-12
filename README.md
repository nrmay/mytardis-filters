# MyTardis-Filters
Project for developing standardized deployments of filters for MyTardis

| Branch | Purpose |
| ------ | ------- |
| Master | Features common to all filters | 
| Develop | Development of common features |
| *Filter Name* | Development of features for a named filter |

To add a new filter:
* create a branch from the current master.
* give the branch a name that represents the filter.

# Current Branches

## samformat

Extracts meta-data from files gene sequencers that have been saved in the 
SAM/BAM format 
--- as described in the following document:

*Title: 		"Sequence Alignment/Map Format Specification" 
*Date:  		18 October 2013
*Version: 	6f8dfe4
*Source:   	[hts-specs github](http://github.com/samtools/hts-specs)

## fcsformat

Extracts meta-data from Flow Cytometry data files 
--- as described in the following document:

*Title: 		"Data File Standard for Flow Cytometry" 
*Date:  		2009
*Version: 	FCS 3.1
*Publisher:   International Society for Advancement of Cytometry
*Source:      [Specification document](http://isac-net.org/getdoc/9cbeb83d-99e4-41ac-b68c-c9ab97b180c6/fcs3-1_normativespecification_20090813.aspx)
