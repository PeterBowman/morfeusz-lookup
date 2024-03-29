# morfeusz-lookup
API endpoint for a web service based on the [Morfeusz morphological analyser](http://morfeusz.sgjp.pl/doc/about/en) in conjunction with the [Concraft-pl morphosyntactic disambiguator](http://zil.ipipan.waw.pl/Concraft).

## Requirements
* Python 3.4+
* Morfeusz bindings for Python and related dependencies (see [downloads page](http://morfeusz.sgjp.pl/download/en))
* (optional) Concraft-pl executable and model (see [downloads page](http://zil.ipipan.waw.pl/Concraft) and [instructions](https://github.com/kawu/concraft-pl))
* see [requirements.txt](./requirements.txt)

## Usage
* make the `MORFEUSZ_DICT_PATH` environment variable point at the path that contains your SGJP binaries (`sgjp-a.dict`, `sgjp-d.dict`)
  * optional, Morfeusz will inspect default paths without this
* make `CONCRAFT_PL_MODEL` point at the .gz model file (e.g. `concraft-pl-model-SGJP-xxxxxxxx.gz`), and `CONCRAFT_PL_EXECUTABLE` at the `concraft-pl` executable
  * optional, leaving these unset will disable the morphosyntactic tagging and disambiguation feature
* configure and launch your uWSGI/Flask-based server
  * make sure `libmorfeusz2.so` can be found on runtime via `dlopen` option ([tips on uWSGI](https://wikitech.wikimedia.org/w/index.php?title=Help_talk:Toolforge/Web&oldid=1867866#Python_(uWSGI/k8s),_egg_files_and_binary_dependencies))

## Licensing
BSD 2-Clause, see [LICENSE.txt](./LICENSE.txt) for details.

## See also
* [WS:AUTOLINK](https://pl.wiktionary.org/wiki/Wikis%C5%82ownik:Narz%C4%99dzia/Linkowanie_automatyczne) at pl.wiktionary.org
* [Java implementation](https://github.com/PeterBowman/wikibot/blob/25dca7da0712b642ab0fb06218e60cd11c54f401/webapp/src/main/java/com/github/wikibot/webapp/MorfeuszLookup.java) (I'm not maintaining this anymore)
* https://morfeusz.toolforge.org/api
