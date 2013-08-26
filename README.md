# Tanzania budget scrapers

NB currently only works with the development budget, but recurrent budgets are 
formatted in a similar way so wouldn't be too much more work to make it work 
with them.

1. Install dependencies:

        virtualenv ./pyenv
        source ./pyenv/bin/activate
        pip install -r requirements.txt

2. Get the data:

        cd pdf
        wget "http://www.mof.go.tz/mofdocs/budget/Budget%20Books/2013_2014/VOLUME%20IV%20PUBLIC%20EXPENDITURE%20ESTIMATES-%20DEVELOPMENT%20AS%20SUBMITTED%20TO%20THE%20NATIONAL%20ASSEMBLY%202013-2014.pdf" -O development.pdf
        wget "http://www.mof.go.tz/mofdocs/budget/Budget%20Books/2013_2014/VOLUME%20II%20PUBLIC%20EXPENDITURE%20ESTIMATES%20SUPPLY%20VOTES%20(MINISTERIAL)%20AS%20SUBMITTED%20TO%20THE%20NATIONAL%20ASSEMBLY%202013-2014.pdf" -O recurrent.pdf
        wget "http://www.mof.go.tz/mofdocs/budget/Budget%20Books/2013_2014/VOLUME%20III%20PUBLIC%20EXPENDITURE%20ESTIMATES%20SUPPLY%20VOTES%20(REGIONS)%20AS%20SUBMITTED%20TO%20THE%20NATIONAL%20ASSEMBLY%202013-2014.pdf" -O recurrent-regions.pdf

3. Run the scraper:

        ./scrape.py
