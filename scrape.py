#!/usr/bin/env python

from pdfminer.pdfparser import PDFParser, PDFDocument, PDFNoOutlines, PDFSyntaxError
from pdfminer.pdfinterp import PDFResourceManager, PDFPageInterpreter
from pdfminer.converter import PDFPageAggregator
from pdfminer.layout import \
  LAParams, LTTextBox, LTTextLine, LTFigure, LTImage, LTTextLineHorizontal, \
  LTTextBoxHorizontal, LTChar, LTRect, LTLine, LTAnon
from binascii import b2a_hex
from operator import itemgetter
import re
import unicodecsv
import copy

def clean(text):
    nicetext = re.sub("\n", "", text).strip()
    try:
        return str(int(re.sub(",", "", nicetext)))
    except ValueError:
        return nicetext

def parseCoverPage(pageno, layout):
    for no, row in enumerate(layout):
        if no == 0:
            vote_code = clean(row.get_text()).split("VOTE ")[1]
        if no == 1:
            vote_name = clean(row.get_text())
        if no == 2:
            page_no = clean(row.get_text())
    print "Vote code", vote_code
    print "Vote name", vote_name
    print "Page", page_no
    default_pagedata = {'vote_code': vote_code,
                        'vote_name': vote_name}
    return default_pagedata

header_names = ['amount', 'year', 'spending_type', 'spending_source', 'gl', 
    'crd', 'donor', 'sub_vote_name', 'sub_vote_code', 'programme_name', 
    'programme_code', 'page', 'vote_name', 'vote_code', 'source']

col_names = ['2011_actual_local', '2011_actual_forex', '2012_approved_local',
    '2012_approved_forex', '2013_estimates_local', '2013_estimates_forex',  'total','gl', 
    'crd', 'donor', 'sub_vote_name', 'sub_vote_code', 'programme_name', 
    'programme_code', 'page', 'vote_name', 'vote_code', 'source']

amount_cols = {'2011_actual_local': {
                'year': '2011',
                'spending_type': 'actual',
                'spending_source': 'local',
                }, 
                '2011_actual_forex': {
                'year': '2011',
                'spending_type': 'actual',
                'spending_source': 'forex',
                }, 
                '2012_approved_local': {
                'year': '2012',
                'spending_type': 'approved',
                'spending_source': 'local',
                },
                '2012_approved_forex': {
                'year': '2012',
                'spending_type': 'approved',
                'spending_source': 'forex',
                }, 
                '2013_estimates_local': {
                'year': '2013',
                'spending_type': 'estimates',
                'spending_source': 'local',
                }, 
                '2013_estimates_forex': {
                'year': '2013',
                'spending_type': 'estimates',
                'spending_source': 'forex',
                }
            }

