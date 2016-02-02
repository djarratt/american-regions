# Traverse the input file line-by-line, determine if the statistic describes
# county-to-county migration, and write out if so.

import csv

headerRow = "fromCountyFIPSid,toCountyFIPSid,countTaxReturns," + \
            "countTaxExemptions,sumAdjustedGrossIncome1000s"
print(headerRow)

with open('government/countyoutflow1213.csv') as csvfile:
    reader = csv.DictReader(csvfile)
    for row in reader:
        fromStateFIPSid = row['y1_statefips']
        toStateFIPSid = row['y2_statefips']
        fromCountyFIPSid = row['y1_countyfips']
        toCountyFIPSid = row['y2_countyfips']

        # restrict to just the US states, not territories or non-US places;
        # restrict to county-to-county information, not county aggregates
        if int(fromStateFIPSid) <= 56 and int(toStateFIPSid) <= 56 and \
           int(fromCountyFIPSid) > 0 and int(toCountyFIPSid) > 0:

            fromFullCountyFIPSid = fromStateFIPSid + fromCountyFIPSid
            toFullCountyFIPSid = toStateFIPSid + toCountyFIPSid

            if fromFullCountyFIPSid != toFullCountyFIPSid:
                countTaxReturns = row['n1']
                countTaxExemptions = row['n2']
                countDollars = row['agi']

                # omit rows with suppressed counts (-1)
                # don't omit rows with suppressed AGI but set to blank
                if countDollars == "-1":
                    countDollars = ""
                if countTaxReturns != "-1" and countTaxExemptions != "-1":
                    print("{0},{1},{2},{3},{4}".format(fromStateFIPSid +
                          fromCountyFIPSid, toStateFIPSid + toCountyFIPSid,
                          countTaxReturns, countTaxExemptions, countDollars))
