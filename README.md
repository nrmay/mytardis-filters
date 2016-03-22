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
 
To install a filter into a MyTardis instance:
* clone the filter branch into the folder: tardis/tardis_portal/filter/*Filter Name*/
* follow the instructions in the README.md file in that folder.

# This Branch

## fcsformat

Extracts meta-data from Flow Cytometry data files 
--- as described in the following document:

* Title: 	   "Data File Standard for Flow Cytometry" 
* Date:  	   2009
* Version: 	   FCS 3.1
* Publisher:   International Society for Advancement of Cytometry
* Source:      [Specification document](http://isac-net.org/getdoc/9cbeb83d-99e4-41ac-b68c-c9ab97b180c6/fcs3-1_normativespecification_20090813.aspx)
* Requires:    flowcytometrytools 
  
  ```bash
  pip install git+http://bitbucket.org/nrmay/flowcytometrytools.git
  ```
* Packages:    
  * CentOS:
  
  ```bash
  yum install -y blas-devel lapach-devel atlas-devel freetype freetype-devel libpng-devel 
  ```
  * Ubuntu: 
  
  ```bash
  apt-get install -y python-numpy python-scipy python-matplotlib ipython ipython-notebook python-pandas python-sympy python-nose libblas-dev liblapack-dev libatlas-base-dev libatlas-dev libfreetype6 libfreetype6-dev  libpng-dev
  ```
    * If installation fails the first time, execute the following:
    
    ```bash
    add-apt-repository universe 
    apt-get update
    ```

Add the following definition to the POST_SAVE_FILTERS:

```python 
POST_SAVE_FILTERS = [
   ("tardis.tardis_portal.filters.fcsformat.template.make_filter",
      ["fcsformat", "http://mytardis.org/fcsformat/"]),
]
```
