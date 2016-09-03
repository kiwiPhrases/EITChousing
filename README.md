# EITChousing
Were EITC credits extended to help with housing for low-income families, what would be the cost?

#### EITC Housing Benefits
In this notebook, we try to estimate the cost of a hypothetical EITC program to aid with rental housing payments. The aim is to supply a family with enough EITC to have them pay no more than 30% of their income for housing. Namely, the algorithm we implement is as follows:

Let $y_i$ denote the income of family $i$. Furthermore, suppose that family $i$ has characteristics married $s \in \{0,1\}$ and children $c \in \{0,\dots, 3\}$. Suppose $y_i$ is such that it qualifies family $i$ for $e_i = e(y_i,s,c)$ amount of EITC benefits. Finally, suppose that family $i$ lives in location $l$ and pays rent $r$ for a $b\in \{0,\dots,4\}$ bedroom housing unit. Then, under our scheme, family $i$ will recieve additional EITC housing benefits $h$ of:

$$h = max(r_{l,b} - .3(y_i+e_i), 0 )$$

#### Data
We have 3 datasets containing the following information:

1. Number of EITC recipients in 356 metros per income bracket. 
2. Number of EITC recipients in 356 metros per number of children.
3. Amount of EITC benefits one recieves for various income levels and family characteristics (ie marriage and number of childre)
4. The FMRs in 356 metros per number of bedrooms of the housing unit.

#### Assumptions
1. Two datasets, taxes and FMRs, are merged based on their CDSA codes but not all of the codes match. Namely, the tax data contains 381 metros but only 351 of them match to the FMR data. We are able to match an additional 5 CDSA codes for a total of 356 metros. However, there is no guarantee that the additional 5 metros match precisely with the metro of the Brookings data. For example, the FMR data contain a CDSA as 'Santa Barbara-Santa Maria-Goleta' while the tax has CDSA 'Santa Maria-Santa Barbara'. clearly, the FMR area is larger but in adding the 5 metros, we disregard this discrepancy. 

2. We have a distribution of files incomes in each metro area. The distributions are binned in increments of \$5k up to \$40k and then are binned at \$10k increments. Since we only have the number of people who filed within each bin, we assume a uniform distribution of incomes in each bin and use the bin mean as the representative income for that bin. However, the highest income for which EITC benefits are given is \$52400k but we must rely on \$55k. The latter will overestimate the income and number of EITC recipients in that bin. One proposal to mediate that is to divide the bin \$50-\$60k in half and to use \$52500 as the median and half the number of \$50-\$60k as the filers.

3. We do not have any figures on marriage but need to differentiate between married and unmarried families. Consequently, we employ *1-50.2% -*figure from some Christian Science article*- as the proportion of adults married. In doing so, we must assume that marriage rates across the income distribution, number of children, and metros do not vary. 

4. Both FMR and EITC data are for year 2014 whereas the tax data is for year 2013. Thus, we assume that FMRs and EITC benefits do not differ drastically between 2013 and 2014. 

5. We only have numbers aggregated based on children and based on income bins but not across both; therefore, to estimate the proportion of families with each child type in each income bin, we assume that the number of children a family has does not vary across the income distributions. 

6. Consider the following variables: 

  * the number $n_{c,l}$ of EITC eligible families in metro $l$ and with number of children $c\in \{0,1,2,3+\}$
  * the number $m_{b,l}$ of EITC filers in each metro $l$ and income bin $b \in \{1,2,\dots, 10\}$

  The tax data contains two sets of numbers data: 1) the number $n_l = \sum_{c} n_{c,l}$ of EITC eligible people in each metro for each family type 2) the number $m_l = \sum_{b} m_{b,l}$ of families who filed for EITC in each income bracket. Note $n_l \geq m_l \quad \forall l$. To acquire the number of family types in each income bracket, we calculate

  $$p_{l,c} = \frac{n_{l,c}}{n_{l}}$$

  then compute 

  $$k_{c,l,b} = p_{l,c} \times m_{b,l}$$

  Where $k_{c,l,b}$ is the number of families with children $c$ and in income bin $b$ in metro $l$. Of course, for this we must assume that the proportions among the eligible hold equally among those who actually file. Finally, let $T(p_{l,c})$ be the total cost calculated using eligible counts and let $T(p_{l,b})$ be that total cost calculated using bin proportions then 
$$T(p_{l,c}) \geq T(p_{l,b})$$
