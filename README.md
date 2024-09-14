# Name matching for company
This is a forked repository from:
[![name_matching](https://github.com/DeNederlandscheBank/name_matching/actions/workflows/python-app.yml/badge.svg?branch=main)](https://github.com/DeNederlandscheBank/name_matching/actions/workflows/python-app.yml)

This is a package that use to match company names in your database. You should be providing:

        - a database that has all company names, including its aliases if possible.
        - a search string that use to match the user input
        


## Installation for this package
```bash
pip install git+https://github.com/DanielCGL/name_matching_for_company.git
```

## Pre-Run

Before running the usage code, user should have a jsonl file that contains the following information:

        - requiredSearchStrings for the string matches with the user_input and,
        - the correspond companyName for output
        
For Example:
```bash
{"requiredSearchStrings":["apples","apple","苹果","itunes"],"aliases":["iTunes","Apple's","Apple","苹果公司"],"companyName":"Apple Inc."}
```


## Usage
See Usage.py


## Contributing
All contributions are welcome. For more substantial changes, please open an issue first to discuss what you would like to change.


## License
The code is licensed under the MIT/X license an extended version of the licence: [MIT](https://choosealicense.com/licenses/mit/)


## Thanks
Thanks to the work of implementing name matching algorithms done in the [Abydos package](https://github.com/chrislit/abydos),the base of this program [name-matching](https://github.com/DeNederlandscheBank/name_matching). These form the basis algorithms used in this package and usage.