def parseDataPage(pageno, layout, csvfile, default_pagedata):
    out = []
    pagedata = {}
    values = {}

    id = 0
    numrows = len(layout)
    # 15 header rows
    # 

    objstack = list(layout._objs)
    if objstack[0].get_text().startswith('A. ESTIMATE'):
        print "Data front page"
    else:
        print "Not data front page"
    if default_pagedata is not None:
        print "Setting default_pagedata", pagedata
        pagedata = default_pagedata

    print "Total values:", len(objstack) 

    for no, x in enumerate(objstack):
        if not hasattr(x, 'get_text'):
            continue

        thex = (x.x0+x.x1)/2
        they = (x.y0+x.y1)/2
        if not they in values:
            values[they] = []
        values[they].append((x.x0, x.get_text()))

    values = list(reversed(sorted(values.items())))

    pagedata['page'] = clean(values[-1][1][0][1])
    for datanum, (y, data) in enumerate(values):
        data = sorted(data)
        originaldata=copy.copy(data)
        usethisrow = False

        # If it's not the page number
        if str(y) != "53.228":

            # Get sub vote, programme data
            if str(data[0][0]) == str(119.0):
                pagedata.update({'sub_vote_code': pagedata['vote_code'] + "-" + clean(data[0][1])})
                pagedata.update({'sub_vote_name': clean(data[1][1])})
            elif str(data[0][0]) == str(81.4):
                pagedata.update({'programme_code': clean(data[0][1])})
            elif str(data[0][0]) == str(123.75):
                pagedata.update({'programme_name': clean(data[0][1])})

            if len(data)==10:
                # Sometimes the vote code gets put to the end
                if len(clean(data[9][1])) == 4:

                    vote_code = data[9]
                    data.pop(9)
                    data.reverse()
                    data.append(vote_code)
                    data.reverse()

                # Sometimes D and donor name are in the same cell
                try:
                    donorname = (data[8][0], clean(data[8][1]).split("D ")[1])
                    data.append(data[9])
                    data[9] = donorname
                    data[8] = (data[8][0], u"D")
                except IndexError:
                    print "Can't parse", data[8][1]
                    # Assume this is because there is no problem with this cell,
                    # but programme code and name are on the following 2 lines

                    print "This row is", data
                    print "Next row is", values[datanum+1]
                    print "Following row is", values[datanum+2]
                    data.reverse()
                    data.append(values[datanum+2][1][0]) # prog name
                    data.append(values[datanum+1][1][0]) # prog code
                    data.reverse()

            if len(data)==12:
                usethisrow = True
                pagedata['programme_name'] = clean(data[1][1])
                data.pop(1)
            if len(data) == 11:
                pagedata['programme_code'] = clean(data[0][1])

                if clean(data[7][1]) == 'G': 
                    pagedata['gl'] = 'Grant'
                elif clean(data[7][1]) == 'L':
                    pagedata['gl'] = 'Loan'
                else:
                    pagedata['gl'] = ""

                pagedata['crd'] = clean(data[8][1])
                pagedata['donor'] = clean(data[9][1])
                data.pop(9)
                data.pop(8)
                data.pop(7)
                data.pop(0)
            elif len(data)==9:
                try:
                    int(re.sub(",", "", clean(data[1][1])))
                except ValueError:
                    # Not a number, so likely to be a programme name
                    usethisrow = True
                    pagedata.update({'programme_name': clean(data[1][1])})
                    pagedata.update({'programme_code': clean(data[0][1])})
                    data.pop(1)
                    data.pop(0)
            else:
                pagedata['gl'] = ""
                pagedata['crd'] = ""
                pagedata['donor'] = ""
                pagedata['programme_code'] = clean(data[0][1])
                data.pop(0)

            if len(data)==8:

                pagedata['programme_code'] = clean(data[7][1])
                data.pop(7)

            if len(data)==7:
                if not usethisrow:
                    nrpn = clean(values[datanum+1][1][0][1])
                    if ((nrpn == "Total of Subvote") and not usethisrow):
                        continue
                    if ((nrpn == "Total of Vote") and not usethisrow):
                        continue
                    else:
                        pagedata['programme_name'] = nrpn
                for num, name in enumerate(col_names):
                    try:
                        pagedata[name] = clean(data[num][1])
                    except Exception:
                        pass
                out.append(copy.copy(pagedata))

    if not out:
        return out, None

    default_pagedata = {}
    default_pagedata['programme_name'] = pagedata['programme_name']
    default_pagedata['programme_code'] = pagedata['programme_code']
    default_pagedata['sub_vote_name'] = pagedata['sub_vote_name']
    default_pagedata['sub_vote_code'] = pagedata['sub_vote_code']
    default_pagedata['vote_name'] = pagedata['vote_name']
    default_pagedata['vote_code'] = pagedata['vote_code']
    return out, default_pagedata

def ParsePage(pageno, layout, csvfile, default_pagedata, source):
    out = []
    if len(layout) == 3:
        print "Cover page"
        default_pagedata = parseCoverPage(pageno, layout)
        out = []
    else:
        print "Data page"
        out, default_pagedata = parseDataPage(pageno, layout, csvfile, default_pagedata)
        if not out:
            return
        for row in out:
            row['source'] = source
            amount_data = {}
            for a, vals in amount_cols.items():
                amount_data[a] = row[a]
                del row[a]
            del row['total']
            for a, vals in amount_cols.items():
                row['amount'] = amount_data[a]
                row['year'] = vals['year']
                row['spending_source'] = vals['spending_source']
                row['spending_type'] = vals['spending_type']
                csvfile.writerow(row)

    return default_pagedata


def run():
    the_file = open('data.csv', 'w')
    csvfile = unicodecsv.DictWriter(the_file, header_names)
    csvfile.writerow(dict([(k, k) for k in header_names]))
    sources = ['development']

    for source in sources:
        cin = open("pdf/"+source+".pdf")

        parser = PDFParser(cin)
        doc = PDFDocument()
        parser.set_document(doc)
        doc.set_parser(parser)

        doc.initialize("")
        rsrcmgr = PDFResourceManager()
        laparams = LAParams()
        device = PDFPageAggregator(rsrcmgr, laparams=laparams)
        interpreter = PDFPageInterpreter(rsrcmgr, device)

        default_pagedata = None
        for n, page in enumerate(doc.get_pages()):
            interpreter.process_page(page)
            layout = device.get_result()

            default_pagedata = ParsePage(n, layout, csvfile, default_pagedata, source)
            print ""

run()
