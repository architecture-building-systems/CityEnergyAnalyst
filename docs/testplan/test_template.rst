:script: template
:version: 2.8
:commit-id: (git commit id tested)
:tester: daren-thomas

- does the ArcGIS interface include the script?

  - if not, why not?

- are all the parameters listed relevant to the script?
- does the CLI interface work? (run ``cea <scriptname>``)
- list of parameter studies

  - hint: enter non-sensical values into the parameters (what happens?)
  - hint: enter values that are wrong, but accepted by the interface (what happens?)
  - try to vary all of the parameters, individually and in combination

    - ask the original author of a script for edge cases to consider
    - document the results of running the edge cases

- does the CEA launcher interface work?

  - can the parameter studies be performed with this interface?

- does the GH interface work for this script?
- is the script name adequate? should it be renamed?
- is the script described in the documentation?
- is the main script document documented properly? (we could auto-generate script documentation based on the docstrings)
- does the script main file have the correct credits?
- is each parameter documented in the interface

  - spell check
  - integrity check
  - appropriate data type?

-