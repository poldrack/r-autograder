# r-autograder
An automated grading system for Rmd files

This system was developed for http://psych10.github.io to provide the ability to automatically grade a large number of RMarkdown files.

The basic idea is that each submission is first knitted (to create plain R code), sourced, and then rendered.  
All of the variables in each submission are then compared to those generated from a master Rmd file.
Results are stored in a MongoDB database; thus, MongoDB must be installed and run in order for the code to work.

Currently this system has some Stanford-specific terminology, which I hope to remove in order to generalize the code.
There is a small set of tests, though they do not fully exercise all possible problems.

