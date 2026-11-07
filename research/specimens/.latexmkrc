# MiKTeX's bibtex ignores the BIBINPUTS that latexmk sets when it runs inside
# the output directory, so name the source directory explicitly.
use File::Spec;
$bibtex = 'bibtex -include-directory="' . File::Spec->rel2abs('.') . '" %O %S';
